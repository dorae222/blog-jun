## 개요

대규모 언어 모델(LLM)의 자기회귀 추론에서 가장 큰 병목은 **KV 캐시(Key-Value Cache)**의 메모리 대역폭 소비입니다. 시퀀스 길이와 배치 크기가 커질수록 KV 캐시를 HBM에서 반복 로드하는 비용이 급증하여, 실제 연산 시간보다 메모리 접근 시간이 추론 속도를 지배하게 됩니다. 이 문제에 대해 MQA(Multi-Query Attention)가 KV 헤드를 하나로 줄이는 급진적 해법을 제시했지만, 표현력 손실이 뒤따랐습니다.

**GQA(Grouped-Query Attention)**는 MHA와 MQA의 중간 지점에서 최적의 품질-효율 균형을 찾는 어텐션 메커니즘입니다. $H$개의 쿼리 헤드를 $G$개의 그룹으로 나누어 각 그룹이 하나의 KV 헤드를 공유함으로써, KV 캐시를 $G/H$ 비율로 줄이면서도 MHA에 근접한 품질을 유지합니다. 또한 기존 MHA 체크포인트를 원본 학습의 **5%** 스텝만으로 GQA로 변환하는 업트레이닝(uptraining) 방법을 함께 제안하여, 이미 학습된 대형 모델의 재활용 경로를 열었습니다.

다음 그림은 MHA, MQA, GQA 세 가지 어텐션 메커니즘의 구조적 차이를 한눈에 보여줍니다.

![MHA, MQA, GQA 세 가지 어텐션 구조 비교 개요](figures/architecture.png)
*MHA는 각 쿼리 헤드가 독립적인 KV 헤드를 보유하고, MQA는 전체 쿼리가 단일 KV를 공유하며, GQA는 쿼리 그룹 단위로 KV를 공유하여 품질과 효율의 균형을 달성한다.*

2023년 5월 Google Research에서 발표된 이 논문은 불과 2개월 후 Meta의 LLaMA 2(2023년 7월)에 채택되면서 산업 표준으로 급부상했으며, 이후 Mistral-7B, LLaMA 3, Gemma, Qwen 등 사실상 모든 최신 LLM의 기본 어텐션 구조로 자리잡았습니다.

## 배경 및 문제

### 자기회귀 추론의 메모리 대역폭 병목

LLM의 자기회귀 생성은 한 번에 하나의 토큰을 생성하며, 각 토큰 생성 시 이전 모든 토큰의 Key와 Value를 KV 캐시에서 로드해야 합니다. 이때 토큰당 KV 로드량은 다음과 같이 산출됩니다:

$$\text{토큰당 KV 로드량} = 2 \times N_L \times H \times d_k \times L \times \text{sizeof(dtype)}$$

여기서 $N_L$은 레이어 수, $H$는 KV 헤드 수, $d_k$는 헤드 차원, $L$은 시퀀스 길이입니다. 예를 들어 LLaMA-65B(MHA, $H=64$, $d_k=128$, $N_L=80$)에서 시퀀스 길이 4096 기준 토큰당 KV 로드량은:

$$2 \times 80 \times 64 \times 128 \times 4096 \times 2 \approx 10.7 \text{ GB}$$

A100 GPU의 HBM 대역폭이 2 TB/s이므로, KV 캐시 로딩만으로 토큰당 약 5.4ms가 소요됩니다. 이는 실제 행렬 곱 연산 시간보다 훨씬 크며, 128K 컨텍스트 윈도우를 사용하는 최신 모델에서는 KV 캐시가 수십 GB에 달하여 단일 GPU 메모리 용량을 초과하기도 합니다.

### Prefill vs Decode: 비대칭적 병목

트랜스포머 추론은 두 단계로 구분됩니다:

