## 개요

OLMo(Open Language Model)는 Allen Institute for AI(AI2)가 2024년 ACL에서 발표한 대규모 언어 모델이다. OLMo의 핵심 목표는 이름 그대로 "진정한 의미의 오픈" 모델을 구축하는 것이다. 기존의 이른바 "오픈소스" LLM들이 모델 가중치만 공개하는 관행이 지배적이었던 반면, OLMo는 **학습 코드, 사전학습 데이터(Dolma), 2,500개 이상의 중간 체크포인트, WandB 학습 로그, 평가 프레임워크(Catwalk, Paloma)**까지 모두 Apache 2.0 라이선스로 공개한다.

이 논문의 핵심 메시지는 "언어 모델의 과학(Science of Language Models)을 가속화하자"는 것이다. LLM 연구가 소수의 거대 기업에 집중되고 재현 불가능한 실험들이 난무하는 상황에서, OLMo는 완전한 투명성을 통해 모든 연구자가 LLM을 독립적으로 연구하고 발전시킬 수 있는 기반을 제공한다. 이는 단일 모델을 공개하는 것이 아니라, **LLM 연구를 위한 완전한 생태계를 구축**하겠다는 야심찬 프로젝트이다.

OLMo는 7B와 1B 두 가지 크기로 제공되며, 총 2.46T 토큰의 Dolma 데이터셋으로 학습되었다. 아키텍처 측면에서는 decoder-only Transformer를 기반으로 SwiGLU 활성화 함수, RoPE(Rotary Position Embedding), non-parametric Layer Normalization 등 최신 기법들을 채택하였다.

---

## 배경 및 문제

### 오픈소스 LLM의 현실

2023~2024년 사이 LLM 분야는 폭발적 성장을 이루었으며, Meta의 [[llama|LLaMA]], Falcon, MPT, Mistral 등 다양한 "오픈소스" 모델들이 등장하였다. 그러나 이들 대부분은 **가중치만 공개**하는 수준에 그쳤다. 학습 데이터의 구성, 전처리 방법, 필터링 기준, 학습 중 발생한 문제와 해결 방법, 하이퍼파라미터 탐색 과정 등은 거의 공개되지 않았다.

이러한 상황이 야기하는 문제를 구체적으로 살펴보면 다음과 같다.

**재현 불가능성 (Irreproducibility)**: 모델 가중치만으로는 학습 과정을 재현할 수 없다. 특정 데이터 구성이 성능에 미치는 영향을 연구하려 해도, 원래 학습에 사용된 데이터와 설정을 알 수 없으므로 통제된 비교 실험이 불가능하다.

**연구 병목 현상 (Research Bottleneck)**: LLM 사전학습은 수백만 달러 규모의 계산 자원을 요구한다. 학습 과정의 노하우가 공유되지 않으면 각 연구 그룹이 동일한 실수를 반복하게 되어 전체 분야의 발전 속도가 저하된다. 이는 단순한 비효율이 아니라, 학술 연구 자체의 기회 비용을 극대화하는 구조적 문제이다.

**오픈워싱 (Openwashing)**: 가중치만 공개하고 "오픈소스"를 표방하는 관행은 진정한 의미의 오픈 사이언스와 거리가 멀다. 모델의 내부를 이해하고 개선하기 위해서는 학습의 모든 측면에 대한 접근이 필수적이다.

**데이터 연구의 부재**: LLM의 성능은 아키텍처뿐 아니라 학습 데이터의 품질과 구성에 크게 의존한다. 그러나 학습 데이터가 비공개인 상황에서 데이터-성능 관계에 대한 체계적 연구는 사실상 불가능하다.

### 오픈의 스펙트럼

기존 모델들의 공개 수준을 비교하면 OLMo의 차별성이 명확해진다.

| 공개 요소 | GPT-4 | LLaMA 2 | Falcon | MPT | OLMo |
|---|---|---|---|---|---|
| 모델 가중치 | X | O | O | O | O |
| 학습 코드 | X | X | X | O | O |
| 학습 데이터 | X | X | 부분 | X | O |
| 데이터 전처리 코드 | X | X | X | X | O |
| 중간 체크포인트 | X | X | X | X | O |
| 학습 로그 | X | X | X | X | O |
| 평가 프레임워크 | X | X | X | X | O |
| 라이선스 | 상용 | 커뮤니티 | Apache 2.0 | Apache 2.0 | Apache 2.0 |

이 표에서 볼 수 있듯이, OLMo는 LLM 연구에 필요한 모든 구성 요소를 완전히 공개한 최초의 모델이다. MPT가 학습 코드를 공개한 것이 당시로서는 진일보한 것이었지만, OLMo는 데이터 전처리, 중간 체크포인트, 학습 로그까지 포함하여 "오픈소스"의 의미를 근본적으로 재정의한다.

---

## 핵심 아이디어

OLMo 프로젝트의 핵심 아이디어는 세 가지로 요약할 수 있다.

### 1. 완전한 투명성 (Full Transparency)

OLMo는 LLM의 모든 구성 요소를 공개한다.

| 공개 요소 | 내용 | 위치 |
|---|---|---|
| 모델 가중치 | 7B, 1B (Apache 2.0) | HuggingFace |
| 학습 코드 | PyTorch + FSDP 기반 | GitHub (allenai/OLMo) |
| 사전학습 데이터 | Dolma 3T 토큰 | HuggingFace (allenai/dolma) |
| 데이터 전처리 | 필터링, 중복 제거 파이프라인 | GitHub (allenai/dolma) |
| 중간 체크포인트 | 2,500개 이상 | AWS S3 |
| 학습 로그 | 전체 학습 곡선, 메트릭 | WandB |
| 평가 프레임워크 | Catwalk (다운스트림), Paloma (perplexity) | GitHub |

