## 개요

DeepSeek-V3는 2024년 12월 DeepSeek AI가 공개한 671B 파라미터 MoE 언어 모델로, 토큰당 37B 파라미터만 활성화하는 효율적인 구조를 갖는다. 전작 DeepSeek-V2의 MLA(Multi-head Latent Attention)와 DeepSeekMoE 아키텍처를 계승하면서, 세 가지 핵심 혁신을 도입했다: (1) 보조 손실 없는 부하 균형 전략(Auxiliary-Loss-Free Load Balancing), (2) Multi-Token Prediction(MTP) 훈련 목표, (3) FP8 혼합 정밀도 훈련 프레임워크. 이를 통해 단 2.788M H800 GPU-시간(약 557만 달러)으로 14.8T 토큰 훈련을 완료하여, 유사 규모 Dense 모델 대비 압도적인 비용 효율성을 달성했다.

아래 그림은 DeepSeek-V3가 6개 핵심 벤치마크에서 주요 경쟁 모델들을 압도하는 성능을 보여준다.

![DeepSeek-V3 주요 벤치마크 비교](figures/fig_1.png)
*Figure 1: DeepSeek-V3와 주요 경쟁 모델들의 벤치마크 성능 비교. MMLU-Pro, GPQA-Diamond, MATH 500, AIME 2024, Codeforces, SWE-bench Verified 6개 지표에서 DeepSeek-V3가 GPT-4o, Claude-3.5-Sonnet 등 클로즈드 모델을 포함한 전 모델 대비 전반적 우위를 보인다. (DeepSeek-AI, 2024)*

발표 직후 오픈소스 LLM의 새로운 기준점을 제시한 것으로 평가받으며, GPT-4o, Claude-3.5-Sonnet 등 최상위 클로즈드 모델과 비견되는 성능으로 업계에 큰 충격을 주었다. 이후 DeepSeek-R1의 추론 모델 기반 아키텍처로 직접 이어졌으며, DeepSeek-V3.1, V3.2 등 지속적으로 업데이트가 이루어지고 있다.

## 배경 및 문제 정의

MoE(Mixture-of-Experts) 아키텍처는 GShard, Switch Transformer 이후로 대규모 언어 모델의 효율적 스케일링 수단으로 자리잡았다. 그러나 MoE 모델을 수백억 파라미터 이상으로 확장할 때 세 가지 근본적인 과제가 존재했으며, DeepSeek-V2에서도 이를 완전히 해결하지 못한 상태였다.

### 보조 손실의 성능 간섭 문제

MoE 모델에서 부하 균형(load balancing)은 필수적이다. 전문가 간 부하가 불균형하면 일부 전문가에 토큰이 집중되어 연산 병목이 발생하고, 극단적인 경우 대부분의 전문가가 전혀 활성화되지 않는 붕괴(collapse) 현상이 나타난다. 기존 접근법은 보조 손실(auxiliary loss)을 통해 이 문제를 해결했다:

$$\mathcal{L}_{total} = \mathcal{L}_{LM} + \alpha \cdot \mathcal{L}_{aux}$$

그러나 이 접근법에는 본질적인 딜레마가 존재한다. 부하 균형 계수 $\alpha$를 키우면 균형은 잡히지만 메인 언어 모델링 성능이 떨어지고, 줄이면 특정 전문가에 토큰이 집중되는 붕괴 현상이 발생한다. Switch Transformer는 $\alpha = 0.01$을 권장했지만, 모델 규모와 전문가 수가 달라지면 최적값도 바뀐다. 근본적으로, 보조 손실의 그래디언트가 메인 태스크의 그래디언트와 충돌하여 최적화 방향을 왜곡시키는 것이 핵심 문제였다.

### 훈련 신호의 밀도 부족

표준 다음 토큰 예측(NTP)은 각 위치에서 단 하나의 토큰만 예측하므로, 특히 대규모 모델의 풍부한 표현 용량을 충분히 활용하지 못할 수 있다. 각 시퀀스에서 추출할 수 있는 학습 신호의 양이 제한적이다. Meta의 연구에서 Multi-Token Prediction이 코드 생성 등 특정 도메인에서 효과적임이 보고되었으나, 초대형 MoE 모델에서의 적용 가능성과 추론 시 활용 방안은 아직 탐구되지 않은 상태였다.

### 초대형 모델의 훈련 비용