- **Prefill 단계**: 입력 프롬프트의 모든 토큰을 병렬 처리하므로 GPU 연산 유닛이 충분히 활용되어 **compute-bound** 작업
- **Decode 단계**: 토큰을 하나씩 생성하면서 KV 캐시 전체를 매번 읽어야 하므로 **memory bandwidth-bound** 작업

이 비대칭성이 GQA의 핵심 동기입니다. Decode 단계에서 KV 캐시의 메모리 접근량을 줄이면 추론 속도가 직접적으로 향상되며, GQA는 바로 이 지점을 공략합니다.

### 기존 어텐션 메커니즘의 한계

**MHA(Multi-Head Attention)**는 $H$개의 헤드가 각각 독립적인 $Q_i, K_i, V_i$ 프로젝션을 갖습니다:

$$\text{head}_i = \text{softmax}\left(\frac{Q_i K_i^T}{\sqrt{d_k}}\right)V_i, \quad \text{MHA} = \text{Concat}(\text{head}_1, \ldots, \text{head}_H) W^O$$

표현력은 최대이지만 KV 캐시가 $H$에 비례하여 커지므로, 추론 시 메모리 대역폭 부담이 큽니다.

**MQA(Multi-Query Attention)**는 Shazeer(2019)가 제안한 방식으로, 모든 쿼리 헤드가 **단 하나의** KV 헤드를 공유합니다:

$$\text{head}_i = \text{Attention}(Q_i, K_{\text{shared}}, V_{\text{shared}})$$

KV 캐시가 $H$배 감소하여 추론 효율이 크게 향상되지만, 모든 쿼리가 동일한 KV 공간에서 정보를 추출해야 하므로 **표현력이 크게 제한**됩니다. 특히 30B 이상의 대형 모델에서 MHA 대비 눈에 띄는 품질 저하가 관찰되며, 기존 MHA 체크포인트에서 MQA로 전환하려면 수조 토큰에 대한 사전학습을 처음부터 반복해야 하는 비현실적인 비용이 발생합니다.

| 속성 | MHA | MQA |
|------|-----|-----|
| KV 헤드 수 | $H$ (전체) | 1 (공유) |
| KV 캐시 크기 | 기준 (100%) | $1/H$ (~3%) |
| 표현력 | 최대 | 제한적 |
| 추론 속도 | 느림 | 빠름 |
| 기존 모델 변환 | - | 처음부터 재학습 필요 |

이처럼 MHA와 MQA 사이에는 명확한 트레이드오프가 존재하며, **이 두 극단 사이의 최적 균형점**을 찾는 것이 GQA의 핵심 목표입니다.

## 핵심 아이디어: Grouped-Query Attention

### 구조

GQA는 $H$개의 쿼리 헤드를 $G$개의 그룹으로 나누고, 각 그룹 내 $H/G$개의 쿼리 헤드들이 하나의 KV 헤드를 공유합니다. 아래 그림은 논문에서 제시한 세 메커니즘의 구조적 차이를 보여줍니다.

![MHA, GQA, MQA 어텐션 구조의 쿼리-키-값 헤드 대응 관계](figures/fig_2.png)
*MHA는 각 쿼리에 독립적인 KV가 대응하고, MQA는 모든 쿼리가 하나의 KV를 공유하며, GQA는 쿼리 그룹 단위로 KV를 공유하여 두 방식 사이를 보간한다 (Ainslie et al., 2023).*

수식으로 표현하면:

$$\text{head}_i = \text{softmax}\left(\frac{Q_i K_{g(i)}^T}{\sqrt{d_k}}\right) V_{g(i)}, \quad g(i) = \left\lfloor \frac{i \cdot G}{H} \right\rfloor$$

여기서 $g(i)$는 쿼리 헤드 $i$가 속한 그룹 인덱스이며, 최종 출력은 $\text{Output} = \text{Concat}(\text{head}_1, \ldots, \text{head}_H) W^O$입니다.

GQA는 $G$ 값을 통해 MHA-MQA 스펙트럼 전체를 아우르는 일반화된 프레임워크를 제공합니다:

