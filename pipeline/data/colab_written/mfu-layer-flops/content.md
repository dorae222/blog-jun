# Layer별 FLOPs 분석과 프로파일링

## 소개

딥러닝 모델을 최적화하려면, 전체 연산량뿐 아니라 **각 레이어가 차지하는 연산 비중**을 파악하는 것이 핵심입니다. 어떤 레이어가 병목인지 알아야 효과적인 최적화 전략을 세울 수 있기 때문입니다.

이 튜토리얼에서는 다음을 다룹니다:
- 각 레이어별 FLOPs를 수식으로 직접 계산하는 방법
- THOP, FVCore 등 자동 프로파일링 도구 활용법
- 배치 크기에 따른 MFU 변화 분석
- Transformer 모델의 FLOPs 구조 분석
- Mixed Precision, Operator Fusion 등 최적화 기법 실습

---

## Part 1: 기초 개념 및 환경 설정

### FLOPs와 MFU 개념

- **FLOPs** (Floating Point Operations): 모델이 수행하는 부동소수점 연산의 총 개수 (소문자 s)
- **FLOPS** (Floating Point Operations Per Second): 초당 연산 수 (대문자 S)
- **MFU** = (실제 달성한 FLOPS) / (이론적 최대 FLOPS) x 100%

GPU가 이론적으로 낼 수 있는 최대 성능 대비, 실제 모델이 활용하는 비율을 나타냅니다.

### 필요 라이브러리 설치

> 아래 라이브러리들을 설치합니다:
> - `thop`: PyTorch 모델의 FLOPs와 파라미터 수를 간단히 계산
> - `fvcore`: Meta에서 제공하는 유틸리티로 FLOPs 분석(FlopCountAnalysis) 지원
> - `ptflops`: 입력 해상도 기준 FLOPs/파라미터 수 계산 (CNN 분석에 유용)
> - `torchprofile`: PyTorch 연산 그래프 기반 FLOPs 프로파일링

```python
# pip install torch torchvision thop fvcore ptflops torchprofile

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import time
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
```

### GPU 정보 확인

GPU의 이론적 최대 FLOPS를 확인합니다. 이 값은 MFU 계산의 기준이 됩니다.

```python
def get_gpu_info():
    """GPU 정보 및 이론적 최대 FLOPS 확인"""
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9

        # GPU별 이론적 TFLOPS (FP16 Tensor Core 기준)
        theoretical_tflops = {
            'A100': 312,
            'V100': 125,
            'T4': 65,
            'P100': 21.2,
        }

        print(f"GPU: {gpu_name}")
        print(f"Memory: {gpu_memory:.2f} GB")

        for gpu_model, tflops in theoretical_tflops.items():
            if gpu_model in gpu_name:
                print(f"Theoretical Peak Performance: {tflops} TFLOPS (FP16)")
                return tflops * 1e12

    return None

peak_flops = get_gpu_info()
```

<details><summary>Output</summary>

```
GPU: NVIDIA A100-SXM4-40GB
Memory: 42.47 GB
Theoretical Peak Performance: 312 TFLOPS (FP16)
```

</details>

---

## Part 2: 기본 Layer별 FLOPs 수동 계산

### FLOPs 계산 클래스 구현

각 레이어 유형별로 FLOPs를 직접 계산하는 클래스를 만듭니다.

