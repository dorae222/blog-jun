## 개요

Qwen2.5는 Alibaba Cloud의 Qwen 팀이 발표한 차세대 대규모 언어 모델(LLM) 시리즈로, 이전 버전인 [[qwen2|Qwen2]]를 기반으로 사전학습 데이터 규모, 후처리 정렬 기법, 실용적 기능 전반에 걸쳐 대폭적인 개선을 이루었습니다. 본 기술 보고서는 Qwen2.5의 설계 철학, 학습 방법론, 평가 결과를 포괄적으로 다루고 있습니다.

Qwen2.5 시리즈는 **0.5B, 1.5B, 3B, 7B, 14B, 32B, 72B**의 7가지 파라미터 규모로 제공됩니다. 이는 모바일 기기나 엣지 환경(0.5B~3B)부터 데이터센터급 고성능 추론(32B~72B)까지 다양한 배포 시나리오를 아우르기 위한 전략적 선택입니다. 또한 코딩 전용 모델인 **Qwen2.5-Coder**와 수학 전용 모델인 **Qwen2.5-Math**가 별도로 공개되어 도메인 특화 활용도를 극대화하였습니다.

핵심 성과를 요약하면 다음과 같습니다:

- 총 **18조(18T) 토큰**의 고품질 사전학습 데이터 활용 (Qwen2 대비 약 2.5배 증가)
- 72B 모델 기준 MMLU 86.1, HumanEval 92.7, MATH 83.1 달성
- 기본 128K 토큰 컨텍스트 윈도우, YaRN 기반 확장 시 최대 1M 토큰 지원
- 구조화된 JSON 출력, 다중 에이전트 협업, 도구 호출 기능 강화
- Apache 2.0 라이선스 기반 오픈소스 공개

---

## 배경 및 문제

### 오픈소스 LLM의 현황

2024년을 기점으로 오픈소스 LLM 생태계는 급격한 성장을 이루었습니다. Meta의 Llama 시리즈, Mistral AI의 Mixtral, Google의 Gemma 등이 경쟁적으로 공개되면서, 상용 모델과 오픈소스 모델 간의 성능 격차가 빠르게 줄어들었습니다. 그러나 여전히 몇 가지 근본적인 과제가 남아 있었습니다.

첫째, **사전학습 데이터의 품질과 규모** 문제입니다. 대부분의 오픈소스 모델은 공개 웹 크롤링 데이터에 의존하며, 데이터 품질 필터링 파이프라인의 정교함에서 상용 모델 대비 열위에 있었습니다. 특히 코딩과 수학 영역에서 고품질 학습 데이터의 부족이 성능 격차의 주요 원인이었습니다.

둘째, **긴 컨텍스트 처리 능력**의 한계입니다. 실무에서는 수십 페이지의 문서 분석, 대규모 코드베이스 이해, 장시간 대화 유지 등 긴 컨텍스트가 필수적이지만, 대부분의 모델은 8K~32K 토큰 수준에 머물러 있었습니다.

셋째, **구조화된 출력과 도구 사용 능력**의 부족입니다. API 서빙 환경에서 JSON 스키마 준수, 함수 호출 정확도, 에이전트 프레임워크와의 통합 등은 상용 모델(GPT-4, Claude 등)이 명확한 우위를 가지고 있었습니다.

Qwen2.5는 이러한 세 가지 핵심 과제를 체계적으로 해결하기 위해 설계되었습니다.

### Qwen2 대비 개선 방향

Qwen2는 2024년 중반에 공개되어 약 7T 토큰으로 사전학습된 모델이었습니다. Qwen2.5에서는 다음과 같은 방향으로 개선이 이루어졌습니다:

- 사전학습 데이터를 7T에서 18T 토큰으로 약 2.5배 확대
- 코드 및 수학 관련 데이터의 비중을 대폭 강화
- 합성 데이터(synthetic data) 파이프라인을 고도화하여 고품질 학습 데이터 생성
- 후처리 정렬(post-training alignment) 파이프라인에 DPO(Direct Preference Optimization) 도입
- 장문 컨텍스트 처리를 위한 YaRN 기반 위치 임베딩 확장 적용