이러한 완전한 공개는 다음과 같은 연구를 가능하게 한다.

- 학습 과정의 완전한 재현 및 검증
- 특정 학습 단계에서의 모델 행동 분석 (예: 지식 획득 시점, 능력 발현 단계)
- 데이터 구성 변화가 모델 성능에 미치는 인과적 영향 연구
- 새로운 파인튜닝 방법론의 공정한 비교
- 학습 불안정성(loss spike) 원인 분석 및 해결 방법 연구

### 2. 재현 가능한 과학 (Reproducible Science)

과학적 방법론의 핵심은 재현 가능성이다. OLMo는 다른 연구자가 동일한 환경에서 동일한 결과를 얻을 수 있도록 모든 실험 조건을 투명하게 공유한다. 단순히 코드를 공개하는 것을 넘어, **학습 중 발생한 문제점과 해결 과정까지 문서화**한다는 점이 핵심이다.

예를 들어, 학습 과정에서 관찰된 loss spike의 원인(특정 데이터 배치의 품질 문제), 이를 해결하기 위한 데이터 필터링 전략의 수정, 수정 전후의 학습 곡선 비교까지 모두 공개되어 있다. 이는 대규모 학습에서 흔히 발생하지만 거의 논의되지 않는 엔지니어링 노하우를 공유한다는 점에서, 다른 연구 그룹에게 귀중한 자산이 된다.

### 3. 생태계 구축 (Ecosystem Building)

OLMo는 단일 모델이 아니라 하나의 생태계이다. 학습 데이터(Dolma), 학습 프레임워크(OLMo), 평가 도구(Catwalk, Paloma), 적응 도구(OLMo-adaptation) 등이 유기적으로 연결되어 LLM 연구의 전체 파이프라인을 지원한다. 이는 개별 구성 요소의 합 이상의 가치를 가진다. 연구자가 파이프라인의 어느 단계에서든 개입하여 실험할 수 있는 modular한 연구 인프라를 제공하기 때문이다.

---

## 방법론

### 아키텍처

![OLMo 아키텍처 다이어그램: Decoder-only Transformer 기반 구조](figures/architecture.png)
*OLMo의 전체 아키텍처 구조. Decoder-only Transformer 기반으로 RoPE 위치 인코딩, Non-parametric Layer Normalization, Multi-Head Attention, SwiGLU FFN을 채택한다. 1B / 7B / 65B 세 가지 스케일로 설계되었으며, 모델 가중치뿐 아니라 학습 코드와 데이터까지 완전히 공개하는 것이 핵심 설계 철학이다.*

OLMo는 표준 decoder-only Transformer를 기반으로 하며, 최신 아키텍처 연구의 성과를 반영한 여러 설계를 채택하였다.

**모델 사양 비교**

| 구성 요소 | OLMo-1B | OLMo-7B | OLMo-65B (계획) |
|---|---|---|---|
| 레이어 수 ($L$) | 16 | 32 | 80 |
| 히든 차원 ($d_{\text{model}}$) | 2,048 | 4,096 | 8,192 |
| FFN 차원 ($d_{\text{ff}}$) | 8,192 | 11,008 | 22,016 |
| 어텐션 헤드 수 ($n_{\text{heads}}$) | 16 | 32 | 64 |
| 헤드 차원 ($d_{\text{head}}$) | 128 | 128 | 128 |
| 컨텍스트 길이 | 2,048 | 2,048 | 2,048 |
| 어휘 크기 ($|V|$) | 50,280 | 50,280 | 50,280 |
| 총 파라미터 | 1.18B | 6.89B | ~65B |

아키텍처의 핵심 설계 선택을 하나씩 살펴보자.

#### SwiGLU 활성화 함수

OLMo는 피드포워드 네트워크(FFN)에 SwiGLU(Swish-Gated Linear Unit)를 채택한다. SwiGLU는 Shazeer(2020)가 제안한 GLU(Gated Linear Unit) 변형으로, 게이팅 메커니즘을 통해 정보 흐름을 제어한다.

일반적인 Transformer의 FFN은 다음과 같이 정의된다.

$$\text{FFN}(x) = \text{ReLU}(xW_1 + b_1)W_2 + b_2$$

SwiGLU FFN은 이를 다음과 같이 변형한다.

$$\text{SwiGLU}(x) = (\text{Swish}(xW_1) \odot xV) W_2$$

여기서 $\odot$는 원소별 곱(Hadamard product)이고, Swish 활성화 함수는 다음과 같다.

$$\text{Swish}(x) = x \cdot \sigma(\beta x) = \frac{x}{1 + e^{-\beta x}}$$

$\beta = 1$인 경우 SiLU(Sigmoid Linear Unit)와 동일하며, OLMo는 $\beta = 1$을 사용한다. SwiGLU는 두 개의 선형 변환 $W_1$과 $V$를 사용하므로 파라미터 수가 기존 FFN의 $\frac{2}{3}$ 비율이 되도록 $d_{\text{ff}}$를 조정한다. 구체적으로 OLMo-7B의 경우 $d_{\text{ff}} = \frac{8}{3} d_{\text{model}} = \frac{8}{3} \times 4096 \approx 10923$이지만, 하드웨어 효율을 위해 128의 배수인 11,008로 설정한다.

