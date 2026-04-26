<!-- infographic-hero -->
![Qwen2 Technical Report 핵심 요약](figures/infographic.svg)

*Figure: Qwen2 Technical Report 한 장 요약 인포그래픽*

## 개요

Qwen2는 알리바바 그룹의 Qwen 팀이 2024년 6월에 발표한 2세대 대형 언어 모델(Large Language Model) 시리즈이다. 전작 Qwen1.5의 후속 모델로서, 아키텍처 설계, 사전학습 데이터, 학습 기법, 정렬(Alignment) 전략 모든 측면에서 대폭적인 개선이 이루어졌다. Qwen2 시리즈는 0.5B, 1.5B, 7B, 57B-A14B(Mixture-of-Experts), 72B의 다섯 가지 모델 크기를 제공하며, 다양한 배포 시나리오와 컴퓨팅 예산에 맞출 수 있도록 설계되었다.

핵심 기술적 특징을 요약하면 다음과 같다:

- **Grouped Query Attention(GQA)**: 0.5B부터 72B까지 모든 모델 크기에 적용하여 추론 시 KV 캐시 메모리를 최대 87.5% 절감한다.
- **Dual Chunk Attention(DCA) + YARN**: 청크 기반 어텐션 분해와 주파수별 차등 RoPE 스케일링을 결합하여 4K 학습 길이에서 128K까지 안정적으로 외삽한다.
- **7조(7T) 토큰 사전학습**: 웹 데이터, 도서, 코드, 수학 데이터 등 29개 언어에 걸친 대규모 다국어 코퍼스로 학습되었다.
- **DPO + GRPO 정렬**: SFT 이후 Direct Preference Optimization과 Group Relative Policy Optimization을 병행하여 지시 따르기 능력과 안전성을 강화했다.

Qwen2-72B-Instruct는 발표 시점에서 Llama-3-70B-Instruct, Mixtral-8x22B-Instruct 등 동급 오픈소스 모델들을 MMLU, GSM8K, HumanEval, MBPP 등 광범위한 벤치마크에서 능가했으며, 일부 벤치마크에서는 GPT-4 수준에 근접하는 성능을 달성했다. 이후 [[qwen2-5|Qwen2.5]], [[qwen2-vl|Qwen2-VL]], Qwen2-Audio 등 멀티모달 확장의 기반이 되었다.

## 배경 및 문제

### 1세대 Qwen의 성과와 한계

Qwen 시리즈의 1세대 모델은 Qwen(2023)과 Qwen1.5(2024 초)로 구성된다. Qwen1.5는 Apache 2.0 라이선스로 오픈소스 공개를 확대하고, 0.5B부터 110B까지 다양한 크기를 제공하여 접근성을 높였다. 그러나 세 가지 핵심 한계가 존재했다.

첫째, **컨텍스트 길이 제약**이다. Qwen1.5는 최대 32K 토큰까지만 안정적으로 동작했으며, 이를 넘어서는 시퀀스에서 성능이 급격히 저하되었다. RAG, 긴 문서 요약, 다중 턴 대화 등 실용적 응용에서 128K 이상의 컨텍스트가 요구되는 상황이 늘어나고 있었고, Claude 3가 200K, GPT-4 Turbo가 128K를 지원하는 상황에서 격차가 벌어지고 있었다.

둘째, **추론 효율성**의 문제이다. Qwen1.5의 소형 모델(0.5B, 1.8B)은 Multi-Head Attention(MHA)을 사용하여 KV 캐시 메모리 사용량이 높았다. 엣지 디바이스나 모바일 환경에서의 배포를 고려하면 KV 캐시 절감이 필수적이었다.

셋째, **수학 및 코드 능력**의 상대적 약점이다. GSM8K, MATH, HumanEval 등 전문 벤치마크에서 Llama 3 등 경쟁 모델 대비 개선 여지가 있었다. Chinchilla scaling laws에 따르면 모델 크기 대비 최적 데이터 비율이 존재하며, 72B 모델에 대해 Qwen1.5의 약 3T 토큰은 데이터 부족(undertrained) 상태에 해당했다.

### 긴 컨텍스트 처리의 기술적 과제

대형 언어 모델에서 긴 컨텍스트를 처리하는 것은 여러 기술적 난관을 수반한다.

가장 근본적인 문제는 **Self-Attention의 이차 복잡도**이다. 시퀀스 길이 $n$에 대해 어텐션 연산의 시간 및 공간 복잡도는 $O(n^2)$으로 증가한다. 128K 토큰 시퀀스의 경우 32K 대비 어텐션 연산량이 16배로 증가하므로, 이를 효율적으로 처리할 메커니즘이 필요하다.

또한 **위치 인코딩의 외삽(extrapolation) 문제**가 있다. RoPE(Rotary Position Embedding)는 학습 시 사용된 최대 시퀀스 길이를 초과하면 성능이 급격히 저하된다. RoPE의 $d$-차원 임베딩에서 $i$번째 차원의 회전 각도는 다음과 같이 정의된다:

$$\theta_i = 10000^{-2i/d}, \quad i = 0, 1, \ldots, d/2 - 1$$

위치 $m$에서의 임베딩은 $e^{im\theta_i}$로 계산되므로, $m$이 학습 범위를 넘어서면 $(m \cdot \theta_i) \bmod 2\pi$의 분포가 학습 시와 크게 달라진다. 특히 고주파 차원(큰 $\theta_i$)에서 회전 각도가 학습 시 관측된 분포를 벗어나면서 어텐션 패턴이 불안정해지는 문제가 심각하다.