---

## 핵심 아이디어

Qwen2.5의 핵심 설계 원칙은 크게 세 가지로 요약할 수 있습니다.

### 1. 데이터 중심 접근법 (Data-Centric Approach)

모델 아키텍처의 급진적 변경보다는 사전학습 데이터의 양과 질을 극대화하는 것에 집중하였습니다. 18T 토큰의 데이터는 단순히 양적 확대만이 아니라, 정교한 다단계 필터링 파이프라인을 통해 품질을 보장하였습니다. 특히 코딩과 수학 데이터는 별도의 품질 검증 프로세스를 거쳐 선별되었으며, GPT-4 기반 합성 데이터 생성을 통해 부족한 영역을 보완하였습니다.

### 2. 스케일링 효율성 (Scaling Efficiency)

동일한 아키텍처 패밀리 내에서 0.5B부터 72B까지 넓은 범위의 모델을 제공함으로써, 각 배포 환경에 최적화된 모델을 선택할 수 있게 하였습니다. 주목할 점은 Qwen2.5-7B가 이전 세대 Qwen2-72B에 근접하는 성능을 보인다는 것으로, 이는 사전학습 데이터 확대와 학습 방법론 개선의 시너지 효과를 보여줍니다.

### 3. 실용적 기능 강화 (Practical Capability Enhancement)

학술적 벤치마크 성능뿐 아니라, 실제 응용에서 필요한 구조화된 출력(JSON 모드), 도구 호출(function calling), 다중 에이전트 시스템 통합, 코드 실행 기반 추론 등의 기능을 체계적으로 강화하였습니다. 이는 LLM이 단순한 텍스트 생성기를 넘어 소프트웨어 시스템의 핵심 구성 요소로 활용되는 현실적 수요를 반영한 것입니다.

---

## 방법론

### 아키텍처

Qwen2.5는 Transformer 디코더 전용(decoder-only) 아키텍처를 기반으로 하며, 다음의 핵심 구성 요소를 포함합니다. 아래 그림은 Qwen2.5의 전체 아키텍처 구조를 보여주며, 각 Transformer 블록이 Pre-RMSNorm, GQA, SwiGLU FFN, Residual Connection으로 구성되는 방식을 시각화한 것입니다.

![Qwen2.5 아키텍처 다이어그램 - Transformer 디코더 블록 구조와 핵심 설계 요소](figures/architecture.png)
*Qwen2.5의 아키텍처 개요. Input Embedding 이후 24~80개의 Transformer 블록을 거치며, 각 블록은 Pre-RMSNorm 정규화 후 Grouped-Query Attention(GQA)과 SwiGLU FFN을 순차적으로 적용한다. 위치 인코딩에는 RoPE(Rotary)를 사용하고, 모델 규모는 0.5B~72B까지 지원한다.*

#### Grouped Query Attention (GQA)

표준 Multi-Head Attention(MHA)에서는 쿼리, 키, 밸류 모두 동일한 수의 헤드를 사용하여 KV 캐시 메모리가 모델 크기에 비례하여 증가합니다. GQA는 키와 밸류의 헤드 수를 줄여 메모리 효율을 개선하면서도 성능 저하를 최소화하는 기법입니다:

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

여기서 $Q \in \mathbb{R}^{n_h \times d_k}$, $K, V \in \mathbb{R}^{n_{kv} \times d_k}$이며, $n_{kv} \ll n_h$로 설정합니다. 72B 모델의 경우 $n_h = 64$, $n_{kv} = 8$로 설정하여 KV 캐시를 8배 절감하면서도 MHA와 거의 동등한 품질을 유지합니다. 각 KV 헤드는 $n_h / n_{kv} = 8$개의 쿼리 헤드 그룹과 공유됩니다.

#### Rotary Position Embedding (RoPE)

위치 정보를 쿼리와 키 벡터에 회전 변환으로 인코딩하는 기법입니다. 절대 위치 임베딩과 달리 내적 계산 시 자연스럽게 상대 위치 정보를 캡처할 수 있습니다:

