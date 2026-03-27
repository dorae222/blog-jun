# NVFP4와 현대 양자화 포맷 비교: FP4·FP8·INT4·INT8의 이해

## 들어가며

:::info
이 글은 [[quantization-guide|양자화 기초 가이드]]의 후속편으로, 현대 LLM 추론에서 사용되는 양자화 포맷들의 수치 표현 원리와 실전 트레이드오프를 다룬다.
:::

LLM의 크기가 커지면서, 모델을 실행하는 데 필요한 GPU 메모리와 연산 비용이 핵심 병목이 되었다. 70B 파라미터 모델을 FP16으로 로드하면 **140GB의 메모리**가 필요한데, 이는 가장 비싼 소비자 GPU(RTX 4090, 24GB)로도 감당할 수 없다.

양자화는 이 문제를 해결하는 가장 직접적인 방법이다. 16비트에서 4비트로 양자화하면 메모리 사용량이 **4분의 1**로 줄어, 70B 모델을 단일 GPU에 탑재할 수 있게 된다. 그러나 모든 양자화 포맷이 동일한 것은 아니다. INT8, INT4, FP8, FP4/NVFP4, 그리고 GPTQ, AWQ 같은 알고리즘 기반 기법까지, 각각의 특성과 트레이드오프를 이해해야 올바른 선택이 가능하다.

[[quantization-guide]]에서는 Dynamic/Static/QAT 양자화의 기초를 다뤘다. 이 글에서는 한 단계 더 나아가, 현대 LLM 추론에서 실제로 사용되는 양자화 포맷들의 **수치 표현 원리, 정확도 손실, 하드웨어 지원, 그리고 실전 코드**까지 비교 분석한다.

---

## 양자화 포맷 한눈에 비교

먼저 전체 포맷을 한 표로 정리한다. 이후 섹션에서 각 포맷을 상세히 설명한다.

| 포맷 | 비트수 | 표현 방식 | 고유 값 수 | 0 근처 해상도 | 하드웨어 가속 | 주요 용도 |
|------|:------:|----------|:----------:|:----------:|:----------:|----------|
| FP16 | 16 | 부동소수점 | 65,536 | 매우 높음 | 범용 GPU | 학습 기준선 |
| BF16 | 16 | 부동소수점 | 65,536 | 높음 | Ampere+ | 학습 (넓은 범위) |
| FP8 E4M3 | 8 | 부동소수점 | 256 | 높음 | Hopper+ | 추론 |
| FP8 E5M2 | 8 | 부동소수점 | 256 | 중간 | Hopper+ | 학습 (gradient) |
| INT8 | 8 | 정수 | 256 | 낮음 | 범용 GPU | 추론 (SmoothQuant) |
| INT4 | 4 | 정수 | 16 | 낮음 | 제한적 | 추론 (GPTQ/AWQ) |
| NF4 | 4 | 정규분포 분위수 | 16 | 높음 | SW 에뮬레이션 | 파인튜닝 (QLoRA) |
| NVFP4 | 4 | 부동소수점 | 16 | 높음 | Blackwell 네이티브 | 차세대 추론/학습 |

---

## 수치 표현의 기초

양자화를 이해하려면, 숫자가 컴퓨터에서 어떻게 표현되는지를 먼저 알아야 한다. 자세한 내용은 [[floating-point-arithmetic|부동소수점 표현]]을 참고하고, 여기서는 양자화에 필요한 핵심만 정리한다.

### 정수(Integer) vs 부동소수점(Floating-Point)

| 특성 | 정수 (INT) | 부동소수점 (FP) |
|------|-----------|---------------|
| 표현 방식 | 균등 간격 | 지수부 + 가수부 |
| 값 분포 | 전체 범위 균등 | 0 근처 밀집, 큰 값 희소 |
| 연산 속도 | 매우 빠름 | INT 대비 느림 |
| 범위 | 제한적 (8비트: -128~127) | 넓음 (지수부가 범위 결정) |
| 딥러닝 적합성 | 보통 | 높음 (가중치 분포 특성) |