### 오픈소스 LLM 생태계의 경쟁 구도

2024년 상반기 기준으로 오픈소스 LLM 생태계는 치열한 경쟁 구도를 형성하고 있었다. Meta의 Llama 3(8B, 70B)가 강력한 기준선을 설정했고, Mistral AI의 Mixtral 8x22B가 MoE 아키텍처에서의 효율성을 입증했다. 이러한 환경에서 Qwen2는 성능뿐 아니라 다국어 지원, 긴 컨텍스트, 모델 크기 다양성 측면에서 차별화를 추구했다.

## 핵심 아이디어

Qwen2의 핵심 기여는 (1) 전 모델 라인업에 걸친 GQA 적용을 통한 추론 효율화, (2) DCA + YARN 조합을 통한 128K 컨텍스트 확장, (3) 7T 토큰 규모의 고품질 다국어 사전학습 데이터 구축이라는 세 축으로 정리할 수 있다.

### Grouped Query Attention (GQA)

Qwen2 시리즈는 0.5B부터 72B까지 모든 모델 크기에 GQA(Grouped Query Attention)를 채택했다. GQA는 Multi-Head Attention(MHA)과 Multi-Query Attention(MQA)의 절충안으로, Key와 Value 헤드를 Query 헤드보다 적게 사용하여 KV 캐시 메모리를 절감하면서도 MHA에 준하는 표현력을 유지한다.

Query 헤드 수 $H_q$와 KV 헤드 수 $H_{kv}$가 주어질 때, 그룹 크기 $g = H_q / H_{kv}$개의 Query 헤드가 하나의 KV 헤드를 공유한다. 쿼리 헤드 $i$는 KV 그룹 $\lfloor i/g \rfloor$를 참조하며, GQA의 출력은 다음과 같이 계산된다:

$$\text{head}_i = \text{Softmax}\left(\frac{Q_i W_i^Q \cdot (K_{\lfloor i/g \rfloor} W^K)^T}{\sqrt{d_k}}\right) V_{\lfloor i/g \rfloor} W^V$$

$$\text{GQA}(Q, K, V) = \text{Concat}\left(\text{head}_1, \text{head}_2, \ldots, \text{head}_{H_q}\right) W^O$$

KV 캐시 절감률은 $(1 - H_{kv}/H_q) \times 100\%$이다. Qwen2-72B의 경우 $H_q = 64$, $H_{kv} = 8$이므로 MHA 대비 87.5% 절감된다. Qwen2-0.5B는 $H_q = 14$, $H_{kv} = 2$로 약 85.7% 절감을 달성한다.

주목할 점은 Qwen2가 **모든 모델 크기**에 GQA를 적용했다는 것이다. 기존에 GQA는 주로 대형 모델(Llama 2 70B 등)에만 적용되었으나, Qwen2는 0.5B 소형 모델에도 $H_{kv} = 2$의 공격적인 KV 헤드 축소를 적용했다. 이는 엣지 디바이스 배포를 염두에 둔 설계로, MQA($H_{kv} = 1$) 대비 충분한 KV 표현 다양성을 확보하면서도 메모리 효율을 극대화하는 균형점이다.

### Dual Chunk Attention (DCA)

Dual Chunk Attention은 긴 시퀀스를 고정 크기 청크로 분할한 뒤, 청크 내(intra-chunk)와 청크 간(inter-chunk) 어텐션을 분리하여 계산하는 기법이다. 핵심 통찰은 RoPE의 상대 위치 인코딩이 청크 내에서는 완전히 보존되므로, 청크 크기를 학습 시 컨텍스트 길이에 맞추면 외삽 문제를 우회할 수 있다는 것이다.

전체 시퀀스 길이 $L$을 청크 크기 $C$로 나누면 총 $\lceil L/C \rceil$개의 청크가 생성된다. 각 토큰에 대한 DCA의 어텐션 출력은 두 성분으로 분해된다:

**Intra-chunk Attention**: 동일 청크 내 토큰들 사이의 어텐션이다. 청크 크기가 학습 시 컨텍스트 길이 이내이므로 RoPE의 상대 위치 인코딩이 정확하게 작동한다. 대부분의 자연어 텍스트에서 토큰은 가까운 토큰과 더 강한 어텐션 관계를 맺으므로, 이 성분이 주된 신호를 포착한다.

**Inter-chunk Attention**: 서로 다른 청크에 속한 토큰들 사이의 어텐션이다. 상대 위치를 청크 단위로 재매핑하여 먼 거리의 의존성을 포착하며, YARN과 결합하여 외삽 안정성을 확보한다.

전체 DCA의 출력은 두 어텐션의 결합으로 표현된다:

$$\text{DCA}(Q, K, V) = \text{IntraAttn}(Q, K_{\text{local}}, V_{\text{local}}) + \text{InterAttn}(Q, K_{\text{remote}}, V_{\text{remote}})$$

이 분해의 장점은 세 가지이다. 첫째, 청크 내 어텐션은 원래의 학습 길이 범위에서 작동하므로 외삽 없이 정확한 위치 인코딩을 유지한다. 둘째, 청크 내 어텐션이 지역적 맥락을, 청크 간 어텐션이 장거리 의존성을 담당하는 분업 구조가 자연스럽다. 셋째, 전체적으로 원본 시퀀스의 모든 토큰 쌍에 대한 정보 흐름이 보존된다.

### YARN (Yet Another RoPE extensioN)