Llama-3.1-405B의 훈련에 약 3,080만 H100 GPU-시간이 소요된 것으로 추정되며, 이는 약 1억 달러 이상의 비용에 해당한다. 671B 규모의 MoE 모델을 합리적 비용 내에서 훈련하려면 BF16/FP32 대신 저정밀도 훈련을 도입해야 하지만, FP8의 제한된 동적 범위($E4M3$: 지수 4비트, 가수 3비트)는 훈련 안정성 저하의 위험을 수반한다. H800 GPU의 FP8 텐서 코어를 최대한 활용하면서도 정밀도 손실을 최소화하는 양자화 전략이 필요했다.

## 핵심 아이디어

DeepSeek-V3의 전체 아키텍처는 아래 그림에서 확인할 수 있다. 왼쪽의 Transformer 블록 내부에는 MLA 어텐션이, 오른쪽 상단에는 DeepSeekMoE 기반 피드포워드 네트워크가 배치된다.

![MLA와 DeepSeekMoE 아키텍처 구조](figures/fig_2.png)
*Figure 2: DeepSeek-V3의 핵심 아키텍처. 왼쪽은 MLA(Multi-head Latent Attention)의 저차원 잠재 압축 구조이며, 오른쪽은 DeepSeekMoE의 라우팅 전문가(Routed Expert)와 공유 전문가(Shared Expert)로 구성된 MoE 레이어를 보여준다. MLA에서는 Key-Value를 저차원 잠재 벡터 $c_t^{KV}$로 압축하여 추론 시 캐시 효율을 극적으로 개선한다. (DeepSeek-AI, 2024)*

### 보조 손실 없는 부하 균형 (Auxiliary-Loss-Free Load Balancing)

DeepSeek-V3의 가장 혁신적인 기여 중 하나다. 기존의 미분 가능한 보조 손실을 완전히 제거하고, 대신 각 전문가에 대한 **편향 항(bias term) $b_i$**를 라우팅 결정에 사용한다.

라우팅 과정에서 전문가 선택은 편향이 포함된 점수로 결정하되, 실제 게이팅 값은 편향 없이 계산한다:

$$g'_{i,t} = \begin{cases} s_{i,t} & \text{if } s_{i,t} + b_i \in \text{TopK}(\{s_{j,t}+b_j\}_{j=1}^{N_r}, K_r) \\ 0 & \text{otherwise} \end{cases}$$

여기서 핵심은 **$b_i$는 전문가 선택에만 영향을 미치고, 실제 가중치 $g'_{i,t}$는 원래의 $s_{i,t}$를 사용**한다는 것이다. 이렇게 하면 모델의 출력에는 편향이 반영되지 않으므로 성능 간섭이 없다.

편향의 동적 업데이트는 매 학습 스텝에서 수행된다:

$$b_i \leftarrow b_i - \gamma \cdot \text{sign}(\text{load}_i - \text{target\_load})$$

과부하 전문가의 $b_i$는 감소시키고 과소부하 전문가의 $b_i$는 증가시켜, 점진적으로 균형에 수렴한다. $\gamma$는 매우 작은 값(예: $10^{-4}$)으로 설정하여 급격한 변화를 방지한다.

이 접근법의 장점은 다음과 같다:
- **메인 손실에 간섭 없음**: 보조 손실 항이 $\mathcal{L}_{total}$에서 완전히 제거됨
- **하이퍼파라미터 튜닝 간소화**: $\alpha$ 조정이 불필요
- **그래디언트 충돌 없음**: 부하 균형과 언어 모델링이 서로 다른 경로로 최적화

아래 히트맵은 이 접근법의 효과를 시각적으로 보여준다. 보조 손실 기반 방식에서는 전문가 부하가 전 도메인에 걸쳐 균일하게 분포하는 반면, 보조 손실 없는 방식에서는 특정 도메인(예: DM Mathematics)에 특화된 전문가가 자연스럽게 출현한다.

![Aux-Loss-Based vs Aux-Loss-Free 전문가 부하 히트맵](figures/fig_9.png)
*Figure 9: 보조 손실 기반(Aux-Loss-Based, 상단)과 보조 손실 없는(Aux-Loss-Free, 하단) 방식의 전문가별 상대 부하 히트맵 비교. Aux-Loss-Free 방식에서 도메인별 전문가 특화가 뚜렷하게 형성되며, 이는 보조 손실이 강제하는 인위적 균일 분포 대신 자연스러운 전문화가 이루어짐을 의미한다. (DeepSeek-AI, 2024)*

추가로 **보완적 시퀀스 단위 보조 손실(Complementary Sequence-Wise Auxiliary Loss)**을 사용하여 배치 전체가 아닌 시퀀스 단위에서도 균형을 유지한다:

$$\mathcal{L}_{seq} = \alpha_{seq} \cdot \frac{1}{B} \sum_{b=1}^{B} N_r \sum_{i=1}^{N_r} f_i^{(b)} P_i^{(b)}$$