**핵심 차이**: INT는 모든 값 사이의 간격이 동일하고, FP는 0 근처에 값이 밀집되고 큰 값에서는 간격이 넓어진다. 딥러닝 가중치의 분포가 대체로 0 근처에 집중되어 있으므로, **FP 표현이 딥러닝에 자연스럽게 적합**하다.

### Scale과 Zero-Point

양자화의 핵심 연산은 고정밀 값을 저정밀 값으로 매핑하는 것이다:

$$x_q = \text{round}\left(\frac{x}{s}\right) + z$$

- $s$ (scale): 스케일링 팩터. 연속 값의 범위를 양자화 범위에 맞춤
- $z$ (zero-point): 비대칭 분포를 보정하기 위한 오프셋

| 그래뉼래리티 | 설명 | 정확도 | 속도 |
|-------------|------|:------:|:----:|
| Per-tensor | 텐서 전체에 하나의 scale/zero-point | 낮음 | 빠름 |
| Per-channel | 채널별로 별도 scale | 중간 | 보통 |
| Per-group | 그룹(예: 128개)별 별도 scale | 높음 | 느림 |

---

## INT8: 입증된 표준

INT8은 현재 가장 널리 배포된 양자화 포맷이다. 거의 모든 현대 GPU/CPU에서 INT8 연산을 네이티브 지원하며, 양자화 생태계가 가장 성숙해 있다.

### 표현 범위와 특성

- **부호 있는 INT8**: -128 ~ 127 (256개 값)
- **균등 간격**: 모든 인접 값의 차이가 동일
- **2x 메모리 절감**: FP16 대비 메모리 절반

### 장점과 한계

| 장점 | 한계 |
|------|------|
| 거의 모든 GPU/CPU에서 네이티브 지원 | 균등 간격으로 0 근처 해상도 부족 |
| SmoothQuant, LLM.int8() 등 성숙한 기법 | Outlier가 전체 양자화 범위 왜곡 |
| FP16 대비 2x 메모리 절감 | FP8 대비 정밀도 불리 |
| 검증된 안정성, 프로덕션 실적 풍부 | 4비트 포맷 대비 압축률 낮음 |

### Outlier 문제와 SmoothQuant

INT8 양자화의 가장 큰 도전은 **outlier 문제**이다. Transformer의 activation에는 소수의 극단적으로 큰 값(outlier)이 존재하는데, 이 값들이 전체 양자화 범위를 왜곡한다.

[[65_smoothquant|SmoothQuant]](Xiao et al., 2023)는 이 문제를 해결하기 위해 activation의 outlier를 weight 쪽으로 "이동"시키는 기법이다. 수학적으로는 다음과 같이 등가 변환을 수행한다:

$$Y = (X \cdot \text{diag}(s)^{-1}) \cdot (\text{diag}(s) \cdot W) = \hat{X} \cdot \hat{W}$$

스케일 팩터 $s$를 적절히 설정하여 activation과 weight 모두 양자화하기 쉬운 분포로 만든다.

### 대표 설정

| 설정 | 설명 | 적용 시점 |
|------|------|----------|
| W8A8 | 가중치/활성화 모두 INT8 | SmoothQuant 적용 시 |
| W8A16 | 가중치 INT8, 활성화 FP16 | 정밀도 우선 |
| Dynamic Quantization | 추론 시 min/max 동적 계산 | 범용 |
| Static Quantization | 캘리브레이션 데이터로 사전 결정 | 최적화 |

---

## INT4: GPTQ와 AWQ

INT4는 메모리 효율을 극대화하려는 시도이다. 4비트로는 **16개의 값만 표현**할 수 있어 정보 손실이 불가피하지만, 정교한 알고리즘으로 이를 보완한다.

### INT4 기본 특성