YARN은 RoPE의 외삽 능력을 개선하기 위한 동적 주파수 스케일링 기법이다. 기존의 단순 선형 보간(Position Interpolation)이 모든 주파수 성분을 균일하게 $1/s$로 압축하여 고주파 정보를 손실시키는 문제를 해결한다.

YARN의 핵심은 **주파수 대역에 따라 차별적인 스케일링**을 적용하는 것이다:

$$\theta_i^{\text{YARN}} = \begin{cases} \theta_i & \text{if } \lambda_i > L_{\text{train}} \quad (\text{저주파: 스케일링 불필요}) \\ \theta_i / s & \text{if } \lambda_i < L_{\text{train}} / r \quad (\text{고주파: 완전 보간}) \\ (1 - \gamma) \cdot \theta_i + \gamma \cdot \theta_i / s & \text{otherwise} \quad (\text{중간 대역: 부분 보간}) \end{cases}$$

여기서 $\lambda_i = 2\pi / \theta_i$는 $i$번째 차원의 파장, $s$는 스케일링 팩터(목표 길이 / 학습 길이), $r$은 조정 가능한 비율 파라미터, $\gamma$는 $\lambda_i$에 따라 연속적으로 변하는 보간 계수이다.

직관적으로, 파장이 학습 시퀀스 길이보다 긴 **저주파 차원**은 이미 충분히 넓은 범위를 커버하므로 스케일링 없이 사용한다. 파장이 매우 짧은 **고주파 차원**은 인접 토큰 간의 미세한 위치 차이를 인코딩하며, 선형 보간으로 압축해도 상대적 순서를 잘 보존한다. **중간 대역** 차원은 두 전략을 연속적으로 혼합하여 부드러운 전환을 보장한다.

Qwen2에서는 DCA와 YARN을 결합하여 사용한다. DCA가 청크 내/간 어텐션을 분리하고, YARN이 청크 간 어텐션에서 발생하는 외삽 문제를 추가로 보정하는 구조이다. 이를 통해 4K 토큰으로 사전학습된 모델이 32K로 확장된 후, 최종적으로 128K까지 안정적으로 외삽된다.

### 사전학습 데이터 전략

Qwen2의 사전학습 데이터는 Qwen1.5 대비 양과 질 모두에서 대폭 개선되었다:

- **총 토큰 수**: 7조(7T)로, Qwen1.5의 약 3T 대비 2배 이상 증가했다.
- **언어 커버리지**: 29개 언어를 포괄하며, 각 언어별 품질 필터링 파이프라인을 독립적으로 구축했다.
- **데이터 소스**: 웹 크롤링, 도서, 학술 논문, 코드 저장소, 수학 문제집, 다국어 뉴스 등에서 수집했다.
- **품질 관리**: 다단계 필터링 파이프라인(규칙 기반 필터, 언어 모델 기반 품질 점수, MinHash 중복 제거, n-gram 오염 제거)을 적용했다.
- **코드/수학 강화**: 코드와 수학 데이터의 비중을 의도적으로 높여 해당 도메인의 성능을 강화했다.

코드 데이터는 GitHub에서 수집된 고품질 저장소를 기반으로 하며, 구문 오류 필터링, 라이선스 확인, 개인정보 제거 등의 전처리를 거쳤다. 수학 데이터는 교과서, 경시대회 문제, 합성 데이터를 포함하며, 단계별 풀이(step-by-step solution)가 포함된 형태로 가공되었다.

토크나이저는 151,643개 어휘의 바이트 레벨 BPE(Byte-Pair Encoding)를 사용한다. CJK(중국어, 일본어, 한국어) 문자에 대해 문자 단위의 세분화된 토큰을 포함하여 동아시아 언어의 토큰화 효율을 높였다.

## 방법론

### 모델 아키텍처 상세

![Qwen2 Transformer 디코더 아키텍처 다이어그램](figures/architecture.png)
*Qwen2의 전체 아키텍처 구조. GQA 기반 어텐션, Pre-RMSNorm, SwiGLU FFN으로 구성된 Transformer 블록이 24~80개 레이어로 쌓이며, DCA와 YARN을 통해 긴 컨텍스트를 처리한다.*

Qwen2의 모든 모델은 Transformer 디코더 아키텍처를 기반으로 하며, 다음과 같은 공통 설계 요소를 공유한다:

- **Pre-Layer Normalization**: 각 Transformer 블록 앞에 RMSNorm을 적용한다. Post-LN 대비 학습 안정성이 높으며, LayerNorm 대신 RMSNorm을 사용하여 평균 계산을 생략함으로써 연산 효율도 개선한다.
- **SwiGLU 활성화 함수**: FFN(Feed-Forward Network)에서 SwiGLU를 사용하여 표현력을 높인다:

$$\text{SwiGLU}(x) = (xW_1) \otimes \text{SiLU}(xW_2), \quad \text{SiLU}(x) = x \cdot \sigma(x)$$

여기서 $\otimes$는 원소별 곱, $\sigma$는 시그모이드 함수이다. SwiGLU는 게이팅 메커니즘을 통해 정보 흐름을 조절하며, 동일 파라미터 수 대비 ReLU/GELU보다 우수한 성능을 보인다. FFN의 중간 차원은 히든 크기의 약 $8/3$배로 설정된다.

- **RoPE(Rotary Position Embedding)**: 절대 위치 인코딩 대신 상대 위치 기반의 RoPE를 사용한다.
- **Byte-level BPE 토크나이저**: 151,643개 토큰 크기의 어휘를 사용하며, 29개 언어를 효율적으로 커버한다.