- $G = H$: **MHA**와 동일 (각 쿼리가 독립 KV 보유)
- $G = 1$: **MQA**와 동일 (전체 쿼리가 단일 KV 공유)
- $1 < G < H$: **GQA** (그룹 단위 KV 공유, 품질-효율 균형)

### KV 캐시 절감 효과

KV 캐시 크기는 $G$에 비례합니다:

$$\text{KV 캐시} = 2 \times N_L \times G \times d_k \times L$$

$H=32$, $G=8$이면 KV 캐시가 MHA 대비 **25%**로 줄어듭니다. 그룹 수에 따른 구체적인 비교는 다음과 같습니다:

| 설정 | KV 헤드 수 | KV 캐시 비율 | 그룹당 쿼리 수 |
|------|-----------|------------|-------------|
| MHA ($G=H=32$) | 32 | 100% | 1 (독립) |
| GQA-8 ($G=8$) | 8 | 25% | 4 |
| GQA-4 ($G=4$) | 4 | 12.5% | 8 |
| MQA ($G=1$) | 1 | 3.1% | 32 |

GQA-8의 경우, 4개의 쿼리 헤드가 하나의 KV 헤드를 공유합니다. 실제 MHA 모델의 어텐션 패턴을 분석하면 인접한 헤드들이 유사한 어텐션 분포를 보이는 경우가 많으며, GQA는 이러한 **중복성(redundancy)**을 활용하여 표현력 손실을 최소화합니다.

### 파라미터 효율성

KV 프로젝션의 파라미터 수를 비교하면 GQA의 효율성이 명확합니다:

| 메커니즘 | KV 프로젝션 파라미터 | MHA 대비 |
|---------|-------------------|---------|
| MHA | $2 H d_k d_{\text{model}}$ | 100% |
| GQA-$G$ | $2 G d_k d_{\text{model}}$ | $G/H$ |
| MQA | $2 d_k d_{\text{model}}$ | $1/H$ |

예를 들어 LLaMA-2-70B($H=64$, $G=8$, $d_k=128$, $d_{\text{model}}=8192$)에서 KV 프로젝션 파라미터는 MHA 대비 12.5%로 감소하며, 이는 모델 전체 파라미터의 약 3%에 해당하는 절감입니다.

## 방법론: 업트레이닝

### MHA에서 GQA로의 변환

GQA의 핵심 실용적 기여는 기존 MHA 체크포인트를 GQA로 효율적으로 변환하는 **업트레이닝(uptraining)** 방법입니다. 수조 토큰에 대한 사전학습을 처음부터 반복하지 않고도 GQA의 이점을 얻을 수 있다는 점에서, 이미 학습된 대형 모델을 재활용하는 실용적 경로를 제시합니다.

아래 그림은 업트레이닝의 첫 단계인 KV 헤드 변환 과정을 보여줍니다.

![MHA의 KV 헤드를 평균 풀링으로 변환하는 업트레이닝 초기화](figures/fig_1.png)
*MHA의 H개 Key Projection 헤드를 그룹별로 평균 풀링(Mean Pool)하여 GQA의 G개 KV 헤드로 압축하는 업트레이닝 초기화 과정. Value Projection에도 동일한 방법이 적용된다 (Ainslie et al., 2023).*

**변환 절차:**

1. **KV 헤드 그룹핑**: 기존 MHA의 $H$개 KV 헤드를 $G$개 그룹으로 분할
2. **평균 풀링 초기화**: 각 그룹 내 KV 헤드들을 평균하여 하나의 대표 헤드 생성

$$K_g^{\text{GQA}} = \frac{1}{|S_g|} \sum_{i \in S_g} K_i^{\text{MHA}}, \quad V_g^{\text{GQA}} = \frac{1}{|S_g|} \sum_{i \in S_g} V_i^{\text{MHA}}$$

