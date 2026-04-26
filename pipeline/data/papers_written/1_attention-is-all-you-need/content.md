<!-- infographic-hero -->
![Attention Is All You Need 핵심 요약](figures/infographic.svg)

*Figure: Attention Is All You Need 한 장 요약 인포그래픽*

## 개요

"Attention Is All You Need"(Vaswani et al., 2017)는 자연어 처리 분야에서 가장 혁신적인 논문 중 하나로, **Transformer** 아키텍처를 처음으로 제안했습니다. 기존의 RNN이나 CNN을 완전히 제거하고, 오직 Self-Attention 메커니즘만을 사용하여 시퀀스-투-시퀀스 학습을 수행합니다. 영어-독일어 번역에서 28.4 BLEU, 영어-프랑스어 번역에서 41.0 BLEU라는 당시 SOTA 성능을 달성했으며, 기존 최고 모델 대비 학습 비용을 1/4 이하로 줄였습니다.

2025년 기준 Google Scholar 인용 수 173,000회 이상으로, 21세기에 발표된 논문 중 가장 많이 인용된 논문 Top 10에 들어가는 기념비적인 연구입니다. Transformer는 NLP뿐만 아니라 컴퓨터 비전(ViT), 음성 인식(Whisper), 단백질 구조 예측(AlphaFold 2), 이미지 생성(DiT/Stable Diffusion 3) 등 거의 모든 딥러닝 영역의 기반 아키텍처로 자리잡았습니다.

논문의 제목 "Attention Is All You Need"는 그 자체로 강력한 주장을 담고 있습니다. 기존에 Attention은 RNN의 **보조 메커니즘**으로 사용되었는데, 이 논문은 Attention **하나만으로** 시퀀스 모델링의 모든 것을 해결할 수 있다고 선언한 것입니다. 이 대담한 주장은 이후 7년간의 연구를 통해 완전히 입증되었습니다.

## 배경 및 문제

### 시퀀스 모델링의 역사

2017년 이전까지 시퀀스 모델링의 주류는 LSTM(Hochreiter & Schmidhuber, 1997), GRU(Cho et al., 2014) 같은 RNN 계열이었습니다. 이들은 은닉 상태(hidden state)를 시간 축을 따라 순차적으로 전달하여 시퀀스 정보를 처리합니다. 2014년에는 Sutskever et al.이 Seq2Seq 모델을 제안하여 인코더-디코더 구조를 확립했고, 2015년에는 Bahdanau et al.이 Attention 메커니즘을 RNN에 결합하여 긴 문장 번역 성능을 크게 개선했습니다.

한편, CNN 기반 시퀀스 모델도 연구되었습니다. Gehring et al.(2017)의 ConvS2S는 합성곱을 사용하여 RNN보다 빠른 학습이 가능했지만, 수용 범위(receptive field)가 레이어 수에 제한되는 한계가 있었습니다.

### RNN의 근본적 한계

RNN 계열 모델은 다음과 같은 근본적인 한계를 가지고 있었습니다:

- **순차 계산(Sequential computation)**: 시퀀스를 순서대로 처리해야 하므로 병렬화가 불가능합니다. 시간 $t$의 은닉 상태 $h_t$를 계산하려면 반드시 $h_{t-1}$이 필요합니다
- **장기 의존성 문제(Long-range dependency)**: 시퀀스가 길어질수록 먼 위치의 정보를 유지하기 어렵습니다. 경로 길이가 $O(n)$이므로 두 토큰 사이의 정보 전달에 $n$번의 연산이 필요합니다
- **기울기 소실(Vanishing gradient)**: 역전파 시 오랜 시간 단계를 거치면 기울기가 지수적으로 감소합니다. LSTM의 게이트 메커니즘이 이를 완화하지만 완전히 해결하지는 못합니다
- **학습 속도의 한계**: GPU의 병렬 처리 능력을 제대로 활용할 수 없어 대규모 데이터 학습에 비효율적입니다. 시퀀스 길이가 $n$이면 $n$번의 순차 연산이 필수적입니다

### Self-Attention이라는 해답

Attention 메커니즘은 이미 Bahdanau et al.(2015)에 의해 RNN과 함께 사용되고 있었지만, Vaswani et al.은 RNN 자체를 제거하고 Attention만으로 모든 것을 처리할 수 있다는 대담한 가설을 제시했습니다. 핵심 아이디어는 시퀀스의 모든 위치 쌍 사이의 관계를 **한 번의 행렬 연산**으로 계산하는 것입니다.

다음 표는 RNN, CNN, Self-Attention의 주요 특성을 비교합니다(논문 Table 1 기반):

| 레이어 타입 | 레이어당 복잡도 | 순차 연산 수 | 최대 경로 길이 |
|-----------|---------------|------------|-------------|
| RNN (Self-Attention 없음) | $O(n \cdot d^2)$ | $O(n)$ | $O(n)$ |
| CNN | $O(k \cdot n \cdot d^2)$ | $O(1)$ | $O(\log_k n)$ |
| Self-Attention | $O(n^2 \cdot d)$ | $O(1)$ | $O(1)$ |
| Self-Attention (restricted) | $O(r \cdot n \cdot d)$ | $O(1)$ | $O(n/r)$ |