```python
class FLOPsCalculator:
    """각 레이어별 FLOPs를 수동으로 계산하는 클래스"""

    @staticmethod
    def conv2d_flops(in_channels, out_channels, kernel_size, input_size, stride=1, padding=0):
        """Conv2D 레이어의 FLOPs 계산
        FLOPs = 2 x K^2 x C_in x C_out x H_out x W_out
        """
        if isinstance(kernel_size, int):
            kernel_size = (kernel_size, kernel_size)
        if isinstance(stride, int):
            stride = (stride, stride)
        if isinstance(padding, int):
            padding = (padding, padding)

        h_out = (input_size[0] + 2 * padding[0] - kernel_size[0]) // stride[0] + 1
        w_out = (input_size[1] + 2 * padding[1] - kernel_size[1]) // stride[1] + 1

        # 곱셈과 덧셈 연산
        multiplications = kernel_size[0] * kernel_size[1] * in_channels * out_channels * h_out * w_out
        additions = (kernel_size[0] * kernel_size[1] * in_channels - 1) * out_channels * h_out * w_out
        bias_additions = out_channels * h_out * w_out

        total_flops = multiplications + additions + bias_additions
        return total_flops, (h_out, w_out)

    @staticmethod
    def linear_flops(in_features, out_features, batch_size=1):
        """Linear 레이어의 FLOPs 계산
        FLOPs = 2 x in_features x out_features x batch_size
        """
        multiplications = in_features * out_features * batch_size
        additions = (in_features - 1) * out_features * batch_size
        bias_additions = out_features * batch_size
        return multiplications + additions + bias_additions

    @staticmethod
    def attention_flops(seq_len, d_model, num_heads, batch_size=1):
        """Multi-Head Attention의 FLOPs 계산
        Q, K, V projection + Attention scores + Output projection
        """
        d_head = d_model // num_heads

        # Q, K, V projections
        qkv_flops = 3 * FLOPsCalculator.linear_flops(d_model, d_model, batch_size * seq_len)

        # Attention scores: Q @ K^T
        attention_scores = 2 * batch_size * num_heads * seq_len * seq_len * d_head

        # Softmax (근사값)
        softmax_flops = batch_size * num_heads * seq_len * seq_len * 5

        # Attention @ V
        attention_output = 2 * batch_size * num_heads * seq_len * seq_len * d_head

        # Output projection
        output_projection = FLOPsCalculator.linear_flops(d_model, d_model, batch_size * seq_len)

        total_flops = qkv_flops + attention_scores + softmax_flops + attention_output + output_projection
        return total_flops
```

### 실제 CNN 모델에 적용

```python
class SimpleCNN(nn.Module):
    def __init__(self):
        super(SimpleCNN, self).__init__()
        self.conv1 = nn.Conv2d(3, 64, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(128, 256, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        self.fc1 = nn.Linear(256 * 4 * 4, 512)
        self.fc2 = nn.Linear(512, 10)

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = self.pool(F.relu(self.conv3(x)))
        x = x.view(-1, 256 * 4 * 4)
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return x

def calculate_model_flops(model, input_size=(32, 32)):
    """모델의 총 FLOPs 계산"""
    calculator = FLOPsCalculator()
    total_flops = 0
    layer_flops = {}

    # Conv1: 3 -> 64
    flops, output_size = calculator.conv2d_flops(3, 64, 3, input_size, padding=1)
    layer_flops['conv1'] = flops
    total_flops += flops
    output_size = (output_size[0]//2, output_size[1]//2)  # MaxPool

    # Conv2: 64 -> 128
    flops, output_size = calculator.conv2d_flops(64, 128, 3, output_size, padding=1)
    layer_flops['conv2'] = flops
    total_flops += flops
    output_size = (output_size[0]//2, output_size[1]//2)

    # Conv3: 128 -> 256
    flops, output_size = calculator.conv2d_flops(128, 256, 3, output_size, padding=1)
    layer_flops['conv3'] = flops
    total_flops += flops
    output_size = (output_size[0]//2, output_size[1]//2)

    # FC1: 256*4*4 -> 512
    flops = calculator.linear_flops(256 * 4 * 4, 512)
    layer_flops['fc1'] = flops
    total_flops += flops

    # FC2: 512 -> 10
    flops = calculator.linear_flops(512, 10)
    layer_flops['fc2'] = flops
    total_flops += flops

    return total_flops, layer_flops

model = SimpleCNN()
total_flops, layer_flops = calculate_model_flops(model)

print(f"Total FLOPs: {total_flops:,}")
print("\nLayer-wise FLOPs:")
for layer, flops in layer_flops.items():
    print(f"  {layer}: {flops:,} ({flops/total_flops*100:.2f}%)")
```