이 손실은 매우 작은 $\alpha_{seq}$로 설정하여 개별 시퀀스의 전문가 드롭을 방지하는 역할만 한다.

### FP8 혼합 정밀도 훈련

H800 GPU의 FP8 텐서 코어를 활용하여 선형 레이어의 GEMM 연산을 FP8로 수행하고, 어텐션, 정규화, 라우팅 등 민감한 연산은 BF16/FP32로 유지한다.

단순히 텐서 전체에 하나의 스케일링 팩터를 적용하는 per-tensor 양자화는 이상치(outlier)에 취약하다. DeepSeek-V3는 이를 해결하기 위해 보다 세밀한 타일 단위 양자화 전략을 도입했다. 아래 그림은 이 전략의 세부 구조를 보여준다.

![세밀한 FP8 양자화와 누적 정밀도 향상](figures/fig_7.png)
*Figure 7: 세밀한 양자화(Fine-grained Quantization) 전략과 고정밀 누적(Increasing Accumulation Precision) 방식. (a) 활성화는 1x128 per-token 타일, 가중치는 128x128 per-block 타일 단위로 개별 스케일링 팩터를 적용하여 FP8의 제한된 동적 범위 문제를 극복한다. (b) WGMMA 명령어의 누적 결과를 주기적으로 FP32 레지스터에 저장하여 누적 오차를 방지한다. (DeepSeek-AI, 2024)*

전체 FP8 훈련의 데이터플로우는 아래 그림에서 확인할 수 있다. Forward 연산과 Weight 그래디언트 연산은 FP8로 수행하고, 마스터 가중치와 옵티마이저 상태는 BF16/FP32로 유지하는 하이브리드 구조이다.

![FP8 혼합 정밀도 훈련 데이터플로우](figures/fig_6.png)
*Figure 6: FP8 혼합 정밀도 훈련의 데이터플로우. Forward(Fprop)와 Weight 그래디언트(Wgrad) GEMM은 FP8 텐서 코어로 가속하고, 마스터 가중치와 옵티마이저 상태는 BF16/FP32로 유지하여 훈련 안정성과 연산 효율을 동시에 확보한다. (DeepSeek-AI, 2024)*

구체적인 양자화 전략은 다음과 같다:
- **활성화(Activation)**: 1x128 per-token tile 양자화 -- 토큰별로 독립적인 스케일링 팩터 적용
- **가중치(Weight)**: 128x128 per-block tile 양자화 -- 가중치 행렬을 블록 단위로 분할하여 각각 양자화
- **누적(Accumulation)**: CUDA 코어에서 FP32로 고정밀 누적 후 BF16으로 변환

실험에서 FP8 훈련의 손실 함수 차이($\Delta$)가 BF16 대비 0.25% 미만임을 확인하여, 671B 규모에서도 정밀도 손실이 무시할 수 있는 수준임을 입증했다.

### DualPipe 알고리즘

파이프라인 병렬화에서 통신 오버헤드를 최소화하기 위한 알고리즘이다. 핵심 아이디어는 **계산과 통신을 겹쳐서(overlap) 실행**하는 것이다:

- Forward/Backward 계산과 MoE All-to-All 통신을 동시에 실행
- 파이프라인 버블(idle 시간)을 기존 대비 50% 감소
- 통신 전용 SM을 20개로 제한하여 나머지 SM을 계산에 할당

이를 통해 모델 규모가 커져도 계산-통신 비율이 일정하게 유지되면 전문가 병렬화의 오버헤드가 거의 제로에 수렴한다. 아래 그림은 DualPipe의 단일 마이크로배치에서 계산과 통신이 어떻게 중첩되는지를 보여준다.

![DualPipe 계산-통신 오버랩 타임라인](figures/fig_4.png)
*Figure 4: DualPipe 알고리즘의 계산-통신 오버랩 타임라인. Forward 청크(삼각형)와 Backward 청크(삼각형) 실행 중에 MoE DISPATCH/COMBINE 통신이 동시에 수행되어, GPU idle 시간을 최소화한다. (DeepSeek-AI, 2024)*

이 설계를 8개 디바이스에 걸친 파이프라인으로 확장하면 아래와 같은 스케줄이 형성된다. Forward, Backward, 그리고 이들이 겹쳐 실행되는 구간이 색상으로 구분되어 있다.

![8-디바이스 파이프라인 병렬화 스케줄](figures/fig_5.png)
*Figure 5: 8개 디바이스에 걸친 DualPipe 파이프라인 스케줄. Forward(주황), Backward for input(녹색), Backward for weights(하늘), Forward+Backward 겹침(청록)이 색상으로 구분되며, 기존 방식 대비 파이프라인 버블이 크게 감소했음을 확인할 수 있다. (DeepSeek-AI, 2024)*