여기서 $n$은 시퀀스 길이, $d$는 표현 차원, $k$는 커널 크기, $r$은 제한된 이웃 크기입니다. Self-Attention은 최대 경로 길이가 $O(1)$이고 순차 연산이 $O(1)$이라는 점에서 RNN과 CNN 모두를 압도합니다. 특히 일반적인 시퀀스 길이($n < d$)에서는 레이어당 복잡도도 RNN보다 유리합니다.

이 논문의 저자 8명은 당시 Google Brain과 Google Research 소속으로, 이후 각각 AI 산업에 큰 영향을 미쳤습니다. Aidan Gomez는 Cohere를, Llion Jones는 Sakana AI를, Illia Polosukhin은 Near Protocol을 공동 창업했습니다.

## 핵심 아이디어

### Scaled Dot-Product Attention

Transformer의 핵심 연산은 **Scaled Dot-Product Attention**입니다. 입력으로 Query($Q$), Key($K$), Value($V$) 행렬을 받아 다음과 같이 계산합니다:

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

여기서 $d_k$는 키 벡터의 차원입니다. 이 수식의 각 단계를 풀어서 설명하면 다음과 같습니다:

1. **$QK^T$ (유사도 계산)**: Query와 Key의 내적으로 모든 위치 쌍 간의 유사도 점수를 계산합니다. 결과는 $n \times n$ 크기의 Attention Score 행렬입니다.
2. **$\frac{1}{\sqrt{d_k}}$ (스케일링)**: 내적값이 $d_k$에 비례하여 커지는 것을 방지합니다. $Q$와 $K$의 각 원소가 평균 0, 분산 1인 독립 확률 변수일 때, 내적 $q \cdot k = \sum_{i=1}^{d_k} q_i k_i$의 분산은 $d_k$가 됩니다. $d_k = 64$일 경우 일부 내적값이 매우 커져 softmax가 극도로 뾰족한(peaked) 분포를 만들고 기울기가 극히 작아지므로, $\sqrt{d_k}$로 나누어 분산을 1로 정규화합니다.
3. **softmax (확률 분포 변환)**: 스케일링된 점수를 행 단위로 확률 분포로 변환합니다.
4. **$\times V$ (가중 합)**: 확률 분포에 따라 Value 벡터의 가중 평균을 구합니다.

아래 그림은 이 연산 흐름을 도식화한 것입니다.

![Scaled Dot-Product Attention의 연산 흐름](figures/fig_2_1.png)
*Figure 2 (좌): Scaled Dot-Product Attention. Q와 K의 내적(MatMul) 후 $\sqrt{d_k}$로 스케일링(Scale)하고, 선택적 마스킹(Mask)을 거쳐 Softmax로 확률 분포를 만든 뒤, V와의 가중합(MatMul)으로 최종 출력을 생성한다.*

이 연산의 직관적 의미는 정보 검색 시스템에 비유할 수 있습니다:
- **Query**: "내가 찾고 싶은 정보"를 나타내는 벡터
- **Key**: "내가 가지고 있는 정보의 색인"을 나타내는 벡터
- **Value**: "실제 정보"를 나타내는 벡터

논문에서는 Additive Attention(Bahdanau et al., 2015)과 Dot-Product Attention의 두 가지 변형을 비교합니다. Additive Attention은 단층 피드포워드 네트워크로 유사도를 계산하는 반면, Dot-Product Attention은 단순한 내적을 사용합니다. 이론적 복잡도는 비슷하지만, Dot-Product Attention이 고도로 최적화된 행렬 곱셈 하드웨어를 활용할 수 있어 실제로 훨씬 빠르고 메모리 효율적입니다.

### Multi-Head Attention

단일 Attention 함수를 한 번 적용하는 것보다, 입력을 여러 부분 공간(subspace)으로 투영하여 병렬로 Attention을 수행하는 것이 더 효과적입니다. 이것이 **Multi-Head Attention**입니다:

$$\text{MultiHead}(Q, K, V) = \text{Concat}(\text{head}_1, \ldots, \text{head}_h)W^O$$

$$\text{head}_i = \text{Attention}(QW_i^Q, KW_i^K, VW_i^V)$$

여기서 각 프로젝션 행렬의 차원은 다음과 같습니다:
- $W_i^Q \in \mathbb{R}^{d_{\text{model}} \times d_k}$, $W_i^K \in \mathbb{R}^{d_{\text{model}} \times d_k}$, $W_i^V \in \mathbb{R}^{d_{\text{model}} \times d_v}$
- $W^O \in \mathbb{R}^{hd_v \times d_{\text{model}}}$

각 헤드는 서로 다른 표현 부분 공간에서 정보를 독립적으로 학습합니다. 논문에서는 $h=8$개의 헤드를 사용하며, $d_k = d_v = d_{\text{model}}/h = 64$로 설정합니다. 이렇게 하면 단일 헤드 Attention($d_k = d_{\text{model}} = 512$)과 총 계산 비용이 거의 동일하면서도 더 풍부한 표현을 학습할 수 있습니다.