<details><summary>Output</summary>

```
Total FLOPs: 83,240,960

Layer-wise FLOPs:
  conv1: 3,538,944 (4.25%)
  conv2: 37,748,736 (45.35%)
  conv3: 37,748,736 (45.35%)
  fc1: 4,194,304 (5.04%)
  fc2: 10,240 (0.01%)
```

</details>

conv2와 conv3가 전체 연산량의 약 90%를 차지하는 것을 확인할 수 있습니다. 최적화를 할 때 이 레이어들에 집중해야 합니다.

---

## Part 3: 자동 FLOPs 프로파일링 도구 활용

### 3.1 THOP 라이브러리

THOP은 PyTorch 모델의 FLOPs와 파라미터 수를 간단하게 계산해주는 라이브러리입니다.

```python
from thop import profile, clever_format

def profile_with_thop(model, input_size=(1, 3, 32, 32)):
    """THOP을 사용한 FLOPs 프로파일링"""
    input_tensor = torch.randn(input_size)
    flops, params = profile(model, inputs=(input_tensor,))
    flops, params = clever_format([flops, params], "%.3f")
    print(f"Model FLOPs: {flops}")
    print(f"Model Parameters: {params}")
    return flops, params

model = SimpleCNN()
flops, params = profile_with_thop(model)
```

<details><summary>Output</summary>

```
Model FLOPs: 41.620M
Model Parameters: 2.474M
```

</details>

> THOP이 보고하는 값은 MACs 기준입니다. 수동 계산 결과(83.2M FLOPs)의 약 절반인 41.6M이 나온 것을 확인할 수 있습니다.

### 3.2 FVCore 라이브러리

FVCore는 Meta에서 제공하는 도구로, 레이어별/연산 타입별 상세 FLOPs 분석이 가능합니다.

```python
from fvcore.nn import FlopCountAnalysis, parameter_count

def profile_with_fvcore(model, input_size=(1, 3, 32, 32)):
    """FVCore를 사용한 상세 FLOPs 분석"""
    input_tensor = torch.randn(input_size)
    flops = FlopCountAnalysis(model, input_tensor)

    total_flops = flops.total()
    layer_flops = flops.by_module()
    op_flops = flops.by_operator()

    print(f"Total FLOPs: {total_flops:,}")
    print("\nFLOPs by Layer:")
    for name, flops_count in layer_flops.items():
        if flops_count > 0:
            print(f"  {name}: {flops_count:,}")

    print("\nFLOPs by Operation Type:")
    for op, flops_count in op_flops.items():
        if flops_count > 0:
            print(f"  {op}: {flops_count:,}")

    return total_flops, layer_flops, op_flops

total_flops, layer_flops, op_flops = profile_with_fvcore(model)
```

<details><summary>Output</summary>

```
Total FLOPs: 41,620,480

FLOPs by Layer:
  : 41,620,480
  conv1: 1,769,472
  conv2: 18,874,368
  conv3: 18,874,368
  fc1: 2,097,152
  fc2: 5,120

FLOPs by Operation Type:
  conv: 39,518,208
  linear: 2,102,272
```

</details>

FVCore도 MACs 기준 값을 반환합니다. 연산 타입별로 보면 conv 연산이 전체의 95% 이상을 차지합니다.

### 3.3 Custom Hook을 사용한 레이어별 분석

PyTorch의 forward hook을 활용하면 각 레이어의 입출력 shape과 FLOPs를 자동으로 기록할 수 있습니다.