여기서 $S_g$는 그룹 $g$에 속하는 원래 헤드 인덱스의 집합입니다.

3. **업트레이닝**: 원본 학습의 **5%** 스텝만 추가 학습하여 변환 완료

### 초기화 전략 비교

논문에서는 KV 헤드 변환 시 세 가지 초기화 전략을 비교합니다:

- **평균 풀링(Mean Pooling)**: 그룹 내 헤드들의 가중치를 평균하여 초기화. 기존 지식을 최대한 보존하며, 가장 안정적인 업트레이닝 성능을 보임
- **랜덤 선택(Random Selection)**: 그룹 내 헤드 중 하나를 무작위로 선택. 평균 풀링 대비 약간 낮은 성능
- **랜덤 초기화(Random Initialization)**: KV 가중치를 처음부터 랜덤으로 설정. 수렴에 더 많은 스텝이 필요

평균 풀링이 최적인 이유는, 그룹 내 여러 헤드가 학습한 정보를 골고루 반영하여 업트레이닝 시작점의 품질을 최대화하기 때문입니다.

### 그룹 수 $G$ 선택 가이드라인

최적의 그룹 수는 모델 크기와 배포 환경에 따라 다르지만, 실용적 기준은 다음과 같습니다:

| 설정 | 적합한 환경 | 채택 사례 |
|------|-----------|---------|
| $G = 8$ | 대형 모델(30B+), 범용 서빙 | LLaMA 2/3, Mistral, Qwen |
| $G = 4$ | 메모리 제한 엣지, 초장문 컨텍스트 | 일부 특수 설정 |
| $G = 1$ (MQA) | 속도 최우선 소형 모델 | Gemma-7B |

그룹 수 선택에 영향을 미치는 핵심 요소는 **(1)** 모델 크기(대형일수록 헤드 간 중복성이 높아 적은 $G$에서도 품질 유지 가능), **(2)** 배치 크기(클수록 KV 캐시 절감 효과 증대), **(3)** 시퀀스 길이(길수록 KV 캐시 부담 증가로 GQA 이점 극대화), **(4)** 하드웨어 제약(GPU 메모리 용량, HBM 대역폭)입니다.

### 추론 속도 분석

자기회귀 생성에서 Decode 단계의 어텐션 연산은 메모리 접근량에 의해 속도가 결정됩니다:

$$\text{MHA 메모리 접근} = 2 H d_k L, \quad \text{GQA-}G\text{ 메모리 접근} = 2 G d_k L$$

따라서 어텐션이 병목인 경우 이론적 속도 향상 비율은 $H/G$에 비례합니다. 다만 FFN 등 다른 연산에 의해 실제 속도 향상은 이론적 상한보다 낮습니다.

GQA는 FlashAttention-2와 결합하면 더욱 효과적입니다. FlashAttention-2는 GQA의 KV 브로드캐스팅을 커널 레벨에서 네이티브로 지원하여, KV를 물리적으로 복제하지 않고 SRAM 타일링 내에서 효율적으로 처리합니다. 이 조합은 vLLM, TGI, SGLang 등 현재 대부분의 LLM 추론 프레임워크의 표준이 되었습니다.

## 실험 결과

### T5 기반 실험 (요약 태스크)

논문은 T5-XXL(11B) 모델을 기반으로 XSum, CNN/DailyMail 요약 태스크에서 체계적인 실험을 수행합니다.

| 모델 | XSum ROUGE-2 | CNN/DM ROUGE-2 | 추론 속도 |
|------|-------------|---------------|-------|
| T5-XXL (MHA) | 21.7 | 21.3 | 1.0x |
| T5-XXL (MQA 업트레이닝) | 21.2 | 20.9 | 2.8x |
| T5-XXL (GQA-8 업트레이닝) | **21.6** | **21.2** | 1.9x |