## 방법론

### Multi-head Latent Attention (MLA)

DeepSeek-V3는 전작 DeepSeek-V2에서 제안한 MLA를 그대로 계승한다. 표준 Multi-Head Attention(MHA)에서는 각 헤드의 Key와 Value를 모두 캐싱해야 하므로 KV 캐시 크기가 $2 \times n_h \times d_h \times L$로 증가한다. MLA는 Key와 Value를 저차원 잠재 벡터로 압축하여 캐시 효율을 극적으로 개선한다:

$$c_t^{KV} = W^{DKV} x_t \quad (d_c \ll n_h \cdot d_h)$$

$$k_t = W^{UK} c_t^{KV}, \quad v_t = W^{UV} c_t^{KV}$$

여기서 $c_t^{KV} \in \mathbb{R}^{d_c}$는 KV 압축 잠재 벡터이고, $d_c = 512$로 설정된다. 실제 캐싱 대상은 $c_t^{KV}$만이므로, GQA(Grouped Query Attention) 대비 추가적인 메모리 절감이 가능하다. 또한 Query에도 동일한 저차원 압축을 적용하고, RoPE(Rotary Position Embedding)를 위한 별도의 비결합 키를 사용하여 위치 인코딩과의 호환성을 유지한다.

### DeepSeekMoE 아키텍처

DeepSeek-V3의 MoE 레이어는 DeepSeek-V2에서 제안한 세밀 전문가(fine-grained expert) 설계를 따른다. 기존 MoE가 소수의 대형 전문가를 사용하는 것과 달리, DeepSeekMoE는 더 많은 수의 소형 전문가를 배치하여 전문가 조합의 다양성을 높인다. DeepSeek-V3에서는 256개의 라우팅 전문가와 1개의 공유 전문가(shared expert)를 사용하며, 각 토큰은 8개의 라우팅 전문가를 활성화한다.

공유 전문가는 모든 토큰에 대해 항상 활성화되어 범용적인 지식을 처리하고, 라우팅 전문가는 토큰별로 선택적으로 활성화되어 전문화된 지식을 담당한다. 최종 출력은 다음과 같이 계산된다:

$$h_t' = \text{FFN}_{\text{shared}}(h_t) + \sum_{i \in \text{TopK}} g'_{i,t} \cdot \text{FFN}_i(h_t)$$

61개의 Transformer 레이어 중 처음 3개 레이어는 Dense FFN을 사용하고, 나머지 58개 레이어가 MoE 구조를 채택한다. 이는 초기 레이어에서 범용 표현을 충분히 학습한 후 전문가 기반 분기를 적용하기 위한 설계이다.

### Multi-Token Prediction (MTP)

MTP는 각 위치에서 다음 1개 토큰이 아닌 $D$개의 연속 토큰을 동시에 예측하도록 한다. DeepSeek-V3에서는 $D=1$ (1개의 추가 토큰 예측 모듈)을 사용한다. 아래 그림은 MTP 모듈이 메인 모델과 어떻게 연결되는지를 보여준다.

![Multi-Token Prediction 모듈 아키텍처](figures/fig_3.png)
*Figure 3: Multi-Token Prediction(MTP) 모듈 구조. 메인 모델(왼쪽)의 히든 스테이트와 미래 토큰 임베딩을 결합하여 MTP Module 1(중간)이 두 번째 미래 토큰을, MTP Module 2(오른쪽)가 세 번째 미래 토큰을 순차적으로 예측한다. 임베딩 레이어와 출력 헤드를 메인 모델과 공유하여 파라미터 효율성을 유지하면서 추가 학습 신호를 생성한다. (DeepSeek-AI, 2024)*

#### MTP 모듈 아키텍처

각 추가 예측 깊이 $k = 1, \ldots, D$에 대해:

1. **입력 결합**: 주 모델의 히든 스테이트 $h_t^{(0)}$와 미래 토큰 임베딩 $e(x_{t+k})$를 결합
2. **추가 Transformer 레이어**: 결합된 입력을 처리하여 $h_t^{(k)}$ 생성
3. **공유 출력 헤드**: 메인 모델과 동일한 출력 임베딩으로 $x_{t+k+1}$ 예측

$$h_t^{(k)} = \text{TRM}_k([\text{RMSNorm}(\text{Linear}([h_t^{(k-1)}; e(x_{t+k})]))])$$

$$\mathcal{L}_{MTP}^k = -\sum_{t} \log P(x_{t+k+1} | h_t^{(k)})$$