```python
class LayerProfiler:
    """Hook을 사용한 레이어별 상세 프로파일링"""

    def __init__(self):
        self.layer_stats = {}

    def hook_fn(self, module, input, output, name):
        """각 레이어의 입출력 shape 및 FLOPs 기록"""
        input_shape = input[0].shape if isinstance(input, tuple) else input.shape
        output_shape = output.shape if hasattr(output, 'shape') else output[0].shape

        self.layer_stats[name] = {
            'input_shape': input_shape,
            'output_shape': output_shape,
            'module_type': module.__class__.__name__
        }

        if isinstance(module, nn.Conv2d):
            flops = self._conv_flops(module, output_shape)
            self.layer_stats[name]['flops'] = flops
        elif isinstance(module, nn.Linear):
            flops = self._linear_flops(module, output_shape)
            self.layer_stats[name]['flops'] = flops

    def _conv_flops(self, module, output_shape):
        batch_size = output_shape[0]
        out_h, out_w = output_shape[2], output_shape[3]
        kernel_h, kernel_w = module.kernel_size
        in_channels = module.in_channels
        out_channels = module.out_channels
        return 2 * batch_size * out_h * out_w * in_channels * out_channels * kernel_h * kernel_w

    def _linear_flops(self, module, output_shape):
        batch_size = output_shape[0]
        return 2 * batch_size * module.in_features * module.out_features

    def profile_model(self, model, input_tensor):
        """모델 전체 프로파일링"""
        handles = []
        for name, module in model.named_modules():
            if len(list(module.children())) == 0:  # Leaf 모듈만
                handle = module.register_forward_hook(
                    lambda m, i, o, n=name: self.hook_fn(m, i, o, n)
                )
                handles.append(handle)

        with torch.no_grad():
            _ = model(input_tensor)

        for handle in handles:
            handle.remove()

        return self.layer_stats

# 프로파일링 실행
profiler = LayerProfiler()
input_tensor = torch.randn(1, 3, 32, 32)
layer_stats = profiler.profile_model(model, input_tensor)

print("Layer-wise Statistics:")
for name, stats in layer_stats.items():
    print(f"\n{name} ({stats['module_type']}):")
    print(f"  Input shape: {stats['input_shape']}")
    print(f"  Output shape: {stats['output_shape']}")
    if 'flops' in stats:
        print(f"  FLOPs: {stats['flops']:,}")
```

<details><summary>Output</summary>

```
Layer-wise Statistics:

conv1 (Conv2d):
  Input shape: torch.Size([1, 3, 32, 32])
  Output shape: torch.Size([1, 64, 32, 32])
  FLOPs: 3,538,944

pool (MaxPool2d):
  Input shape: torch.Size([1, 256, 8, 8])
  Output shape: torch.Size([1, 256, 4, 4])

conv2 (Conv2d):
  Input shape: torch.Size([1, 64, 16, 16])
  Output shape: torch.Size([1, 128, 16, 16])
  FLOPs: 37,748,736

conv3 (Conv2d):
  Input shape: torch.Size([1, 128, 8, 8])
  Output shape: torch.Size([1, 256, 8, 8])
  FLOPs: 37,748,736

fc1 (Linear):
  Input shape: torch.Size([1, 4096])
  Output shape: torch.Size([1, 512])
  FLOPs: 4,194,304

fc2 (Linear):
  Input shape: torch.Size([1, 512])
  Output shape: torch.Size([1, 10])
  FLOPs: 10,240
```

</details>

Hook 기반 프로파일링의 장점은 모델 구조를 변경하지 않고도 각 레이어의 상세 정보를 자동으로 수집할 수 있다는 점입니다.

---

## Part 4: MFU 측정 및 배치 크기별 분석

### 4.1 처리량(Throughput) 측정