### 모델 사양 테이블

| 사양 | Qwen2-0.5B | Qwen2-1.5B | Qwen2-7B | Qwen2-57B-A14B (MoE) | Qwen2-72B |
|------|-----------|-----------|---------|---------------------|----------|
| 파라미터 수 | 0.49B | 1.54B | 7.07B | 57.4B (14.7B active) | 72.7B |
| 레이어 수 | 24 | 28 | 28 | 28 | 80 |
| 히든 차원 | 896 | 1,536 | 3,584 | 4,096 | 8,192 |
| Query 헤드 수 | 14 | 16 | 28 | 64 | 64 |
| KV 헤드 수 | 2 | 2 | 4 | 8 | 8 |
| GQA 그룹 크기 | 7 | 8 | 7 | 8 | 8 |
| FFN 히든 차원 | 4,864 | 8,960 | 18,944 | 2,560 x 64 experts | 29,568 |
| 컨텍스트 길이 | 32K | 32K | 128K | 64K | 128K |
| 어휘 크기 | 151,643 | 151,643 | 151,643 | 151,643 | 151,643 |
| Tying Embeddings | Yes | Yes | No | No | No |

사양 테이블에서 주목할 설계 선택이 몇 가지 있다. 0.5B와 1.5B 모델은 입력/출력 임베딩 가중치를 공유(Embedding Tying)하여 파라미터 효율성을 높였다. 이 기법은 소형 모델에서 임베딩 레이어가 전체 파라미터의 상당 비율을 차지하기 때문에 효과적이다. 반면 7B 이상 모델에서는 임베딩을 독립적으로 유지하여 표현력을 극대화한다.

57B-A14B MoE 모델은 각 MoE 레이어에 64개의 전문가(expert)를 배치하고, 각 토큰에 대해 8개의 전문가만 활성화하는 **Top-8 라우팅**을 사용한다. MoE 레이어와 Dense 레이어를 번갈아 배치하는 하이브리드 구조를 사용하여 전문가 간 정보 교환을 원활하게 한다. 전체 파라미터 57.4B 중 각 토큰 처리 시 활성화되는 파라미터는 약 14.7B로, Dense 72B 모델에 비해 훨씬 적은 연산으로 유사한 수준의 성능을 달성한다.

### 사전학습 설정

Qwen2의 사전학습은 다음과 같은 설정으로 진행되었다:

- **옵티마이저**: AdamW ($\beta_1 = 0.9$, $\beta_2 = 0.95$, 가중치 감쇠 0.1)
- **학습률 스케줄러**: 코사인 스케줄러 (워밍업 후 점진적 감소)
- **최대 학습률**: 모델 크기에 따라 $3 \times 10^{-4}$ ~ $1 \times 10^{-4}$
- **배치 크기**: 학습 초기 작은 배치에서 시작하여 점진적으로 증가 (최대 4M 토큰/배치)
- **정밀도**: BFloat16 혼합 정밀도 학습

시퀀스 길이의 **단계적 확장**은 학습 효율성의 핵심 전략이다:

1. **단계 1 (4K 컨텍스트)**: 전체 7T 토큰 중 대부분(약 90%)을 4K 시퀀스로 학습하여 계산 비용을 절감한다. 어텐션 연산의 $O(n^2)$ 복잡도를 고려하면, 4K와 128K의 연산량 차이는 약 1,024배에 달하므로 이 단계에서 대부분의 언어 능력을 학습하는 것이 효율적이다.
2. **단계 2 (32K 컨텍스트)**: 긴 시퀀스 데이터를 혼합하여 추가 학습한다.
3. **단계 3 (128K 컨텍스트)**: DCA + YARN을 활성화하여 최종 확장한다. 학습률은 이전 단계 종료 시점에서 시작하여 점진적으로 감쇠시킨다.

### 정렬 학습 (Post-Training)

Qwen2-Instruct 모델은 사전학습된 기본 모델에 2단계 정렬 학습을 적용하여 생성된다.

**1단계: Supervised Fine-Tuning (SFT)**

50만 건 이상의 고품질 instruction-response 쌍을 사용하여 지도 학습을 수행한다. SFT 데이터의 구성 전략은 다음과 같다:

- 코딩, 수학, 논리 추론, 창의적 글쓰기, 역할극 등 다양한 태스크 포함
- 29개 언어에 걸친 다국어 커버리지
- 자동 생성 데이터와 인간 작성 데이터의 비율 조절로 품질과 다양성을 균형 있게 유지
- 인간 평가자 및 LLM 기반 자동 평가를 병행하여 품질 검증

**2단계: RLHF (DPO + GRPO)**

DPO(Direct Preference Optimization)와 GRPO(Group Relative Policy Optimization)를 병행한다. DPO는 보상 모델 학습과 PPO 최적화 과정을 단일 목적 함수로 통합한 기법으로, 손실 함수는 다음과 같다:

$$\mathcal{L}_{\text{DPO}}(\pi_\theta; \pi_{\text{ref}}) = -\mathbb{E}_{(x, y_w, y_l)}\left[\log \sigma\left(\beta \log \frac{\pi_\theta(y_w|x)}{\pi_{\text{ref}}(y_w|x)} - \beta \log \frac{\pi_\theta(y_l|x)}{\pi_{\text{ref}}(y_l|x)}\right)\right]$$