$$f_q(x_m, m) = (W_q x_m) e^{im\theta}, \quad f_k(x_n, n) = (W_k x_n) e^{in\theta}$$

여기서 $\theta_j = 10000^{-2j/d}$는 주파수 파라미터입니다. 쿼리와 키의 내적은 다음과 같이 상대 위치 $m - n$에만 의존합니다:

$$\langle f_q(x_m, m), f_k(x_n, n) \rangle = \text{Re}\left[(W_q x_m)(W_k x_n)^* e^{i(m-n)\theta}\right]$$

이 특성 덕분에 RoPE는 학습 시 보지 못한 긴 시퀀스에 대해서도 일반화가 가능합니다.

#### YaRN (Yet another RoPE extensioN)

기본 학습 길이를 초과하는 시퀀스를 처리하기 위해 YaRN 기법을 적용하였습니다. YaRN은 RoPE의 주파수 파라미터를 동적으로 조정하여 128K 기본 컨텍스트를 최대 1M 토큰까지 확장합니다:

$$\theta_j' = \theta_j \cdot s^{-2j/d}, \quad s = \frac{L_{\text{target}}}{L_{\text{base}}}$$

여기서 $s$는 스케일 팩터, $L_{\text{target}}$은 목표 컨텍스트 길이, $L_{\text{base}}$는 기본 학습 길이입니다.

#### SwiGLU 활성화 함수

피드포워드 네트워크(FFN)에 SwiGLU 활성화 함수를 사용합니다. 기존 ReLU나 GELU 대비 학습 효율이 높으며, 게이팅 메커니즘을 통해 정보의 선택적 전달이 가능합니다:

$$\text{FFN}_{\text{SwiGLU}}(x) = (\text{Swish}(xW_1) \odot xW_2) W_3$$

$$\text{Swish}(x) = x \cdot \sigma(x) = \frac{x}{1 + e^{-x}}$$

여기서 $W_1, W_2 \in \mathbb{R}^{d \times d_{ff}}$, $W_3 \in \mathbb{R}^{d_{ff} \times d}$이고, $\odot$는 원소별 곱셈, $\sigma$는 시그모이드 함수입니다.

#### RMSNorm

각 서브레이어의 정규화에 RMSNorm을 사용합니다. 표준 LayerNorm 대비 평균 계산을 생략하여 연산 효율을 높입니다:

$$\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{d}\sum_{i=1}^{d} x_i^2 + \epsilon}} \cdot \gamma$$

### 모델 사양

다음 표는 Qwen2.5 시리즈의 각 모델별 상세 사양을 정리한 것입니다.

| 모델 | 파라미터 수 | 레이어 수 | 히든 차원 | 쿼리 헤드 | KV 헤드 | FFN 차원 | 컨텍스트 길이 |
|---|---|---|---|---|---|---|---|
| Qwen2.5-0.5B | 0.49B | 24 | 896 | 14 | 2 | 4,864 | 32K |
| Qwen2.5-1.5B | 1.54B | 28 | 1,536 | 12 | 2 | 8,960 | 128K |
| Qwen2.5-3B | 3.09B | 36 | 2,048 | 16 | 2 | 11,008 | 128K |
| Qwen2.5-7B | 7.61B | 28 | 3,584 | 28 | 4 | 18,944 | 128K |
| Qwen2.5-14B | 14.7B | 48 | 5,120 | 40 | 8 | 13,824 | 128K |
| Qwen2.5-32B | 32.5B | 64 | 5,120 | 40 | 8 | 27,648 | 128K |
| Qwen2.5-72B | 72.7B | 80 | 8,192 | 64 | 8 | 29,568 | 128K |

모든 모델은 공통적으로 RoPE, GQA, SwiGLU, RMSNorm을 사용하며, 어휘 크기는 151,646 토큰입니다. Tiktoken 기반 BPE 토크나이저를 사용하여 다국어 토큰화 효율을 극대화하였습니다.

### 사전학습 (Pre-training)