```python
def measure_throughput(model, batch_size, input_size=(3, 32, 32), num_iterations=100):
    """모델의 실제 처리량 측정"""
    model = model.cuda()
    model.eval()

    dummy_input = torch.randn(batch_size, *input_size).cuda()

    # Warm-up (중요!)
    for _ in range(10):
        _ = model(dummy_input)

    torch.cuda.synchronize()
    start_time = time.time()

    for _ in range(num_iterations):
        with torch.no_grad():
            _ = model(dummy_input)

    torch.cuda.synchronize()
    end_time = time.time()

    elapsed_time = end_time - start_time
    throughput = (batch_size * num_iterations) / elapsed_time
    return throughput, elapsed_time

batch_sizes = [1, 8, 16, 32, 64, 128]
throughputs = []

for bs in batch_sizes:
    try:
        throughput, elapsed_time = measure_throughput(model, bs)
        throughputs.append(throughput)
        print(f"Batch size {bs}: {throughput:.2f} samples/sec")
    except RuntimeError:
        print(f"Batch size {bs}: OOM")
        throughputs.append(0)
```

<details><summary>Output</summary>

```
Batch size 1: 2,279 samples/sec
Batch size 8: 18,718 samples/sec
Batch size 16: 37,526 samples/sec
Batch size 32: 69,799 samples/sec
Batch size 64: 144,646 samples/sec
Batch size 128: 194,946 samples/sec
```

</details>

배치 크기가 클수록 처리량이 증가하는 것을 확인할 수 있습니다. GPU의 병렬 연산 능력을 더 잘 활용하기 때문입니다.

### 4.2 배치 크기별 MFU 분석

```python
def calculate_mfu(model, batch_size, input_size=(3, 32, 32), peak_flops=None):
    """MFU 계산"""
    device = next(model.parameters()).device
    input_tensor = torch.randn(batch_size, *input_size).to(device)

    # FLOPs 계산 (fvcore 사용)
    from fvcore.nn import FlopCountAnalysis
    flops = FlopCountAnalysis(model, input_tensor).total()

    # 처리량 측정
    throughput, elapsed_time = measure_throughput(model, batch_size, input_size)

    # 실제 FLOPS 계산
    actual_flops_per_sec = flops * throughput / batch_size

    # MFU 계산
    mfu = (actual_flops_per_sec / peak_flops) * 100 if peak_flops else None

    return {
        'batch_size': batch_size,
        'model_flops': flops,
        'throughput': throughput,
        'actual_flops_per_sec': actual_flops_per_sec,
        'mfu_percentage': mfu,
    }
```

<details><summary>Output (배치 크기별 MFU)</summary>

```
Model FLOPs: 1,331,855,360
Batch 32: MFU = 0.94%
```

</details>

배치 크기가 커질수록 MFU가 증가하는 경향을 보입니다. 이는 GPU의 병렬 연산 유닛을 더 효율적으로 활용하기 때문입니다. 하지만 간단한 CNN 모델로는 MFU가 1% 미만으로, A100 같은 고성능 GPU의 연산 능력을 거의 활용하지 못하고 있음을 보여줍니다.

> 시각화 결과: 배치 크기가 1에서 64까지 증가함에 따라 MFU가 0.03%에서 약 0.95%까지 선형에 가깝게 증가하는 그래프가 생성됩니다.

---

## Part 5: Transformer 모델 FLOPs 분석

### 5.1 Transformer 블록 구현

```python
class TransformerBlock(nn.Module):
    def __init__(self, d_model=512, num_heads=8, d_ff=2048, dropout=0.1):
        super().__init__()
        self.attention = nn.MultiheadAttention(d_model, num_heads, dropout=dropout)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.feed_forward = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_ff, d_model)
        )
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        attn_output, _ = self.attention(x, x, x)
        x = self.norm1(x + self.dropout(attn_output))
        ff_output = self.feed_forward(x)
        x = self.norm2(x + self.dropout(ff_output))
        return x
```

### 시퀀스 길이별 FLOPs 분석