아래 그림은 Multi-Head Attention의 구조를 보여줍니다. 입력 Q, K, V가 각각 $h$개의 Linear 투영을 거쳐 병렬 Attention을 수행한 뒤, 결과를 Concat하여 최종 Linear 투영을 통과합니다.

![Multi-Head Attention의 구조](figures/fig_2_2.png)
*Figure 2 (우): Multi-Head Attention. Q, K, V를 $h$개의 헤드로 분리하여 각각 Linear 투영 후 병렬로 Scaled Dot-Product Attention을 수행하고, Concat한 결과에 최종 Linear 투영을 적용한다.*

Multi-Head Attention이 효과적인 이유를 직관적으로 설명하면, 자연어에서 단어 간의 관계는 다차원적이기 때문입니다. 예를 들어, "The cat sat on the mat because it was tired"라는 문장에서:
- 한 헤드는 **구문적 관계**를 포착합니다 ("cat"과 "sat"의 주어-동사 관계)
- 다른 헤드는 **코어퍼런스**를 학습합니다 ("it"이 "cat"을 지칭)
- 또 다른 헤드는 **의미적 유사성**을 추적합니다 ("cat"과 "tired"의 의미적 연관)

이후 연구(Clark et al., 2019; Voita et al., 2019)에서 각 헤드가 실제로 이러한 다양한 유형의 언어적 관계를 전문적으로 포착한다는 것이 시각화를 통해 확인되었습니다.

Transformer에서 Multi-Head Attention은 세 가지 방식으로 사용됩니다:

| 사용 위치 | Q 출처 | K, V 출처 | 설명 |
|----------|-------|----------|------|
| 인코더 Self-Attention | 인코더 입력 | 인코더 입력 | 입력 시퀀스 내 관계 모델링 |
| 디코더 Masked Self-Attention | 디코더 입력 | 디코더 입력 | 출력 시퀀스 내 관계 (미래 마스킹) |
| 디코더 Cross-Attention | 디코더 출력 | 인코더 출력 | 입력-출력 시퀀스 간 정렬 |

### Positional Encoding

Self-Attention은 본질적으로 순서에 무관(permutation invariant)하므로, 위치 정보를 별도로 주입해야 합니다. 다음과 같은 **Sinusoidal Positional Encoding**을 임베딩에 더합니다:

$$PE_{(pos, 2i)} = \sin\left(\frac{pos}{10000^{2i/d_{\text{model}}}}\right)$$

$$PE_{(pos, 2i+1)} = \cos\left(\frac{pos}{10000^{2i/d_{\text{model}}}}\right)$$

여기서 $pos$는 시퀀스 내 위치, $i$는 차원 인덱스입니다. 각 차원은 서로 다른 주파수의 사인/코사인 파형을 사용하며, 파장은 $2\pi$에서 $10000 \cdot 2\pi$까지 기하급수적으로 분포합니다.

이 설계의 핵심 장점은 **상대적 위치를 선형 변환으로 표현**할 수 있다는 것입니다. 삼각함수의 덧셈 정리에 의해:

$$PE_{pos+k} = f(PE_{pos}, k)$$

즉, 위치 $pos$에서 $pos+k$로의 이동을 고정된 선형 변환으로 나타낼 수 있어, 모델이 상대적 위치 관계를 쉽게 학습할 수 있습니다. 또한 학습 시 보지 못한 더 긴 시퀀스에도 외삽(extrapolation)이 가능하다는 이론적 장점이 있습니다(단, 실제로는 학습 길이를 크게 넘어가면 성능이 저하됩니다).

이후 RoPE(Rotary Position Embedding, Su et al., 2024), ALiBi(Press et al., 2022) 등 더 효과적인 위치 인코딩이 제안되었으며, 현대 LLM에서는 RoPE가 사실상 표준입니다.

## 방법론

### 전체 아키텍처

Transformer는 **Encoder-Decoder** 구조로 이루어져 있습니다. 아래 그림은 논문에서 제시한 전체 아키텍처를 보여줍니다. 왼쪽의 인코더는 입력 시퀀스를 연속적인 표현으로 변환하고, 오른쪽의 디코더는 이 표현을 참조하여 출력 시퀀스를 자동회귀적으로 생성합니다.

![Transformer 전체 아키텍처](figures/fig_1.png)
*Figure 1: Transformer 모델의 전체 아키텍처. 왼쪽이 인코더, 오른쪽이 디코더이며 각각 $N=6$개의 동일한 레이어가 반복된다. 인코더 레이어는 Multi-Head Self-Attention과 Feed Forward로 구성되고, 디코더 레이어는 Masked Multi-Head Self-Attention, Cross-Attention, Feed Forward로 구성된다. 모든 서브레이어에 Residual Connection과 Layer Normalization이 적용된다.*

### Encoder

인코더는 $N=6$개의 동일한 레이어로 구성되며, 각 레이어는:
1. **Multi-Head Self-Attention** 서브레이어
2. **Position-wise Feed-Forward Network** 서브레이어