#### 데이터 구성

Qwen2.5의 사전학습 데이터는 총 18T 토큰 규모이며, 다음과 같이 구성됩니다.

| 데이터 유형 | 비중 (추정) | 설명 |
|---|---|---|
| 일반 웹 텍스트 | 약 45% | Common Crawl 기반, 다단계 품질 필터링 적용, 30개 이상 언어 |
| 코드 | 약 18% | GitHub, Stack 등에서 수집, 92개 프로그래밍 언어 |
| 수학 | 약 12% | 교과서, 논문, 수학 포럼, 합성 데이터 |
| 합성 데이터 | 약 20% | GPT-4 기반 생성, 지시 따르기 및 추론 데이터 |
| 기타 (서적, 논문 등) | 약 5% | 학술 논문, 위키피디아, 전문 서적 |

데이터 품질 관리를 위해 다단계 파이프라인을 운용합니다. 언어 식별, 중복 제거(deduplication), 유해 콘텐츠 필터링, 품질 분류기(quality classifier) 적용, 도메인별 균형 조정 등의 단계를 거칩니다. 특히 품질 분류기는 자체 학습된 모델로, 웹 페이지의 교육적 가치와 정보 밀도를 기준으로 점수를 매깁니다.

#### 학습 절차

사전학습은 표준 자기회귀(autoregressive) 언어 모델링 목표를 따릅니다:

$$\mathcal{L}_{\text{pretrain}} = -\sum_{t=1}^{T} \log P_\theta(x_t \mid x_1, x_2, \ldots, x_{t-1})$$

학습은 여러 단계에 걸쳐 진행됩니다. 초기에는 4K 토큰 시퀀스 길이로 대부분의 학습을 수행하고, 이후 32K, 128K로 점진적으로 확장합니다. 이렇게 단계적으로 시퀀스 길이를 늘리는 방식은 학습 안정성과 효율성을 동시에 확보하기 위함입니다.

옵티마이저는 AdamW를 사용하며, 학습률은 워밍업 이후 코사인 감소 스케줄을 따릅니다. 72B 모델의 경우 최대 학습률 $3 \times 10^{-4}$, 배치 크기 약 4M 토큰으로 학습되었습니다.

### 후처리 정렬 (Post-Training Alignment)

사전학습 이후 모델의 유용성과 안전성을 높이기 위한 후처리 과정은 두 단계로 구성됩니다.

#### SFT (Supervised Fine-Tuning)

고품질 지시-응답(instruction-response) 쌍을 활용하여 미세조정합니다. SFT 데이터는 다음과 같은 다양한 태스크를 포함합니다:

- 일반 질의응답 및 대화
- 코드 생성 및 디버깅
- 수학 문제 풀이 (Chain-of-Thought 방식)
- 구조화된 출력 (JSON, XML 등)
- 도구 호출 및 함수 실행
- 다국어 번역 및 요약
- 장문 컨텍스트 이해 및 추론

#### RLHF / DPO

인간 선호도 데이터를 활용하여 모델의 응답 품질을 추가로 개선합니다. Qwen2.5에서는 기존 PPO(Proximal Policy Optimization) 기반 RLHF 외에 DPO(Direct Preference Optimization)도 함께 적용하였습니다.

DPO는 별도의 보상 모델 없이 선호도 데이터로부터 직접 정책을 최적화합니다:

$$\mathcal{L}_{\text{DPO}}(\pi_\theta; \pi_{\text{ref}}) = -\mathbb{E}_{(x, y_w, y_l)}\left[\log \sigma\left(\beta \log \frac{\pi_\theta(y_w|x)}{\pi_{\text{ref}}(y_w|x)} - \beta \log \frac{\pi_\theta(y_l|x)}{\pi_{\text{ref}}(y_l|x)}\right)\right]$$

여기서 $y_w$는 선호 응답, $y_l$은 비선호 응답, $\pi_{\text{ref}}$는 참조 정책(SFT 모델), $\beta$는 KL 발산 제약 강도를 조절하는 하이퍼파라미터입니다.