```python
def analyze_transformer_flops(seq_len=128, d_model=512, num_heads=8, d_ff=2048, batch_size=1):
    """Transformer 블록의 FLOPs 분석"""
    calculator = FLOPsCalculator()

    attention_flops = calculator.attention_flops(seq_len, d_model, num_heads, batch_size)
    ff_flops = (calculator.linear_flops(d_model, d_ff, batch_size * seq_len)
                + calculator.linear_flops(d_ff, d_model, batch_size * seq_len))
    ln_flops = 2 * 5 * d_model * seq_len * batch_size  # 근사값

    total_flops = attention_flops + ff_flops + ln_flops

    print(f"Transformer Block FLOPs Analysis:")
    print(f"  Attention: {attention_flops:,} ({attention_flops/total_flops*100:.1f}%)")
    print(f"  Feed-forward: {ff_flops:,} ({ff_flops/total_flops*100:.1f}%)")
    print(f"  LayerNorm: {ln_flops:,} ({ln_flops/total_flops*100:.1f}%)")
    print(f"  Total: {total_flops:,}")
    return total_flops

seq_lengths = [64, 128, 256, 512, 1024]
for seq_len in seq_lengths:
    flops = analyze_transformer_flops(seq_len=seq_len)
    print(f"Seq Length {seq_len}: {flops:,} FLOPs\n")
```

<details><summary>Output</summary>

```
Seq Length 64:    Attention 34.7%, Feed-forward 65.2% -> 411M FLOPs
Seq Length 128:   Attention 36.0%, Feed-forward 63.9% -> 840M FLOPs
Seq Length 256:   Attention 38.5%, Feed-forward 61.4% -> 1.75G FLOPs
Seq Length 512:   Attention 43.0%, Feed-forward 56.9% -> 3.77G FLOPs
Seq Length 1024:  Attention 50.2%, Feed-forward 49.7% -> 8.64G FLOPs
```

</details>

시퀀스 길이가 길어질수록 **Attention의 FLOPs 비중이 증가**합니다. 이는 Self-Attention의 시간 복잡도가 $O(n^2)$이기 때문입니다. 시퀀스 길이 1024에서는 Attention이 전체의 50%를 차지하게 됩니다.

### 5.2 실제 Transformer 모델 프로파일링

```python
class SimpleTransformer(nn.Module):
    def __init__(self, vocab_size=10000, d_model=512, num_heads=8,
                 num_layers=6, d_ff=2048, max_seq_len=512):
        super().__init__()
        self.d_model = d_model
        self.embedding = nn.Embedding(vocab_size, d_model)
        self.positional_encoding = nn.Parameter(torch.randn(1, max_seq_len, d_model))
        self.layers = nn.ModuleList([
            TransformerBlock(d_model, num_heads, d_ff)
            for _ in range(num_layers)
        ])
        self.ln_final = nn.LayerNorm(d_model)
        self.output_projection = nn.Linear(d_model, vocab_size)

    def forward(self, x):
        seq_len = x.size(1)
        x = self.embedding(x) * (self.d_model ** 0.5)
        x = x + self.positional_encoding[:, :seq_len, :]
        for layer in self.layers:
            x = layer(x)
        x = self.ln_final(x)
        x = self.output_projection(x)
        return x

transformer_model = SimpleTransformer(num_layers=6)
input_ids = torch.randint(0, 10000, (1, 128))

from thop import profile, clever_format
flops, params = profile(transformer_model, inputs=(input_ids,))
flops, params = clever_format([flops, params], "%.3f")
print(f"Transformer Model FLOPs: {flops}")
print(f"Transformer Model Parameters: {params}")
```

<details><summary>Output</summary>

```
Transformer Model FLOPs: 2.269G
Transformer Model Parameters: 17.742M
```

</details>

6-layer Transformer 모델은 약 2.27 GFLOPs의 연산량과 17.7M 파라미터를 가집니다.

---

## Part 6: 최적화 기법 실습

### 6.1 Mixed Precision (FP32 vs FP16)

Mixed Precision은 FP16을 사용하여 메모리와 연산 속도를 개선하는 기법입니다.