각 서브레이어에는 Residual Connection과 Layer Normalization이 적용됩니다:

$$\text{LayerOutput} = \text{LayerNorm}(x + \text{Sublayer}(x))$$

이 구조를 **Post-LN**(Layer Norm이 서브레이어 출력 이후)이라 합니다. Residual Connection을 용이하게 하기 위해 모든 서브레이어의 출력 차원은 $d_{\text{model}} = 512$로 통일됩니다.

이후 연구(Xiong et al., 2020)에서 **Pre-LN**(Layer Norm이 서브레이어 입력 이전)이 학습 안정성에 더 유리하다는 것이 밝혀져, GPT-3, LLaMA 등 현대 모델은 Pre-LN을 사용합니다:

$$\text{LayerOutput} = x + \text{Sublayer}(\text{LayerNorm}(x))$$

### Decoder

디코더도 $N=6$개의 레이어로 구성되며, 인코더와 달리 세 번째 서브레이어로 **Cross-Attention**(인코더 출력에 대한 Multi-Head Attention)이 추가됩니다. 또한 Self-Attention에는 미래 위치를 보지 못하도록 **Causal Masking**이 적용됩니다. 이는 Attention 스코어 행렬에서 미래 위치에 $-\infty$를 넣어 softmax 이후 0이 되게 합니다.

Causal Masking은 이후 GPT 계열 모델의 핵심 메커니즘이 됩니다. 디코더-온리 모델(GPT 계열)에서는 인코더와 Cross-Attention을 제거하고, Causal Masked Self-Attention만으로 자동회귀 생성을 수행합니다.

### Feed-Forward Network

각 레이어의 FFN은 두 선형 변환 사이에 ReLU를 적용합니다:

$$\text{FFN}(x) = \max(0, xW_1 + b_1)W_2 + b_2$$

$d_{\text{model}} = 512$, $d_{\text{ff}} = 2048$을 사용합니다. 이는 은닉 차원이 모델 차원의 4배인 구조로, 이후 대부분의 Transformer 변형에서도 이 비율이 유지됩니다. FFN은 각 위치에 독립적으로 적용되며, 일종의 **키-밸류 메모리**로 해석할 수 있습니다(Geva et al., 2021). 첫 번째 선형 변환이 패턴을 감지(키 매칭)하고, 두 번째 선형 변환이 해당 패턴에 대응하는 정보(밸류)를 출력하는 것으로 볼 수 있습니다. 이후 모델에서는 ReLU 대신 GELU나 SwiGLU 활성화 함수가 사용됩니다.

### 모델 구성

논문에서는 두 가지 모델 크기를 실험했습니다:

| 하이퍼파라미터 | Transformer (base) | Transformer (big) |
|-------------|-------------------|-------------------|
| $N$ (레이어 수) | 6 | 6 |
| $d_{\text{model}}$ | 512 | 1024 |
| $d_{\text{ff}}$ | 2048 | 4096 |
| $h$ (헤드 수) | 8 | 16 |
| $d_k = d_v$ | 64 | 64 |
| $P_{drop}$ | 0.1 | 0.3 |
| 파라미터 수 | 65M | 213M |
| 학습 시간 | 12시간 (8 P100) | 3.5일 (8 P100) |

### 학습 설정

- **데이터**: WMT 2014 영어-독일어 (약 450만 문장 쌍), 영어-프랑스어 (약 3,600만 문장 쌍)
- **토크나이저**: Byte-Pair Encoding(BPE). EN-DE는 공유 어휘 37,000개, EN-FR는 공유 어휘 32,000개
- **옵티마이저**: Adam ($\beta_1=0.9$, $\beta_2=0.98$, $\epsilon=10^{-9}$)
- **학습률 스케줄**: Warmup + Inverse Square Root Decay

$$lr = d_{\text{model}}^{-0.5} \cdot \min(\text{step}^{-0.5}, \text{step} \cdot \text{warmup\_steps}^{-1.5})$$

이 스케줄은 처음 $\text{warmup\_steps}$(=4000) 동안 학습률을 선형으로 증가시킨 후, 이후에는 스텝 수의 역제곱근에 비례하여 감소시킵니다. 이렇게 하면 학습 초기에 파라미터가 아직 불안정할 때 너무 큰 업데이트를 방지하고, 학습이 진행됨에 따라 점진적으로 미세 조정할 수 있습니다.

- **정규화**: Residual Dropout ($P_{drop}=0.1$), Label Smoothing ($\epsilon_{ls}=0.1$)
- **배치**: 약 25,000개의 소스 토큰과 25,000개의 타깃 토큰을 포함하는 배치
- **학습 하드웨어**: 8개의 NVIDIA P100 GPU에서 base 모델 12시간, big 모델 3.5일

Label Smoothing은 정답 레이블에 $1 - \epsilon_{ls}$ 확률을 할당하고, 나머지 확률을 다른 토큰들에 균등 배분합니다. 이는 모델이 지나치게 자신있는 예측을 하는 것을 방지하고, perplexity는 약간 증가하지만 BLEU 점수와 정확도는 향상시킵니다.