안전성 정렬 과정에서는 문화적 맥락을 고려한 세밀한 데이터 구축이 필요합니다. 아래 그림은 다양한 모델과 인간 주석자가 중국어 혐오 표현을 어떻게 해석하는지 비교한 사례 연구로, 동일한 텍스트에 대해서도 모델마다 문화적 맥락에 대한 이해도가 크게 달라질 수 있음을 보여줍니다.

![Qwen2.5 안전성 평가 사례 연구 - 모델 간 문화적 맥락 이해 비교](figures/fig_1.png)
*Qwen2.5 안전성 평가 사례 연구. ShieldGemma-9B, DeepSeek-v3, 인간 주석자가 혐오 표현이 포함된 중국어 텍스트를 해석하는 방식을 비교한 것으로, 각 모델의 문화적 맥락 이해 능력 차이를 보여준다. 이러한 분석을 바탕으로 Qwen2.5의 안전성 정렬 데이터가 설계되었다.*

### Qwen2.5-Coder

코딩 특화 변형 모델인 Qwen2.5-Coder는 기본 모델에 **5.5T 토큰의 코드 관련 데이터**로 추가 사전학습을 수행하였습니다. 92개 프로그래밍 언어를 지원하며, 코드 생성, 코드 완성, 버그 수정, 코드 리뷰, 테스트 생성 등 폭넓은 코딩 태스크에 최적화되어 있습니다.

학습 데이터는 GitHub 공개 저장소, Stack Overflow, 프로그래밍 교재, 기술 문서 등에서 수집되었으며, 코드 품질 분류기를 통해 고품질 코드만을 선별하였습니다. 특히 저장소 수준(repo-level) 코드 이해를 강화하기 위해 파일 간 의존성을 보존한 학습 데이터 구성을 적용하였습니다.

### Qwen2.5-Math

수학 특화 변형 모델인 Qwen2.5-Math는 **Process Reward Model(PRM)**을 도입하여 추론 과정의 각 단계별 정확성을 검증합니다. 기존의 Outcome Reward Model(ORM)이 최종 답만을 평가하는 것과 달리, PRM은 중간 추론 단계의 논리적 정합성을 세밀하게 평가합니다.

Chain-of-Thought(CoT) 방식과 Tool-Integrated Reasoning(TIR) 방식을 모두 지원합니다. TIR은 Python 코드 실행을 통해 계산 정확도를 높이는 기법으로, 복잡한 수치 계산이 포함된 문제에서 특히 효과적입니다.

---

## 실험 결과

### 종합 벤치마크

다음 표는 Qwen2.5-72B-Instruct와 주요 경쟁 모델의 종합 벤치마크 성능을 비교한 것입니다.

| 모델 | MMLU | MMLU-Pro | HumanEval | MBPP | MATH | GSM8K | ARC-C | IFEval |
|---|---|---|---|---|---|---|---|---|
| **Qwen2.5-72B-Instruct** | **86.1** | **71.1** | **92.7** | **88.2** | **83.1** | **95.9** | **68.3** | **86.5** |
| GPT-4o (2024-08) | 85.7 | 72.6 | 90.2 | 87.0 | 76.6 | 94.8 | 66.4 | 84.9 |
| Claude 3.5 Sonnet | 88.7 | 78.0 | 92.0 | 91.0 | 71.1 | 96.4 | 65.0 | 88.0 |
| Llama-3.1-70B-Instruct | 83.6 | 66.4 | 80.5 | 82.4 | 64.7 | 92.1 | 63.6 | 83.6 |
| Mistral-Large-2 (123B) | 84.0 | 69.4 | 92.1 | 85.5 | 74.1 | 93.8 | 64.3 | 85.1 |
| Qwen2-72B-Instruct | 82.3 | 64.4 | 86.0 | 80.2 | 69.6 | 93.0 | 60.8 | 77.6 |