여기서 $\pi_\theta$는 학습 중인 정책, $\pi_{\text{ref}}$는 SFT 모델(참조 정책), $y_w$와 $y_l$은 각각 선호/비선호 응답, $\beta$는 KL 발산 페널티 강도이다.

GRPO는 하나의 프롬프트에서 여러 응답을 샘플링한 뒤, 그룹 내 상대적 보상을 기반으로 정책을 최적화하는 기법이다. 수학과 코드처럼 **정답 검증이 가능한 태스크**에서 보상 모델 없이도 효과적으로 작동한다는 점이 핵심이다. 정답이 존재하는 태스크에서는 정답 여부 자체를 보상 신호로 사용할 수 있으므로, 별도의 보상 모델 학습 비용을 절감하면서도 정확한 보상 신호를 확보할 수 있다. Qwen2는 일반적인 선호 학습에는 DPO를, 수학/코드 특화 학습에는 GRPO를 적용하여 태스크 특성에 맞는 최적화를 수행했다.

## 실험 결과

### 7B 급 기본 모델 비교

| 모델 | MMLU | MMLU-Pro | GSM8K | MATH | HumanEval | MBPP | ARC-C |
|------|------|----------|-------|------|-----------|------|-------|
| Llama-3-8B | 66.6 | 35.4 | 79.6 | 30.0 | 62.2 | 65.0 | 59.2 |
| Mistral-7B-v0.3 | 64.2 | 30.9 | 52.2 | 13.1 | 40.2 | 49.0 | 55.0 |
| Gemma-7B | 64.6 | 33.7 | 59.8 | 24.3 | 37.2 | 50.6 | 53.2 |
| **Qwen2-7B** | **70.3** | **40.2** | **89.5** | **52.9** | **79.9** | **67.2** | **64.3** |

Qwen2-7B는 동일 규모의 모든 오픈소스 모델을 전 벤치마크에서 능가한다. 특히 수학과 코드 벤치마크에서의 격차가 두드러진다:

- **GSM8K**: 89.5 vs 79.6(Llama-3-8B), 약 10점 차이. 초등 수준 수학 문제 해결에서의 확실한 우위.
- **MATH**: 52.9 vs 30.0(Llama-3-8B), 약 23점 차이. 경시대회 수준의 수학 추론에서 질적으로 다른 수준의 능력을 보인다.
- **HumanEval**: 79.9 vs 62.2(Llama-3-8B), 17.7점 차이. Python 함수 생성 능력에서의 현격한 차이.

이 결과는 사전학습 데이터에서 수학 및 코드 데이터의 비중을 의도적으로 높이고, 단계별 풀이가 포함된 고품질 수학 데이터를 확보한 전략이 효과적이었음을 시사한다.

### 70B 급 기본 모델 비교

| 모델 | MMLU | MMLU-Pro | GSM8K | MATH | HumanEval | MBPP | ARC-C |
|------|------|----------|-------|------|-----------|------|-------|
| Llama-3-70B | 79.5 | 52.8 | 93.0 | 50.4 | 81.7 | 80.2 | 68.8 |
| Mixtral-8x22B | 77.8 | 49.8 | 78.6 | 41.7 | 46.3 | 71.7 | 65.7 |
| **Qwen2-72B** | **84.2** | **55.6** | **93.2** | **59.7** | **86.0** | **82.6** | **70.1** |

Qwen2-72B는 MMLU 84.2%로 Llama-3-70B(79.5%)를 약 5점 앞선다. 이는 GPT-3.5 Turbo(70.0%)를 크게 상회하는 수치이다. MATH에서도 59.7 vs 50.4로 약 9점 차이를 보이며, 대형 모델에서도 수학 추론 강점이 유지됨을 확인할 수 있다.

7B 모델에서 관찰된 수학/코드 우위가 72B 규모에서도 일관되게 유지된다는 점은 중요하다. 이는 Qwen2의 성능 향상이 특정 규모에서만 작동하는 트릭이 아니라, 데이터 품질과 학습 전략의 근본적인 개선에서 비롯된 것임을 시사한다.

### Instruct 모델 벤치마크

정렬 학습 후의 Instruct 모델 성능이다:

| 모델 | MT-Bench | IFEval | GSM8K | HumanEval | MMLU |
|------|----------|--------|-------|-----------|------|
| Llama-3-8B-Instruct | 8.05 | 76.8 | 79.6 | 62.2 | 68.4 |
| **Qwen2-7B-Instruct** | **8.41** | **77.6** | **85.7** | **79.9** | **70.5** |
| Llama-3-70B-Instruct | 8.95 | 86.2 | 93.0 | 81.7 | 82.0 |
| **Qwen2-72B-Instruct** | **9.12** | **87.6** | **91.1** | **86.0** | **84.2** |

MT-Bench 9.12점은 명령 수행의 질적 수준이 높음을 보여주며, IFEval 87.6%는 복잡한 지시 사항(형식 제약, 길이 제약 등)을 정확히 따르는 능력이 뛰어남을 의미한다. DPO + GRPO 병행 전략이 일반적 선호 정렬과 정답 기반 정렬 모두에서 효과적이었음을 확인할 수 있다.

### 다국어 벤치마크

29개 언어 지원의 실질적인 성능을 확인하기 위한 다국어 평가 결과이다:

| 모델 | 중국어(C-Eval) | 일본어(JLPT) | 한국어(KMMLU) | 아랍어(ArabicMMLU) | 평균 |
|------|---------------|-------------|--------------|-------------------|------|
| Llama-3-70B | 67.5 | 68.1 | 62.8 | 59.0 | 64.4 |
| Mixtral-8x22B | 58.6 | 61.3 | 55.7 | 52.4 | 57.0 |
| **Qwen2-72B** | **91.1** | **79.3** | **73.2** | **71.5** | **78.8** |