전체 MTP 훈련 목표:

$$\mathcal{L}_{total} = \mathcal{L}_{LM} + \lambda \sum_{k=1}^{D} \mathcal{L}_{MTP}^k$$

여기서 $\lambda = 0.3$으로 설정했다. MTP의 이중 이점:
- **훈련 시**: 추가적인 학습 신호로 주 모델의 표현을 더 풍부하게 만듦
- **추론 시**: MTP 모듈을 투기적 디코딩(speculative decoding)의 드래프트 모델로 활용하여 1.8배 처리량 향상 (TPS 기준)

### 아키텍처 하이퍼파라미터

| 구성 요소 | 설정값 |
|---|---|
| 총 파라미터 | 671B |
| 활성화 파라미터 | 37B |
| Transformer 레이어 | 61 |
| 어텐션 헤드 수 | 128 |
| KV 압축 차원 ($d_c$) | 512 |
| 라우팅 전문가 수 | 256 |
| 공유 전문가 수 | 1 |
| 활성화 라우팅 전문가 수 | 8 |
| 최대 시퀀스 길이 | 128K |
| 훈련 토큰 수 | 14.8T |
| MTP 깊이 ($D$) | 1 |
| MTP 가중치 ($\lambda$) | 0.3 |
| 훈련 비용 | 2.788M H800 GPU-hours |
| 추정 훈련 비용 | ~$5.57M USD |

### V2 대비 변경점

| 구성 요소 | DeepSeek-V2 | DeepSeek-V3 |
|---|---|---|
| 총 파라미터 | 236B | 671B |
| 활성화 파라미터 | 21B | 37B |
| 라우팅 전문가 수 | 160 | 256 |
| 공유 전문가 수 | 2 | 1 |
| 부하 균형 | 보조 손실 | 편향 기반 (Aux-Free) |
| 훈련 정밀도 | BF16 | FP8 혼합 |
| MTP | 미사용 | $D=1$, $\lambda=0.3$ |
| 파이프라인 | 기존 | DualPipe |

## 실험 결과

### 주요 벤치마크 비교 (종합)

| 벤치마크 | GPT-4o | Claude-3.5-Sonnet | DeepSeek-V3 | Llama-3.1-405B | Qwen-2.5-72B |
|---|---|---|---|---|---|
| MMLU | 88.0 | 88.3 | **88.5** | 87.3 | 85.3 |
| MMLU-Pro | 72.6 | 78.0 | **75.9** | 73.3 | 71.6 |
| MATH-500 | 76.6 | 78.3 | **90.2** | 73.8 | 80.0 |
| AIME 2024 | 9.3 | 16.0 | **39.2** | 23.3 | 23.3 |
| HumanEval | 90.2 | **92.0** | 89.0 | 89.0 | 86.6 |
| LiveCodeBench | 33.4 | 36.3 | **43.4** | 27.4 | 26.7 |
| GPQA Diamond | 53.6 | **65.0** | 59.1 | 51.1 | 49.0 |
| Codeforces Rating | 1673 | 1735 | **1996** | 1573 | 1510 |
| C-Eval | 83.6 | - | **86.5** | - | 86.1 |

DeepSeek-V3는 특히 다음 영역에서 두드러진 성능을 보인다:
- **수학**: MATH-500 (90.2%), AIME 2024 (39.2%)에서 모든 모델을 압도. 특히 AIME 2024에서 GPT-4o(9.3%) 대비 4배 이상의 정답률을 기록한 것이 인상적이다.
- **코딩**: LiveCodeBench (43.4%), Codeforces (1996)에서 SOTA. Codeforces 레이팅 1996은 상위 약 4%에 해당하는 수준이다.
- **중국어**: C-Eval (86.5%)에서 최상위 수준으로, 중국어 데이터에 대한 충실한 사전 훈련의 효과를 보여준다.

### 128K 컨텍스트 능력 검증

DeepSeek-V3는 128K 토큰까지 확장된 컨텍스트 윈도우를 지원한다. 아래 Needle-in-a-Haystack 테스트에서 전 구간에 걸쳐 완벽한 점수를 기록하여, 초장문 컨텍스트에서도 정보 검색 능력이 저하되지 않음을 입증했다.

![128K 컨텍스트 Needle-in-a-Haystack 평가](figures/fig_8.png)
*Figure 8: DeepSeek-V3의 128K 컨텍스트 Needle-in-a-Haystack 압박 테스트 결과. 컨텍스트 길이(2K~128K)와 문서 깊이(0%~100%) 전 구간에서 10점 만점을 기록하여, YaRN 기반 컨텍스트 확장의 효과를 확인한다. (DeepSeek-AI, 2024)*