GQA-8은 MHA 대비 ROUGE-2 차이가 0.1 이내로, 품질을 거의 유지하면서 1.9배의 속도 향상을 달성합니다. MQA는 2.8배의 더 높은 속도를 보이지만 0.5 ROUGE 하락이 동반됩니다.

### 업트레이닝 효율성

| 방법 | 학습 비율 (원본 대비) | MHA 대비 품질 | 추론 속도 |
|------|---------------------|-------------|--------|
| MQA 처음부터 학습 | 100% | -0.5 ROUGE | 2.8x |
| MQA 업트레이닝 | **5%** | -0.5 ROUGE | 2.8x |
| GQA-8 업트레이닝 | **5%** | **-0.1 ROUGE** | 1.9x |

주목할 점은 MQA 업트레이닝(5%)과 MQA 처음부터 학습(100%)의 성능이 거의 동일하다는 것입니다. 이는 업트레이닝 자체가 처음부터의 재학습을 대체할 수 있는 충분히 효과적인 변환 방법임을 입증합니다.

### 그룹 수에 따른 품질-속도 트레이드오프

| 그룹 수 $G$ | KV 캐시 (MHA 대비) | 요약 품질 변화 | 추론 속도 |
|------------|------|---------|--------|
| 32 (MHA) | 100% | 기준 | 1.0x |
| 8 (GQA-8) | 25% | -0.1 | 1.9x |
| 4 (GQA-4) | 12.5% | -0.2 | 2.3x |
| 2 (GQA-2) | 6.25% | -0.3 | 2.6x |
| 1 (MQA) | 3.1% | -0.5 | 2.8x |

$G$를 줄일수록 속도는 향상되지만 품질 하락이 가속됩니다. $G=8 \to G=4$로 줄이면 속도는 0.4x 추가 향상되지만 품질 하락은 2배로 커져 효율이 떨어집니다. 이 결과는 $G=8$이 대부분의 실용적 시나리오에서 최적의 균형점임을 시사합니다.

### 프로덕션 환경에서의 메모리 효율

배치 크기 16, 시퀀스 길이 4096 기준 70B 모델의 KV 캐시 메모리 사용량을 비교하면:

| 어텐션 방식 | KV 캐시 크기 | 80GB GPU 기준 최대 동시 요청 |
|-----------|------------|-------------------------|
| MHA ($G=64$) | 40.0 GB | 1 |
| GQA-8 ($G=8$) | 5.0 GB | 8 |
| GQA-4 ($G=4$) | 2.5 GB | 16 |
| MQA ($G=1$) | 0.625 GB | 64 |

GQA-8은 MHA 대비 8배 더 많은 동시 요청을 처리할 수 있어, 프로덕션 서빙의 비용 효율에 직접적인 영향을 미칩니다.

### 실제 모델 채택 현황

GQA 발표 이후, 주요 LLM들이 빠르게 GQA를 채택했습니다:

| 모델 | 쿼리 헤드 ($H$) | KV 헤드 ($G$) | 출시일 |
|------|--------------|-------------|-------|
| LLaMA-2-70B | 64 | **8** | 2023.07 |
| Mistral-7B | 32 | **8** | 2023.09 |
| LLaMA-3-8B | 32 | **8** | 2024.04 |
| LLaMA-3-70B | 64 | **8** | 2024.04 |
| Gemma-7B | 16 | **1** (MQA) | 2024.02 |
| Qwen-2.5-72B | 64 | **8** | 2024.09 |
| DeepSeek-V2 | 128 | MLA (별도) | 2024.05 |

$G=8$이 사실상의 산업 표준으로, 소형 모델인 Gemma-7B만이 MQA($G=1$)를 선택했습니다.

## 의의 및 한계

### 의의