Qwen2.5-72B-Instruct는 MMLU 86.1로 GPT-4o(85.7)를 소폭 상회하며, HumanEval 92.7과 MATH 83.1에서는 경쟁 모델 대비 현저한 우위를 보입니다. 특히 이전 세대 Qwen2-72B-Instruct 대비 전 영역에서 큰 폭의 성능 향상을 달성하였으며, MATH 벤치마크에서는 69.6에서 83.1로 약 13.5점이 상승하여 데이터 확대와 학습 방법론 개선의 효과가 극적으로 나타났습니다.

한편, Claude 3.5 Sonnet이 MMLU(88.7)와 MMLU-Pro(78.0)에서 여전히 우위를 보이는 점은 주목할 만합니다. 이는 범용 지식 이해 영역에서는 상용 모델과의 격차가 완전히 해소되지 않았음을 시사합니다.

### 모델 크기별 성능 비교

소형 모델의 성능 또한 주목할 만합니다. 아래 표는 Qwen2.5의 다양한 크기 모델과 경쟁 모델 간의 성능을 비교한 것으로, 데이터 품질 향상이 모델 크기를 뛰어넘는 성능 개선을 가져올 수 있음을 보여줍니다.

| 모델 | MMLU | HumanEval | MATH | GSM8K |
|---|---|---|---|---|
| Qwen2.5-7B-Instruct | 74.2 | 84.8 | 75.5 | 91.6 |
| Qwen2.5-14B-Instruct | 79.9 | 88.4 | 80.0 | 94.3 |
| Qwen2.5-32B-Instruct | 83.3 | 90.9 | 81.6 | 95.1 |
| Llama-3.1-8B-Instruct | 69.4 | 72.6 | 47.2 | 84.5 |
| Llama-3.1-70B-Instruct | 83.6 | 80.5 | 64.7 | 92.1 |
| Qwen2-72B-Instruct | 82.3 | 86.0 | 69.6 | 93.0 |

Qwen2.5-7B-Instruct가 MATH 75.5를 기록하여 이전 세대의 Qwen2-72B-Instruct(69.6)를 오히려 능가한 점이 가장 인상적입니다. 파라미터 수가 10분의 1에 불과한 모델이 수학 추론에서 더 높은 성능을 보인다는 것은, 18T 토큰의 고품질 데이터와 개선된 합성 데이터 파이프라인이 모델 크기의 한계를 보상할 수 있음을 실증합니다. 비슷한 크기의 Llama-3.1-8B-Instruct(MATH 47.2)와 비교하면 그 격차는 더욱 극명합니다.

### 코딩 벤치마크

| 모델 | HumanEval | HumanEval+ | MBPP | MBPP+ | LiveCodeBench | BigCodeBench |
|---|---|---|---|---|---|---|
| **Qwen2.5-Coder-32B-Instruct** | **92.7** | **87.2** | **90.9** | **78.1** | **67.3** | **53.2** |
| GPT-4o (2024-08) | 90.2 | 86.0 | 87.0 | 72.7 | 62.4 | 51.1 |
| Claude 3.5 Sonnet | 92.0 | 86.6 | 91.0 | 76.1 | 65.9 | 56.2 |
| DeepSeek-Coder-V2 | 90.2 | 84.8 | 89.4 | 73.9 | 60.1 | 48.5 |

Qwen2.5-Coder-32B-Instruct는 HumanEval 92.7, LiveCodeBench 67.3으로 GPT-4o를 상회하는 코딩 성능을 보여줍니다. 특히 LiveCodeBench는 데이터 오염(contamination) 위험이 낮은 최신 벤치마크로, 이 지표에서의 우위는 실질적인 코딩 능력을 반영합니다. 다만 BigCodeBench에서는 Claude 3.5 Sonnet(56.2)이 여전히 앞서 있어, 복잡한 실세계 코딩 태스크에서의 개선 여지가 남아 있습니다.

### 수학 벤치마크

Qwen2.5-Math-72B-Instruct는 수학 전문 벤치마크에서 최고 수준의 성능을 달성하였습니다:

- MATH: 85.9 (CoT) / 90.3 (TIR)
- GSM8K: 96.8
- AIME 2024: 29/30 문제 정답
- AMC 2023: 40/40 문제 정답