SwiGLU의 장점은 동일한 FLOPs 예산에서 표준 ReLU MLP 대비 일관되게 우수한 성능을 보이는 것으로, PaLM, LLaMA 등 최신 LLM에서 널리 채택되고 있다.

#### RoPE (Rotary Position Embedding)

OLMo는 절대 Positional Embedding이나 ALiBi 대신 RoPE(Su et al., 2021)를 채택한다. RoPE는 위치 정보를 복소수 공간에서의 회전으로 인코딩하는 방법이다.

쿼리 벡터 $\mathbf{q}$와 키 벡터 $\mathbf{k}$에 위치 정보를 주입하는 과정은 다음과 같다. 위치 $m$에서의 쿼리는 다음과 같이 회전된다.

$$f(\mathbf{q}, m) = \begin{pmatrix} q_0 \\ q_1 \\ q_2 \\ q_3 \\ \vdots \\ q_{d-2} \\ q_{d-1} \end{pmatrix} \otimes \begin{pmatrix} \cos m\theta_0 \\ \cos m\theta_0 \\ \cos m\theta_1 \\ \cos m\theta_1 \\ \vdots \\ \cos m\theta_{d/2-1} \\ \cos m\theta_{d/2-1} \end{pmatrix} + \begin{pmatrix} -q_1 \\ q_0 \\ -q_3 \\ q_2 \\ \vdots \\ -q_{d-1} \\ q_{d-2} \end{pmatrix} \otimes \begin{pmatrix} \sin m\theta_0 \\ \sin m\theta_0 \\ \sin m\theta_1 \\ \sin m\theta_1 \\ \vdots \\ \sin m\theta_{d/2-1} \\ \sin m\theta_{d/2-1} \end{pmatrix}$$

각 주파수 성분의 기저 주파수는 다음과 같이 정의된다.

$$\theta_j = 10000^{-2j/d}, \quad j = 0, 1, \ldots, d/2 - 1$$

RoPE의 핵심 성질은 두 위치 $m$, $n$에서의 쿼리-키 내적이 상대 위치 $m - n$의 함수가 된다는 것이다.

$$\langle f(\mathbf{q}, m), f(\mathbf{k}, n) \rangle = g(\mathbf{q}, \mathbf{k}, m - n)$$

이 성질 덕분에 RoPE는 상대 위치 인코딩의 이점을 가지면서도, 절대 위치 인코딩처럼 효율적으로 구현할 수 있다. 또한 학습 시 보지 못한 더 긴 시퀀스에 대한 외삽(extrapolation) 가능성도 제공한다.

#### Non-parametric Layer Normalization

OLMo는 학습 가능한 어파인 파라미터(scale $\gamma$, shift $\beta$)가 없는 비모수적(non-parametric) Layer Normalization을 사용한다.

$$\text{LayerNorm}(x) = \frac{x - \mu}{\sqrt{\sigma^2 + \epsilon}}$$

여기서 $\mu = \frac{1}{d}\sum_{i=1}^{d} x_i$, $\sigma^2 = \frac{1}{d}\sum_{i=1}^{d}(x_i - \mu)^2$이다.

이는 최근 LLM에서 자주 사용되는 RMSNorm과도 차이가 있다. RMSNorm은 평균 빼기를 생략하고 제곱 평균 제곱근만 사용한다.

$$\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{d}\sum_{i=1}^{d} x_i^2 + \epsilon}} \cdot \gamma$$

OLMo가 RMSNorm이 아닌 non-parametric LayerNorm을 선택한 것은 흥미로운 결정이다. LLaMA 계열이 RMSNorm을 표준으로 채택한 것과 달리, OLMo는 학습 파라미터 수를 최소화하면서 평균 제거(mean subtraction)를 통한 안정성을 유지하는 전략을 택했다. 이는 대규모 학습에서의 수치 안정성과 파라미터 효율 사이의 트레이드오프에 대한 AI2의 경험적 판단을 반영한다.

#### No Biases

OLMo는 모든 선형 변환(attention projection, feed-forward 레이어)에서 편향 항(bias)을 제거하였다. 이는 LLaMA, PaLM 등 최신 LLM의 설계 트렌드와 일치하며, 학습 안정성 향상과 파라미터 효율 개선에 기여한다.

### Dolma 데이터셋

Dolma(Data for Open Language Model Adaptation)는 OLMo 학습을 위해 AI2가 구축한 오픈소스 사전학습 데이터셋이다. 총 3T 토큰 규모이며, 다양한 소스에서 수집된 텍스트를 체계적으로 정제하여 구성하였다.

| 소스 | 토큰 수 | 학습 비중 | 설명 |
|---|---|---|---|
| Common Crawl | ~2.1T | 67% | 웹 크롤링 데이터, 품질 필터링 적용 |
| C4 | ~0.2T | 7% | Common Crawl 기반 정제 코퍼스 |
| GitHub 코드 | ~0.2T | 7% | 오픈소스 코드 저장소 |
| Stack (코드) | ~0.1T | 3% | 코드 데이터 보강 |
| 학술 논문 (S2ORC) | ~0.1T | 3% | Semantic Scholar 논문 |
| Wikipedia | ~0.04T | 1.5% | 영어 위키피디아 |
| OpenSubtitles | ~0.02T | 1% | 대화체 텍스트 |
| 도서 (Project Gutenberg) | ~0.05T | 2% | 공개 도서 |
| 기타 | ~0.1T | 8.5% | 다양한 소규모 소스 |