- **범위**: -8 ~ 7 (16개 값, 균등 간격)
- **Per-group quantization 필수**: 텐서 전체에 하나의 scale을 사용하면 정확도 심하게 저하. 보통 128개 원소 단위로 그룹별 별도 scale 적용
- **4x 메모리 절감**: FP16 대비

### GPTQ: Post-Training Quantization의 대표

[[63_gptq|GPTQ]](Frantar et al., 2023)는 OBS(Optimal Brain Surgeon) 프레임워크를 기반으로, 양자화 오차를 최소화하도록 가중치를 조정하는 기법이다.

| 항목 | 설명 |
|------|------|
| 원리 | Hessian 역행렬 기반 오차 보상 |
| 캘리브레이션 | 128~256 샘플 (몇 분 소요) |
| 그룹 크기 | 보통 128 |
| 장점 | 빠른 양자화, 높은 정확도 |
| 한계 | Weight-only (activation은 FP16) |

### AWQ: Activation-Aware Weight Quantization

[[64_awq|AWQ]](Lin et al., 2024)는 "모든 가중치가 동등하지 않다"는 관찰에 기반한다. Activation의 크기가 큰 채널에 연결된 가중치가 모델 성능에 더 중요하므로, 이 **salient weight**를 보호하는 전략을 사용한다.

| 항목 | 설명 |
|------|------|
| 원리 | Salient weight 채널별 스케일링 |
| 캘리브레이션 | 소량 (몇 분 소요) |
| 장점 | GPTQ 대비 더 나은 정확도, 빠른 추론 |
| 한계 | Weight-only |

### GPTQ vs AWQ 비교

| 항목 | GPTQ | AWQ |
|------|------|-----|
| 양자화 원리 | Hessian 기반 오차 보상 | Activation-aware 스케일링 |
| 양자화 속도 | 보통 (Hessian 계산) | 빠름 |
| 추론 속도 | 빠름 | 더 빠름 (커널 최적화) |
| 정확도 (Perplexity) | 높음 | 약간 더 높음 |
| 생태계 | AutoGPTQ, ExLlama | AutoAWQ, vLLM |

---

## NF4: QLoRA의 핵심

QLoRA(Dettmers et al., 2023)에서 제안된 NF4(NormalFloat4)는 딥러닝 가중치의 분포 특성을 활용한 4비트 포맷이다.

### 핵심 아이디어

딥러닝 가중치는 대체로 **정규분포**를 따르므로, 16개의 양자화 값을 정규분포의 분위수(quantile)에 맞추면 정보 이론적으로 최적의 양자화가 된다.

| 특성 | INT4 | NF4 |
|------|------|-----|
| 값 배치 | 균등 간격 (-8~7) | 정규분포 분위수 기반 |
| 0 근처 해상도 | 낮음 | 높음 |
| 적합 대상 | 범용 | 가중치 양자화 특화 |
| 하드웨어 가속 | 제한적 | 소프트웨어 에뮬레이션 |

### Double Quantization

QLoRA의 또 다른 혁신으로, 양자화 파라미터(scale 값) 자체를 다시 양자화하는 기법이다. Per-group scale이 차지하는 메모리 오버헤드를 줄여, 실질적으로 **0.5비트 추가 절감** 효과를 제공한다.

---

## FP8: 차세대 학습/추론 표준

FP8(8비트 부동소수점)은 NVIDIA H100 GPU에서 네이티브 지원되며, INT8의 한계를 극복하기 위해 설계되었다.

### 두 가지 변형

| 포맷 | 구성 | 범위 | 정밀도 | 용도 |
|------|------|:----:|:------:|------|
| E4M3 | 1(부호)+4(지수)+3(가수) | ~448 | 높음 | 가중치/활성화 (추론) |
| E5M2 | 1(부호)+5(지수)+2(가수) | ~57,344 | 중간 | 그래디언트 (학습) |

- **E4M3**: 지수 4비트로 적당한 범위, 가수 3비트로 INT8에 근접한 정밀도. 추론에 최적
- **E5M2**: 지수 5비트로 넓은 범위 확보, 그래디언트의 큰 변동을 수용. BF16과 범위가 유사

