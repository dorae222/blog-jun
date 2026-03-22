---
title: "LoRA: Low-Rank Adaptation of Large Language Models"
slug: lora
category: llm
tags: []
status: published
post_type: paper_review
quality_score: 0.0
created_at: "2026-03-17T21:24:56.400190+00:00"
architecture_entry: lora
---

## 개요

GPT-3(175B)와 같은 대규모 언어 모델을 특정 태스크에 맞게 파인튜닝하려면 전체 파라미터를 업데이트해야 하므로 막대한 GPU 메모리와 저장 공간이 필요합니다. 프롬프트 튜닝, 어댑터 등 기존 PEFT 방법들은 파라미터를 줄이지만 추론 지연 증가, 훈련 불안정 등의 한계가 있었습니다.

LoRA(Low-Rank Adaptation)는 가중치 행렬의 변화량($\Delta W$)이 본질적으로 낮은 랭크(intrinsic low rank)를 가진다는 가설을 기반으로, 두 개의 작은 행렬 곱으로 변화량을 근사합니다.

## 배경 및 문제

### 전체 파인튜닝의 문제

모델 파라미터 $\Theta_0$를 가진 사전학습 모델을 태스크 데이터로 파인튜닝할 때:

$$\max_{\Theta} \sum_{(x,y) \in \mathcal{Z}} \sum_{t=1}^{|y|} \log P_\Theta(y_t | x, y_{<t})$$

전체 파인튜닝은 $|\Delta\Theta| = |\Theta_0|$, 즉 175B 파라미터 모델의 경우 175B개의 파라미터를 모두 업데이트합니다. 이는 GPU 메모리 요구량, 저장 비용, 배포 복잡도 측면에서 매우 비효율적입니다.

### 내재적 저랭크 가설

Aghajanyan et al.(2020)의 연구에서 사전학습 모델의 내재적 차원(intrinsic dimension)이 낮다는 사실이 밝혀졌습니다. LoRA는 이를 확장하여 파인튜닝 시 가중치 변화량 $\Delta W$도 낮은 랭크를 가진다고 가정합니다.

## 핵심 아이디어

LoRA의 핵심 수식:

$$h = W_0 x + \Delta W x = W_0 x + BA x$$

여기서:
- $W_0 \in \mathbb{R}^{d \times k}$: 동결된 사전학습 가중치
- $B \in \mathbb{R}^{d \times r}$: 학습 가능한 저랭크 행렬 (0으로 초기화)
- $A \in \mathbb{R}^{r \times k}$: 학습 가능한 저랭크 행렬 (가우시안 초기화)
- $r \ll \min(d, k)$: 랭크 하이퍼파라미터 (보통 4, 8, 16)

학습 초기에 $BA = 0$이 되도록 $B=0$으로 초기화하여 학습 시작 시 동작이 원본 모델과 동일합니다.

### 파라미터 수 비교

$d = k = 4096$, $r = 8$인 경우:
- 전체 파인튜닝: $4096 \times 4096 = 16,777,216$개 파라미터
- LoRA: $(4096 \times 8) + (8 \times 4096) = 65,536$개 파라미터
- 감소율: **256배 감소** (단일 레이어 기준)

### 스케일링 팩터

실제 구현에서는 $\Delta W = \frac{\alpha}{r} BA$로 스케일링합니다. $\alpha$는 상수(보통 $r$과 동일값 설정)이며, 이를 통해 랭크 $r$ 변경 시 러닝레이트를 재조정할 필요가 없어집니다.

## 방법론

### 어디에 적용할 것인가

LoRA 논문은 트랜스포머의 셀프 어텐션 레이어의 네 가지 가중치 행렬 $W_q, W_k, W_v, W_o$와 FFN 레이어에 적용하는 것을 실험했습니다.

실험 결과: 동일한 파라미터 예산에서 **$W_q$와 $W_v$에만 적용**하는 것이 $W_q$에만 적용하거나 모든 행렬에 낮은 랭크로 적용하는 것보다 일반적으로 성능이 좋았습니다.

### 추론 시 가중치 병합

배포 시 $W_0$와 $BA$를 미리 합산하여 원본 모델과 동일한 구조로 배포할 수 있습니다:

$$W = W_0 + BA$$

이로 인해 **추론 시 추가 지연이 전혀 없습니다**. 어댑터(Adapter) 방법과 비교하여 가장 큰 실용적 장점입니다.

### 다중 태스크 전환

LoRA는 태스크별로 $B$, $A$ 행렬만 저장하면 되므로:
- 기반 모델(동결): 1회 GPU 로드
- 태스크 전환: $BA$ 행렬만 교체 (수 MB ~ 수십 MB)
- vs 전체 파인튜닝: 태스크마다 수백 GB 모델 저장

## 실험 결과

### GPT-3 175B 자연어 생성 태스크

| 방법 | 학습 파라미터 | E2E BLEU | WebNLG BLEU | DART BLEU |
|------|------------|---------|------------|----------|
| FT (전체) | 175B | 68.2 | 46.2 | 46.0 |
| Adapter(H=256) | 40.1M | 66.3 | 45.9 | 45.2 |
| LoRA (r=4) | 4.7M | **70.4** | **46.8** | **47.1** |

LoRA는 전체 파인튜닝보다 파라미터를 37,000배 줄이면서 성능이 오히려 향상되는 결과를 보였습니다.

### RoBERTa, DeBERTa GLUE 벤치마크

