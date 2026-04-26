<!-- infographic-hero -->
![QLoRA: Efficient Finetuning of Quantized LLMs 핵심 요약](figures/infographic.svg)

*Figure: QLoRA: Efficient Finetuning of Quantized LLMs 한 장 요약 인포그래픽*

## 개요

대규모 언어 모델(LLM)의 파인튜닝은 모델 성능을 특정 태스크에 최적화하는 핵심 단계이지만, 모델 크기가 커짐에 따라 필요한 GPU 메모리가 급격히 증가하는 문제에 직면합니다. [[lora|LoRA]]가 학습 가능한 파라미터 수를 획기적으로 줄였음에도 불구하고, 사전학습 모델의 가중치 자체를 FP16 또는 BF16으로 GPU에 로드해야 하므로 여전히 막대한 메모리가 필요합니다. 예를 들어, LLaMA-65B 모델을 FP16으로 로드하는 것만으로도 약 130GB의 GPU 메모리가 소요되며, 여기에 그래디언트와 옵티마이저 상태까지 포함하면 실질적으로 수백 GB의 메모리가 요구됩니다.

QLoRA(Quantized Low-Rank Adaptation)는 이러한 메모리 병목을 근본적으로 해결하기 위해 Tim Dettmers 등 워싱턴 대학교 연구팀이 제안한 방법론입니다. 핵심 아이디어는 사전학습된 모델의 가중치를 4비트로 양자화하여 메모리 사용량을 대폭 줄이고, 양자화된 모델 위에 BF16 정밀도의 LoRA 어댑터만 학습하는 것입니다. 이를 위해 세 가지 새로운 기술을 도입합니다: (1) 정보 이론적으로 최적인 4-bit NormalFloat(NF4) 데이터 타입, (2) 양자화 상수 자체를 다시 양자화하는 이중 양자화(Double Quantization), (3) 메모리 스파이크를 자동으로 처리하는 페이지드 옵티마이저(Paged Optimizers). 이 세 가지 기술의 조합을 통해 QLoRA는 단일 48GB A100 GPU에서 65B 파라미터 모델의 파인튜닝을 가능하게 하면서도, 16비트 전체 파인튜닝과 사실상 동일한 성능을 달성합니다.

다음 그림은 QLoRA의 전체 아키텍처를 요약합니다. 사전학습 가중치 $W_0$를 NF4로 양자화하여 동결하고, 저랭크 행렬 $B \cdot A$로 구성된 LoRA 어댑터만 학습하는 구조입니다.