### FP8 vs INT8 비교

| 항목 | INT8 | FP8 E4M3 |
|------|------|----------|
| 값 분포 | 균등 간격 | 0 근처 밀집 |
| 동적 범위 | 좁음 (256단계 선형) | 넓음 (지수부 활용) |
| Outlier 대응 | SmoothQuant 필요 | 지수부가 자동 커버 |
| 학습 통합 | 별도 포맷 필요 | E5M2와 조합 가능 |
| 하드웨어 지원 | 범용 GPU | Hopper+ 전용 |
| Transformer Engine | 미지원 | 자동 Mixed Precision |

### FP8의 핵심 장점

1. **동적 범위**: 지수부 덕분에 outlier를 자연스럽게 수용
2. **SmoothQuant 불필요**: INT8에서 필요했던 outlier 이동 기법이 불필요
3. **학습+추론 통합**: E5M2(학습)와 E4M3(추론)의 조합으로 전체 파이프라인을 8비트로 통일
4. **Transformer Engine**: H100의 Transformer Engine이 FP8 Mixed Precision을 자동 관리

---

## NVFP4: Blackwell의 4비트 부동소수점

NVIDIA의 Blackwell 아키텍처(B100/B200/GB200)에서 도입된 NVFP4는 4비트 부동소수점 포맷이다. 기존 4비트 양자화(INT4, NF4)가 소프트웨어 기법에 의존했던 것과 달리, NVFP4는 **하드웨어 네이티브 가속**을 제공한다.

### 표현 구조

NVFP4는 **1(부호) + 1(지수) + 2(가수)** 구성이다:

| 비트 위치 | 역할 | 가능한 값 |
|----------|------|----------|
| 비트 3 | 부호 | +, - |
| 비트 2 | 지수 | $2^0 = 1$ 또는 $2^1 = 2$ |
| 비트 1-0 | 가수 | 1.00, 1.01, 1.10, 1.11 |

총 **16개 값**을 표현할 수 있으며, 0을 포함하면 실제 사용 가능한 고유 값은 제한적이다. 이 적은 수의 표현 값에도 불구하고, 부동소수점 구조 덕분에 **0 근처의 해상도가 INT4보다 높다**.

### NVFP4 vs INT4 vs NF4 상세 비교

| 특성 | INT4 | NF4 | NVFP4 |
|------|------|-----|-------|
| 표현 방식 | 균등 정수 | 정규분포 분위수 | 부동소수점 (E1M2) |
| 하드웨어 가속 | 제한적 | 없음 (SW 에뮬레이션) | **Blackwell 네이티브** |
| 0 근처 해상도 | 낮음 | 높음 | 높음 |
| 스케일링 | Per-group 필수 | Per-group 필수 | Block scaling (FP8) |
| 디퀀타이제이션 | 간단 (정수 연산) | 룩업 테이블 | 하드웨어 자동 |
| 추론 TFLOPS | SW 의존 | SW 의존 | Tensor Core 직접 |
| 주요 프레임워크 | GPTQ, AWQ | bitsandbytes | TensorRT-LLM |

### Block Scaling: NVFP4의 핵심 혁신

NVFP4는 **micro-scaling** 방식을 사용한다. FP4 값에 블록 단위의 FP8 scale을 곱하여 실효 정밀도를 높이는 구조다:

$$x \approx s_{\text{FP8}} \times x_{\text{FP4}}$$

| 항목 | 설명 |
|------|------|
| 블록 크기 | 보통 16~32개 요소 |
| Scale 정밀도 | FP8 (E4M3) |
| 실효 정밀도 | 순수 FP4보다 크게 향상 |
| 메모리 오버헤드 | Scale 저장에 추가 0.25~0.5비트 |

### 왜 NVFP4가 중요한가