Dolma의 데이터 구성에서 특히 주목할 점은 **Common Crawl의 압도적 비중(67%)**이다. 이후 실험 결과에서 보겠지만, 이 데이터 분포 특성이 Paloma 벤치마크에서 C4 소스에 대한 OLMo의 우위를 직접적으로 설명한다. 학습 데이터와 모델이 함께 공개되어 있기에 이러한 인과적 분석이 가능하다는 것 자체가 OLMo의 가치를 증명한다.

Dolma의 데이터 처리 파이프라인은 다음 5단계로 구성된다.

**1단계 - 언어 필터링**: fastText 기반 언어 분류기를 사용하여 영어 텍스트만 선별한다.

**2단계 - 품질 필터링**: 규칙 기반(heuristic) 필터와 분류기 기반 필터를 조합하여 저품질 텍스트를 제거한다. 반복률이 높은 텍스트, 특수 문자 비율이 과도한 텍스트, 토큰 대비 단어 수 비율이 비정상적인 텍스트 등을 필터링한다.

**3단계 - 중복 제거 (Deduplication)**: URL 기반 정확 중복 제거와 MinHash LSH 기반 유사 중복 제거를 수행한다. 중복 제거는 학습 데이터의 다양성을 보장하고, 모델이 특정 패턴을 암기하는 것을 방지하는 데 중요하다.

**4단계 - 유해 콘텐츠 제거**: 유해하거나 부적절한 콘텐츠를 분류기를 사용하여 필터링한다.

**5단계 - PII 제거**: 개인 식별 정보(이메일, 전화번호, IP 주소 등)를 정규 표현식 기반으로 마스킹한다.

Dolma의 토크나이저는 GPT-NeoX-20B 토크나이저를 기반으로 하며, BPE(Byte-Pair Encoding) 알고리즘을 사용한다. 어휘 크기는 50,280개이다.

### 학습 (Training)

#### 학습 인프라

**하드웨어**: OLMo-7B의 학습은 AMD MI250X GPU 클러스터(LUMI 슈퍼컴퓨터, 핀란드)에서 수행되었다. 총 256개의 노드, 각 노드당 4개의 MI250X GPU를 사용하여 총 1,024개의 GCD(Graphics Compute Die)를 활용하였다. 일부 실험은 NVIDIA A100 80GB GPU 클러스터에서도 수행되었다.

**분산 학습 전략**: PyTorch FSDP(Fully Sharded Data Parallel)를 사용하여 모델 파라미터, 그래디언트, 옵티마이저 상태를 모든 GPU에 걸쳐 샤딩한다. FSDP는 ZeRO-3과 유사한 메모리 최적화를 제공하면서 PyTorch 네이티브 지원의 이점을 가진다.

FSDP의 메모리 절감 효과는 다음과 같이 계산할 수 있다. 모델 파라미터가 $\Phi$이고 GPU 수가 $N_d$일 때, 각 GPU의 메모리 사용량은 다음과 같다.

$$M_{\text{FSDP}} = \frac{\Phi \cdot (K_{\text{param}} + K_{\text{grad}} + K_{\text{opt}})}{N_d} + M_{\text{activation}}$$

여기서 $K_{\text{param}}, K_{\text{grad}}, K_{\text{opt}}$는 각각 파라미터, 그래디언트, 옵티마이저 상태의 바이트 수이고, $M_{\text{activation}}$은 활성화 메모리이다. BF16 학습 시 $K_{\text{param}} = K_{\text{grad}} = 2$, AdamW 옵티마이저의 경우 $K_{\text{opt}} = 12$ (FP32 파라미터 복사본 + 1차/2차 모멘텀)이다.

**혼합 정밀도 (Mixed Precision)**: 연산은 BFloat16으로 수행하되, 그래디언트 리덕션은 FP32로 수행하여 수치 안정성을 확보한다.

#### 학습 설정

| 하이퍼파라미터 | OLMo-1B | OLMo-7B |
|---|---|---|
| 총 학습 토큰 | 2T | 2.46T |
| 글로벌 배치 크기 (토큰) | ~2M | ~4M (2048 시퀀스 x 2048 토큰) |
| 시퀀스 길이 | 2,048 | 2,048 |
| 최대 학습률 ($\eta_{\text{max}}$) | 4e-4 | 3e-4 |
| 최소 학습률 ($\eta_{\text{min}}$) | 4e-5 | 3e-5 |
| 워밍업 스텝 | 2,000 | 5,000 |
| 옵티마이저 | AdamW | AdamW |
| $\beta_1, \beta_2$ | 0.9, 0.95 | 0.9, 0.95 |
| 가중치 감쇠 ($\lambda$) | 0.1 | 0.1 |
| 그래디언트 클리핑 | 1.0 | 1.0 |
| 드롭아웃 | 0.0 | 0.0 |

**학습률 스케줄**은 선형 워밍업 후 코사인 감소를 따른다.

$$\eta(t) = \begin{cases} \eta_{\text{max}} \cdot \frac{t}{T_{\text{warmup}}} & \text{if } t \leq T_{\text{warmup}} \\ \eta_{\text{min}} + \frac{1}{2}(\eta_{\text{max}} - \eta_{\text{min}})\left(1 + \cos\left(\frac{t - T_{\text{warmup}}}{T_{\text{total}} - T_{\text{warmup}}} \pi\right)\right) & \text{if } t > T_{\text{warmup}} \end{cases}$$

#### 학습 안정화 기술

OLMo는 대규모 학습의 안정성을 위해 여러 기술을 도입하였다.