Qwen2-72B는 모든 비영어 벤치마크에서 압도적인 우위를 보인다. 중국어 C-Eval에서 91.1점은 Llama-3-70B 대비 약 24점 차이이며, 한국어 KMMLU에서도 73.2 vs 62.8로 약 10점 차이를 기록했다. 이는 7T 토큰 중 다국어 데이터의 비율이 충분히 높았으며, 언어별 독립 품질 필터링 파이프라인이 효과적으로 작동했음을 시사한다.

특히 Llama 3가 영어 중심의 학습 데이터를 사용한 반면, Qwen2는 각 언어별로 전용 필터링 파이프라인을 구축하여 데이터 품질을 관리했다는 점에서 구조적인 차이가 있다.

### 긴 컨텍스트 성능

![Qwen2 Instruct 모델들의 Needle-in-a-Haystack 테스트 결과](figures/fig_1.png)
*Qwen2 Instruct 모델들의 컨텍스트 길이(8K~128K)와 문서 내 위치 깊이(depth)에 따른 사실 검색 정확도. Qwen2-72B-Instruct는 128K 전 범위에서 거의 완벽한 검색 정확도를 유지한다. 32K 이상을 지원하는 모델은 모두 YARN 메커니즘을 통합했다.*

Needle-in-a-Haystack(NIAH) 평가에서 Qwen2-7B-Instruct와 Qwen2-72B-Instruct 모두 128K 토큰 길이까지 거의 완벽한 검색 정확도(98% 이상)를 유지한다. 이 평가는 긴 텍스트의 임의 위치에 특정 정보("needle")를 삽입한 뒤, 해당 정보를 정확히 추출하는 능력을 측정한다.

위 그림에서 몇 가지 흥미로운 패턴을 관찰할 수 있다:

- **Qwen2-72B-Instruct**: 128K 전 범위에서 거의 균일한 녹색(높은 정확도)을 보이며, DCA + YARN의 긴 컨텍스트 처리가 매우 안정적으로 작동함을 확인할 수 있다.
- **Qwen2-7B-Instruct**: 대부분의 범위에서 높은 정확도를 보이지만, 32K~48K 부근의 특정 깊이에서 소폭의 정확도 감소(노란색 영역)가 관찰된다. 이는 모델 용량의 한계로 DCA의 청크 간 어텐션 신호가 약해질 수 있음을 시사한다.
- **Qwen2-0.5B-Instruct**: 32K 컨텍스트만 지원하며, 후반부에서 정확도가 현저히 떨어지는 패턴을 보인다. 소형 모델의 용량 제약이 긴 컨텍스트 처리에 직접적인 영향을 미침을 보여준다.

Passkey Retrieval 벤치마크에서도 128K 토큰 범위 내에서 100%에 가까운 정확도를 달성하여, DCA + YARN 조합의 실용성을 검증한다.

### MoE 모델 효율성

Qwen2-57B-A14B(MoE)는 비용 효율적 배포에서 독특한 위치를 차지한다:

| 모델 | MMLU | GSM8K | HumanEval | 활성 파라미터 | 상대 연산량 |
|------|------|-------|-----------|-------------|----------|
| Qwen2-57B-A14B | 82.0 | 91.5 | 81.7 | 14.7B | ~20% |
| Qwen2-72B | 84.2 | 93.2 | 86.0 | 72.7B | 100% |

전체 파라미터 57.4B 중 각 토큰당 14.7B만 활성화하여, Dense 72B 모델 대비 약 80% 적은 연산량으로 유사한 성능을 달성한다. MMLU 82.0은 72B의 84.2 대비 2.2점 차이에 불과하며, 연산 비용 대비 성능 효율이 매우 높다.

다만 전체 57.4B 파라미터를 메모리에 적재해야 하므로, 실제 메모리 요구량은 Dense 72B 모델과 크게 다르지 않을 수 있다. 따라서 MoE 모델의 이점은 메모리 절감보다는 추론 속도(처리량) 향상에서 주로 발현된다.

## 의의 및 한계

### 의의

**1. 오픈소스 LLM의 기준 재설정**

Qwen2-72B는 발표 시점에서 가장 강력한 오픈소스 LLM 중 하나로, 특히 수학(MATH 59.7), 코딩(HumanEval 86.0), 다국어 처리에서 새로운 기준을 설정했다. MMLU 84.2%는 GPT-3.5 Turbo를 크게 상회하며, 오픈소스 생태계의 전반적인 수준을 끌어올린 기여로 평가된다.

**2. 실용적 긴 컨텍스트 처리**

DCA + YARN의 조합은 128K 토큰 컨텍스트를 안정적으로 지원하면서도, 기존 Transformer 아키텍처와의 호환성을 유지한다. 이전까지 128K 이상의 컨텍스트는 GPT-4 Turbo, Claude 3 등 폐쇄형 모델의 전유물이었는데, Qwen2가 이 격차를 줄이는 데 기여했다.

**3. 다국어 격차 해소**

대부분의 오픈소스 LLM이 영어 중심으로 학습되는 반면, Qwen2는 29개 언어에 대한 균형 잡힌 지원을 제공한다. 특히 동아시아 언어(중국어, 일본어, 한국어)와 아랍어에서의 강점은 해당 언어권 사용자들에게 실질적인 가치를 제공한다.

