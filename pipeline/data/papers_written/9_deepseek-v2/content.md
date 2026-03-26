## 개요

DeepSeek-V2는 DeepSeek AI가 2024년 5월 발표한 MoE(Mixture-of-Experts) 기반 대규모 언어 모델이다. 총 236B 파라미터를 가지지만 토큰당 21B만 활성화하는 희소 활성화 구조를 채택하여, 강력한 성능을 경제적으로 달성한다. 핵심 기여는 두 가지 혁신적인 아키텍처 구성 요소인 **Multi-head Latent Attention(MLA)**와 **DeepSeekMoE**이며, 이를 통해 DeepSeek 67B 대비 훈련 비용 42.5% 절감, KV 캐시 93.3% 절감, 추론 처리량 5.76배 향상을 달성했다.

이 논문은 MoE 기반 언어 모델이 Dense 모델과 동등하거나 우수한 성능을 훨씬 낮은 비용으로 달성할 수 있음을 실증적으로 입증한 중요한 연구로, 이후 DeepSeek-V3, DeepSeek-R1으로 이어지는 아키텍처 혁신의 기반을 마련했다. Semantic Scholar 기준 수백 회 이상 인용되었으며, MLA는 현대 LLM 아키텍처의 핵심 기술로 자리잡았다.

다음 그림은 DeepSeek-V2의 핵심 가치를 한눈에 보여준다. 21B 활성화 파라미터만으로 70B급 Dense 모델과 동등한 MMLU 성능을 달성하면서도, 훈련 비용과 추론 효율 모두에서 압도적인 개선을 이루었다.

![DeepSeek-V2의 성능 대비 활성화 파라미터 효율](figures/fig_1_1.png)
*Figure 1(a): 오픈소스 모델들의 MMLU 정확도 대비 활성화 파라미터 수 비교. DeepSeek-V2는 21B 활성화 파라미터만으로 Llama3 70B, Mixtral 8x22B 등 훨씬 큰 모델과 동등하거나 우수한 성능을 보이며, 파라미터 효율의 새로운 기준을 제시한다.*

논문의 주요 기여를 정리하면 다음과 같다:

1. KV 캐시를 저차원 잠재 공간으로 압축하는 MLA를 제안하여, 표현력 손실 없이 캐시 메모리를 93.3% 절감
2. 세분화된 전문가(Fine-grained Experts)와 공유 전문가(Shared Experts)를 결합한 DeepSeekMoE 아키텍처로 전문가 활용 효율 극대화
3. 8.1T 토큰 사전훈련과 SFT + GRPO 정렬을 통해 오픈소스 최고 수준의 성능-비용 효율 달성
4. 모델 가중치와 아키텍처를 완전 공개하여 업계 최저가 API 서비스 제공

## 배경 및 문제

대형 언어 모델의 성능은 스케일링 법칙(Scaling Law)에 따라 파라미터 수와 훈련 데이터 양에 비례하여 향상된다. 그러나 모델 크기가 커질수록 훈련 비용과 추론 비용이 급격히 증가하여, 성능과 효율성 사이의 균형이 핵심 과제로 부상했다. DeepSeek-V2는 이 문제를 어텐션 메커니즘과 FFN 구조 양쪽에서 동시에 해결하고자 한다.

### KV 캐시 메모리 병목

표준 Multi-Head Attention(MHA)은 추론 시 각 레이어마다 $2 \times n_{heads} \times d_{head}$ 크기의 KV 캐시를 유지해야 한다. 시퀀스 길이 $L$, 레이어 수 $N_L$일 때 전체 KV 캐시 크기는 다음과 같다:

$$\text{KV Cache} = 2 \times N_L \times n_{heads} \times d_{head} \times L \times \text{sizeof(dtype)}$$

예를 들어 67B Dense 모델(96 헤드, 128 차원, 95 레이어)에서 128K 컨텍스트를 FP16으로 처리할 경우, KV 캐시만으로 약 300GB 이상의 메모리가 필요하다. 이로 인해 배치 크기 확대와 긴 시퀀스 처리가 극도로 제한되며, 추론 서버의 GPU 메모리 대부분이 KV 캐시에 소비되어 실질적인 처리량(throughput)이 크게 저하된다.

### Dense 모델의 계산 비용 문제

Dense 모델은 모든 파라미터를 매 토큰마다 활성화하므로 계산 비용이 파라미터 수에 선형 비례한다. 67B Dense 모델의 경우 토큰당 약 134 GFLOPs의 연산이 필요하다. 모델 크기를 늘려 성능을 개선하려면 비례적으로 더 많은 계산 자원이 필요하며, 이는 훈련 비용과 추론 비용 모두에 직결된다.

### MoE의 기존 문제점

MoE(Mixture-of-Experts) 아키텍처는 전체 파라미터의 일부만 활성화하여 계산 효율을 높이는 접근법이다. GShard(2020), Switch Transformer(2021), Mixtral(2024) 등의 선행 연구가 있었으나, 다음과 같은 근본적인 한계를 가지고 있었다:

- **전문가 활용 불균형(Load Imbalance)**: 특정 전문가에 토큰이 집중되어 일부 전문가는 과도하게 사용되고 나머지는 유휴 상태에 머무르는 현상이 발생한다.
- **지식 중복(Knowledge Redundancy)**: 여러 전문가가 유사한 일반 지식을 중복으로 학습하여 파라미터 효율이 저하된다.
- **지식 분절(Knowledge Fragmentation)**: 하나의 복합적인 작업에 필요한 지식이 여러 전문가에 분산되어 각 전문가가 충분한 전문성을 갖추지 못하는 문제가 있다.

### 기존 KV 캐시 압축 기법의 한계

Grouped Query Attention(GQA)이나 Multi-Query Attention(MQA) 같은 KV 캐시 압축 기법들은 KV 헤드 수를 줄여 메모리를 절감하지만, 여러 Query 헤드가 동일한 K/V 헤드를 공유해야 하므로 헤드 간 표현력 다양성이 감소한다. 구체적으로, MQA는 모든 Query 헤드가 단일 K/V 헤드를 공유하여 캐시를 $1/n_h$로 줄이지만 성능 저하가 크고, GQA-$G$는 $G$개의 그룹으로 나누어 절충하지만 그룹 수 $G$의 선택이 경험적이며 표현력과 효율성 사이의 트레이드오프가 불가피하다.

## 핵심 아이디어

DeepSeek-V2의 핵심 아이디어는 Transformer의 두 가지 주요 구성 요소인 어텐션과 FFN을 각각 MLA와 DeepSeekMoE로 대체하여, 성능 손실 없이 효율성을 극대화하는 것이다. 아래 그림은 기존 어텐션 메커니즘들과 MLA의 구조적 차이를 시각적으로 비교한다.

![MHA, GQA, MQA, MLA 어텐션 메커니즘의 구조 비교](figures/fig_5.png)
*Figure 3: MHA(Multi-Head Attention), GQA(Grouped-Query Attention), MQA(Multi-Query Attention), MLA(Multi-head Latent Attention) 구조 비교. MHA는 각 헤드마다 독립적인 K, V를 캐시하는 반면, MLA는 K와 V를 하나의 저차원 잠재 벡터(Compressed Latent KV)로 공동 압축하여 추론 시 KV 캐시를 획기적으로 절감한다.*

### Multi-head Latent Attention (MLA)

MLA는 DeepSeek-V2의 가장 혁신적인 기여로, KV 캐시 문제를 근본적으로 해결하는 새로운 어텐션 메커니즘이다. 핵심 아이디어는 **KV 벡터를 저차원 잠재 공간(latent space)으로 압축(down-projection)한 뒤, 실제 어텐션 계산 시에만 복원(up-projection)**하는 것이다.

#### KV 압축

기존 MHA에서는 각 토큰의 전체 K, V 벡터($n_h \times d_h$ 차원)를 캐시에 저장해야 했지만, MLA는 이를 $d_c$ 차원의 잠재 벡터 하나로 압축하여 저장한다:

$$c_t^{KV} = W^{DKV} h_t$$

$$k_t^C = W^{UK} c_t^{KV}, \quad v_t^C = W^{UV} c_t^{KV}$$

여기서 $c_t^{KV} \in \mathbb{R}^{d_c}$는 압축된 잠재 벡터이며, $d_c \ll n_h \cdot d_h$이다. DeepSeek-V2에서는 $d_c = 512$이고 $n_h \cdot d_h = 128 \times 128 = 16384$이므로, **캐시 크기가 약 32배 감소**한다. 이 과정은 Low-Rank Approximation의 원리를 활용한 것으로, 원래의 KV 행렬이 가진 정보를 최소한의 차원으로 보존한다.

#### Q 압축

MLA는 Query 벡터에도 동일한 압축 전략을 적용한다. 이는 KV 캐시 절감과는 직접적인 관련이 없지만, 훈련 시 활성화 메모리(activation memory)를 절감하는 효과가 있다:

$$c_t^Q = W^{DQ} h_t, \quad q_t^C = W^{UQ} c_t^Q$$