**Z-loss**: 출력 로짓의 크기를 제어하여 소프트맥스 연산의 수치적 안정성을 보장한다.

$$\mathcal{L}_{\text{z-loss}} = \alpha \cdot \mathbb{E}\left[\log^2 Z\right], \quad Z = \sum_{i=1}^{|V|} e^{z_i}$$

여기서 $z_i$는 로짓 값이고, $\alpha$는 z-loss의 가중치(일반적으로 $10^{-4}$)이다. Z-loss는 로짓 값이 과도하게 커지는 것을 방지하여 학습 중 발산(divergence)을 예방한다. 이 기법은 PaLM에서도 효과적으로 사용되었다.

**그래디언트 클리핑 (Gradient Clipping)**: 그래디언트의 글로벌 L2 노름을 최대 1.0으로 제한하여 학습 불안정성을 방지한다.

$$\mathbf{g} \leftarrow \begin{cases} \mathbf{g} & \text{if } \|\mathbf{g}\|_2 \leq c \\ c \cdot \frac{\mathbf{g}}{\|\mathbf{g}\|_2} & \text{if } \|\mathbf{g}\|_2 > c \end{cases}$$

여기서 $c = 1.0$이다.

**드롭아웃 제거**: 충분히 큰 데이터셋에서 학습할 때 드롭아웃의 정규화 효과는 미미하며, 오히려 학습 효율을 저하시킬 수 있다. OLMo 역시 드롭아웃을 사용하지 않는다. 이는 LLaMA, GPT-3 등 최신 대규모 LLM 학습의 일반적 관행과 일치한다.

---

## 실험 결과

### 다운스트림 벤치마크 성능

OLMo-7B는 동급 규모의 오픈소스 모델들과 비교하여 경쟁력 있는 성능을 달성하였다. 아래 표는 zero-shot 및 few-shot 설정에서의 정확도를 보여준다.

| 벤치마크 | OLMo-7B | LLaMA-2-7B | Falcon-7B | MPT-7B | Pythia-6.9B |
|---|---|---|---|---|---|
| ARC-Easy (0-shot) | **76.4** | 74.5 | 75.9 | 73.9 | 67.3 |
| ARC-Challenge (0-shot) | **44.2** | 40.0 | 39.5 | 39.9 | 35.2 |
| HellaSwag (0-shot) | 76.4 | 76.0 | **78.2** | 77.5 | 64.2 |
| PIQA (0-shot) | 79.4 | 79.1 | **80.3** | **80.6** | 76.2 |
| WinoGrande (0-shot) | 68.2 | 68.9 | **71.0** | 68.3 | 64.0 |
| BoolQ (0-shot) | **73.4** | 71.2 | 68.4 | 72.1 | 63.8 |
| OBQA (0-shot) | **42.8** | 41.6 | 40.8 | 41.2 | 37.2 |
| MMLU (5-shot) | 46.2 | **46.8** | 26.2 | 30.8 | 25.4 |
| 평균 | **63.4** | 62.3 | 60.0 | 60.5 | 54.2 |

OLMo-7B는 ARC, BoolQ, OBQA 등 추론 중심 벤치마크에서 LLaMA-2-7B를 상회하며, 전체 평균에서도 가장 높은 점수를 기록한다. 특히 **완전 오픈 모델임에도 비공개 데이터로 학습된 LLaMA-2와 동등 이상의 성능을 달성**한 것은 주목할 만하다. 다만 MMLU에서 LLaMA-2에 약간 뒤처지는 것은 Dolma의 학술/지식 데이터 비중이 상대적으로 낮기 때문으로 분석된다.

HellaSwag과 PIQA에서 Falcon-7B와 MPT-7B에 뒤처지는 점도 눈여겨볼 만한데, 이들 벤치마크는 상식 추론과 물리적 직관을 측정하며, 학습 데이터의 웹 크롤링 품질과 필터링 전략의 차이가 반영된 것으로 해석할 수 있다.

### 모델 크기별 비교

| 벤치마크 | OLMo-1B | Pythia-1B | TinyLlama-1.1B | OLMo-7B |
|---|---|---|---|---|
| ARC-Easy | 57.2 | 52.1 | 55.3 | 76.4 |
| HellaSwag | 62.5 | 56.3 | 59.2 | 76.4 |
| PIQA | 73.7 | 70.8 | 73.2 | 79.4 |
| WinoGrande | 58.9 | 53.4 | 59.1 | 68.2 |
| 평균 | 63.1 | 58.2 | 61.7 | 75.1 |

1B 규모에서도 OLMo는 동급 모델들 대비 우수한 성능을 보인다. Pythia-1B 대비 평균 4.9점, TinyLlama-1.1B 대비 1.4점의 우위는 Dolma 데이터셋의 품질과 체계적인 하이퍼파라미터 튜닝의 결과로 볼 수 있다.

### 학습 역학 분석

![OLMo-7B 학습 과정에서 8개 핵심 벤치마크의 정확도 변화 추이](figures/fig_1.png)
*OLMo-7B의 학습 토큰 수(500B~2,500B) 증가에 따른 8개 핵심 다운스트림 벤치마크(ARC-c, ARC-e, BoolQ, HellaSwag, OBQA, PIQA, SciQ, WinoGrande) 정확도 변화. 대부분의 태스크에서 학습 마지막 1,000 스텝 동안 학습률을 0으로 감소시킨 효과(그래프 우측 끝의 급격한 상승)가 관찰된다. 2,500개 이상의 중간 체크포인트를 통해 이러한 세밀한 학습 역학 추적이 가능하다.*