```python
from torch.amp import autocast

def compare_precision_performance(model, input_tensor, num_iterations=100):
    """FP32 vs FP16 성능 비교"""
    model = model.cuda()
    input_tensor = input_tensor.cuda()

    # FP32 측정
    torch.cuda.synchronize()
    start_fp32 = time.time()
    for _ in range(num_iterations):
        with torch.no_grad():
            _ = model(input_tensor)
    torch.cuda.synchronize()
    time_fp32 = time.time() - start_fp32

    # FP16 측정
    torch.cuda.synchronize()
    start_fp16 = time.time()
    for _ in range(num_iterations):
        with torch.no_grad():
            with autocast('cuda'):
                _ = model(input_tensor)
    torch.cuda.synchronize()
    time_fp16 = time.time() - start_fp16

    speedup = time_fp32 / time_fp16
    print(f"FP32 time: {time_fp32:.3f} sec")
    print(f"FP16 time: {time_fp16:.3f} sec")
    print(f"Speedup: {speedup:.2f}x")
    return time_fp32, time_fp16, speedup

model = SimpleCNN()
input_tensor = torch.randn(32, 3, 32, 32)
compare_precision_performance(model, input_tensor)
```

<details><summary>Output</summary>

```
FP32 time: 0.047 sec
FP16 time: 0.437 sec
Speedup: 0.11x
```

</details>

이 경우 FP16이 오히려 느린 결과가 나왔습니다. 이는 모델이 너무 작아서 autocast의 오버헤드가 실제 연산 절감보다 크기 때문입니다. **큰 모델에서는 FP16의 이점이 명확하게 나타납니다.**

### 6.2 모델 최적화: TorchScript

```python
import copy

def optimize_model_for_inference(model):
    """추론 최적화 기법 적용"""
    model.eval()
    example_input = torch.randn(1, 3, 32, 32)
    scripted_model = torch.jit.trace(model, example_input)

    if torch.cuda.is_available():
        model = model.cuda()
        scripted_model = scripted_model.cuda()
        torch.backends.cudnn.benchmark = True

    return scripted_model

original_model = SimpleCNN()
optimized_model = optimize_model_for_inference(copy.deepcopy(original_model))

# 성능 비교
input_tensor = torch.randn(32, 3, 32, 32).cuda()

start = time.time()
for _ in range(100):
    with torch.no_grad():
        _ = original_model.cuda()(input_tensor)
torch.cuda.synchronize()
original_time = time.time() - start

start = time.time()
for _ in range(100):
    with torch.no_grad():
        _ = optimized_model(input_tensor)
torch.cuda.synchronize()
optimized_time = time.time() - start

print(f"Original model: {original_time:.3f} sec")
print(f"Optimized model: {optimized_time:.3f} sec")
print(f"Speedup: {original_time/optimized_time:.2f}x")
```

<details><summary>Output</summary>

```
Original model: 0.062 sec
Optimized model: 0.041 sec
Speedup: 1.52x
```

</details>

TorchScript(JIT) 변환만으로도 약 1.5배의 속도 향상을 달성했습니다.

### 6.3 Operator Fusion의 영향

Conv + BatchNorm + ReLU를 분리해서 실행하는 것과 Sequential로 묶어서 실행하는 것의 성능을 비교합니다.

```python
class UnfusedBlock(nn.Module):
    """Fusion이 안된 블록"""
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, 3, padding=1)
        self.bn = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.conv(x)
        x = self.bn(x)
        x = self.relu(x)
        return x

class FusedBlock(nn.Module):
    """Fusion된 블록"""
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.conv_bn_relu = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, 3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        return self.conv_bn_relu(x)

unfused = UnfusedBlock(64, 128).cuda()
fused = FusedBlock(64, 128).cuda()
input_tensor = torch.randn(32, 64, 32, 32).cuda()

for name, module in [("Unfused", unfused), ("Fused", fused)]:
    torch.cuda.synchronize()
    start = time.time()
    for _ in range(1000):
        with torch.no_grad():
            _ = module(input_tensor)
    torch.cuda.synchronize()
    elapsed = time.time() - start
    print(f"{name}: {elapsed:.3f} sec")
```