- **산업 표준 확립**: 발표 2개월 만에 LLaMA 2에 채택되어, 이후 사실상 모든 최신 LLM의 기본 어텐션 구조로 자리잡았습니다.
- **업트레이닝의 실용성**: 기존 MHA 체크포인트를 5% 추가 학습만으로 GQA로 변환할 수 있어, 수천 GPU 시간의 재학습 비용을 극적으로 절감합니다.
- **유연한 품질-효율 제어**: 그룹 수 $G$를 조절하여 엣지 디바이스부터 데이터센터까지 다양한 배포 환경에 맞춤 설정이 가능합니다.
- **구현 단순성**: MHA 대비 변경사항이 KV 프로젝션의 차원 축소뿐이므로, 기존 코드베이스에 최소한의 수정으로 적용 가능합니다.
- **FlashAttention 시너지**: FlashAttention-2와 네이티브 호환되어 추가적인 속도 향상을 얻습니다.

### 한계

- **그룹 내 표현력 제한**: 같은 그룹의 쿼리 헤드들이 KV를 공유하므로, 매우 세밀한 어텐션 패턴이 필요한 태스크에서 MHA 대비 품질 손실이 발생할 수 있습니다.
- **최적 $G$의 태스크 의존성**: 최적의 그룹 수는 모델 크기, 태스크, 하드웨어에 따라 달라지므로 별도 탐색이 필요합니다 (다만 실무적으로 $G=8$이 대부분 잘 동작합니다).
- **MLA 대비 한계**: DeepSeek-V2의 MLA(Multi-head Latent Attention)는 KV를 저차원 잠재 공간으로 압축한 뒤 각 헤드에 고유한 KV를 복원할 수 있어, GQA보다 더 높은 압축률과 표현력을 동시에 달성한다고 주장합니다.
- **Prefill 단계에서의 무효과**: GQA는 Decode 단계의 메모리 대역폭 병목을 해결하는 기법이므로, compute-bound인 Prefill 단계에서는 속도 향상이 미미합니다.
- **소형 모델에서의 제한적 효과**: 7B 이하 모델에서는 KV 캐시가 상대적으로 작아 GQA의 메모리 절감 효과가 체감되기 어려울 수 있습니다.

### 후속 연구와의 관계

GQA 이후 KV 캐시 효율화 연구는 더욱 활발해졌습니다:

- **MLA (Multi-head Latent Attention)**: DeepSeek-V2에서 제안. KV를 저차원 잠재 벡터로 압축하여 GQA보다 높은 압축률 달성
- **KV Cache Quantization**: KV 캐시를 INT8/INT4로 양자화하여 메모리를 추가 절감. GQA와 병행 적용 가능
- **Sliding Window Attention**: Mistral에서 GQA와 결합하여 고정 크기 KV 캐시로 긴 시퀀스 처리

## 코드 예제

### GQA 구현 및 MHA/MQA 비교 (PyTorch)

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
import math