## 실험 결과

### Machine Translation (WMT 2014)

#### 영어-독일어 (EN-DE)

| 모델 | BLEU | Training Cost (FLOPs) |
|------|------|-----------------------|
| ByteNet (Kalchbrenner et al., 2016) | 23.75 | - |
| GNMT+RL (Wu et al., 2016) | 24.6 | 2.3 x 10^19 |
| ConvS2S (Gehring et al., 2017) | 25.16 | 9.6 x 10^18 |
| MoE (Shazeer et al., 2017) | 26.03 | 2.0 x 10^19 |
| GNMT+RL Ensemble | 26.30 | 1.8 x 10^20 |
| ConvS2S Ensemble | 26.36 | 7.7 x 10^19 |
| Transformer (base) | 27.3 | **3.3 x 10^18** |
| **Transformer (big)** | **28.4** | 2.3 x 10^19 |

#### 영어-프랑스어 (EN-FR)

| 모델 | BLEU | Training Cost (FLOPs) |
|------|------|-----------------------|
| GNMT+RL (Wu et al., 2016) | 39.92 | 1.4 x 10^20 |
| ConvS2S (Gehring et al., 2017) | 40.46 | 1.5 x 10^20 |
| MoE (Shazeer et al., 2017) | 40.56 | 1.2 x 10^20 |
| GNMT+RL Ensemble | 41.16 | 1.1 x 10^21 |
| Transformer (base) | 38.1 | **3.3 x 10^18** |
| **Transformer (big)** | **41.0** | 2.3 x 10^19 |

핵심 관찰 결과는 다음과 같습니다:

1. **Transformer(big)는 모든 단일 모델과 앙상블 모델을 능가**합니다. EN-DE에서 기존 최고 앙상블 대비 +2.0 BLEU 이상 개선했습니다
2. **학습 비용이 극적으로 낮습니다**. Transformer(base)는 3.3 x 10^18 FLOPs로, 경쟁 모델 대비 1/3 ~ 1/50 수준의 비용으로 기존 SOTA에 근접하는 성능을 보여줍니다
3. **EN-FR에서 Transformer(big)는 기존 최고 단일 모델 대비 +0.5 BLEU**를 달성하면서 학습 비용은 1/4 미만입니다

### Ablation Study

논문의 Table 3은 다양한 아키텍처 변형에 대한 Ablation 실험 결과를 보여줍니다:

| 변형 | $h$ | $d_k$ | $d_v$ | $d_{\text{model}}$ | $d_{\text{ff}}$ | EN-DE BLEU | 분석 |
|------|-----|-------|-------|-------------------|----------------|-----------|------|
| base | 8 | 64 | 64 | 512 | 2048 | 27.3 | 기준선 |
| (A) 헤드 1개 | 1 | 512 | 512 | 512 | 2048 | 25.8 | Multi-Head가 필수적 |
| (A) 헤드 4개 | 4 | 128 | 128 | 512 | 2048 | 26.5 | 헤드 수 부족 시 성능 저하 |
| (A) 헤드 16개 | 16 | 32 | 32 | 512 | 2048 | 27.0 | $d_k$ 감소로 약간 저하 |
| (A) 헤드 32개 | 32 | 16 | 16 | 512 | 2048 | 26.5 | $d_k$가 너무 작으면 성능 하락 |
| (B) $d_k$ = 16 | 8 | 16 | 64 | 512 | 2048 | 26.9 | Dot-Product에 충분한 차원 필요 |
| (C) big model | 8 | 64 | 64 | 1024 | 4096 | 27.8 | 모델 크기 증가는 성능 향상 |
| (D) Dropout 제거 | 8 | 64 | 64 | 512 | 2048 | 26.9 | 정규화의 중요성 확인 |
| (E) 학습된 PE | 8 | 64 | 64 | 512 | 2048 | 27.3 | Sinusoidal과 거의 동일 |

이 실험에서 얻을 수 있는 핵심 교훈은 다음과 같습니다:
- Multi-Head는 반드시 필요하며, 단일 헤드 대비 +1.5 BLEU의 차이를 만듭니다
- 키 차원 $d_k$를 너무 줄이면 Dot-Product의 표현력이 저하됩니다
- Dropout은 과적합 방지에 효과적이며, 제거 시 0.4 BLEU 하락합니다
- 학습된 Positional Embedding과 Sinusoidal PE는 거의 동일한 성능을 보여, 고정된 PE로도 충분함을 입증합니다

### Attention 시각화

논문에서는 학습된 Attention 패턴을 시각화하여 각 헤드가 서로 다른 언어적 관계를 전문적으로 포착함을 보여줍니다. 아래 그림은 인코더 레이어 5에서 동사 "making"에 대한 Attention을 시각화한 것으로, 여러 헤드가 "making...more difficult"이라는 장거리 의존성 구문을 정확히 포착하는 모습을 확인할 수 있습니다.