<details><summary>Output</summary>

```
Unfused: 0.269 sec
Fused: 0.172 sec
```

</details>

Fused 블록이 약 36% 더 빠릅니다. Operator Fusion은 중간 결과를 메모리에 저장하지 않아 메모리 접근 횟수를 줄여주기 때문입니다.

---

## Part 7: 종합 프로파일링 도구

모델 정보, FLOPs, 메모리, 배치별 성능, MFU를 한번에 측정하는 종합 프로파일러를 구축합니다.

```python
class ComprehensiveProfiler:
    """종합적인 모델 프로파일링 도구"""

    def __init__(self, model, input_shape, device='cuda'):
        self.model = model.to(device)
        self.input_shape = input_shape
        self.device = device
        self.results = {}

    def profile_all(self, batch_sizes=[1, 8, 16, 32]):
        """전체 프로파일링 수행"""
        self._profile_model_info()
        self._profile_flops()
        self._profile_memory()
        self._profile_batch_performance(batch_sizes)
        self._calculate_mfu()
        return self.results

    def generate_report(self):
        """프로파일링 결과 리포트 생성"""
        # ... (모델 정보, FLOPs, 메모리, 성능, MFU 출력)
```

<details><summary>Output (프로파일링 리포트)</summary>

```
============================================================
MODEL PROFILING REPORT
============================================================

Model Information:
  Total Parameters: 2,473,610
  Model Size: 9.44 MB

Computational Complexity:
  Total FLOPs: 0.04 GFLOPs

Memory Usage:
  Peak Memory: 64.39 MB

Performance by Batch Size:
  Batch   1:  2,359 samples/sec, Latency: 0.42 ms
  Batch   4:  9,366 samples/sec, Latency: 0.43 ms
  Batch   8: 18,173 samples/sec, Latency: 0.44 ms
  Batch  16: 38,301 samples/sec, Latency: 0.42 ms
  Batch  32: 71,205 samples/sec, Latency: 0.45 ms

Model FLOPs Utilization (Peak: 312 TFLOPS):
  Batch   1: 0.03% (0.10 TFLOPS)
  Batch   4: 0.12% (0.39 TFLOPS)
  Batch   8: 0.24% (0.76 TFLOPS)
  Batch  16: 0.51% (1.59 TFLOPS)
  Batch  32: 0.95% (2.96 TFLOPS)
============================================================
```

</details>

> 시각화 대시보드: Throughput vs Batch Size, Inference Latency, MFU vs Batch Size, Model Stats를 4개의 서브플롯으로 구성한 대시보드를 생성합니다. MFU가 배치 크기에 비례하여 증가하지만, 이 간단한 CNN 모델로는 GPU 성능의 1%도 채 활용하지 못하는 것을 시각적으로 확인할 수 있습니다.

---

## 결론

이 튜토리얼에서 다룬 핵심 내용을 정리합니다:

1. **수동 FLOPs 계산**: Conv2d, Linear, Attention 각 레이어의 FLOPs를 수식으로 직접 계산할 수 있습니다.
2. **자동 프로파일링 도구**: THOP, FVCore, Custom Hook 등 다양한 도구로 모델의 FLOPs를 자동 측정할 수 있습니다.
3. **배치 크기와 MFU**: 배치 크기가 클수록 GPU를 더 효율적으로 활용하여 MFU가 증가합니다.
4. **Transformer FLOPs**: 시퀀스 길이가 길어질수록 Self-Attention의 $O(n^2)$ 복잡도로 인해 Attention의 FLOPs 비중이 증가합니다.
5. **최적화 기법**: TorchScript(1.52x), Operator Fusion(1.56x) 등의 기법으로 성능을 개선할 수 있습니다. Mixed Precision은 충분히 큰 모델에서 효과적입니다.

다음 튜토리얼에서는 이러한 분석 결과를 바탕으로 실제 MFU 최적화 프로젝트를 수행해보겠습니다.