**4. 모델 크기 스펙트럼의 완성**

0.5B부터 72B까지, 그리고 MoE 변형까지 포함하는 포괄적인 모델 제품군은 엣지 디바이스 배포(0.5B, 1.5B)부터 서버 기반 고성능 추론(72B)까지 다양한 배포 시나리오를 커버한다.

**5. 후속 연구의 기반**

Qwen2는 이후 [[qwen2-5|Qwen2.5]](텍스트), [[qwen2-vl|Qwen2-VL]](비전-언어), Qwen2-Audio(오디오-언어), Qwen-Agent(에이전트) 등 멀티모달 및 에이전트 확장의 기반 아키텍처로 활용되었다.

### 한계

**1. 학습 데이터 투명성 부족**

7조 토큰의 학습 데이터에 대한 상세한 구성 비율, 소스별 분류, 라이선스 상태, 품질 기준 등이 충분히 공개되지 않았다. 오픈소스 모델임에도 데이터 재현성이 보장되지 않는 점은 학술적 관점에서 한계이다. Llama 3가 학습 데이터 구성 비율과 필터링 전략을 상세히 공개한 것과 대비된다.

**2. 다국어 안전성 정렬의 한계**

29개 언어 전반에 걸쳐 일관된 안전성을 확보하는 것은 현실적으로 매우 어려운 과제이다. 특히 저자원(low-resource) 언어에서의 안전성 정렬 데이터가 부족할 수 있으며, 언어 간 jailbreak 공격(영어로 거부된 요청을 다른 언어로 우회)에 대한 취약성이 존재할 수 있다.

**3. 벤치마크 오염 가능성**

7T 토큰 규모의 웹 크롤링 데이터에서 벤치마크 문제가 학습 데이터에 포함되었을 가능성을 완전히 배제하기 어렵다. n-gram 기반 오염 제거를 적용했다고 언급하지만, 패러프레이즈된 형태의 벤치마크 데이터는 이 방법으로 탐지하기 어렵다.

**4. MoE 모델의 배포 복잡성**

57B-A14B MoE 모델은 활성 파라미터가 14.7B에 불과하지만, 전체 57.4B 파라미터를 메모리에 적재해야 하므로 실제 메모리 요구량은 Dense 72B 모델과 크게 다르지 않다. Expert 병렬화 등 추가적인 인프라 고려가 필요하다.

**5. DCA 청크 크기의 고정성**

DCA의 청크 크기가 고정적이어서, 태스크와 입력 특성에 따라 최적 청크 크기가 달라질 수 있지만 적응적 청크 크기 결정 메커니즘이 부재하다.

**6. 폐쇄형 모델 대비 격차**

오픈소스 최강을 달성했음에도, GPT-4, Claude 3 Opus 등 폐쇄형 모델과의 격차는 특히 복잡한 추론, 긴 형식 생성, 지시 따르기 등에서 여전히 존재한다. 이 격차는 이후 [[qwen2-5|Qwen2.5]]에서 상당 부분 축소되었다.

## 코드 예제

### HuggingFace Transformers를 활용한 추론

다음은 Qwen2-7B-Instruct 모델을 HuggingFace Transformers 라이브러리로 로드하여 추론하는 예제이다.

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# 모델과 토크나이저 로드
model_name = "Qwen/Qwen2-7B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    attn_implementation="flash_attention_2",  # FlashAttention-2 사용
    trust_remote_code=True,
)

# 대화 형식 입력 구성
messages = [
    {"role": "system", "content": "You are a helpful AI assistant."},
    {"role": "user", "content": "Transformer의 Self-Attention 메커니즘을 수학적으로 설명해주세요."},
]

# 토크나이저의 chat template 적용
text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True,
)

# 토큰화 및 추론
inputs = tokenizer(text, return_tensors="pt").to(model.device)
with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=1024,
        temperature=0.7,
        top_p=0.9,
        repetition_penalty=1.05,
        do_sample=True,
    )