![QLoRA 전체 아키텍처 ( NF4 양자화된 사전학습 가중치 위에 학습 가능한 LoRA 어댑터를 결합하는 구조](figures/architecture.png)
*QLoRA 아키텍처 개요: 사전학습 가중치 $W_0$는 NF4로 양자화되어 동결(frozen)되고, 저랭크 행렬 $B \cdot A$만 BF16으로 학습된다. Full Fine-tuning이 100%의 파라미터를 16비트로 학습하는 것과 달리, QLoRA는 전체의 약 0.01%만 학습하면서 4비트 양자화 모델 위에서 동작하여 단일 48GB GPU에서 65B 모델 파인튜닝을 실현한다.*

QLoRA로 학습된 Guanaco 모델 패밀리는 Vicuna 벤치마크에서 ChatGPT 성능의 99.3%에 도달하며, 이전까지 수십 개의 GPU가 필요했던 대규모 모델 파인튜닝을 단일 소비자용 GPU에서도 수행할 수 있는 길을 열었습니다. 이 논문은 NeurIPS 2023에 채택되었으며, LLM 파인튜닝의 민주화에 결정적인 기여를 한 연구로 평가받고 있습니다.

## 배경 및 문제

### 기존 양자화의 한계

모델 양자화는 가중치의 비트 정밀도를 낮추어 메모리를 절약하는 기법으로, 추론(inference) 단계에서는 이미 널리 활용되고 있습니다. INT8 양자화의 경우 FP16 대비 메모리를 절반으로 줄이면서도 추론 정확도를 대체로 유지할 수 있습니다. 그러나 학습(training) 단계에서의 양자화는 근본적으로 다른 도전을 수반합니다.

학습 시에는 역전파(backpropagation)를 통해 그래디언트가 모델의 모든 레이어를 거쳐 전파됩니다. 양자화된 가중치에서 발생하는 양자화 오차(quantization error)가 이 과정에서 증폭되어 학습을 불안정하게 만들 수 있습니다. 구체적으로, 양자화 함수 $Q(\cdot)$는 비연속적(discontinuous)이므로 미분 불가능하며, 이로 인해 정확한 그래디언트 계산이 어렵습니다. 기존의 양자화 학습(Quantization-Aware Training, QAT) 방법들은 이 문제를 STE(Straight-Through Estimator) 등으로 우회하지만, 대규모 LLM에 적용하기에는 학습 비용이 과도하거나 수렴이 불안정한 한계가 있었습니다.

또한 기존의 4비트 양자화 방법인 INT4는 값을 균등 간격(uniform spacing)으로 분할합니다. 그러나 신경망 가중치는 대체로 정규분포를 따르며, 0 근처에 대부분의 값이 집중되어 있습니다. 균등 간격 양자화는 이러한 분포 특성을 무시하므로, 밀도가 높은 0 근처 영역에서의 표현력이 부족하고 밀도가 낮은 꼬리(tail) 영역에서는 불필요하게 많은 격자점을 할당하는 비효율이 발생합니다.

### 메모리 구성 분석

LLM 파인튜닝 시 GPU 메모리는 크게 네 가지 요소로 구성됩니다:

1. **모델 가중치**: 파라미터 수 $\times$ 바이트/파라미터 (FP16: 2B, FP32: 4B, INT4: 0.5B)
2. **그래디언트**: 학습 가능한 파라미터에 대한 그래디언트 저장
3. **옵티마이저 상태**: Adam의 경우 파라미터당 1차 모멘트($m$)와 2차 모멘트($v$) 각각 FP32
4. **활성화 메모리**: 순전파 중간 결과물 (배치 크기와 시퀀스 길이에 비례)

아래 그림은 LLaMA 모델 크기별 QLoRA 파인튜닝 시 GPU 메모리 구성을 보여줍니다. 기본 모델 가중치(파란색)가 전체 메모리의 대부분을 차지하며, 어댑터나 그래디언트의 비중은 미미합니다. 이는 모델 가중치의 양자화가 메모리 절감의 핵심 레버임을 시사합니다.

![LLaMA 모델 크기별(7B~65B) QLoRA 파인튜닝 시 GPU 메모리 구성 분석](figures/fig_6.png)
*LLaMA 7B~65B 모델의 QLoRA 파인튜닝 시 GPU 메모리 구성 비율. 7B 모델은 6.9GB, 65B 모델은 45.0GB로, 기본 모델 가중치(Model)가 메모리의 절대적 비중을 차지한다. NF4 양자화는 바로 이 가장 큰 구성 요소를 압축하여 메모리를 절감한다.*

다음 표는 모델 크기별 가중치 로딩만을 위한 메모리 요구량을 정밀도별로 비교합니다:

| 모델 크기 | FP32 메모리 | FP16/BF16 메모리 | INT8 메모리 | NF4 메모리 |
|---------|-----------|----------------|-----------|----------|
| 7B | ~28 GB | ~14 GB | ~7 GB | ~3.5 GB |
| 13B | ~52 GB | ~26 GB | ~13 GB | ~6.5 GB |
| 33B | ~132 GB | ~66 GB | ~33 GB | ~16.5 GB |
| 65B | ~260 GB | ~130 GB | ~65 GB | ~33 GB |

전체 파인튜닝(Full Fine-tuning)의 경우, 가중치 외에도 그래디언트(FP16/BF16)와 Adam 옵티마이저 상태(FP32, 파라미터당 8바이트)가 추가로 필요합니다. LLaMA-65B를 FP16으로 전체 파인튜닝하려면 가중치 130GB + 그래디언트 130GB + 옵티마이저 상태 520GB로 총 약 780GB의 GPU 메모리가 필요하여, A100 80GB GPU 10장 이상이 요구됩니다.

QLoRA는 모델 가중치를 NF4로 양자화하고(~33GB), LoRA 어댑터만 학습(전체 파라미터의 0.1~1%)하므로, 학습 가능한 파라미터에 대한 그래디언트와 옵티마이저 상태가 극히 적어집니다. 결과적으로 65B 모델의 파인튜닝을 단일 48GB GPU에서 수행할 수 있습니다.

### QLoRA 이전의 시도들

QLoRA 이전에도 양자화와 파인튜닝을 결합하려는 시도가 있었습니다. LLM.int8()(Dettmers et al., 2022)은 INT8 혼합 정밀도 분해를 통해 추론 메모리를 절반으로 줄였지만 학습에는 적용되지 않았습니다. GPTQ(Frantar et al., 2022)는 레이어별 양자화를 통해 고품질 4비트 양자화를 달성했으나, 역시 추론 전용이었습니다. QLoRA는 이러한 양자화 기법들의 발전을 학습 단계로 확장한 최초의 실용적 프레임워크입니다.

## 핵심 아이디어

QLoRA의 핵심은 세 가지 기술의 유기적 결합에 있습니다. 각 기술이 독립적으로도 의미가 있지만, 함께 적용될 때 시너지를 발휘하여 메모리 효율과 성능 보존의 최적 균형점을 달성합니다.

### 4-bit NormalFloat (NF4)

NF4는 QLoRA의 가장 핵심적인 기여 중 하나로, 정보 이론적으로 최적인 4비트 양자화 데이터 타입입니다. 핵심 통찰은 사전학습된 신경망의 가중치가 평균 0, 표준편차 $\sigma$인 정규분포 $\mathcal{N}(0, \sigma^2)$를 따른다는 경험적 사실에 기반합니다.

기존 INT4 양자화는 값의 범위를 16개의 균등한 구간으로 나누지만, 정규분포 데이터에서는 0 근처에 값이 밀집되어 있으므로 이 영역에서의 표현 정밀도가 부족합니다. NF4는 이를 해결하기 위해 **동등 확률 구간(equal quantile)** 기반의 비균등 격자(non-uniform grid)를 사용합니다.

NF4 양자화 절차는 다음과 같습니다:

**1단계 - 정규화**: 블록 크기 $B$(일반적으로 64)의 가중치 블록을 절대 최대값으로 정규화합니다.

$$w_i^{\text{norm}} = \frac{w_i}{\text{absmax}(W_B)} = \frac{w_i}{\max_{j \in B}(|w_j|)}$$

정규화 후 모든 값은 $[-1, 1]$ 범위에 위치하며, 이론적으로 표준정규분포 $\mathcal{N}(0, 1)$에 근사합니다.

**2단계 - 최적 격자점 계산**: 표준정규분포의 누적분포함수(CDF)의 역함수인 분위수 함수 $Q_X^{-1}$를 사용하여 $2^k = 16$개의 격자점을 계산합니다. 각 격자점 $q_i$는 연속된 두 분위수의 중간값으로 결정됩니다:

$$q_i = \frac{1}{2}\left(Q_X^{-1}\left(\frac{i}{2^k + 1}\right) + Q_X^{-1}\left(\frac{i+1}{2^k + 1}\right)\right), \quad i = 0, 1, \ldots, 2^k - 1$$

여기서 $Q_X^{-1}$는 표준정규분포 $\mathcal{N}(0,1)$의 분위수 함수이고, $k=4$입니다. 이렇게 계산된 16개의 격자점은 정규분포의 확률 밀도가 높은 0 근처에 촘촘하게 배치되고, 밀도가 낮은 꼬리 부분에는 성기게 배치됩니다.

**3단계 - 양자화 매핑**: 각 정규화된 가중치를 가장 가까운 격자점으로 매핑합니다:

$$\hat{w}_i = \arg\min_{q \in \{q_0, \ldots, q_{15}\}} |w_i^{\text{norm}} - q|$$

이 과정의 결과로 각 가중치는 4비트 인덱스(0~15)로 표현됩니다.

**NF4 vs INT4 양자화 오차 비교**: NF4는 동일한 4비트를 사용하면서도 정규분포 데이터에 대해 INT4보다 현저히 낮은 양자화 오차를 보입니다. 논문에서는 NF4가 정규분포 입력에 대해 정보 이론적으로 최적(information-theoretically optimal)임을 증명합니다. 즉, 4비트로 표현할 수 있는 한계 내에서 기대 양자화 오차를 최소화합니다:

$$E[|X - Q(X)|^2] \leq E[|X - Q'(X)|^2], \quad \forall Q' \text{ (4-bit quantizer)}$$

아래 그림은 이러한 이론적 우위가 실제 모델 성능으로 어떻게 이어지는지를 보여줍니다. 4비트 LLaMA 모델에서 NFloat(NF4)는 동일한 총 모델 비트 수 조건에서 Float(FP4)보다 일관되게 높은 제로샷 정확도를 달성하며, 이중 양자화(DQ)를 추가 적용하면 메모리 오버헤드를 더 줄이면서도 성능을 유지합니다.

![4비트 LLaMA 모델에서 총 모델 비트 수에 따른 평균 제로샷 정확도 비교](figures/fig_3.png)
*4비트 LLaMA 모델의 총 모델 비트 수 대비 평균 제로샷 정확도. NFloat(NF4, 주황)는 Float(FP4, 초록) 대비 모든 모델 크기에서 우위를 보이며, 이중 양자화(NFloat+DQ, 파랑)를 적용해도 정확도 손실 없이 비트 수(메모리)를 추가 절감할 수 있다.*

### 이중 양자화 (Double Quantization)

블록별 양자화(block-wise quantization)에서는 각 블록마다 스케일 팩터(양자화 상수)를 FP32로 저장해야 합니다. 블록 크기 $B=64$를 사용할 경우, 스케일 팩터로 인한 추가 메모리 오버헤드는 다음과 같이 계산됩니다:

$$\text{오버헤드}_{\text{단일}} = \frac{32 \text{ bits}}{B} = \frac{32}{64} = 0.5 \text{ bits/param}$$

65B 모델 기준으로 $65 \times 10^9 \times 0.5 / 8 \approx 4.04$ GB의 추가 메모리가 소요됩니다. 이는 무시할 수 없는 양입니다.

이중 양자화는 이 스케일 팩터들을 다시 양자화합니다. 첫 번째 양자화의 블록 크기 $B_1=64$에서 생성된 FP32 스케일 팩터들을 모아 두 번째 양자화의 블록 크기 $B_2=256$으로 그룹화한 뒤 INT8로 양자화합니다:

$$c_1^{\text{FP32}} \xrightarrow{\text{2nd quant}} c_1^{\text{INT8}} + c_2^{\text{FP32}}$$

이중 양자화 후의 메모리 오버헤드는 다음과 같습니다:

$$\text{오버헤드}_{\text{이중}} = \frac{8}{B_1} + \frac{32}{B_1 \times B_2} = \frac{8}{64} + \frac{32}{64 \times 256} = 0.125 + 0.00195 \approx 0.127 \text{ bits/param}$$

따라서 이중 양자화를 통한 메모리 절감량은 다음과 같습니다:

$$\Delta = 0.5 - 0.127 = 0.373 \text{ bits/param}$$

65B 모델 기준으로 $65 \times 10^9 \times 0.373 / 8 \approx 3.03$ GB의 메모리를 추가 절약할 수 있습니다. 이중 양자화는 양자화 품질에 거의 영향을 주지 않으면서도 상당한 메모리 절감을 제공하는 실용적 기법입니다.

### 페이지드 옵티마이저 (Paged Optimizers)

Adam 옵티마이저는 각 학습 가능한 파라미터에 대해 1차 모멘트($m_t$)와 2차 모멘트($v_t$)를 FP32로 유지합니다:

$$m_t = \beta_1 m_{t-1} + (1-\beta_1) g_t, \quad v_t = \beta_2 v_{t-1} + (1-\beta_2) g_t^2$$

QLoRA에서는 LoRA 파라미터만 학습하므로 옵티마이저 상태 자체는 크지 않지만, 긴 시퀀스를 처리할 때 활성화 메모리가 급증하여 일시적으로 GPU 메모리가 부족해지는 메모리 스파이크(memory spike)가 발생할 수 있습니다.

페이지드 옵티마이저는 NVIDIA의 통합 메모리(Unified Memory) 기능을 활용하여 이 문제를 해결합니다. 핵심 메커니즘은 다음과 같습니다:

- GPU 메모리가 부족해지면 옵티마이저 상태 페이지를 자동으로 CPU RAM으로 퇴거(evict)
- 옵티마이저 업데이트가 필요한 시점에 해당 페이지를 다시 GPU로 불러옴
- 이 과정은 CUDA의 `cudaMallocManaged` API를 통해 투명하게 처리됨
- 정상 상태에서는 모든 데이터가 GPU에 상주하므로 성능 저하가 없음
- 메모리 스파이크 발생 시에만 페이징이 활성화되어 OOM(Out of Memory)을 방지

이 방식은 운영체제의 가상 메모리 페이징과 유사한 원리로, GPU 메모리를 가상화하여 물리적 한계를 넘어서는 모델 학습을 가능하게 합니다.

## 방법론

### QLoRA 학습 프로세스

다음 그림은 전체 파인튜닝(Full Finetuning), LoRA, QLoRA 세 가지 접근 방식의 메모리 구조를 직접 비교합니다. 전체 파인튜닝은 모든 파라미터에 대한 32비트 옵티마이저 상태를 유지해야 하고, LoRA는 16비트 모델 위에 어댑터만 학습합니다. QLoRA는 여기서 한 단계 더 나아가 기본 모델을 4비트로 압축하고, 옵티마이저 상태의 CPU 페이징까지 지원하여 메모리 효율을 극대화합니다.

![Full Finetuning, LoRA, QLoRA의 메모리 구성 비교 다이어그램](figures/fig_1.png)
*Full Finetuning, LoRA, QLoRA의 메모리 구성 비교. Full Finetuning은 32비트 옵티마이저 상태와 16비트 모델 전체를 메모리에 유지해야 한다. LoRA는 어댑터만 학습하여 옵티마이저 상태를 줄이지만 모델은 여전히 16비트이다. QLoRA는 모델을 4비트로 양자화하고, 옵티마이저 상태를 필요 시 CPU로 페이징하여 단일 GPU 학습을 실현한다.*

QLoRA의 전체 학습 프로세스는 다음과 같은 단계로 구성됩니다:

**1단계 - 모델 로드 및 양자화**: 사전학습된 모델의 가중치를 NF4 4비트로 양자화하여 GPU에 로드합니다. 이 과정에서 이중 양자화도 함께 적용되어 양자화 상수의 메모리도 최소화됩니다.

**2단계 - LoRA 어댑터 삽입**: 양자화된 모델의 각 Transformer 레이어에 BF16 정밀도의 LoRA 어댑터를 삽입합니다. 일반적으로 어텐션 레이어의 $W_q$, $W_k$, $W_v$, $W_o$와 FFN 레이어의 $W_{\text{gate}}$, $W_{\text{up}}$, $W_{\text{down}}$에 어댑터를 적용합니다.

**3단계 - 순전파**: 입력 데이터가 모델을 통과할 때, NF4 가중치는 실시간으로 BF16으로 역양자화(dequantize)되어 연산에 사용됩니다. LoRA 어댑터의 출력은 역양자화된 가중치의 출력에 더해집니다:

$$Y = X \cdot \text{dequant}(W^{\text{NF4}}) + X \cdot B \cdot A$$

여기서 $B \in \mathbb{R}^{d \times r}$, $A \in \mathbb{R}^{r \times d}$는 LoRA의 저랭크 행렬이고, $r \ll d$는 LoRA의 랭크입니다.

**4단계 - 역전파 및 그래디언트 계산**: 손실 함수에 대한 그래디언트가 역전파됩니다. 이 과정에서 NF4 가중치는 다시 BF16으로 역양자화되어 그래디언트 계산에 사용되지만, NF4 가중치 자체는 업데이트되지 않습니다(동결). 그래디언트는 LoRA 파라미터 $A$, $B$에 대해서만 계산됩니다:

$$\frac{\partial \mathcal{L}}{\partial A} = B^T \cdot X^T \cdot \frac{\partial \mathcal{L}}{\partial Y}, \quad \frac{\partial \mathcal{L}}{\partial B} = X^T \cdot \frac{\partial \mathcal{L}}{\partial Y} \cdot A^T$$

**5단계 - 파라미터 업데이트**: 페이지드 Adam 옵티마이저를 사용하여 LoRA 파라미터만 업데이트합니다. 전체 파라미터 대비 0.1~1% 수준의 파라미터만 업데이트되므로 옵티마이저 상태 메모리가 극히 적습니다.

### 수치 정밀도와 혼합 정밀도 전략

QLoRA의 연산 과정에서는 세 가지 정밀도가 혼합되어 사용됩니다:

| 구성 요소 | 저장 정밀도 | 연산 정밀도 |
|---------|----------|----------|
| 기본 가중치 $W$ | NF4 (4-bit) | BF16 (역양자화 후) |
| LoRA 파라미터 $A$, $B$ | BF16 | BF16 |
| 그래디언트 | BF16 | BF16 |
| 옵티마이저 상태 | FP32 | FP32 |
| 양자화 상수 (1차) | INT8 | FP32 (역양자화 후) |
| 양자화 상수 (2차) | FP32 | FP32 |

이러한 혼합 정밀도 전략의 핵심은, 순전파와 역전파의 실제 연산은 모두 BF16 이상의 정밀도로 수행되므로 그래디언트의 수치 안정성이 보장된다는 점입니다. NF4는 순수히 저장(storage) 형식으로만 사용되며, 연산 시에는 항상 BF16으로 변환됩니다.

### 메모리 절감 수학적 분석

65B 모델 기준으로 QLoRA의 메모리 절감을 정량적으로 분석할 수 있습니다.

**기본 가중치 메모리**:

$$M_{\text{weight}} = N \times (k + \text{오버헤드}_{\text{이중}}) / 8 = 65 \times 10^9 \times (4 + 0.127) / 8 \approx 33.5 \text{ GB}$$

**LoRA 파라미터 메모리** (랭크 $r=64$, 모든 선형 레이어에 적용 시):

LoRA 파라미터 수를 $N_{\text{LoRA}} \approx 0.5\%N$으로 추정하면:

$$M_{\text{LoRA}} = N_{\text{LoRA}} \times 2 / (1024^3) \approx 0.6 \text{ GB}$$

**옵티마이저 상태 메모리** (Adam, LoRA 파라미터에 대해서만):

$$M_{\text{opt}} = N_{\text{LoRA}} \times 8 / (1024^3) \approx 2.4 \text{ GB}$$

**총 QLoRA 메모리**: $M_{\text{total}} \approx 33.5 + 0.6 + 2.4 + M_{\text{activation}} \approx 37 \sim 48 \text{ GB}$

이는 FP16 전체 파인튜닝의 약 780GB 대비 **약 95% 이상의 메모리 절감**에 해당합니다.

## 실험 결과

QLoRA의 유효성은 다양한 벤치마크와 모델 크기에 걸쳐 광범위하게 검증되었습니다.

### 양자화 방식별 성능 비교

논문에서는 NF4와 다른 4비트 양자화 방식의 성능을 직접 비교합니다. LLaMA 모델에 대한 실험 결과:

| 양자화 방식 | 데이터 타입 | MMLU (5-shot) | 평균 양자화 오차 |
|-----------|----------|-------------|-------------|
| Float16 (기준선) | FP16 | 63.1 | 0 |
| NF4 + DQ | NF4 | 62.9 | 최소 |
| FP4 + DQ | FP4 | 62.4 | 중간 |
| INT4 + DQ | INT4 | 61.8 | 최대 |

NF4는 동일한 4비트 예산 내에서 가장 낮은 양자화 오차를 보이며, FP16 대비 MMLU 성능 손실이 0.2%에 불과합니다.

### Guanaco 벤치마크 결과

QLoRA로 학습된 Guanaco 모델 패밀리는 OASST1(OpenAssistant) 데이터셋으로 파인튜닝되었습니다. 아래 그림은 모델 평가에 사용된 인간 평가 인터페이스를 보여줍니다. 두 모델의 응답을 나란히 제시하고, 평가자가 유용성, 정확성, 상세도를 기준으로 1~10점 척도의 점수를 부여하는 방식입니다.

![Vicuna 벤치마크에 사용된 인간 평가 인터페이스 ) 두 모델의 응답을 비교 평가](figures/fig_5.png)
*Figure 5: Vicuna 벤치마크의 인간 평가 인터페이스. 동일한 질문에 대한 두 모델(Response A, B)의 응답을 나란히 보여주고, 평가자가 각각 1~10점으로 평가한다. 이 방식으로 Guanaco 모델이 ChatGPT 수준의 응답 품질을 달성했는지 검증하였다. (Dettmers et al., 2023)*

Vicuna 벤치마크에서 GPT-4를 평가자로 사용한 결과:

| 모델 | 파라미터 | ChatGPT 대비 성능 | 필요 GPU 메모리 | 학습 시간 |
|------|---------|----------------|--------------|---------|
| GPT-4 | - | 97.9% | - | - |
| Guanaco-65B (QLoRA) | 65B | **99.3%** | ~41 GB | ~24h (1x A100) |
| Guanaco-33B (QLoRA) | 33B | 97.8% | ~21 GB | ~12h (1x A100) |
| Vicuna-13B (Full FT) | 13B | 92.4% | ~160 GB | - |
| Guanaco-13B (QLoRA) | 13B | 91.2% | ~7.5 GB | ~6h (1x A100) |
| Alpaca-13B (Full FT) | 13B | 84.1% | ~160 GB | - |
| Guanaco-7B (QLoRA) | 7B | 87.5% | ~5 GB | ~4h (1x A100) |

주목할 점은 Guanaco-65B가 ChatGPT 대비 **99.3%**의 성능을 달성했다는 것입니다. 이는 단일 48GB GPU에서 24시간 학습만으로 달성한 결과입니다. 또한 Guanaco-33B는 Vicuna-13B(전체 파인튜닝)보다 높은 성능을 달성하면서도 훨씬 적은 메모리를 사용합니다.

### MMLU 5-shot 결과

MMLU(Massive Multitask Language Understanding)는 57개 과목에 걸친 지식 평가 벤치마크입니다:

| 모델 | 방법 | 정밀도 | MMLU (5-shot) |
|------|------|------|-------------|
| GPT-3.5-turbo | - | - | 70.0 |
| LLaMA-65B | Full FT (16-bit) | FP16 | 63.1 |
| LLaMA-65B | QLoRA (NF4) | NF4+BF16 | **62.9** |
| LLaMA-65B | QLoRA (FP4) | FP4+BF16 | 62.4 |
| LLaMA-33B | QLoRA (NF4) | NF4+BF16 | 60.4 |
| LLaMA-13B | QLoRA (NF4) | NF4+BF16 | 54.7 |
| LLaMA-7B | QLoRA (NF4) | NF4+BF16 | 47.3 |

QLoRA(NF4)는 전체 16비트 파인튜닝 대비 MMLU에서 0.2%p의 미미한 성능 차이만 보입니다. 이는 NF4 양자화가 모델의 지식을 사실상 손실 없이 보존함을 증명합니다.

### 메모리 사용량 상세 비교 (65B 기준)

| 방법 | 가중치 메모리 | 그래디언트+옵티마이저 | 총 GPU 메모리 | 필요 GPU 수 |
|------|-----------|------------------|-----------|----------|
| FP16 전체 파인튜닝 | ~130 GB | ~650 GB | ~780 GB | A100 80GB x 10+ |
| LoRA (BF16) | ~130 GB | ~30 GB | ~160 GB | A100 80GB x 2 |
| QLoRA (NF4) | ~33 GB | ~15 GB | ~48 GB | **A100 48GB x 1** |

QLoRA는 LoRA 대비 약 3.3배, 전체 파인튜닝 대비 약 16배의 메모리 절감을 달성합니다.

### LoRA 하이퍼파라미터 분석

논문에서는 다양한 LoRA 하이퍼파라미터 설정에 대한 체계적인 실험도 수행했습니다.

먼저, LoRA 어댑터를 어느 모듈에 적용하느냐에 따른 성능 차이가 뚜렷하게 나타납니다. 다음 그림은 모든 선형 레이어(QLoRA-All), FFN만(QLoRA-FFN), 어텐션만(QLoRA-Attention) 적용한 경우의 RougeL 성능을 비교합니다.

![QLoRA 어댑터 타겟 모듈별 RougeL 성능 비교 ( All, FFN, Attention 모듈 적용 결과](figures/fig_2.png)
*Figure 6: LoRA 어댑터 타겟 모듈별 RougeL 성능 비교. QLoRA-All(모든 선형 레이어 적용)이 QLoRA-FFN, QLoRA-Attention보다 일관되게 높은 성능을 보인다. 4비트(파랑)와 16비트(주황) 간 성능 차이가 미미하여 NF4 양자화의 손실이 거의 없음을 확인할 수 있다. (Dettmers et al., 2023)*

또한, LoRA의 랭크 $r$에 따른 성능 변화도 중요한 분석 대상입니다. 다음 그림은 랭크 값에 따른 RougeL 성능의 분포를 보여줍니다.

![LoRA 랭크(r) 값에 따른 RougeL 성능 분포 ) 8, 16, 32, 64 비교](figures/fig_4.png)
*Figure 7: LoRA 랭크 $r$에 따른 RougeL 성능 분포. $r=8$에서 $r=64$까지 성능이 점진적으로 향상되지만, $r=32$ 이후의 개선 폭은 미미하다. $r=64$가 성능과 효율의 최적 균형점으로, QLoRA 논문의 기본 권장값이다. (Dettmers et al., 2023)*

이 실험 결과를 종합하면 다음과 같은 결론을 도출할 수 있습니다:

- **랭크 $r$**: $r=64$가 대부분의 설정에서 최적. $r$을 더 높여도 성능 향상은 미미하고 메모리만 증가
- **타겟 모듈**: 모든 선형 레이어에 적용하는 것이 어텐션 레이어만 적용하는 것보다 우수
- **데이터 품질**: 학습 데이터 9,000개만으로도 ChatGPT 수준의 대화 품질 달성 가능. 데이터 양보다 품질이 결정적

## 의의 및 한계

### 의의

**대규모 모델 파인튜닝의 민주화**: QLoRA 이전에는 65B 이상의 모델을 파인튜닝하려면 수십 개의 고가 GPU가 필요했습니다. QLoRA는 이를 단일 GPU로 가능하게 하여, 소규모 연구팀, 스타트업, 개인 연구자도 대규모 모델을 자유롭게 실험할 수 있는 환경을 조성했습니다. 이는 AI 연구의 접근성을 근본적으로 변화시킨 기여입니다.

**정보 이론적 최적 양자화**: NF4 데이터 타입은 신경망 가중치 분포에 대해 정보 이론적으로 최적임이 증명되었습니다. 이는 단순한 공학적 트릭이 아닌 이론적 기반 위에 세워진 방법론으로, 양자화 연구에 새로운 방향을 제시했습니다.

**실용적 생태계 구축**: bitsandbytes 라이브러리와 HuggingFace PEFT/Transformers와의 긴밀한 통합을 통해, 연구자들이 몇 줄의 코드만으로 QLoRA를 적용할 수 있는 실용적 도구를 제공했습니다. 이 생태계는 현재 LLM 파인튜닝의 사실상 표준(de facto standard)이 되었습니다.

**후속 연구의 촉매**: QLoRA는 GPTQ+LoRA, AWQ+LoRA, LoftQ, GGUF 양자화 등 양자화와 효율적 파인튜닝을 결합하는 후속 연구의 기반이 되었습니다. 또한 QA-LoRA, LQ-LoRA 등 양자화 인식 LoRA 변형들의 발전을 촉진했습니다.

### 한계

**학습 속도 저하**: 순전파와 역전파 과정에서 NF4 가중치를 BF16으로 역양자화하는 추가 연산이 필요합니다. 이로 인해 QLoRA의 학습 속도는 동일 하드웨어에서의 BF16 LoRA 대비 약 1.5~2배 느립니다. 그러나 단일 GPU로 학습할 수 있다는 점에서 절대적 학습 시간은 다수 GPU를 확보하지 못한 환경에서 오히려 유리합니다.

**양자화 오차의 누적**: 4비트 양자화는 개별 가중치 수준에서는 미미한 오차를 유발하지만, 이 오차가 수십~수백 레이어를 거치며 누적될 수 있습니다. 특히 7B 이하의 소규모 모델에서는 양자화 오차의 상대적 영향이 커져 성능 저하가 더 두드러질 수 있습니다.

**추론 시 오버헤드**: QLoRA로 학습된 모델을 추론에 사용할 때, NF4 가중치를 매 연산마다 역양자화해야 하므로 순수 FP16 모델 대비 추론 속도가 다소 느립니다. 이를 완화하기 위해 학습 후 LoRA 가중치를 기본 가중치에 병합(merge)하고 별도의 추론용 양자화(GPTQ, AWQ 등)를 적용하는 방법이 일반적으로 사용됩니다.

**정규분포 가정의 한계**: NF4는 가중치가 정규분포를 따른다는 가정에 기반합니다. 대부분의 사전학습 모델에서 이 가정은 잘 성립하지만, 일부 특수한 아키텍처나 학습 방법(예: Sparse 모델)에서는 가중치 분포가 정규분포에서 벗어날 수 있으며, 이 경우 NF4의 최적성이 보장되지 않습니다.

## 코드 예제

### QLoRA: 4비트 양자화 + LoRA 파인튜닝 (bitsandbytes + PEFT)

```python
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from peft import (
    prepare_model_for_kbit_training,
    LoraConfig,
    get_peft_model,
    TaskType,
)
from trl import SFTTrainer
from datasets import load_dataset

# =============================================
# 1. NF4 양자화 설정 (QLoRA 핵심 구성)
# =============================================
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,                    # 4비트 양자화 활성화
    bnb_4bit_quant_type="nf4",             # NormalFloat 4-bit (정규분포 최적)
    bnb_4bit_compute_dtype=torch.bfloat16, # 연산 정밀도: BF16
    bnb_4bit_use_double_quant=True,        # 이중 양자화: 양자화 상수도 INT8로 양자화
)

# =============================================
# 2. 모델 로드 (NF4로 양자화된 상태)
# =============================================
model_id = "meta-llama/Llama-2-7b-hf"

tokenizer = AutoTokenizer.from_pretrained(model_id)
tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=bnb_config,
    device_map="auto",
    torch_dtype=torch.bfloat16,
)

# k-bit 학습을 위한 모델 준비 (그래디언트 체크포인팅 활성화)
model = prepare_model_for_kbit_training(model)

# =============================================
# 3. LoRA 어댑터 설정
# =============================================
lora_config = LoraConfig(
    r=64,                       # 랭크 (QLoRA 논문 권장값)
    lora_alpha=16,              # 스케일링 팩터
    target_modules=[            # 어댑터 적용 대상 모듈
        "q_proj", "k_proj", "v_proj", "o_proj",   # 어텐션 레이어
        "gate_proj", "up_proj", "down_proj",       # FFN 레이어
    ],
    lora_dropout=0.05,          # 드롭아웃
    bias="none",                # 바이어스 학습 안 함
    task_type=TaskType.CAUSAL_LM,
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
# 출력 예: trainable params: 33,554,432 || all params: 6,771,970,048
#          || trainable%: 0.4957

# =============================================
# 4. 학습 설정 (페이지드 옵티마이저 포함)
# =============================================
training_args = TrainingArguments(
    output_dir="./qlora-output",
    num_train_epochs=1,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    weight_decay=0.01,
    warmup_ratio=0.03,
    lr_scheduler_type="cosine",
    logging_steps=10,
    save_strategy="steps",
    save_steps=200,
    bf16=True,
    # 페이지드 옵티마이저: 메모리 스파이크 시 자동으로 CPU 페이징
    optim="paged_adamw_32bit",
    gradient_checkpointing=True,  # 활성화 메모리 절감
    max_grad_norm=0.3,
    group_by_length=True,
)

# =============================================
# 5. 데이터 로드 및 학습 실행
# =============================================
dataset = load_dataset("timdettmers/openassistant-guanaco", split="train")

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    args=training_args,
    train_dataset=dataset,
    max_seq_length=512,
)

trainer.train()

# =============================================
# 6. 모델 저장 (LoRA 어댑터만 저장)
# =============================================
model.save_pretrained("./qlora-adapter")
tokenizer.save_pretrained("./qlora-adapter")
# 저장 크기: ~100-200MB (전체 모델 대비 극히 적음)
```

### NF4 양자화 원리 구현 (이해용)

```python
import torch
import numpy as np
from scipy import stats

def create_nf4_lookup_table(num_bits=4):
    """NF4 양자화 테이블 생성.
    정규분포의 동등 확률 구간(equal quantile)을 기반으로
    2^num_bits개의 최적 격자점을 계산합니다.
    """
    num_bins = 2 ** num_bits  # 16개

    # 동등 확률 분위수 경계 계산
    quantile_boundaries = np.linspace(0, 1, num_bins + 1)

    # 각 구간의 중간 분위수에 해당하는 값을 격자점으로 사용
    grid_points = []
    for i in range(num_bins):
        lower = quantile_boundaries[i]
        upper = quantile_boundaries[i + 1]
        midpoint = (lower + upper) / 2
        grid_points.append(stats.norm.ppf(midpoint))

    grid_points = np.array(grid_points)

    # [-1, 1] 범위로 정규화
    grid_points = grid_points / np.max(np.abs(grid_points))

    return torch.tensor(grid_points, dtype=torch.float32)


def quantize_block_nf4(weight_block, nf4_table):
    """가중치 블록을 NF4로 양자화.

    Args:
        weight_block: (block_size,) 형태의 가중치 텐서
        nf4_table: (16,) 형태의 NF4 격자점 테이블

    Returns:
        indices: (block_size,) 4비트 인덱스
        absmax: 스케일 팩터 (역양자화에 필요)
    """
    # 절대 최대값으로 정규화
    absmax = weight_block.abs().max()
    if absmax == 0:
        return torch.zeros_like(weight_block, dtype=torch.uint8), absmax

    normalized = weight_block / absmax  # [-1, 1] 범위

    # 가장 가까운 NF4 격자점에 매핑
    # distances: (block_size, 16)
    distances = (normalized.unsqueeze(-1) - nf4_table.unsqueeze(0)).abs()
    indices = distances.argmin(dim=-1).to(torch.uint8)  # 4비트 인덱스

    return indices, absmax


def dequantize_block_nf4(indices, absmax, nf4_table):
    """NF4 인덱스를 BF16 가중치로 복원 (순전파/역전파 시 호출)."""
    quantized_values = nf4_table[indices.long()]
    return (quantized_values * absmax).to(torch.bfloat16)


# 양자화 오차 비교: NF4 vs INT4
def compare_quantization_error():
    """NF4와 INT4의 양자화 오차를 비교합니다."""
    torch.manual_seed(42)

    # 정규분포를 따르는 가중치 시뮬레이션
    weights = torch.randn(10000)

    # NF4 양자화
    nf4_table = create_nf4_lookup_table(4)
    nf4_indices, nf4_absmax = quantize_block_nf4(weights, nf4_table)
    nf4_restored = dequantize_block_nf4(nf4_indices, nf4_absmax, nf4_table)
    nf4_error = (weights - nf4_restored.float()).pow(2).mean().item()

    # INT4 양자화 (균등 간격)
    int4_absmax = weights.abs().max()
    int4_normalized = weights / int4_absmax
    int4_grid = torch.linspace(-1, 1, 16)
    int4_distances = (int4_normalized.unsqueeze(-1) - int4_grid.unsqueeze(0)).abs()
    int4_indices = int4_distances.argmin(dim=-1)
    int4_restored = int4_grid[int4_indices] * int4_absmax
    int4_error = (weights - int4_restored).pow(2).mean().item()

    print("=== 양자화 오차 비교 (정규분포 데이터) ===")
    print(f"NF4  MSE: {nf4_error:.6f}")
    print(f"INT4 MSE: {int4_error:.6f}")
    print(f"NF4 오차 감소율: {(1 - nf4_error/int4_error)*100:.1f}%")


# 메모리 절감 계산
def memory_analysis(num_params_billion=65):
    """QLoRA의 메모리 절감량을 계산합니다."""
    N = num_params_billion * 1e9
    GB = 1024 ** 3

    # 전체 파인튜닝 (FP16)
    fp16_weights = N * 2 / GB           # 모델 가중치
    fp16_grads = N * 2 / GB             # 그래디언트 (FP16)
    fp16_optim = N * 8 / GB             # Adam 상태 (FP32 x 2)
    fp16_total = fp16_weights + fp16_grads + fp16_optim

    # QLoRA
    nf4_weights = N * (4 + 0.127) / 8 / GB  # NF4 + 이중 양자화 오버헤드
    lora_ratio = 0.005                       # LoRA 파라미터 비율 (0.5%)
    lora_params = N * lora_ratio
    lora_weights = lora_params * 2 / GB      # BF16
    lora_grads = lora_params * 2 / GB        # BF16
    lora_optim = lora_params * 8 / GB        # Adam FP32
    qlora_total = nf4_weights + lora_weights + lora_grads + lora_optim

    print(f"=== {num_params_billion}B 모델 메모리 분석 ===")
    print(f"FP16 전체 파인튜닝: {fp16_total:.1f} GB")
    print(f"  - 가중치: {fp16_weights:.1f} GB")
    print(f"  - 그래디언트: {fp16_grads:.1f} GB")
    print(f"  - 옵티마이저: {fp16_optim:.1f} GB")
    print(f"QLoRA: {qlora_total:.1f} GB")
    print(f"  - NF4 가중치: {nf4_weights:.1f} GB")
    print(f"  - LoRA 파라미터: {lora_weights:.2f} GB")
    print(f"  - LoRA 그래디언트: {lora_grads:.2f} GB")
    print(f"  - LoRA 옵티마이저: {lora_optim:.2f} GB")
    print(f"메모리 절감: {(1 - qlora_total/fp16_total)*100:.1f}%")


if __name__ == "__main__":
    compare_quantization_error()
    print()
    memory_analysis(7)
    print()
    memory_analysis(65)
```

> **QLoRA 핵심 공식**: `frozen(NF4(W)) + trainable(LoRA_BF16)` -- 베이스 모델은 NF4 4비트로 동결하여 저장하고, LoRA 어댑터만 BF16으로 학습합니다. 순전파/역전파 시 NF4 가중치는 BF16으로 역양자화되어 연산에 사용되며, 그래디언트는 LoRA 파라미터에 대해서만 계산됩니다. 이중 양자화와 페이지드 옵티마이저가 남은 메모리 오버헤드까지 최소화하여, 단일 GPU에서의 대규모 모델 파인튜닝을 현실화합니다.

## 관련 문서

- [[lora|LoRA: Low-Rank Adaptation of Large Language Models]] -- QLoRA의 기반 기술
- [[gptq|GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers]] -- 대안적 양자화 접근
- [[llm_int8|LLM.int8(): 8-bit Matrix Multiplication for Transformers at Scale]] -- 8비트 양자화의 선행 연구