![인코더 Self-Attention의 장거리 의존성 포착](figures/fig_3.png)
*Figure 3: 인코더 Self-Attention 레이어 5에서 동사 "making"에 대한 Attention 패턴. 여러 헤드가 "making...more difficult"이라는 먼 거리의 의존 관계를 정확히 포착한다. 서로 다른 색상은 서로 다른 헤드를 나타낸다.*

또한 대명사의 조응어(anaphora) 해석에서도 Attention의 능력이 드러납니다. 아래 그림에서 "its"라는 대명사에 대해 헤드 5와 6이 날카롭게(sharp) 집중하여, 모델이 대명사가 지칭하는 명사를 정확히 파악하고 있음을 보여줍니다.

![어텐션 헤드의 조응어 해석 ( 헤드 5의 전체 어텐션](figures/fig_4_1.png)
*Figure 4 (상): 레이어 5의 어텐션 헤드 5에서 조응어 해석에 관여하는 전체 어텐션 패턴. 'its'라는 대명사가 지칭하는 명사를 파악하는 데 헤드들이 예리하게 집중하는 모습을 시각화한다. (Vaswani et al., 2017)*

![어텐션 헤드의 대명사 조응어 해석](figures/fig_4_2.png)
*Figure 4 (하): 레이어 5의 헤드 5, 6에서 'its' 단어만의 격리된 어텐션. 이 단어에 대해 어텐션이 매우 날카롭게(sharp) 나타나, 모델이 대명사 해석 관계를 명시적으로 학습함을 보여준다. (Vaswani et al., 2017)*

이러한 시각화 결과는 Multi-Head Attention이 단순한 성능 향상을 넘어, 각 헤드가 **구문 분석**, **코어퍼런스 해석**, **장거리 의존성 추적** 등 서로 다른 언어적 역할을 자발적으로 분담한다는 것을 실증적으로 보여줍니다.

### English Constituency Parsing

번역 이외의 태스크에 대한 일반화 능력도 검증되었습니다. Wall Street Journal(WSJ) 데이터셋의 영어 구문 분석에서, 4-layer Transformer(디코더 전용, $d_{\text{model}}=1024$)를 사용한 결과:

| 모델 | WSJ 23 F1 |
|------|----------|
| Vinyals & Kaiser (2014) | 88.3 |
| Petrov et al. (2006) | 90.4 |
| Zhu et al. (2013) | 90.4 |
| Dyer et al. (2016) | 91.7 |
| **Transformer (4 layers)** | **91.3** |
| Luong et al. (2016) 5.8M sentences | 93.0 |

별도의 태스크 특화 설계 없이도 기존 RNN 기반 모델들과 경쟁력 있는 성능을 보여, Transformer의 범용성을 입증했습니다. 특히 대규모 데이터(BPE 준지도 학습 포함)를 사용하면 Luong et al.의 결과에 근접합니다.

## 의의 및 한계

### 의의

- **병렬 처리 혁명**: 모든 위치를 동시에 처리할 수 있어 GPU 활용도가 극적으로 향상되었습니다. RNN 대비 학습 속도가 수배~수십배 빨라졌으며, 이는 이후 대규모 사전학습을 가능하게 한 핵심 요인입니다
- **장거리 의존성 해결**: 두 위치 사이의 경로 길이가 $O(1)$로, RNN의 $O(n)$에 비해 훨씬 효율적입니다. 어떤 두 토큰이든 한 번의 Attention 연산으로 직접 상호작용할 수 있습니다
- **확장성(Scalability)**: 모델 크기를 쉽게 늘릴 수 있어 이후 BERT(340M), GPT-2(1.5B), GPT-3(175B), PaLM(540B), GPT-4에 이르기까지 수천억 파라미터로의 확장이 가능했습니다. Kaplan et al.(2020)의 Scaling Law 연구는 이 확장성이 예측 가능한 성능 향상으로 이어진다는 것을 보여주었습니다
- **범용성**: 번역 외 텍스트 요약, 질의응답, 이미지 처리(ViT), 음성(Whisper), 단백질(AlphaFold 2), 비디오 생성(Sora) 등 거의 모든 AI 도메인으로 확장되었습니다
- **AI 산업의 토대**: 거의 모든 상용 AI 시스템(ChatGPT, Claude, Gemini, LLaMA 등)이 Transformer 기반입니다
- **해석 가능성**: Attention Weight를 시각화하여 모델이 어떤 토큰 간의 관계에 주목하는지 직관적으로 파악할 수 있습니다. 이는 모델의 행동을 이해하고 디버깅하는 데 도움을 줍니다

![문장 구조에 민감한 어텐션 헤드 패턴 (헤드 2)](figures/fig_5_2.png)
*Figure 5 (하): 동일 레이어의 두 번째 헤드에서 나타나는 또 다른 문장 구조 관련 어텐션 패턴. 헤드 1과 다른 언어적 관계를 포착하며, 멀티-헤드 어텐션의 다양성을 시각적으로 입증한다. (Vaswani et al., 2017)*

![문장 구조 반영 어텐션 패턴 ) 첫 번째 헤드 시각화](figures/fig_5_1.png)
*Figure 5 (상): 인코더 Self-Attention 레이어 5의 서로 다른 두 헤드에서 문장 구조와 관련된 행동을 보이는 예시. 각 헤드가 서로 다른 태스크를 전문적으로 수행하도록 학습되었음을 명확히 보여준다. (Vaswani et al., 2017)*