1. **2x 추가 절감**: FP8 대비 메모리/대역폭 2배 절감. 거대 모델의 실용적 배포에 결정적
2. **네이티브 하드웨어 지원**: NF4는 소프트웨어 에뮬레이션이지만, NVFP4는 Blackwell GPU의 Tensor Core에서 직접 연산
3. **학습+추론 통합 가능**: FP4 Forward + FP8 Backward 조합으로 4비트 학습도 탐색 중
4. **추론 모델과의 시너지**: DeepSeek-R1 같은 대규모 추론 모델을 소비자급 GPU에서 실행할 수 있는 가능성

---

## Blackwell 아키텍처와 FP4 가속

NVFP4를 이해하려면 Blackwell 아키텍처의 하드웨어 변화를 알아야 한다. Blackwell은 NVIDIA의 차세대 GPU 아키텍처로, FP4 Tensor Core를 처음으로 탑재했다.

| 항목 | Hopper (H100) | Blackwell (B200) |
|------|:------------:|:----------------:|
| FP4 Tensor Core | X | O |
| FP8 Tensor Core | O | O |
| FP4 TFLOPS | - | 2x FP8 |
| HBM 용량 | 80 GB | 192 GB |
| 메모리 대역폭 | 3.35 TB/s | 8 TB/s |
| NVLink 대역폭 | 900 GB/s | 1,800 GB/s |

Blackwell의 핵심은 FP4 Tensor Core가 **FP8 대비 2배의 연산 처리량**을 제공한다는 점이다. 메모리 대역폭도 2배 이상 증가하여, NVFP4의 이론적 이점이 실제 성능으로 직결된다. 또한 HBM 용량이 192GB로 늘어, FP4 양자화 시 405B급 모델도 단일 GPU에서 실행할 수 있는 가능성이 열렸다.

---

## 모델 크기별 메모리 사용량

실제 배포 시 어느 포맷이 가능한지를 판단하려면 메모리 계산이 필수다.

| 모델 | FP16 | FP8 | INT8 | INT4/NVFP4 | 단일 GPU 탑재 (24GB) |
|------|-----:|----:|-----:|-----------:|:-------------------:|
| 7B | 14 GB | 7 GB | 7 GB | 3.5 GB | FP8 이상 가능 |
| 13B | 26 GB | 13 GB | 13 GB | 6.5 GB | INT8/FP8 가능 |
| 34B | 68 GB | 34 GB | 34 GB | 17 GB | INT4만 가능 |
| 70B | 140 GB | 70 GB | 70 GB | 35 GB | 불가 (듀얼 GPU) |
| 405B | 810 GB | 405 GB | 405 GB | 203 GB | 불가 (멀티 노드) |

:::tip
위 수치는 **가중치만의 메모리**이다. 실제 추론에는 KV Cache, activation, 프레임워크 오버헤드가 추가로 필요하므로, 가중치 메모리의 **1.2~1.5배**를 기준으로 잡는 것이 안전하다.
:::

---

## 하드웨어 지원 매트릭스

양자화 포맷의 선택은 보유 GPU에 따라 결정된다. 각 GPU 세대별 지원 현황을 정리한다.

| GPU 세대 | 대표 모델 | FP16 | BF16 | INT8 | FP8 | INT4 | NVFP4 |
|----------|----------|:----:|:----:|:----:|:---:|:----:|:-----:|
| Turing (2018) | RTX 2080 Ti | O | X | O | X | SW | X |
| Ampere (2020) | A100, RTX 3090 | O | O | O | X | SW | X |
| Ada Lovelace (2022) | L40S, RTX 4090 | O | O | O | X | SW | X |
| Hopper (2022) | H100, H200 | O | O | O | O | SW | X |
| Blackwell (2024) | B100, B200, GB200 | O | O | O | O | SW | O |

- **O**: 하드웨어 네이티브 지원 (Tensor Core 가속)
- **SW**: 소프트웨어 에뮬레이션 (커널 라이브러리 의존)
- **X**: 미지원