공개된 WandB 로그와 중간 체크포인트를 통해 학습 과정을 상세히 분석할 수 있다. 이는 OLMo의 가장 독특한 기여 중 하나이다.

Figure 1에서 관찰되는 핵심 패턴은 다음과 같다.

- **태스크별 학습 곡선의 다양성**: HellaSwag과 SciQ는 비교적 안정적으로 상승하는 반면, BoolQ는 초반에 큰 변동을 보인 후 후반에 급격히 개선된다. 이는 각 태스크가 요구하는 능력이 학습 과정에서 서로 다른 시점에 발현됨을 시사한다.
- **학습률 감소의 극적 효과**: 그래프 우측 끝에서 관찰되는 성능 점프는 학습 마지막 1,000 스텝에서 학습률을 0으로 감소시킨 결과이다. 특히 ARC-c에서 약 3점, BoolQ에서 약 5점의 상승이 관찰되며, 이는 학습률 스케줄링이 최종 모델 품질에 미치는 영향을 실증적으로 보여주는 중요한 발견이다.
- **WinoGrande의 비단조적 행동**: WinoGrande는 학습 중반에 오히려 성능이 하락하는 구간이 존재하며, 이는 대조적 추론(commonsense reasoning) 능력의 발달이 비선형적임을 보여준다.

학습 손실(training loss)의 추이는 세 단계로 구분된다.

- **초기 단계** (0~50B 토큰): 손실이 급격히 감소한다. 모델이 기본적인 언어 패턴(문법, 일반 어휘)을 빠르게 학습한다.
- **중반 단계** (50B~1T 토큰): 안정적이면서 완만한 하강이 지속된다. 더 복잡한 언어 구조와 세상 지식을 점진적으로 획득한다.
- **후반 단계** (1T~2.46T 토큰): 하강 속도가 더욱 느려지지만 여전히 개선이 이루어진다. 코사인 학습률 감소와 맞물려 안정적으로 수렴한다.

약 150B 토큰 시점에서 일시적인 loss spike가 관찰되었다는 점도 주목할 만하다. AI2 팀은 이를 특정 데이터 배치의 품질 문제로 진단하고 데이터 필터링을 수정하여 해결하였다. 이러한 실패 사례와 해결 과정까지 투명하게 공개되어 있다는 것은, 대규모 학습에서 흔히 발생하지만 논문에서는 거의 다루지 않는 실전 노하우를 공유한다는 점에서 큰 가치를 가진다.

### Paloma 벤치마크: 도메인별 언어 모델링 분석

![다양한 평가 소스에서 모델별 bits per byte 스케일링 비교](figures/fig_2.png)
*OLMo-7B를 포함한 7개 오픈소스 모델의 Paloma 12개 평가 데이터 소스에서의 bits per byte(BPB) 비교. X축은 학습 토큰 수(log scale), Y축은 BPB(낮을수록 우수)이다. 모든 모델이 일반적인 데이터 스케일링 추세를 따르지만, 학습 데이터와 유사한 분포의 소스에서 표본 효율이 가장 높다. OLMo-7B(청록색 별)는 C4 소스에서 모든 모델을 능가하는데, 이는 88.8%가 Common Crawl인 학습 데이터 분포와 직접적으로 연관된다.*

Paloma는 AI2가 OLMo와 함께 발표한 표준화된 perplexity 벤치마크로, 다양한 도메인과 언어 레지스터에서 모델의 언어 모델링 능력을 평가한다. Perplexity는 다음과 같이 정의된다.

$$\text{PPL} = \exp\left(-\frac{1}{N}\sum_{i=1}^{N} \log P(w_i | w_{<i})\right)$$

낮은 perplexity는 모델이 텍스트를 더 잘 예측할 수 있음을 의미한다. Paloma는 585개의 텍스트 도메인에 걸쳐 perplexity를 측정하며, 도메인별 성능 편차를 분석할 수 있는 세분화된 평가를 제공한다.

Figure 2에서 드러나는 핵심 통찰은 **학습 데이터 분포와 평가 데이터의 관계**이다. OLMo-7B는 C4와 Dolma V1.5 소스에서 특히 강한 성능을 보이는데, 이는 학습 데이터의 88.8%가 Common Crawl 기반이라는 점과 직결된다. 반면 M2D2 S2ORC(학술 논문)이나 M2D2 Wikipedia 같은 특수 도메인에서는 해당 도메인 데이터 비중이 높은 다른 모델들과 경쟁적인 수준을 보인다.

이러한 결과는 사전학습 데이터의 도메인 구성이 모델의 도메인별 성능에 직접적인 영향을 미친다는 것을 실증적으로 보여준다.

![추가 7개 Paloma 평가 소스에서의 모델별 성능 비교](figures/fig_3.png)
*Figure 2에 포함되지 않은 나머지 7개 Paloma 데이터 소스(Pile, 100 Programming Languages, ICE, Twitter AAE, Manosphere, Gab, 4chan)에서의 bits per byte 비교. 소셜 미디어 및 비표준 텍스트 도메인(Twitter AAE, 4chan 등)에서 모델 간 성능 차이가 더 두드러지며, 학습 데이터의 도메인 커버리지가 이러한 특수 영역에서 결정적 역할을 함을 보여준다.*