### 훈련 비용 효율성

| 모델 | 훈련 비용 (추정) | 성능 수준 |
|---|---|---|
| Llama-3.1-405B | ~$100M+ | DeepSeek-V3보다 낮음 |
| GPT-4 (추정) | ~$100M+ | 비슷 |
| DeepSeek-V3 | **~$5.57M** | 최상위 |

약 557만 달러라는 훈련 비용은 동급 성능 대비 전례 없이 낮은 수준이다. 이는 FP8 훈련으로 인한 연산량 절감, DualPipe의 효율적 계산-통신 중첩, 그리고 MoE의 희소 활성화(토큰당 37B/671B = 5.5%만 활성화)가 만들어낸 시너지 효과이다.

### 훈련 안정성

14.8T 토큰 훈련 전반에 걸쳐 **손실 스파이크(loss spike) 없이 안정적인 수렴**을 달성했다. 이는 MoE 대규모 모델에서 매우 이례적인 결과로, 보조 손실 제거와 FP8 양자화 전략의 안정성을 동시에 입증한다. 전체 훈련 과정에서 롤백(rollback)이 한 번도 발생하지 않았다는 점은 특히 주목할 만하다.

아래 그림은 FP8과 BF16 정밀도의 사전학습 perplexity 수렴 곡선을 비교한 것이다. 100B 토큰과 1T 토큰 규모 모두에서 두 정밀도의 수렴 특성이 사실상 동일함을 확인할 수 있다.

![FP8 vs BF16 사전학습 perplexity 비교](figures/fig_10.png)
*Figure 10: FP8(파란색)과 BF16(빨간색)의 사전학습 PPL 수렴 곡선 비교. 100B 토큰(왼쪽)과 1T 토큰(오른쪽) 규모 모두에서 FP8 훈련이 BF16과 동등한 수렴 특성을 보이며, 671B 규모 FP8 훈련의 실용성을 뒷받침한다. (DeepSeek-AI, 2024)*

### Ablation Study: 핵심 기법의 기여도

소규모 모델(15.7B 파라미터, 2.4B 활성화)에서 수행한 Ablation 실험 결과, 각 핵심 기법의 개별 기여도를 정량적으로 확인할 수 있다.

| 설정 | 평균 벤치마크 점수 | 상대 변화 |
|---|---|---|
| Baseline (Aux-Loss + NTP) | 46.4 | - |
| + Aux-Loss-Free | 47.5 | +2.4% |
| + MTP ($D=1$, $\lambda=0.3$) | 48.2 | +3.9% |
| + Aux-Loss-Free + MTP | **49.0** | **+5.6%** |

보조 손실 제거와 MTP가 독립적으로 성능 향상에 기여하며, 두 기법을 결합할 때 시너지 효과가 나타난다. 특히 MTP의 효과는 수학 및 코딩 벤치마크에서 가장 두드러졌으며, 이는 MTP가 모델의 계획(planning) 능력을 향상시키기 때문으로 분석된다. 두 기법 모두 성능 향상에 독립적으로 기여하면서도 결합 시 단순 합산(+6.3%) 대비 약간 낮은 +5.6%로, 일부 중첩되는 효과가 있음을 시사한다.

### 훈련 비용 상세 분석

| 훈련 단계 | GPU-시간 | 비율 |
|---|---|---|
| Pre-training (14.8T 토큰) | 2,664K H800 | 95.6% |
| Context Extension (32K→128K) | 119K H800 | 4.3% |
| SFT + RLHF | 5K H800 | 0.2% |
| **합계** | **2,788K H800** | **100%** |

주목할 점은 사전 훈련이 전체 비용의 95.6%를 차지하며, 컨텍스트 확장(YaRN 적용)은 4.3%, 정렬(SFT + RLHF)은 겨우 0.2%에 불과하다는 것이다. H800 GPU의 시간당 비용을 약 $2로 가정하면, 사전 훈련에 약 533만 달러, 전체 과정에 약 557만 달러가 소요된 것으로 추정된다.

## 의의 및 한계

### 의의

**오픈소스 LLM의 새로운 기준점**: DeepSeek-V3는 GPT-4o, Claude-3.5-Sonnet 등 최상위 클로즈드 모델과 경쟁하는 첫 번째 오픈소스 모델로, 오픈소스 AI의 가능성을 입증했다.

**보조 손실 없는 부하 균형**: MoE 훈련의 오랜 딜레마($\alpha$ 튜닝)를 해결한 중요한 기여다. 편향 기반 접근법은 이후 다른 MoE 모델 설계에도 영향을 미치고 있다.