:::warning
INT4/GPTQ/AWQ는 모든 GPU에서 "SW" 레벨로 작동하지만, 전용 CUDA 커널(ExLlama, Marlin 등)의 품질에 따라 실제 성능이 크게 달라진다. RTX 4090에서 Marlin 커널을 사용한 INT4가 네이티브 INT8보다 빠른 경우도 있다.
:::

---

## 정확도 벤치마크

양자화의 핵심 질문은 "정확도를 얼마나 잃는가"이다. LLaMA 2 70B 기준으로 각 포맷별 정확도 손실을 정리한다.

### Perplexity 비교 (WikiText-2, 낮을수록 좋음)

| 포맷 | 비트 | Perplexity | FP16 대비 증가 |
|------|:----:|:----------:|:-------------:|
| FP16 (기준) | 16 | 3.32 | - |
| FP8 E4M3 | 8 | 3.33 | +0.01 |
| INT8 (SmoothQuant) | 8 | 3.35 | +0.03 |
| INT4 (GPTQ, g128) | 4 | 3.48 | +0.16 |
| INT4 (AWQ, g128) | 4 | 3.44 | +0.12 |
| NF4 (bitsandbytes) | 4 | 3.41 | +0.09 |
| NVFP4 (block scaling) | 4 | ~3.40 | ~+0.08 |

### 태스크별 정확도 영향

| 태스크 유형 | FP8 손실 | INT4 손실 | 비고 |
|-----------|:--------:|:--------:|------|
| 일반 대화/생성 | 무시 가능 | 1~2% | 체감 차이 거의 없음 |
| 요약/번역 | 무시 가능 | 2~3% | 미세한 뉘앙스 차이 |
| 수학 추론 | 0.5~1% | 3~5% | 정밀 계산 오류 증가 |
| 코드 생성 | 0.5~1% | 2~4% | 문법 오류 소폭 증가 |
| 과학 지식 QA | 무시 가능 | 1~3% | 사실 정확도 소폭 감소 |

---

## 실전 코드 예제

### bitsandbytes로 4비트 양자화 (NF4)

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

# NF4 양자화 설정
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",           # NF4 포맷
    bnb_4bit_compute_dtype="bfloat16",    # 연산은 BF16
    bnb_4bit_use_double_quant=True,       # Double Quantization
)

model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.1-70B-Instruct",
    quantization_config=bnb_config,
    device_map="auto",
)

tokenizer = AutoTokenizer.from_pretrained(
    "meta-llama/Llama-3.1-70B-Instruct"
)

# 70B 모델이 약 35GB + alpha로 로드됨
inputs = tokenizer("양자화란", return_tensors="pt").to("cuda")
outputs = model.generate(**inputs, max_new_tokens=100)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

### AutoGPTQ로 INT4 양자화

```python
from transformers import AutoTokenizer
from auto_gptq import AutoGPTQForCausalLM, BaseQuantizeConfig

# 양자화 설정
quantize_config = BaseQuantizeConfig(
    bits=4,
    group_size=128,
    desc_act=True,              # Activation order 기반 양자화
    damp_percent=0.1,
)

# 캘리브레이션 데이터 준비
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.1-8B")
calibration_data = [
    tokenizer(text, return_tensors="pt")
    for text in calibration_texts[:128]
]

# 양자화 실행
model = AutoGPTQForCausalLM.from_pretrained(
    "meta-llama/Llama-3.1-8B",
    quantize_config=quantize_config,
)
model.quantize(calibration_data)

# 양자화된 모델 저장
model.save_quantized("llama3-8b-gptq-int4")
```

### AutoAWQ로 INT4 양자화

```python
from awq import AutoAWQForCausalLM
from transformers import AutoTokenizer

model_path = "meta-llama/Llama-3.1-8B"
quant_path = "llama3-8b-awq-int4"

# 모델 로드
model = AutoAWQForCausalLM.from_pretrained(model_path)
tokenizer = AutoTokenizer.from_pretrained(model_path)

# AWQ 양자화 설정
quant_config = {
    "zero_point": True,
    "q_group_size": 128,
    "w_bit": 4,
    "version": "GEMM",   # GEMM 또는 GEMV 커널
}

# 양자화 실행 (salient weight 보호)
model.quantize(tokenizer, quant_config=quant_config)
model.save_quantized(quant_path)
tokenizer.save_pretrained(quant_path)
```