Figure 3은 소셜 미디어, 프로그래밍 언어, 비표준 영어 등 더 특수한 도메인에서의 성능을 보여준다. 특히 Twitter AAE(African American English)에서 모델 간 큰 성능 차이가 나타나는 것은, 사전학습 데이터의 언어적 다양성이 소수 방언에 대한 모델 능력에 직접 영향을 미침을 시사한다. Dolma의 완전 공개 덕분에, 연구자들은 이러한 도메인별 성능 편차의 원인을 데이터 구성 수준에서 추적할 수 있다.

### 스케일링 법칙과의 관계

Kaplan et al.(2020)과 Hoffmann et al.(2022, Chinchilla)이 제시한 스케일링 법칙에 따르면, 최적의 모델 크기 $N$과 학습 토큰 수 $D$는 총 계산 예산 $C$에 대해 다음과 같은 관계를 따른다.

$$L(N, D) = \frac{A}{N^\alpha} + \frac{B}{D^\beta} + E$$

Chinchilla 스케일링 법칙에 따르면 $N$과 $D$는 거의 동일한 비율로 증가해야 하며, 모델 파라미터 수의 약 20배에 해당하는 토큰으로 학습하는 것이 최적이다. OLMo-7B의 경우 6.89B 파라미터에 2.46T 토큰(약 357배)으로 학습하여 Chinchilla 최적점을 크게 초과한다.

이는 LLaMA 계열이 시작한 **"over-training" 전략**과 일치하며, 실용적 관점에서 합리적인 선택이다. Chinchilla-optimal은 학습 비용을 최소화하는 것이지, 추론 비용을 최소화하는 것이 아니다. 배포 환경에서는 더 작은 모델을 더 많은 데이터로 학습시키는 것이 서빙 비용을 절감하면서도 경쟁력 있는 성능을 유지하는 전략이 된다.

---

## 의의 및 한계

### 의의

**완전 오픈의 표준 정립**: OLMo는 LLM 분야에서 진정한 오픈소스가 무엇인지 기준을 제시하였다. 가중치만 공개하는 "오픈워싱(openwashing)"과 달리, 재현 가능한 과학을 위한 모든 요소를 Apache 2.0 라이선스로 공개하였다. 이후 등장한 많은 프로젝트들이 OLMo의 공개 범위를 벤치마크로 삼고 있다.

**LLM 과학의 민주화**: 소수 빅테크 기업이 독점하던 LLM 연구를 모든 연구자에게 개방함으로써, 학계와 소규모 기관의 참여를 가능하게 하였다. 특히 자원이 제한된 기관에서도 중간 체크포인트를 활용한 분석 연구를 수행할 수 있게 되었다. 사전학습을 재현하지 않더라도, 체크포인트 분석만으로 학습 역학에 관한 독립적 연구가 가능하다는 것이 핵심이다.

**데이터-모델 공동 연구 기반**: 학습 데이터(Dolma)와 모델(OLMo)이 함께 공개됨으로써, 데이터 선택이 모델 성능에 미치는 영향을 직접적으로 연구할 수 있게 되었다. Paloma 결과에서 확인된 데이터 분포-성능 상관관계처럼, 인과적 분석을 위한 통제 변수가 완전히 제공된다.

**중간 체크포인트의 학술적 가치**: 2,500개 이상의 중간 체크포인트는 LLM의 학습 역학(training dynamics)을 연구하는 데 독보적 자산이다. 지식 획득 시점, 능력 발현(emergence) 단계, 망각(catastrophic forgetting) 현상, 특정 능력의 점진적 발전 과정 등을 높은 시간적 해상도로 분석할 수 있다.

**공정한 비교 기반 마련**: 완전히 공개된 모델과 데이터를 기반으로 새로운 학습 방법론, 데이터 필터링 전략, 아키텍처 변형 등을 공정하게 비교할 수 있는 환경이 조성되었다.

### 한계

**절대적 성능의 한계**: 완전 오픈에 집중하다 보니 동시대 최고 성능 모델(LLaMA 2 70B, Mixtral 8x7B 등)에 비해 절대 성능이 낮다. 특히 MMLU와 같은 지식 집약적 벤치마크에서의 격차가 두드러진다. 이는 Dolma의 학술/도서 데이터 비중(약 5%)이 다른 모델들의 학습 데이터 대비 낮기 때문일 가능성이 있으나, 다른 모델들의 데이터 구성이 비공개이므로 정확한 비교는 불가능하다.

**컨텍스트 길이 제한**: 기본 컨텍스트 길이가 2,048 토큰으로, 당시 경쟁 모델들(LLaMA 2: 4,096, Mistral: 8,192)에 비해 짧다. 이는 장문 처리, RAG, 코드 생성 등의 태스크에서 불리하게 작용한다. RoPE를 채택했으므로 이론적으로는 컨텍스트 확장이 가능하지만, 논문 시점에서는 이를 활용하지 않았다.

**다국어 능력 부족**: Dolma가 영어 중심으로 구성되어 있어 비영어권 언어에서의 성능이 제한적이다. "오픈"을 표방하면서도 영어에 집중한 것은 글로벌 연구 커뮤니티를 위한 인프라로서의 한계를 드러낸다.

**계산 자원 요구**: 완전한 재현을 위해서는 여전히 수백 개의 고성능 GPU가 필요하다. 코드와 데이터가 공개되어 있더라도 이를 실제로 활용할 수 있는 기관은 제한적이다. 이는 OLMo의 "민주화" 목표와 현실 사이의 괴리를 보여준다. 다만 중간 체크포인트를 활용한 분석 연구는 소규모 자원으로도 가능하므로, 이를 부분적으로 완화한다.