TIR(Tool-Integrated Reasoning) 모드에서는 Python 코드 실행을 활용하여 MATH 점수가 85.9에서 90.3으로 4.4점 상승하며, 계산 정확도가 중요한 문제에서의 효과를 입증합니다. AMC 2023 만점 달성은 고등학교 수준의 수학 경시대회 문제를 완벽하게 풀어낼 수 있는 수준에 도달했음을 의미합니다.

### 장문 컨텍스트 평가

128K 컨텍스트 윈도우의 실효성을 검증하기 위해 RULER(Really Useful Long-context Evaluation Resource) 벤치마크에서 평가하였습니다. Qwen2.5-72B는 128K 토큰 길이에서도 90% 이상의 정확도를 유지하며, 이는 동급 모델 중 최상위 수준입니다.

YaRN을 통해 1M 토큰까지 확장한 경우에도 실용적인 추론 속도를 유지하는 것이 중요합니다. 아래 그림은 컨텍스트 길이에 따른 첫 토큰 생성 시간(TTFT)을 Full Attention과 Qwen 팀의 최적화 방법으로 비교한 것입니다.

![Qwen2.5-7B의 컨텍스트 길이별 첫 토큰 생성 시간(TTFT) 비교 - H20 GPU 기준](figures/p18_fig01.png)
*Qwen2.5-7B 모델의 H20 GPU에서 컨텍스트 길이별 TTFT(Time To First Token) 비교. Full Attention 방식은 컨텍스트 길이가 200K에서 1M으로 증가할 때 TTFT가 약 20배(~17초에서 ~340초) 급증하는 반면, 최적화 방법(Our Method)은 약 8배(~7초에서 ~60초) 수준으로 증가를 억제한다. 1M 토큰 시점에서 약 5.7배의 속도 향상을 달성하였다.*

---

## 의의 및 한계

### 의의

**오픈소스 LLM의 새로운 이정표**: Qwen2.5-72B는 Apache 2.0 라이선스로 공개된 모델 중 GPT-4 수준에 가장 근접한 성능을 달성하였습니다. 이는 LLM 기술의 민주화 측면에서 중요한 의미를 가집니다. 연구자와 기업이 상용 API에 의존하지 않고도 최고 수준의 LLM을 활용할 수 있게 되었습니다.

**효율적 스케일링의 실증**: 소형 모델(0.5B~7B)이 이전 세대의 훨씬 큰 모델과 경쟁할 수 있는 성능을 보이는 것은, 모델 크기 증가만이 아닌 데이터 품질 향상과 학습 방법론 개선이 성능 향상의 핵심 동력임을 실증합니다. 이는 엣지 디바이스, 모바일 환경에서의 LLM 배포 가능성을 크게 높입니다.

**도메인 특화 전략의 성공**: Qwen2.5-Coder와 Qwen2.5-Math의 성공은 범용 모델에 도메인 특화 데이터와 기법을 추가 적용하는 접근법의 실효성을 입증합니다. 특히 Process Reward Model과 Tool-Integrated Reasoning의 결합은 수학적 추론 영역에서 새로운 패러다임을 제시합니다.

**다국어 지원 강화**: 29개 이상의 언어를 지원하며, 한국어, 일본어, 아랍어 등 비영어권 언어에서도 개선된 성능을 보입니다. 이는 영어 중심 학습 데이터에 편중된 기존 모델들의 한계를 일정 부분 극복한 것입니다.

**실용적 기능의 체계적 강화**: JSON 모드, 함수 호출, 에이전트 프레임워크 통합 등은 LLM이 소프트웨어 시스템에 깊숙이 통합되는 현실적 요구를 반영합니다. IFEval 86.5의 높은 점수는 지시 따르기 능력이 실제 응용에서 충분히 활용 가능한 수준임을 보여줍니다.

### 한계

**추론 비용**: 72B 모델은 최소 A100 80GB GPU 2장 이상을 요구하며, 이는 일반 사용자나 소규모 기업에게 여전히 높은 진입 장벽입니다. 양자화(quantization) 기법으로 일부 완화 가능하지만, 성능 손실이 수반됩니다.