여기서 $c_t^Q \in \mathbb{R}^{d_c'}$이고, $d_c' = 1536$으로 설정된다. Q의 압축 차원이 KV보다 큰 이유는, Query가 현재 토큰의 의도를 직접 표현하므로 더 높은 표현력이 필요하기 때문이다.

#### RoPE 디커플링

MLA의 핵심적인 설계 결정 중 하나는 **RoPE 디커플링(decoupled RoPE)**이다. RoPE(Rotary Position Embedding)는 위치 정보를 Key 벡터에 인코딩하는데, 압축된 잠재 벡터에 직접 RoPE를 적용하면 압축-복원 과정에서 위치 정보가 손상된다. 이는 RoPE가 벡터의 각 차원 쌍에 회전 변환을 적용하는 구조인데, 압축(down-projection)이 이 회전 구조를 파괴하기 때문이다.

이를 해결하기 위해 별도의 위치 전용 키 벡터 $k_t^R$를 도입한다:

$$q_t = [q_t^C; q_t^R], \quad k_t = [k_t^C; k_t^R]$$

$$k_t^R = \text{RoPE}(W^{KR} h_t), \quad q_t^R = \text{RoPE}(W^{QR} c_t^Q)$$

이로써 내용 기반 어텐션($q_t^C$, $k_t^C$)과 위치 기반 어텐션($q_t^R$, $k_t^R$)이 분리되어, 각각 최적의 표현력을 유지할 수 있다. 위치 전용 키 $k_t^R$의 차원 $d_h^R = 64$는 전체 헤드 차원 128에 비해 매우 작으므로 KV 캐시 추가 부담이 미미하다.

#### 어텐션 계산과 흡수 트릭

최종 어텐션 출력은 다음과 같이 계산된다:

$$o_{t,i} = \sum_{j \leq t} \text{softmax}\left(\frac{q_{t,i}^\top k_{j,i}}{\sqrt{d_h + d_h^R}}\right) v_{j,i}^C$$

실제 추론에서는 **흡수 트릭(absorption trick)**을 활용하여 효율성을 더욱 높인다. $q_{t,i}^{C\top} W_i^{UK}$와 $W_i^{UV}$를 각각 $q_{t,i}^{C\top}$에 미리 흡수시켜, 캐시된 $c_t^{KV}$에 대해 직접 어텐션을 계산할 수 있다. 이렇게 하면 추론 시 $W^{UK}$와 $W^{UV}$의 up-projection을 명시적으로 수행할 필요가 없어, 계산량이 추가로 절감된다:

$$q_{t,i}^{C\top} k_{j,i}^C = q_{t,i}^{C\top} W_i^{UK} c_j^{KV} = \tilde{q}_{t,i}^{C\top} c_j^{KV}$$

이 설계의 핵심 장점은 **KV 캐시에는 $c_t^{KV}$와 $k_t^R$만 저장**하면 되므로, 전체 K, V 벡터를 저장하는 MHA 대비 캐시를 93.3% 절감하면서도 성능 저하 없이 **풀 어텐션 표현력**을 유지한다는 것이다. GQA/MQA와 달리 MLA는 각 헤드가 고유한 K, V를 복원할 수 있어 표현력 손실이 없다.

#### MLA와 기존 어텐션의 비교

| 메커니즘 | KV 캐시 크기 (토큰당) | 표현력 | 추론 속도 |
|---|---|---|---|
| MHA | $2 n_h d_h$ | 최고 | 느림 |
| MQA | $2 d_h$ | 제한적 | 빠름 |
| GQA-$G$ | $2 G d_h$ | 중간 | 중간 |
| **MLA** | $d_c + d_h^R$ | **MHA 수준** | **빠름** |

구체적인 수치로 비교하면, DeepSeek-V2 설정(128 헤드, 128 차원)에서 토큰당 레이어당 KV 캐시 원소 수는 MHA가 32,768개, GQA-8이 2,048개, MQA가 256개, MLA가 576개($512 + 64$)이다. MLA는 MQA보다 약간 크지만 MHA의 128개 헤드 전체의 고유한 K/V를 복원할 수 있으므로, 압축 효율 대비 표현력이 압도적으로 우수하다.

### DeepSeekMoE

DeepSeekMoE는 두 가지 전략을 결합하여 전통적 MoE의 한계를 극복한다. 다음 그림은 DeepSeekMoE의 전체 처리 흐름을 개략적으로 보여준다. 입력 토큰이 Self-Attention을 거친 후, Router(게이팅 네트워크)가 160개의 세분화된 전문가 중 Top-6을 동적으로 선택하고, 선택된 전문가의 가중 출력을 합산하여 최종 결과를 생성한다.

![DeepSeekMoE의 전체 처리 흐름과 라우팅 구조](figures/architecture.png)
*Figure 6: DeepSeekMoE 아키텍처 개요. 입력 토큰이 Self-Attention Layer를 거친 후 Router/Gating Network를 통해 Top-K 전문가가 선택되며, 선택된 전문가들의 가중합으로 출력이 생성된다. 236B 총 파라미터 중 토큰당 21B만 활성화하는 희소 구조의 핵심 원리를 보여준다. (DeepSeek AI, 2024)*

**세분화된 전문가(Fine-grained Experts)**: 전통적 MoE가 $N$개의 전문가에서 $K$개를 활성화한다면, DeepSeekMoE는 전문가의 FFN 차원을 $1/m$로 줄이고 전문가 수를 $m$배 늘려 $mN$개의 더 작은 전문가에서 $mK$개를 활성화한다. 이를 통해 동일한 활성화 파라미터 수를 유지하면서 전문가 조합의 가짓수가 $\binom{mN}{mK}$로 기하급수적으로 증가하여, 더 정밀한 지식 분할과 유연한 전문가 조합이 가능해진다.

**공유 전문가(Shared Experts)**: 일부 전문가를 항상 활성화되는 공유 전문가로 지정하여 범용적이고 공통적인 지식(예: 기본 문법, 일반 상식, 토큰 임베딩 보정)을 담당하게 하고, 나머지 라우팅 전문가들은 특수화된 도메인 지식에 집중한다. 이 설계는 전문가 간 지식 중복(redundancy)을 크게 줄이고, 라우팅 전문가가 범용 지식까지 학습해야 하는 부담을 제거한다.

전체 FFN 출력은 다음과 같이 공유 전문가 출력과 라우팅 전문가 출력의 합으로 구성된다:

$$h_t' = \sum_{i=1}^{K_s} \text{FFN}_i^{(s)}(h_t) + \sum_{i=1}^{N_r} g_{i,t} \cdot \text{FFN}_i^{(r)}(h_t)$$

여기서 $K_s$는 공유 전문가 수, $N_r$은 라우팅 전문가 수이며, 게이팅 점수 $g_{i,t}$는 소프트맥스 기반의 Top-K 선택으로 계산된다:

$$g_{i,t} = \frac{e^{s_{i,t}}}{\sum_{j \in \text{TopK}} e^{s_{j,t}}}, \quad s_{i,t} = \text{softmax}_i(W_g h_t)$$

선택되지 않은 전문가의 게이팅 점수는 0으로 설정되므로, 토큰당 실제로 계산을 수행하는 전문가는 $K_s + K_r = 2 + 6 = 8$개에 불과하다.

#### 장치 제한 라우팅 (Device-Limited Routing)

DeepSeek-V2는 전문가 병렬화(Expert Parallelism) 환경에서의 통신 오버헤드를 줄이기 위해 장치 제한 라우팅 메커니즘을 도입한다. 160개의 라우팅 전문가가 여러 GPU에 분산 배치될 때, 각 토큰이 모든 장치의 전문가에 접근하면 all-to-all 통신 비용이 과도해진다. 이를 방지하기 위해 먼저 각 장치에 배치된 전문가 그룹별로 점수를 합산하여 상위 장치를 선택하고, 선택된 장치 내에서만 Top-K 전문가를 활성화한다. 이를 통해 장치 간 통신량을 크게 줄이면서도 전문가 선택의 다양성을 유지할 수 있다.

#### 부하 균형 손실

전문가 활용의 균형을 위해 보조 손실(auxiliary loss)을 추가하여 전문가 활용이 고르게 분포되도록 강제한다:

$$\mathcal{L}_{balance} = \alpha \cdot N_r \cdot \sum_{i=1}^{N_r} f_i \cdot P_i$$

여기서 $f_i$는 전문가 $i$에 라우팅된 토큰 비율, $P_i$는 소프트 라우팅 확률의 평균이다. 이 손실은 특정 전문가에 토큰이 집중되는 것을 방지하며, 균형 계수 $\alpha$를 통해 메인 언어 모델링 손실과의 가중치를 조절한다.

## 방법론

아래 그림은 DeepSeek-V2의 전체 아키텍처를 보여준다. 왼쪽의 Transformer Block 구조에서 어텐션 레이어가 MLA로, FFN 레이어가 DeepSeekMoE로 대체된 것을 확인할 수 있다. MLA(하단)는 입력 히든 벡터 $h_t$로부터 잠재 벡터 $c_t^Q$와 $c_t^{KV}$를 생성하고, RoPE가 적용되는 위치 전용 벡터를 분리하여 처리한다. DeepSeekMoE(상단)는 공유 전문가와 라우터에 의해 선택된 라우팅 전문가의 출력을 합산하여 최종 히든 상태를 생성한다.

![DeepSeek-V2 전체 아키텍처 구성도](figures/fig_4.png)
*Figure 2: DeepSeek-V2 아키텍처 전체 구성도. 왼쪽은 Transformer Block의 전체 흐름이고, 오른쪽 상단은 DeepSeekMoE(공유 전문가 + Top-$K_r$ 라우팅 전문가), 오른쪽 하단은 MLA(잠재 벡터 기반 KV 압축 + 디커플링된 RoPE)의 상세 구조를 나타낸다. 추론 시 캐시되는 요소는 빗금으로 표시되어 있다.*

### 전체 아키텍처 구성

| 구성 요소 | 설정값 |
|---|---|
| 총 파라미터 | 236B |
| 활성화 파라미터 | 21B |
| 히든 차원 ($d_{model}$) | 5,120 |
| Transformer 레이어 | 60 |
| 어텐션 헤드 수 ($n_h$) | 128 |
| 헤드 차원 ($d_h$) | 128 |
| KV 압축 차원 ($d_c$) | 512 |
| Q 압축 차원 ($d_c'$) | 1,536 |
| RoPE 키 차원 ($d_h^R$) | 64 |
| 라우팅 전문가 수 ($N_r$) | 160 |
| 공유 전문가 수 ($K_s$) | 2 |
| 활성화 라우팅 전문가 수 ($K_r$) | 6 |
| 전문가 FFN 중간 차원 | 1,536 |
| 최대 시퀀스 길이 | 128K |
| 훈련 토큰 수 | 8.1T |
| 어휘 크기 | 100K |

60개 Transformer 레이어 중 처음 1개 레이어는 Dense FFN을 사용하고, 나머지 59개 레이어에서 MoE FFN을 적용한다. 이는 초기 레이어에서 충분한 공통 표현을 학습시킨 후 전문화된 라우팅을 시작하기 위한 설계이다.

### 훈련 파이프라인

#### 사전훈련

훈련 데이터는 8.1T 토큰의 다국어 코퍼스(영어, 중국어 중심)를 사용했다. 학습률은 코사인 스케줄러로 최대 $2.4 \times 10^{-4}$까지 워밍업한 후 서서히 감소시켰다. 컨텍스트 길이는 초기 4K에서 시작하여 단계적으로 확장했으며, 최종적으로 YaRN(Yet another RoPE extensioN) 기법을 적용하여 128K까지 확장했다. YaRN은 RoPE의 주파수 기저를 조정하여 훈련 시 사용한 시퀀스 길이보다 더 긴 컨텍스트에서도 위치 인코딩이 적절하게 작동하도록 하는 기법이다.

#### 정렬 (Alignment)

사전훈련 후 두 단계의 정렬 과정을 거친다:

1. **SFT(Supervised Fine-Tuning)**: 1.5M개의 고품질 대화 데이터로 지도 학습을 수행한다. 데이터는 수학, 코딩, 작문, 질의응답 등 다양한 도메인을 포괄하며, 응답 품질을 엄격하게 필터링했다.

2. **GRPO(Group Relative Policy Optimization)**: PPO의 변형으로, 별도의 critic(가치 함수) 모델 없이 강화학습을 수행한다. 각 프롬프트에 대해 그룹 크기 $G$개의 응답을 샘플링한 후, 그룹 내 보상의 상대적 순위를 기반으로 정책을 최적화한다:

$$\mathcal{L}_{GRPO} = -\mathbb{E}_{q, \{o_i\}_{i=1}^G} \left[ \frac{1}{G} \sum_{i=1}^{G} \min\left( r_i \hat{A}_i, \text{clip}(r_i, 1-\epsilon, 1+\epsilon) \hat{A}_i \right) \right]$$

여기서 $r_i = \frac{\pi_\theta(o_i|q)}{\pi_{\text{ref}}(o_i|q)}$는 확률 비율이고, $\hat{A}_i = \frac{R_i - \text{mean}(\{R_j\})}{\text{std}(\{R_j\})}$는 그룹 내 정규화된 어드밴티지이다. GRPO는 critic 모델이 불필요하여 PPO 대비 메모리 효율이 약 50% 높으며, 이후 DeepSeek-R1에서도 핵심 강화학습 알고리즘으로 채택되었다.

이를 통해 DeepSeek-V2-Chat 버전을 제공한다.

## 실험 결과

### 주요 벤치마크 (Base 모델)

| 벤치마크 | DeepSeek 67B | DeepSeek-V2 (21B activated) | Llama3 70B | Mixtral 8x22B |
|---|---|---|---|---|
| MMLU | 71.3 | **78.5** | 79.5 | 77.8 |
| HumanEval | 45.1 | **48.8** | 81.7 | 46.3 |
| MATH | 18.7 | **43.6** | 30.0 | 41.8 |
| GSM8K | 63.4 | **79.2** | 83.0 | 78.6 |
| BBH | 68.7 | **78.9** | 81.0 | 78.9 |
| C-Eval | 66.1 | **81.7** | 67.7 | 58.6 |
| CMATH | 63.8 | **84.3** | 72.3 | 67.9 |

DeepSeek-V2는 파라미터 대비 활성화 비율이 매우 낮음에도(21B/236B = 8.9%) 불구하고 DeepSeek 67B를 전반적으로 능가한다. 특히 수학(MATH: 43.6% vs 18.7%, +133% 향상)과 중국어(C-Eval: 81.7% vs 66.1%, +23.6% 향상) 벤치마크에서 압도적 향상을 보인다. Llama3 70B와 비교해도 중국어 벤치마크에서 크게 앞서며, 수학 성능에서도 우위를 보인다. Mixtral 8x22B와는 대부분의 벤치마크에서 동등하거나 우수한 성능을 달성하면서, 활성화 파라미터 수는 절반 이하이다.

### DeepSeek-V2-Chat 성능

| 벤치마크 | GPT-4-0613 | DeepSeek-V2-Chat | Llama3-70B-Chat |
|---|---|---|---|
| MMLU | 86.4 | 78.4 | 82.0 |
| MATH | 52.6 | 52.7 | 46.9 |
| HumanEval | 84.1 | 81.1 | 81.7 |
| LiveCodeBench | 33.4 | 18.8 | 14.2 |
| C-Eval | 69.9 | 78.0 | 55.4 |

Chat 모델도 MATH에서 GPT-4-0613과 동등한 성능(52.7% vs 52.6%)을 보이며, 중국어 벤치마크(C-Eval)에서는 GPT-4를 +11.6% 크게 능가한다. 다음 그림은 코딩 벤치마크에서의 DeepSeek-V2-Chat의 위치를 보다 직관적으로 보여준다.

![HumanEval과 LiveCodeBench 코딩 벤치마크 결과 산점도](figures/fig_7.png)
*Figure 5: HumanEval(Pass@1)과 LiveCodeBench(Pass@1) 코딩 벤치마크 결과. DeepSeek-V2-Chat(SFT)은 오픈소스 모델 중 최상위권에 위치하며, LiveCodeBench에서 Llama3-70B-Chat을 크게 상회한다. GPT-4-Turbo 및 Claude 3 Opus 등 프로프라이어터리 모델과도 비교적 좁은 격차를 보인다.*

### 아키텍처 Ablation 결과

논문에서는 MLA와 DeepSeekMoE의 효과를 검증하기 위한 ablation 실험도 수행했다.

| 어텐션 메커니즘 | KV 캐시/토큰 | 성능 (평균) |
|---|---|---|
| MHA (기준) | 32,768 | 기준 |
| MQA | 256 | -1.2% |
| GQA-8 | 2,048 | -0.6% |
| MLA (제안) | 576 | **+0.1%** |

MLA는 MHA보다 오히려 약간 더 나은 성능을 보이면서도 KV 캐시를 98.2% 절감한다. 이는 잠재 공간 압축이 일종의 정규화(regularization) 효과를 제공하기 때문으로 해석된다. GQA-8은 MHA 대비 캐시를 93.8% 절감하지만 성능이 0.6% 하락하는 반면, MLA는 더 큰 캐시 절감과 동시에 성능 유지/향상을 달성한다.

### 경제성 및 효율성 비교

다음 그림은 DeepSeek 67B(Dense)와 DeepSeek-V2 사이의 훈련 비용, KV 캐시, 추론 처리량 차이를 정량적으로 비교한다. MLA와 DeepSeekMoE의 결합이 세 지표 모두에서 어떤 수준의 개선을 가져오는지 명확히 확인할 수 있다.

![DeepSeek 67B 대비 DeepSeek-V2의 훈련 비용, KV 캐시, 생성 처리량 비교](figures/fig_1_2.png)
*Figure 1(b): DeepSeek 67B(Dense) 대비 DeepSeek-V2의 정량 비교. 훈련 비용은 42.5% 절감(180.0 vs 104.9 K GPU Hours/T Tokens), KV 캐시는 93.3% 절감(93.75 vs 6.25 KB/Token), 최대 생성 처리량은 5.76배 향상(28.5 vs 164.2 Tokens/Sec)을 달성한다.*

| 모델 | 활성화 파라미터 | 훈련 비용 | KV 캐시 크기 | 생성 처리량 |
|---|---|---|---|---|
| DeepSeek 67B | 67B | 기준 (1.0x) | 기준 (1.0x) | 기준 (1.0x) |
| DeepSeek-V2 | 21B | 0.575x | 0.067x | 5.76x |

추론 시 구체적인 수치:
- **프리필(Prefill) 처리량**: 6.54배 향상 -- 입력 인코딩 단계에서의 속도 향상
- **생성(Generation) 처리량**: 5.76배 향상 -- 자기회귀 디코딩 단계에서의 속도 향상
- **KV 캐시**: 93.3% 절감 (128K 컨텍스트에서도 실용적 배포 가능)
- **훈련 비용**: 42.5% 절감 (8.1T 토큰 기준)

이는 API 서비스 비용 측면에서도 큰 의미를 가지며, DeepSeek AI는 실제로 DeepSeek-V2 기반 API를 업계 최저가($0.14/M input tokens, $0.28/M output tokens)로 제공했다. 이 가격은 당시 GPT-4 Turbo의 약 1/100 수준으로, AI 서비스 접근성에 큰 변화를 가져왔다.

## 의의 및 한계

### 의의

**MoE 실용화의 전환점**: DeepSeek-V2는 MoE 모델이 Dense 모델과 동등하거나 우수한 성능을 훨씬 낮은 비용으로 달성할 수 있음을 대규모 실험으로 입증했다. 이는 이후 Mixtral, Qwen-MoE, DBRX 등 MoE 모델 개발의 가속화에 기여했다.

**MLA의 기술적 기여**: MLA는 KV 캐시 문제를 GQA/MQA와는 완전히 다른 접근법으로 해결했으며, 표현력 손실 없이 메모리를 절감한다는 점에서 혁신적이다. 이후 DeepSeek-V3, DeepSeek-R1 등 후속 모델들의 표준 어텐션 메커니즘으로 채택되었으며, 다른 연구 그룹에서도 MLA에 기반한 변형을 연구하고 있다.

**128K 컨텍스트 실용화**: MLA의 극도로 작은 KV 캐시 덕분에 128K 토큰 컨텍스트를 실질적으로 배포 가능한 수준의 메모리로 처리할 수 있게 되었다. 기존 MHA로는 128K 컨텍스트를 위해 수백 GB의 KV 캐시가 필요했으나, MLA는 이를 수 GB 수준으로 줄여 상용 서비스에서의 긴 컨텍스트 지원을 실현했다.

**오픈소스 생태계 기여**: 모델 가중치를 완전 공개하여 오픈소스 LLM 커뮤니티에 기여했으며, API 가격을 업계 최저 수준으로 설정하여 AI 접근성 민주화에 기여했다.

**DeepSeek 시리즈의 기반**: DeepSeek-V2에서 도입된 MLA와 DeepSeekMoE는 이후 DeepSeek-V3(671B 파라미터, 37B 활성화)와 DeepSeek-R1(추론 특화 모델)의 핵심 아키텍처로 계승되었다. 특히 DeepSeek-V3에서는 보조 손실 없는 부하 균형(Auxiliary-Loss-Free Load Balancing)과 Multi-Token Prediction이 추가로 도입되었으며, 이 모든 혁신의 시작점이 DeepSeek-V2이다.

### 한계

**배포 인프라 요구사항**: MoE 모델 특성상 전체 236B 파라미터를 메모리에 올려야 하므로, 전문가 병렬화를 위한 다수의 GPU가 필요하다. 소규모 배포 환경에서의 접근성이 제한된다.

**전문가 설계의 경험적 결정**: 공유 전문가와 라우팅 전문가 사이의 최적 비율($K_s = 2$, $K_r = 6$), 세분화 계수($m$) 등이 여전히 경험적으로 결정된다. 이론적 최적값에 대한 분석이 부족하다.

**보조 손실의 성능 간섭**: 부하 균형을 위한 보조 손실($\mathcal{L}_{balance}$)이 메인 언어 모델링 손실과 상충할 수 있다. 균형 계수 $\alpha$가 너무 크면 라우팅의 유연성이 저하되고, 너무 작으면 전문가 활용 불균형이 발생한다. 이 문제는 후속 DeepSeek-V3에서 보조 손실 없는(Auxiliary-Loss-Free) 부하 균형 전략으로 해결되었다.

**전문가 전문화의 불투명성**: 각 전문가가 어떤 유형의 입력에 특화되는지에 대한 해석가능성(interpretability)이 부족하며, 전문가 간 지식 분절 문제가 완전히 해결되지 않았다.

**MLA와 FlashAttention 호환성**: MLA의 압축-복원 구조는 기존 FlashAttention 커널과 직접적으로 호환되지 않아, 최적의 추론 성능을 위해 별도의 커스텀 커널 구현이 필요하다. 이는 MLA 채택의 엔지니어링 장벽으로 작용할 수 있다.

## 코드 예제

### MLA (Multi-head Latent Attention) 핵심 구현 (PyTorch)

```python
import torch
import torch.nn as nn
import math

class MultiHeadLatentAttention(nn.Module):
    """DeepSeek-V2의 MLA: KV를 저차원 잠재 벡터로 압축.
    표준 MHA 대비 KV 캐시를 93% 줄이면서 풀 어텐션 표현력 유지.
    """
    def __init__(self, d_model=5120, num_heads=128, kv_lora_rank=512,
                 q_lora_rank=1536, head_dim=128, rope_head_dim=64):
        super().__init__()
        self.num_heads = num_heads
        self.head_dim = head_dim
        self.rope_head_dim = rope_head_dim
        self.kv_lora_rank = kv_lora_rank

        # KV 다운-업 프로젝션 (핵심: 압축 -> 캐시 -> 복원)
        self.kv_down = nn.Linear(d_model, kv_lora_rank, bias=False)   # 압축: d_model -> kv_lora_rank
        self.kv_norm = nn.RMSNorm(kv_lora_rank)  # 잠재 벡터 정규화
        self.k_up = nn.Linear(kv_lora_rank, num_heads * head_dim, bias=False)   # K 복원
        self.v_up = nn.Linear(kv_lora_rank, num_heads * head_dim, bias=False)   # V 복원

        # Q 다운-업 프로젝션 (활성화 메모리 절감용)
        self.q_down = nn.Linear(d_model, q_lora_rank, bias=False)
        self.q_norm = nn.RMSNorm(q_lora_rank)
        self.q_up = nn.Linear(q_lora_rank, num_heads * head_dim, bias=False)

        # RoPE용 분리 키/쿼리 (decoupled RoPE)
        self.k_rope = nn.Linear(d_model, rope_head_dim, bias=False)
        self.q_rope = nn.Linear(q_lora_rank, num_heads * rope_head_dim, bias=False)

        self.out_proj = nn.Linear(num_heads * head_dim, d_model, bias=False)

    def forward(self, x, past_kv=None):
        B, T, _ = x.shape

        # ========== KV 압축 (캐시에 c_kv와 k_rope만 저장!) ==========
        c_kv = self.kv_norm(self.kv_down(x))  # (B, T, kv_lora_rank)
        k_rope_vec = self.k_rope(x)           # (B, T, rope_head_dim)

        # 추론 시: 캐시 업데이트 (c_kv + k_rope만 저장)
        if past_kv is not None:
            past_c_kv, past_k_rope = past_kv
            c_kv = torch.cat([past_c_kv, c_kv], dim=1)
            k_rope_vec = torch.cat([past_k_rope, k_rope_vec], dim=1)
        current_kv = (c_kv, k_rope_vec)  # 캐시할 값

        # K, V 복원 (어텐션 계산 시에만 up-projection)
        S = c_kv.shape[1]  # 전체 시퀀스 길이 (캐시 포함)
        K_content = self.k_up(c_kv).view(B, S, self.num_heads, self.head_dim)
        V = self.v_up(c_kv).view(B, S, self.num_heads, self.head_dim)

        # ========== Q 계산 ==========
        c_q = self.q_norm(self.q_down(x))
        Q_content = self.q_up(c_q).view(B, T, self.num_heads, self.head_dim)

        # ========== RoPE 디커플링 ==========
        # 위치 정보는 별도의 작은 벡터에 인코딩 (압축과 분리)
        k_rope_expanded = k_rope_vec.unsqueeze(2).expand(-1, -1, self.num_heads, -1)
        q_rope_vec = self.q_rope(c_q).view(B, T, self.num_heads, self.rope_head_dim)
        # 실제로는 여기에 RoPE 회전 변환 적용

        # Q, K에 위치 벡터를 연결 (concatenate)
        Q = torch.cat([Q_content, q_rope_vec], dim=-1)     # (B, T, H, d_h + d_h^R)
        K = torch.cat([K_content, k_rope_expanded], dim=-1) # (B, S, H, d_h + d_h^R)

        # ========== Attention 계산 ==========
        scale = math.sqrt(self.head_dim + self.rope_head_dim)
        Q, K, V = [t.transpose(1, 2) for t in (Q, K, V)]  # (B, H, T/S, D)
        scores = torch.matmul(Q, K.transpose(-2, -1)) / scale

        # Causal mask
        mask = torch.tril(torch.ones(T, S, device=x.device), diagonal=S - T)
        scores = scores.masked_fill(mask.unsqueeze(0).unsqueeze(0) == 0, float('-inf'))

        attn = torch.softmax(scores, dim=-1)
        out = torch.matmul(attn, V).transpose(1, 2).contiguous().view(B, T, -1)
        return self.out_proj(out), current_kv


class DeepSeekMoELayer(nn.Module):
    """DeepSeekMoE: 공유 전문가 + 세분화된 라우팅 전문가."""
    def __init__(self, d_model=5120, num_shared=2, num_routed=160,
                 num_activated=6, expert_dim=1536):
        super().__init__()
        self.num_shared = num_shared
        self.num_routed = num_routed
        self.num_activated = num_activated

        # 공유 전문가: 항상 활성화 (범용 지식 담당)
        self.shared_experts = nn.ModuleList([
            nn.Sequential(
                nn.Linear(d_model, expert_dim),
                nn.SiLU(),
                nn.Linear(expert_dim, d_model)
            ) for _ in range(num_shared)
        ])

        # 라우팅 전문가: Top-K 선택 (특수 지식 담당)
        self.routed_experts = nn.ModuleList([
            nn.Sequential(
                nn.Linear(d_model, expert_dim),
                nn.SiLU(),
                nn.Linear(expert_dim, d_model)
            ) for _ in range(num_routed)
        ])

        # 게이팅 네트워크 (라우터)
        self.gate = nn.Linear(d_model, num_routed, bias=False)

    def forward(self, x):
        B, T, D = x.shape

        # 공유 전문가 출력 (항상 실행)
        shared_out = sum(expert(x) for expert in self.shared_experts)

        # 라우팅: Top-K 전문가 선택
        gate_logits = self.gate(x)  # (B, T, num_routed)
        topk_values, topk_indices = torch.topk(
            gate_logits, self.num_activated, dim=-1
        )
        gate_scores = torch.softmax(topk_values, dim=-1)  # (B, T, K)

        # 선택된 전문가의 가중합
        routed_out = torch.zeros_like(x)
        for k in range(self.num_activated):
            expert_idx = topk_indices[:, :, k]  # (B, T)
            weight = gate_scores[:, :, k:k+1]   # (B, T, 1)
            for i in range(self.num_routed):
                mask = (expert_idx == i)
                if mask.any():
                    expert_input = x[mask]
                    routed_out[mask] += weight[mask] * self.routed_experts[i](expert_input)

        return shared_out + routed_out

    def load_balance_loss(self, gate_logits, topk_indices):
        """부하 균형 보조 손실 계산."""
        # f_i: 전문가 i에 라우팅된 토큰 비율
        num_tokens = gate_logits.shape[0] * gate_logits.shape[1]
        f = torch.zeros(self.num_routed, device=gate_logits.device)
        for i in range(self.num_routed):
            f[i] = (topk_indices == i).float().sum() / num_tokens

        # P_i: 전문가 i의 평균 라우팅 확률
        probs = torch.softmax(gate_logits, dim=-1)  # (B, T, N_r)
        P = probs.mean(dim=[0, 1])  # (N_r,)

        return self.num_routed * (f * P).sum()


# ========== KV 캐시 크기 비교 ==========
d_model, num_heads, head_dim = 5120, 128, 128
kv_lora_rank = 512
rope_head_dim = 64

mha_kv_per_token = num_heads * head_dim * 2   # K + V
mla_kv_per_token = kv_lora_rank + rope_head_dim  # c_kv + k_rope

print(f"MHA KV 캐시/토큰/레이어: {mha_kv_per_token:,} elements")
print(f"MLA KV 캐시/토큰/레이어: {mla_kv_per_token:,} elements")
print(f"절감률: {(1 - mla_kv_per_token / mha_kv_per_token) * 100:.1f}%")
# MHA: 32,768 elements -> MLA: 576 elements -> 98.2% 절감

# 128K 컨텍스트, 60 레이어 기준 (FP16)
seq_len = 128_000
num_layers = 60
mha_total = mha_kv_per_token * seq_len * num_layers * 2  # bytes (FP16)
mla_total = mla_kv_per_token * seq_len * num_layers * 2
print(f"\n128K 컨텍스트 KV 캐시:")
print(f"  MHA: {mha_total / 1024**3:.1f} GB")
print(f"  MLA: {mla_total / 1024**3:.1f} GB")
```

## 관련 문서

- [[deepseek-v3|DeepSeek-V3 Technical Report]] -- 후속 모델 (671B, Auxiliary-Loss-Free Load Balancing)
- [[deepseek-r1|DeepSeek-R1]] -- 추론 특화 후속 모델 (GRPO 기반 강화학습)
- [[deepseek-vl2|DeepSeek-VL2]] -- 멀티모달 후속 모델
- [[mixtral|Mixtral of Experts]] -- MoE 아키텍처 선행 연구