**MTP의 이중 활용**: 훈련 시 학습 신호 강화와 추론 시 투기적 디코딩이라는 두 가지 이점을 동시에 제공하는 우아한 설계다.

**AI 민주화**: 약 557만 달러의 훈련 비용은 동급 성능 대비 전례 없이 낮은 수준으로, 소규모 조직도 최상위 LLM을 훈련할 수 있는 가능성을 열었다.

**FP8 훈련의 실용성 입증**: 671B 규모에서 FP8 훈련이 BF16과 동등한 성능을 달성함을 보여, 향후 대규모 모델 훈련의 표준 정밀도가 될 가능성을 제시했다.

**DeepSeek-R1의 토대**: DeepSeek-V3는 이후 강화학습 기반 추론 모델인 DeepSeek-R1의 기반 아키텍처로 사용되어, o1/o3 수준의 추론 능력을 가진 오픈소스 모델의 탄생을 이끌었다.

### 한계

**배포 리소스 요구**: 671B 전체 모델 배포에 여전히 상당한 GPU 메모리(최소 80GB x 8개 이상)가 필요하다. 양자화를 적용해도 개인 수준 배포에는 접근이 제한적이다.

**MTP 최적화의 경험적 특성**: MTP의 추가 예측 깊이 $D$와 가중치 $\lambda$ 결정이 경험적이다. $D > 1$의 효과나 도메인별 최적값에 대한 체계적 분석이 부족하다.

**FP8의 하드웨어 의존성**: FP8 훈련은 H800/H100 등 최신 NVIDIA GPU에서만 가능하여, 이전 세대 GPU나 다른 벤더의 하드웨어에서는 활용할 수 없다.

**편향 기반 부하 균형의 수렴 보장 부재**: $b_i$ 업데이트의 수렴 속도와 안정성에 대한 이론적 분석이 부족하며, 극단적 부하 불균형 상황에서의 동작이 충분히 검증되지 않았다.

## 코드 예제

### MTP 모듈 (Multi-Token Prediction Module)

주 모델의 히든 스테이트와 미래 토큰 임베딩을 결합하여 추가 예측을 수행하는 단위 모듈이다.

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class MTPModule(nn.Module):
    """DeepSeek-V3의 Multi-Token Prediction 모듈.
    주 모델의 히든 스테이트 + 미래 토큰 임베딩을 결합하여
    다음 토큰을 추가로 예측. 학습 신호 강화 + 추론 시 speculative decoding.
    """
    def __init__(self, d_model=7168, vocab_size=129280):
        super().__init__()
        # 결합 레이어: h_t^(k-1)와 embed(x_{t+k})를 결합
        self.combine = nn.Linear(d_model * 2, d_model)
        self.norm = nn.RMSNorm(d_model)
        # 간소화된 Transformer 레이어 (실제로는 전체 블록 사용)
        self.attn = nn.MultiheadAttention(d_model, num_heads=32, batch_first=True)
        self.ffn = nn.Sequential(
            nn.Linear(d_model, d_model * 4),
            nn.SiLU(),
            nn.Linear(d_model * 4, d_model)
        )
        self.norm2 = nn.RMSNorm(d_model)

    def forward(self, h_prev, future_embed):
        """h_prev: 이전 깊이의 히든 스테이트, future_embed: 미래 토큰 임베딩."""
        combined = self.combine(torch.cat([h_prev, future_embed], dim=-1))
        x = self.norm(combined)
        x = x + self.attn(x, x, x, is_causal=True)[0]
        x = x + self.ffn(self.norm2(x))
        return x