### INT8 양자화 (bitsandbytes LLM.int8())

```python
from transformers import AutoModelForCausalLM, BitsAndBytesConfig

# INT8 양자화 (Mixed-precision decomposition)
bnb_config = BitsAndBytesConfig(
    load_in_8bit=True,
    llm_int8_threshold=6.0,       # Outlier 임계값
)

model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.1-70B-Instruct",
    quantization_config=bnb_config,
    device_map="auto",
)
# Outlier 채널은 FP16, 나머지는 INT8로 자동 분리
```

---

## GGUF와 llama.cpp 양자화

GPTQ/AWQ가 GPU 추론에 최적화된 포맷이라면, GGUF는 **CPU 및 CPU+GPU 혼합 추론**에 특화된 포맷이다. llama.cpp 프로젝트에서 개발되었으며, 소비자 하드웨어에서 LLM을 실행하는 데 가장 널리 사용된다.

### 주요 양자화 레벨

| GGUF 타입 | 비트 | 설명 | 품질 vs 크기 |
|-----------|:----:|------|:----------:|
| Q2_K | 2 | 극한 압축, 품질 저하 큼 | 크기 최소 |
| Q3_K_M | 3 | 작은 모델에 적합 | 낮음 |
| Q4_K_M | 4 | 가장 추천되는 균형점 | 중간 |
| Q5_K_M | 5 | 높은 품질, 적당한 크기 | 높음 |
| Q6_K | 6 | FP16에 근접한 품질 | 매우 높음 |
| Q8_0 | 8 | 거의 무손실 | 최고 |

Q4_K_M은 "K-quant Mixed" 방식으로, 레이어의 중요도에 따라 일부는 4비트, 일부는 높은 비트로 양자화한다. 단순 균일 양자화보다 동일 크기에서 더 나은 품질을 제공한다.

---

## 양자화 기법별 종합 비교

| 기법 | 포맷 | 비트 | Weight | Activation | 캘리브레이션 | 속도 |
|------|------|:----:|:------:|:----------:|:----------:|:----:|
| LLM.int8() | INT8 | 8 | INT8 | FP16 | 불필요 | 느림 |
| SmoothQuant | INT8 | 8 | INT8 | INT8 | 필요 | 빠름 |
| GPTQ | INT4 | 4 | INT4 | FP16 | 필요 | 빠름 |
| AWQ | INT4 | 4 | INT4 | FP16 | 필요 | 매우 빠름 |
| QLoRA (NF4) | NF4 | 4 | NF4 | BF16 | 불필요 | 보통 |
| FP8 (native) | FP8 | 8 | FP8 | FP8 | 선택적 | 매우 빠름 |
| NVFP4 | FP4 | 4 | FP4 | FP8 | 필요 | 매우 빠름 |

---

## 실전 선택 가이드

### GPU별 최적 양자화 전략

| GPU | VRAM | 최적 포맷 | 추천 라이브러리 | 가능 모델 크기 |
|-----|-----:|----------|--------------|:------------:|
| RTX 3090 | 24 GB | INT4 (GPTQ/AWQ) | AutoGPTQ, vLLM | ~13B (FP16), ~34B (INT4) |
| RTX 4090 | 24 GB | INT4 (AWQ) | AutoAWQ, vLLM | ~13B (FP16), ~34B (INT4) |
| A100 40GB | 40 GB | FP8 또는 INT4 | TensorRT-LLM | ~20B (FP16), ~70B (INT4) |
| A100 80GB | 80 GB | FP8 또는 INT8 | TensorRT-LLM | ~40B (FP16), ~70B (INT8) |
| H100 80GB | 80 GB | FP8 E4M3 | TensorRT-LLM | ~40B (FP16), ~70B (FP8) |
| B200 192GB | 192 GB | NVFP4 | TensorRT-LLM | ~96B (FP16), ~405B (FP4) |