class GroupedQueryAttention(nn.Module):
    """GQA: 쿼리 헤드 H개를 G개 그룹으로 나누어 KV 공유.
    G=1: MQA, G=H: MHA, 1<G<H: GQA.
    """
    def __init__(self, d_model, num_heads, num_kv_heads):
        super().__init__()
        assert num_heads % num_kv_heads == 0, "H must be divisible by G"
        self.num_heads = num_heads          # 쿼리 헤드 수 (H)
        self.num_kv_heads = num_kv_heads    # KV 헤드 수 (G)
        self.head_dim = d_model // num_heads
        self.num_groups = num_heads // num_kv_heads  # 그룹당 쿼리 헤드 수

        self.q_proj = nn.Linear(d_model, num_heads * self.head_dim, bias=False)
        self.k_proj = nn.Linear(d_model, num_kv_heads * self.head_dim, bias=False)
        self.v_proj = nn.Linear(d_model, num_kv_heads * self.head_dim, bias=False)
        self.o_proj = nn.Linear(num_heads * self.head_dim, d_model, bias=False)

    def forward(self, x):
        B, T, _ = x.shape

        Q = self.q_proj(x).view(B, T, self.num_heads, self.head_dim)
        K = self.k_proj(x).view(B, T, self.num_kv_heads, self.head_dim)
        V = self.v_proj(x).view(B, T, self.num_kv_heads, self.head_dim)

        # KV 확장: G개 KV 헤드를 H개 쿼리에 맞춰 반복
        # (B, T, G, D) -> (B, T, G, 1, D) -> (B, T, G, H/G, D) -> (B, T, H, D)
        K = K.unsqueeze(3).expand(-1, -1, -1, self.num_groups, -1)
        K = K.reshape(B, T, self.num_heads, self.head_dim)
        V = V.unsqueeze(3).expand(-1, -1, -1, self.num_groups, -1)
        V = V.reshape(B, T, self.num_heads, self.head_dim)

        Q, K, V = [t.transpose(1, 2) for t in (Q, K, V)]  # (B, H, T, D)
        scale = math.sqrt(self.head_dim)
        scores = torch.matmul(Q, K.transpose(-2, -1)) / scale
        mask = torch.tril(torch.ones(T, T, device=x.device))
        scores = scores.masked_fill(mask == 0, float('-inf'))
        attn = F.softmax(scores, dim=-1)
        out = torch.matmul(attn, V).transpose(1, 2).contiguous().view(B, T, -1)
        return self.o_proj(out)


def uptraining_convert(mha_model, num_kv_heads):
    """MHA 체크포인트를 GQA로 변환 (업트레이닝 전처리).
    핵심: KV 헤드를 그룹별로 평균 풀링.
    """
    num_heads = mha_model.num_heads
    head_dim = mha_model.head_dim
    group_size = num_heads // num_kv_heads

    # K, V 가중치를 그룹별로 평균
    k_weight = mha_model.k_proj.weight.view(num_heads, head_dim, -1)
    v_weight = mha_model.v_proj.weight.view(num_heads, head_dim, -1)

    k_grouped = k_weight.view(num_kv_heads, group_size, head_dim, -1).mean(dim=1)
    v_grouped = v_weight.view(num_kv_heads, group_size, head_dim, -1).mean(dim=1)

    print(f"K 가중치: {k_weight.shape} -> {k_grouped.shape}")
    print(f"V 가중치: {v_weight.shape} -> {v_grouped.shape}")
    print(f"KV 파라미터 감소: {1 - num_kv_heads/num_heads:.0%}")
    return k_grouped, v_grouped


# ===== KV 캐시 크기 비교 =====
def compare_kv_cache(num_heads, head_dim, seq_len, num_layers, dtype_bytes=2):
    configs = [
        ("MHA", num_heads),
        ("GQA-8", 8),
        ("GQA-4", 4),
        ("MQA", 1),
    ]
    print(f"\n=== KV 캐시 비교 (H={num_heads}, d={head_dim}, L={seq_len}, layers={num_layers}) ===")
    for name, g in configs:
        kv_bytes = 2 * num_layers * g * head_dim * seq_len * dtype_bytes
        print(f"  {name:>6}: {kv_bytes / 1024**3:.2f} GB  (MHA 대비 {g/num_heads*100:.0f}%)")

# LLaMA-2-70B 기준
compare_kv_cache(num_heads=64, head_dim=128, seq_len=4096, num_layers=80)

# GQA 동작 테스트
print("\n=== GQA 동작 테스트 ===")
for g in [1, 4, 8, 32]:
    gqa = GroupedQueryAttention(d_model=2048, num_heads=32, num_kv_heads=g)
    kv_params = sum(p.numel() for p in [gqa.k_proj.weight, gqa.v_proj.weight])
    x = torch.randn(1, 10, 2048)
    out = gqa(x)
    name = {1: "MQA", 32: "MHA"}.get(g, f"GQA-{g}")
    print(f"  {name:>6}: KV 파라미터={kv_params:>8,}, 출력={out.shape}")
```