| 방법 | 파라미터 | GLUE 평균 |
|------|---------|--------|
| FT | 355M | 90.2 |
| Adapter | 0.9M | 89.9 |
| LoRA (r=8) | 0.8M | **90.6** |

### 랭크 민감도 분석

| 랭크 r | 학습 파라미터 | GPT-3 WikiSQL 성능 |
|--------|------------|------------------|
| 1 | 0.15M | 70.4% |
| 2 | 0.30M | 72.3% |
| 4 | 0.59M | 73.4% |
| 8 | 1.18M | 73.8% |
| 64 | 9.44M | 73.9% |

$r=4$ 이상에서 성능 포화 경향이 나타나, 매우 낮은 랭크로도 충분한 표현력을 가짐을 보입니다.

## 의의 및 한계

### 의의

- **파라미터 효율성**: GPT-3 175B 기준 학습 파라미터를 10,000배 이상 감소 (175B → 수 MB)
- **추론 지연 없음**: 가중치 병합으로 어댑터 방법의 추론 지연 문제를 해결
- **범용성**: Stable Diffusion, 코드 생성, 의료 AI 등 다양한 도메인에 폭넓게 적용
- **후속 기법의 토대**: QLoRA, DoRA, LoftQ, AdaLoRA 등 수많은 변형 기법의 기반
- **생태계**: HuggingFace PEFT 라이브러리에 공식 지원

### 한계

- 최적의 랭크 $r$과 적용 레이어는 태스크별로 다르므로 탐색이 필요
- 전체 파인튜닝에 비해 매우 다른 도메인(out-of-domain)에서는 여전히 성능 격차 존재
- 낮은 랭크 가설이 성립하지 않는 태스크(예: 근본적 다른 지식 습득)에는 효과가 제한적

## 코드 예제

### LoRA 구현 및 PEFT 라이브러리 활용 (PyTorch)

```python
import torch
import torch.nn as nn
import math

class LoRALayer(nn.Module):
    """LoRA: 가중치 행렬의 변화량을 저랭크 행렬 BA로 근사.
    W = W0 + (alpha/r) * B @ A
    W0는 동결, A와 B만 학습.
    """
    def __init__(self, in_features, out_features, rank=4, alpha=16, dropout=0.0):
        super().__init__()
        self.rank = rank
        self.alpha = alpha
        self.scaling = alpha / rank  # 논문의 α/r 스케일링

        # LoRA 행렬 A (가우시안 초기화), B (0으로 초기화)
        self.lora_A = nn.Linear(in_features, rank, bias=False)
        self.lora_B = nn.Linear(rank, out_features, bias=False)
        nn.init.kaiming_uniform_(self.lora_A.weight, a=math.sqrt(5))
        nn.init.zeros_(self.lora_B.weight)  # 초기에는 ΔW=0

        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        # ΔW @ x = B(A(x)) * scaling
        return self.lora_B(self.lora_A(self.dropout(x))) * self.scaling

class LinearWithLoRA(nn.Module):
    """기존 Linear 레이어에 LoRA를 추가."""
    def __init__(self, linear: nn.Linear, rank=4, alpha=16):
        super().__init__()
        self.linear = linear
        self.lora = LoRALayer(linear.in_features, linear.out_features, rank, alpha)
        # 기존 가중치 동결
        for param in self.linear.parameters():
            param.requires_grad = False

    def forward(self, x):
        return self.linear(x) + self.lora(x)  # W0x + BAx

    def merge_weights(self):
        """추론 최적화: LoRA 가중치를 원래 가중치에 병합 (지연 없이 추론)."""
        with torch.no_grad():
            delta_W = self.lora.lora_B.weight @ self.lora.lora_A.weight * self.lora.scaling
            self.linear.weight.data += delta_W
            # 병합 후 LoRA 레이어 제거 가능

# 트랜스포머 모델에 LoRA 적용 예시
class SimpleTransformer(nn.Module):
    def __init__(self, d_model=512, num_heads=8):
        super().__init__()
        self.Wq = nn.Linear(d_model, d_model, bias=False)
        self.Wv = nn.Linear(d_model, d_model, bias=False)
        # ... 나머지 레이어

def apply_lora(model, rank=4, alpha=16, target_modules=['Wq', 'Wv']):
    """모델의 특정 레이어에 LoRA 적용."""
    for name, module in model.named_modules():
        if any(target in name for target in target_modules):
            if isinstance(module, nn.Linear):
                parent = model
                parts = name.split('.')
                for part in parts[:-1]:
                    parent = getattr(parent, part)
                setattr(parent, parts[-1], LinearWithLoRA(module, rank, alpha))
    return model

# 파라미터 수 비교
model = SimpleTransformer(d_model=512)
total_params = sum(p.numel() for p in model.parameters())
print(f"원래 모델 파라미터: {total_params:,}")

lora_model = apply_lora(model, rank=4)
trainable = sum(p.numel() for p in lora_model.parameters() if p.requires_grad)
print(f"LoRA 학습 파라미터: {trainable:,} ({trainable/total_params*100:.2f}%)")

# 실제 사용: Hugging Face PEFT 라이브러리
from peft import LoraConfig, get_peft_model  # pip install peft
from transformers import AutoModelForCausalLM

lora_config = LoraConfig(
    r=16,          # 랭크
    lora_alpha=32, # α 스케일링
    target_modules=["q_proj", "v_proj"],  # 어텐션 Q, V에만 적용
    lora_dropout=0.05,
    bias="none",
)
# model = get_peft_model(AutoModelForCausalLM.from_pretrained('...'), lora_config)
```