### 한계

- **2차 복잡도**: Self-Attention의 계산 복잡도가 시퀀스 길이 $n$에 대해 $O(n^2)$이므로 매우 긴 시퀀스 처리에 제약이 있습니다. 예를 들어, 시퀀스 길이가 2배가 되면 메모리와 계산량은 4배가 됩니다. 128K 토큰 컨텍스트에서는 Attention 행렬만 128K x 128K = 약 16.4B 원소가 필요합니다
- **Positional Encoding의 한계**: 사인/코사인 인코딩은 학습되지 않으며, 훈련 시 보지 못한 길이의 시퀀스에 일반화하기 어렵습니다. 이후 RoPE, ALiBi 등으로 개선되었습니다
- **데이터 효율성**: RNN에 비해 학습에 더 많은 데이터가 필요한 경향이 있습니다. Self-Attention은 강한 Inductive bias가 없어(RNN의 순차적 편향, CNN의 지역적 편향과 달리) 데이터로부터 구조를 학습해야 합니다
- **인과 관계 학습의 한계**: Attention은 상관관계를 포착하지만, 인과 관계를 직접 모델링하지는 않습니다
- **메모리 대역폭**: 추론 시 자동회귀 생성은 여전히 순차적이며, 각 토큰 생성 시 전체 KV 캐시를 참조해야 하므로 메모리 대역폭에 병목이 발생합니다

이후 연구들은 Sparse Attention(Longformer, BigBird), Flash Attention(Dao et al., 2022), Ring Attention, 상대적 Positional Encoding(RoPE, ALiBi), Mixture of Experts(Switch Transformer), State Space Model(Mamba) 등으로 이러한 한계를 극복해 나가고 있습니다.

## 후속 연구의 흐름

Transformer 논문이 촉발한 주요 연구 방향을 정리하면 다음과 같습니다:

| 연구 방향 | 대표 연구 | 핵심 기여 |
|----------|---------|----------|
| 인코더 중심 | [[bert|BERT]], RoBERTa, DeBERTa | 양방향 사전학습, 이해 태스크 |
| 디코더 중심 | [[gpt-1|GPT]], GPT-2, GPT-3, LLaMA | 자동회귀 생성, 스케일링 |
| 인코더-디코더 | [[t5|T5]], [[bart|BART]], mT5 | 통합 Text-to-Text 프레임워크 |
| 효율적 Attention | Longformer, Linformer, Flash Attention | $O(n^2)$ 복잡도 해결 |
| 비전 확장 | [[vit|ViT]], DeiT, Swin Transformer | 이미지 패치를 토큰으로 |
| 멀티모달 | [[clip|CLIP]], Flamingo, GPT-4V | 텍스트+이미지 통합 |
| 위치 인코딩 개선 | RoPE, ALiBi, NTK-Aware | 긴 컨텍스트 처리 |
| 비-Attention 대안 | [[retnet|RetNet]], [[rwkv|RWKV]], Mamba | 선형 복잡도 시퀀스 모델링 |

## 코드 예제

### Scaled Dot-Product Attention (PyTorch)

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
import math

def scaled_dot_product_attention(Q, K, V, mask=None, dropout=None):
    """Scaled Dot-Product Attention 구현.

    논문 수식: Attention(Q,K,V) = softmax(QK^T / sqrt(d_k)) V

    Args:
        Q: Query  (batch, heads, seq_len, d_k)
        K: Key    (batch, heads, seq_len, d_k)
        V: Value  (batch, heads, seq_len, d_v)
        mask: 마스킹 텐서 (선택적)
        dropout: Dropout 레이어 (선택적)
    Returns:
        output: Attention 출력 (batch, heads, seq_len, d_v)
        attn_weights: Attention 가중치 (batch, heads, seq_len, seq_len)
    """
    d_k = Q.size(-1)

    # Step 1: QK^T 계산 (유사도 점수)
    scores = torch.matmul(Q, K.transpose(-2, -1))  # (batch, heads, seq, seq)

    # Step 2: sqrt(d_k)로 스케일링 (기울기 소실 방지)
    scores = scores / math.sqrt(d_k)

    # Step 3: 마스킹 (Decoder의 Causal Mask 또는 Padding Mask)
    if mask is not None:
        scores = scores.masked_fill(mask == 0, float('-inf'))

    # Step 4: Softmax (확률 분포로 변환)
    attn_weights = F.softmax(scores, dim=-1)

    # Step 5: Attention Dropout (선택적)
    if dropout is not None:
        attn_weights = dropout(attn_weights)

    # Step 6: Value의 가중 평균
    output = torch.matmul(attn_weights, V)

    return output, attn_weights