**환각(Hallucination)**: 사실 오류나 근거 없는 정보 생성 문제는 완전히 해결되지 않았습니다. 특히 최신 이벤트나 학습 데이터에 포함되지 않은 주제에 대해서는 자신 있게 잘못된 정보를 생성할 수 있습니다.

**멀티모달 제약**: Qwen2.5는 텍스트 전용 모델로, 이미지, 오디오, 비디오 처리는 별도의 Qwen-VL, Qwen-Audio 시리즈에서 다룹니다. 통합 멀티모달 모델에 비해 크로스모달 추론 능력에 한계가 있습니다.

**평가 데이터 오염 가능성**: 18T 토큰의 대규모 웹 크롤링 데이터에 벤치마크 문제가 포함될 가능성이 있습니다. LiveCodeBench 같은 시간 제한 벤치마크에서의 높은 성능이 이 우려를 일부 불식시키지만, 모든 벤치마크에 대해 완전한 오염 방지를 보장하기는 어렵습니다.

**추론 능력의 한계**: Chain-of-Thought 방식으로 복잡한 추론 문제를 해결할 수 있지만, 다단계 논리적 추론이나 반직관적인 문제에서는 여전히 실수를 보입니다. 이는 o1이나 DeepSeek-R1 같은 추론 특화 모델과의 차별점이기도 합니다.

---

## 코드 예제

### HuggingFace Transformers를 이용한 기본 추론

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "Qwen/Qwen2.5-72B-Instruct"

# 토크나이저 및 모델 로딩
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="auto",
    device_map="auto"
)

# 대화 메시지 구성
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is the integral of x^2?"}
]

# 추론 실행
text = tokenizer.apply_chat_template(
    messages, tokenize=False, add_generation_prompt=True
)
model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

generated_ids = model.generate(
    **model_inputs,
    max_new_tokens=512,
    temperature=0.7,
    top_p=0.9
)
output = tokenizer.batch_decode(
    generated_ids[:, model_inputs.input_ids.shape[1]:],
    skip_special_tokens=True
)[0]
print(output)
```

### vLLM을 이용한 고속 서빙

```python
from vllm import LLM, SamplingParams

# vLLM 엔진 초기화 (텐서 병렬 처리)
llm = LLM(
    model="Qwen/Qwen2.5-72B-Instruct",
    tensor_parallel_size=2,  # GPU 2장 사용
    max_model_len=32768
)

sampling_params = SamplingParams(
    temperature=0.7,
    top_p=0.9,
    max_tokens=1024
)

# 배치 추론
prompts = [
    "Explain the concept of attention mechanism in transformers.",
    "Write a Python function to find the longest common subsequence."
]
outputs = llm.generate(prompts, sampling_params)

for output in outputs:
    print(output.outputs[0].text)
```

### JSON 구조화 출력 예제

```python
import json
from transformers import AutoModelForCausalLM, AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")
model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-7B-Instruct",
    torch_dtype="auto",
    device_map="auto"
)

# JSON 스키마를 시스템 프롬프트에 지정
system_prompt = """You are a helpful assistant that extracts information
and returns it in JSON format. Always respond with valid JSON matching
the schema: {"name": str, "age": int, "skills": [str]}"""

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": "John is 28 years old and knows Python, Rust, and Go."}
]

text = tokenizer.apply_chat_template(
    messages, tokenize=False, add_generation_prompt=True
)
model_inputs = tokenizer([text], return_tensors="pt").to(model.device)
generated_ids = model.generate(**model_inputs, max_new_tokens=256)
result = tokenizer.batch_decode(
    generated_ids[:, model_inputs.input_ids.shape[1]:],
    skip_special_tokens=True
)[0]

# 결과를 JSON으로 파싱
parsed = json.loads(result)
print(json.dumps(parsed, indent=2))
```

---

## 관련 문서

- [[qwen2|Qwen2 Technical Report]] -- Qwen2.5의 기반 모델
- [[qwen3|Qwen3]] -- 후속 모델