### 추론(Inference) 시나리오

| 시나리오 | 추천 포맷 | 이유 |
|---------|----------|------|
| H100/H200 보유 | FP8 E4M3 | 정밀도 손실 최소, 네이티브 2x 가속 |
| A100/RTX 4090 | INT4 (AWQ) | 대형 모델 탑재, Marlin 커널 활용 |
| RTX 3090 (24GB) | INT4 (GPTQ) | 7B~13B 최적, 70B는 듀얼 GPU |
| Blackwell GPU | NVFP4 | 네이티브 4비트 가속, FP8 대비 추가 2x |
| CPU 추론 (GGUF) | Q4_K_M | llama.cpp 최적화 커널 |

### 파인튜닝(Fine-tuning) 시나리오

| 시나리오 | 추천 포맷 | 이유 |
|---------|----------|------|
| 메모리 제약 심한 경우 | QLoRA (NF4) | 4비트 양자화 + LoRA 어댑터 |
| 메모리 여유 있는 경우 | FP8 또는 BF16 | 정밀도 우선 |
| 대규모 분산 학습 | BF16 + FSDP | 안정성과 성능 균형 |

### 도메인별 권장

| 도메인 | 최소 권장 | 이유 |
|--------|----------|------|
| 일반 대화/챗봇 | INT4 충분 | 양자화 오차의 영향 최소 |
| 요약/번역 | INT4 충분 | 미세한 차이만 존재 |
| 수학/코드 추론 | FP8 이상 | 추론 정밀도가 정확도에 직접 영향 |
| 의료/법률 | FP8 이상 | 사실 정확도가 중요 |
| 과학 계산 | FP16/BF16 | 수치 안정성이 중요 |

---

## 향후 전망

### 양자화 포맷의 진화 방향

양자화 기술은 "더 적은 비트로 더 많은 정보를 보존"하는 방향으로 빠르게 진화하고 있다:

| 시기 | 주요 발전 | 영향 |
|------|----------|------|
| 2022 | GPTQ, LLM.int8() 등장 | INT4/INT8 양자화 대중화 |
| 2023 | QLoRA, AWQ, SmoothQuant | 4비트 파인튜닝, 추론 최적화 성숙 |
| 2023 | H100 FP8 네이티브 지원 | 8비트 부동소수점 표준화 |
| 2024 | Blackwell NVFP4 발표 | 4비트 하드웨어 네이티브 시대 개막 |
| 2025+ | FP4 학습, 2비트 양자화 연구 | 극한 압축의 새로운 가능성 |

---

## 정리

현대 양자화 포맷의 핵심을 다시 정리하면 다음과 같다:

- **INT8**: 검증된 표준. 범용 하드웨어에서 작동하며, SmoothQuant로 outlier 문제를 해결
- **FP8**: INT8의 한계를 극복. Hopper GPU부터 네이티브 지원, 학습+추론 통합 가능
- **INT4 (GPTQ/AWQ)**: 극한 압축. 정교한 알고리즘으로 4비트에서도 높은 정확도 유지
- **NF4**: 정규분포 기반 최적 양자화. QLoRA의 핵심, 파인튜닝에 특화
- **NVFP4**: 4비트 부동소수점의 하드웨어 네이티브 지원. Blackwell GPU에서 차세대 표준

[[inference-optimization-mfu|추론 최적화 가이드]]에서 설명한 것처럼, 양자화는 메모리 대역폭 병목을 해소하는 가장 직접적인 수단이다. 어떤 포맷을 선택하느냐는 보유 GPU, 모델 크기, 태스크 요구 정밀도의 세 축에서 결정되며, 이 글에서 다룬 비교표와 코드 예제가 그 판단에 도움이 되기를 바란다.