```

### MTP 학습 목표 (DeepSeek-V3 MTP)

메인 NTP 손실과 MTP 보조 손실을 결합한 전체 학습 목표 구현이다. 공유 출력 헤드를 통해 추가 토큰을 예측한다.

```python
class DeepSeekV3MTP(nn.Module):
    """DeepSeek-V3 전체 MTP 학습 목표."""
    def __init__(self, d_model=7168, vocab_size=129280, mtp_depth=1, mtp_lambda=0.3):
        super().__init__()
        self.mtp_depth = mtp_depth
        self.mtp_lambda = mtp_lambda
        self.embed = nn.Embedding(vocab_size, d_model)
        self.main_head = nn.Linear(d_model, vocab_size, bias=False)
        # MTP 모듈들 (깊이 D개)
        self.mtp_modules = nn.ModuleList([
            MTPModule(d_model, vocab_size) for _ in range(mtp_depth)
        ])
        # 출력 헤드는 메인과 공유 (shared output head)

    def forward(self, hidden_states, input_ids, labels):
        B, T, D = hidden_states.shape

        # 1. 메인 NTP 손실
        main_logits = self.main_head(hidden_states)
        main_loss = F.cross_entropy(
            main_logits[:, :-1].reshape(-1, main_logits.size(-1)),
            labels[:, 1:].reshape(-1)
        )

        # 2. MTP 손실 (각 추가 깊이)
        h = hidden_states
        mtp_loss = 0.0
        for k, mtp_module in enumerate(self.mtp_modules, start=1):
            if T <= k + 1:
                break
            # 미래 토큰 임베딩: embed(x_{t+k})
            future_embed = self.embed(input_ids[:, k:T])
            # 히든 스테이트 정렬 (t=0..T-k-1)
            h_aligned = h[:, :T-k]
            # MTP 모듈로 h^(k) 계산
            h_k = mtp_module(h_aligned, future_embed)
            # 공유 출력 헤드로 x_{t+k+1} 예측
            mtp_logits = self.main_head(h_k)
            mtp_loss_k = F.cross_entropy(
                mtp_logits.reshape(-1, mtp_logits.size(-1)),
                labels[:, k+1:T+1].reshape(-1)
            )
            mtp_loss += mtp_loss_k
            h = h_k  # 다음 깊이를 위해 업데이트

        total_loss = main_loss + self.mtp_lambda * mtp_loss
        return main_logits, total_loss

```

### 보조 손실 없는 MoE 라우터

편향(bias)을 전문가 선택에만 활용하고 실제 게이팅 값에는 영향을 주지 않는 Aux-Loss-Free 라우터이다.

```python
class AuxLossFreeMoERouter(nn.Module):
    """DeepSeek-V3의 보조 손실 없는 부하 균형 라우터.
    핵심: 편향(bias)은 전문가 선택에만 영향, 실제 가중치에는 무영향.
    """
    def __init__(self, d_model, num_experts, top_k, gamma=1e-4):
        super().__init__()
        self.router = nn.Linear(d_model, num_experts, bias=False)
        self.bias = nn.Parameter(torch.zeros(num_experts), requires_grad=False)
        self.top_k = top_k
        self.gamma = gamma
        self.num_experts = num_experts

    def forward(self, x):
        """x: (B, T, D)"""
        logits = self.router(x)  # (B, T, E)
        scores = torch.sigmoid(logits)  # 라우팅 점수 (DeepSeek-V3는 sigmoid 사용)

        # 전문가 선택: 편향 포함된 점수로 Top-K
        biased_scores = scores + self.bias  # 선택용
        _, selected = torch.topk(biased_scores, self.top_k, dim=-1)

        # 실제 게이팅 값: 편향 없이 원래 점수 사용 (핵심!)
        gate_values = torch.gather(scores, -1, selected)
        gate_values = gate_values / gate_values.sum(dim=-1, keepdim=True)  # 정규화

        return selected, gate_values

    @torch.no_grad()
    def update_bias(self, selected_experts):
        """학습 스텝마다 편향 업데이트: 과부하 → 감소, 과소 → 증가."""
        load = torch.zeros(self.num_experts, device=selected_experts.device)
        load.scatter_add_(0, selected_experts.flatten(),
                         torch.ones_like(selected_experts.flatten(), dtype=torch.float))
        target = selected_experts.numel() / self.num_experts
        self.bias.data -= self.gamma * torch.sign(load - target)


# 사용 예시
print("=== DeepSeek-V3 핵심 기술 시연 ===")
mtp = DeepSeekV3MTP(d_model=256, vocab_size=1000, mtp_depth=1, mtp_lambda=0.3)
hidden = torch.randn(2, 20, 256)
input_ids = torch.randint(0, 1000, (2, 20))
labels = torch.randint(0, 1000, (2, 21))  # 타겟은 한 토큰 더
logits, loss = mtp(hidden, input_ids, labels[:, :20])
print(f"MTP loss: {loss.item():.4f}")

router = AuxLossFreeMoERouter(d_model=256, num_experts=256, top_k=8)
x = torch.randn(2, 20, 256)
selected, gates = router(x)
print(f"선택된 전문가: {selected.shape}, 게이트 값: {gates.shape}")
router.update_bias(selected)
print(f"편향 범위: [{router.bias.min():.6f}, {router.bias.max():.6f}]")
```

## 관련 문서

- [[deepseek-v2|DeepSeek-V2: A Strong, Economical, and Efficient Mixture-of-Experts Language Model]] — 발전 기반
- [[deepseek-r1|DeepSeek-R1]] — 후속 모델
- [[deepseek-r1-zero|DeepSeek-R1-Zero]] — 후속 모델
- [[kimi-k2|Kimi K2]] — 영감을 줌