```

### Multi-Head Attention

```python
class MultiHeadAttention(nn.Module):
    """Multi-Head Attention 구현.

    논문 수식: MultiHead(Q,K,V) = Concat(head_1,...,head_h) W^O
              head_i = Attention(Q W_i^Q, K W_i^K, V W_i^V)
    """
    def __init__(self, d_model=512, num_heads=8, dropout=0.1):
        super().__init__()
        assert d_model % num_heads == 0, "d_model must be divisible by num_heads"

        self.d_model = d_model
        self.num_heads = num_heads
        self.d_k = d_model // num_heads  # 논문: d_k = d_model / h = 64

        # W^Q, W^K, W^V, W^O 프로젝션 행렬
        self.W_q = nn.Linear(d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)
        self.W_o = nn.Linear(d_model, d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, Q, K, V, mask=None):
        batch_size = Q.size(0)

        # 1) 선형 변환 후 (batch, seq, d_model) -> (batch, heads, seq, d_k)
        Q = self.W_q(Q).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        K = self.W_k(K).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        V = self.W_v(V).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)

        # 2) Scaled Dot-Product Attention (모든 헤드에 동시 적용)
        x, attn_weights = scaled_dot_product_attention(
            Q, K, V, mask=mask, dropout=self.dropout
        )

        # 3) 헤드 결합: (batch, heads, seq, d_k) -> (batch, seq, d_model)
        x = x.transpose(1, 2).contiguous().view(batch_size, -1, self.d_model)

        # 4) 출력 프로젝션 W^O
        return self.W_o(x)
```

### Positional Encoding

```python
class PositionalEncoding(nn.Module):
    """Sinusoidal Positional Encoding.

    PE(pos, 2i)   = sin(pos / 10000^(2i/d_model))
    PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))
    """
    def __init__(self, d_model=512, max_len=5000, dropout=0.1):
        super().__init__()
        self.dropout = nn.Dropout(dropout)

        pe = torch.zeros(max_len, d_model)  # (max_len, d_model)
        position = torch.arange(0, max_len).unsqueeze(1).float()  # (max_len, 1)

        # 10000^(2i/d_model) 계산 (로그 공간에서 수치 안정성 확보)
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
        )

        pe[:, 0::2] = torch.sin(position * div_term)  # 짝수 차원: sin
        pe[:, 1::2] = torch.cos(position * div_term)  # 홀수 차원: cos

        # 배치 차원 추가하여 버퍼로 등록 (학습 파라미터 아님)
        self.register_buffer('pe', pe.unsqueeze(0))  # (1, max_len, d_model)

    def forward(self, x):
        """입력 임베딩에 위치 인코딩을 더합니다."""
        x = x + self.pe[:, :x.size(1)]
        return self.dropout(x)
```

### 전체 Transformer Encoder Layer

```python
class TransformerEncoderLayer(nn.Module):
    """Transformer Encoder Layer (Post-LN, 원래 논문 구조).

    구조: Input -> Self-Attention -> Add & Norm -> FFN -> Add & Norm -> Output
    """
    def __init__(self, d_model=512, num_heads=8, d_ff=2048, dropout=0.1):
        super().__init__()
        self.self_attn = MultiHeadAttention(d_model, num_heads, dropout)
        self.ffn = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_ff, d_model),
        )
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout1 = nn.Dropout(dropout)
        self.dropout2 = nn.Dropout(dropout)

    def forward(self, x, mask=None):
        # Sub-layer 1: Multi-Head Self-Attention + Residual + LayerNorm
        attn_out = self.self_attn(x, x, x, mask)  # Q=K=V=x (Self-Attention)
        x = self.norm1(x + self.dropout1(attn_out))

        # Sub-layer 2: Position-wise FFN + Residual + LayerNorm
        ffn_out = self.ffn(x)
        x = self.norm2(x + self.dropout2(ffn_out))
        return x


def create_causal_mask(seq_len):
    """Decoder용 Causal Mask 생성.

    하삼각 행렬로 미래 위치를 마스킹합니다.
    position i는 position 0..i만 볼 수 있습니다.
    """
    mask = torch.tril(torch.ones(seq_len, seq_len)).bool()
    return mask.unsqueeze(0).unsqueeze(0)  # (1, 1, seq_len, seq_len)


# === 사용 예시 ===
d_model, num_heads, seq_len, batch_size = 512, 8, 20, 4

# 인코더 레이어 구성
pe = PositionalEncoding(d_model)
encoder_layer = TransformerEncoderLayer(d_model, num_heads)

# 입력: 랜덤 임베딩 (실제로는 토큰 임베딩 * sqrt(d_model))
x = torch.randn(batch_size, seq_len, d_model)
x = x * math.sqrt(d_model)  # 논문: 임베딩에 sqrt(d_model)을 곱함
x = pe(x)                    # Positional Encoding 추가
out = encoder_layer(x)       # Encoder Layer 통과
print(f"Encoder output: {out.shape}")  # (4, 20, 512)

# Causal Mask 예시 (Decoder용)
causal_mask = create_causal_mask(seq_len)
print(f"Causal mask: {causal_mask.shape}")  # (1, 1, 20, 20)
```