**Instruction Tuning의 부재**: 초기 공개 시점에서 OLMo는 사전학습 모델만 제공하였다. Instruction following이나 RLHF가 적용되지 않아 실용적 활용에는 추가 작업이 필요하였다. (이후 Tulu 기반 instruction-tuned 버전이 공개되었다.)

### 후속 발전

OLMo의 철학을 이어받아 후속 모델들이 지속적으로 발표되고 있다.

- **OLMo 2 (2024)**: 아키텍처 개선(GQA, 확장된 컨텍스트)과 데이터 품질 향상을 통해 성능을 크게 개선한 후속 모델이다. 초기 OLMo의 한계로 지적되었던 컨텍스트 길이와 절대 성능 문제를 상당 부분 해결하였다.
- **OLMo-2-13B**: 13B 규모로 확장하여 LLaMA 2 13B와 경쟁하는 성능을 달성하였다.
- **OLMoE (Mixture of Experts)**: MoE 아키텍처를 적용한 변형으로, 추론 효율성을 높였다.
- **Dolma v1.7**: 데이터셋도 지속적으로 개선되어 더 높은 품질과 다양성을 확보하고 있다.

AI2는 이러한 후속 프로젝트들을 통해 완전 오픈 LLM 생태계를 지속적으로 확장하고 있으며, 이는 오픈소스 AI 연구 커뮤니티의 투명성 기준을 높이는 데 지대한 영향을 미치고 있다.

---

## 코드 예제

### OLMo 추론 코드

HuggingFace Transformers를 사용하여 OLMo를 로드하고 텍스트를 생성하는 기본적인 방법이다.

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# OLMo-7B 모델 로드
model_name = "allenai/OLMo-7B"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.bfloat16,
    device_map="auto",
)

# 텍스트 생성
prompt = "The future of open-source AI is"
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=256,
        do_sample=True,
        temperature=0.7,
        top_p=0.9,
        top_k=50,
    )

generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(generated_text)
```

### 중간 체크포인트 활용

OLMo의 고유한 장점인 중간 체크포인트를 활용하여 학습 과정에서 모델 행동의 변화를 분석하는 예제이다.

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# 다양한 학습 단계의 체크포인트 로드
checkpoints = [
    "allenai/OLMo-7B-step1000",
    "allenai/OLMo-7B-step50000",
    "allenai/OLMo-7B-step100000",
    "allenai/OLMo-7B",  # 최종 체크포인트
]

tokenizer = AutoTokenizer.from_pretrained("allenai/OLMo-7B")
test_text = "The capital of France is"

for ckpt_name in checkpoints:
    model = AutoModelForCausalLM.from_pretrained(
        ckpt_name,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )
    inputs = tokenizer(test_text, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits[:, -1, :]  # 마지막 토큰의 로짓
        probs = torch.softmax(logits, dim=-1)
        top_token = tokenizer.decode(probs.argmax(dim=-1))

    print(f"Checkpoint: {ckpt_name}")
    print(f"  Next token prediction: {top_token}")
    print(f"  Confidence: {probs.max().item():.4f}")
    del model  # 메모리 해제
```

### FSDP 기반 학습 설정

OLMo의 학습에 사용된 PyTorch FSDP 설정을 개념적으로 보여주는 코드이다.

```python
import torch
import torch.distributed as dist
from torch.distributed.fsdp import (
    FullyShardedDataParallel as FSDP,
    MixedPrecision,
    ShardingStrategy,
)
from torch.distributed.fsdp.wrap import transformer_auto_wrap_policy
from functools import partial

# 분산 환경 초기화
dist.init_process_group(backend="nccl")
local_rank = int(os.environ["LOCAL_RANK"])
torch.cuda.set_device(local_rank)

# 혼합 정밀도 정책
bf16_policy = MixedPrecision(
    param_dtype=torch.bfloat16,
    reduce_dtype=torch.float32,  # 그래디언트 리덕션은 FP32
    buffer_dtype=torch.bfloat16,
)

# Transformer 블록 단위 래핑 정책
auto_wrap_policy = partial(
    transformer_auto_wrap_policy,
    transformer_layer_cls={TransformerBlock},
)

# FSDP 래핑
model = FSDP(
    model,
    auto_wrap_policy=auto_wrap_policy,
    sharding_strategy=ShardingStrategy.FULL_SHARD,
    mixed_precision=bf16_policy,
    device_id=local_rank,
    limit_all_gathers=True,
    use_orig_params=True,
)

# AdamW 옵티마이저
optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=3e-4,
    betas=(0.9, 0.95),
    weight_decay=0.1,
    eps=1e-8,
)

# 학습 루프 (개념적)
for step, batch in enumerate(dataloader):
    optimizer.zero_grad()
    loss = model(batch).loss

    # Z-loss 추가
    z_loss_weight = 1e-4
    logits = model(batch).logits
    log_z = torch.logsumexp(logits, dim=-1)
    z_loss = z_loss_weight * (log_z ** 2).mean()
    total_loss = loss + z_loss

    total_loss.backward()

    # 그래디언트 클리핑
    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
    optimizer.step()
    scheduler.step()
```

OLMo는 단순히 하나의 LLM이 아니라, 오픈소스 AI 연구가 나아가야 할 방향을 제시한 중요한 이정표이다. 모든 연구 자산을 완전히 공개함으로써 LLM 연구의 민주화에 기여하였으며, 이후 등장한 수많은 오픈 LLM 프로젝트들에게 투명성의 기준을 제시하였다.

## 관련 문서

- [[llama|LLaMA: Open and Efficient Foundation Language Models]] -- 영감