# 응답 디코딩 (입력 부분 제외)
response = tokenizer.decode(
    outputs[0][inputs["input_ids"].shape[-1]:],
    skip_special_tokens=True,
)
print(response)
```

### PyTorch에서 GQA 직접 구현

GQA의 동작 원리를 이해하기 위한 간소화된 PyTorch 구현이다.

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
import math


class GroupedQueryAttention(nn.Module):
    """Grouped Query Attention 구현

    Query 헤드가 KV 헤드를 그룹 단위로 공유하여
    KV 캐시 메모리를 절감한다.
    """
    def __init__(
        self,
        d_model: int,
        n_heads: int,      # Query 헤드 수
        n_kv_heads: int,   # KV 헤드 수
    ):
        super().__init__()
        assert n_heads % n_kv_heads == 0, "n_heads must be divisible by n_kv_heads"

        self.n_heads = n_heads
        self.n_kv_heads = n_kv_heads
        self.n_groups = n_heads // n_kv_heads  # 그룹 크기
        self.head_dim = d_model // n_heads

        # Query, Key, Value, Output 프로젝션
        self.q_proj = nn.Linear(d_model, n_heads * self.head_dim, bias=True)
        self.k_proj = nn.Linear(d_model, n_kv_heads * self.head_dim, bias=True)
        self.v_proj = nn.Linear(d_model, n_kv_heads * self.head_dim, bias=True)
        self.o_proj = nn.Linear(n_heads * self.head_dim, d_model, bias=False)

    def forward(
        self,
        x: torch.Tensor,            # (batch, seq_len, d_model)
        mask: torch.Tensor = None,   # (batch, 1, seq_len, seq_len)
    ) -> torch.Tensor:
        B, S, _ = x.shape

        # 프로젝션: Q, K, V 계산
        q = self.q_proj(x).view(B, S, self.n_heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(x).view(B, S, self.n_kv_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(x).view(B, S, self.n_kv_heads, self.head_dim).transpose(1, 2)

        # KV 헤드를 Query 헤드 수에 맞게 반복 확장
        # (B, n_kv_heads, S, head_dim) -> (B, n_heads, S, head_dim)
        k = k.unsqueeze(2).expand(
            B, self.n_kv_heads, self.n_groups, S, self.head_dim
        ).reshape(B, self.n_heads, S, self.head_dim)
        v = v.unsqueeze(2).expand(
            B, self.n_kv_heads, self.n_groups, S, self.head_dim
        ).reshape(B, self.n_heads, S, self.head_dim)

        # Scaled Dot-Product Attention
        scale = math.sqrt(self.head_dim)
        attn_weights = torch.matmul(q, k.transpose(-2, -1)) / scale

        if mask is not None:
            attn_weights = attn_weights.masked_fill(mask == 0, float("-inf"))

        attn_weights = F.softmax(attn_weights, dim=-1)
        attn_output = torch.matmul(attn_weights, v)

        # 헤드 결합 및 출력 프로젝션
        attn_output = attn_output.transpose(1, 2).contiguous().view(B, S, -1)
        return self.o_proj(attn_output)


# 사용 예시: Qwen2-7B 구성
if __name__ == "__main__":
    gqa = GroupedQueryAttention(
        d_model=3584,
        n_heads=28,     # Qwen2-7B의 Query 헤드 수
        n_kv_heads=4,   # Qwen2-7B의 KV 헤드 수 (그룹 크기 = 7)
    )

    x = torch.randn(1, 512, 3584)  # (batch=1, seq=512, dim=3584)
    output = gqa(x)
    print(f"Input shape: {x.shape}")
    print(f"Output shape: {output.shape}")

    # KV 캐시 메모리 비교
    head_dim = 3584 // 28  # = 128
    mha_kv_cache = 28 * 2 * head_dim * 512  # MHA: 28 KV heads
    gqa_kv_cache = 4 * 2 * head_dim * 512   # GQA: 4 KV heads
    print(f"MHA KV cache: {mha_kv_cache:,} elements")
    print(f"GQA KV cache: {gqa_kv_cache:,} elements")
    print(f"Memory reduction: {1 - gqa_kv_cache/mha_kv_cache:.1%}")
    # 결과: 85.7% 절감
```

### vLLM을 활용한 고성능 서빙

프로덕션 환경에서는 vLLM을 사용하여 높은 처리량의 추론 서빙을 구성할 수 있다.

```python
from vllm import LLM, SamplingParams

# vLLM 엔진 초기화 (텐서 병렬화 적용)
llm = LLM(
    model="Qwen/Qwen2-72B-Instruct-AWQ",  # AWQ 양자화 모델
    tensor_parallel_size=4,  # 4-GPU 텐서 병렬화
    max_model_len=32768,
    gpu_memory_utilization=0.85,
    dtype="auto",
)

# 샘플링 파라미터 설정
sampling_params = SamplingParams(
    temperature=0.7,
    top_p=0.9,
    max_tokens=2048,
    repetition_penalty=1.05,
)

# 배치 추론
prompts = [
    "Qwen2의 Dual Chunk Attention이 긴 컨텍스트 처리에 어떻게 기여하는지 설명하세요.",
    "GQA와 MHA의 메모리 효율성을 비교 분석하세요.",
    "YARN이 기존 Position Interpolation 대비 가지는 장점을 서술하세요.",
]

outputs = llm.generate(prompts, sampling_params)
for output in outputs:
    print(f"Prompt: {output.prompt[:50]}...")
    print(f"Response: {output.outputs[0].text[:200]}...")
    print("---")
```

### 긴 컨텍스트 처리 예시

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# 128K 컨텍스트를 활용한 장문 처리
model_name = "Qwen/Qwen2-7B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    attn_implementation="flash_attention_2",
    trust_remote_code=True,
)

# 긴 문서 입력 구성 (예: 논문 전문 요약)
long_document = open("long_paper.txt").read()  # 수만 토큰 분량
messages = [
    {"role": "system", "content": "You are a research assistant."},
    {"role": "user", "content": f"다음 논문을 읽고 핵심 기여를 3가지로 요약하세요:\n\n{long_document}"},
]

text = tokenizer.apply_chat_template(
    messages, tokenize=False, add_generation_prompt=True
)
inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=131072)
print(f"입력 토큰 수: {inputs['input_ids'].shape[1]:,}")

# rope_scaling 설정은 config.json에 자동 포함됨
# "rope_scaling": {"type": "yarn", "factor": 4.0}
inputs = inputs.to(model.device)
with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=1024,
        temperature=0.3,  # 요약 태스크에는 낮은 temperature
    )

response = tokenizer.decode(
    outputs[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True
)
print(response)
```

## 관련 문서

- [[qwen2-5|Qwen2.5 Technical Report]] -- 후속 모델
- [[qwen2-vl|Qwen2-VL]] -- 멀티모달 확장
- [[llama-2|Llama 2: Open Foundation and Fine-Tuned Chat Models]] -- 경쟁 모델
