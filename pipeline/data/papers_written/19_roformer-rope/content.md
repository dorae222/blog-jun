## 개요

"RoFormer: Enhanced Transformer with Rotary Position Embedding"은 Jianlin Su, Yu Lu, Shengfeng Pan, Ahmed Murtadha, Bo Wen, Yunfeng Liu가 2021년 발표한 논문으로, **RoPE(Rotary Position Embedding)**라는 새로운 위치 임베딩 기법을 제안한다. 이후 Neurocomputing 저널(2024)에도 정식 게재되었다.

RoPE는 2022년 이후 등장한 거의 모든 주요 오픈소스 LLM의 사실상 표준 위치 임베딩으로 채택되었다. LLaMA 1/2/3, PaLM, GPT-NeoX, Falcon, Mistral, Qwen, Yi, DeepSeek 등이 이를 사용하며, 현대 LLM 아키텍처의 근간을 이루는 핵심 기술로 평가받는다.

RoPE가 해결하고자 한 핵심 문제는 **위치 정보를 어텐션 메커니즘에 효율적이고 우아하게 통합하는 방법**이다. 기존 절대 위치 임베딩은 학습 범위 밖 위치로의 일반화(외삽)가 불가능하며, 상대 위치 임베딩은 구현이 복잡하고 계산 비용이 높았다. RoPE는 이 두 접근법의 장점을 결합하여, 절대 위치 임베딩처럼 단순하게 적용하면서도 어텐션 점수에서는 상대 위치 정보를 자연스럽게 인코딩하는 방법을 제시한다.

---

## 배경 및 문제

### 위치 정보의 필요성

Transformer의 셀프 어텐션은 본질적으로 **순서에 무관(permutation-invariant)**한 연산이다. 어텐션 점수 $\text{softmax}(QK^T/\sqrt{d})V$에서 입력 토큰의 순서를 바꿔도 동일한 출력이 나온다. 이는 어텐션 연산이 집합(set) 위에서 정의된 함수와 동치이기 때문이다. 구체적으로, 입력 시퀀스 $(x_1, x_2, \ldots, x_n)$에 임의의 순열 $\sigma$를 적용하여 $(x_{\sigma(1)}, x_{\sigma(2)}, \ldots, x_{\sigma(n)})$을 만들어도, 각 토큰이 받는 어텐션 가중치의 합은 변하지 않는다.

자연어 처리에서 "나는 너를 좋아한다"와 "너를 나는 좋아한다"는 의미가 다르고, "The dog bit the man"과 "The man bit the dog"는 전혀 다른 문장이다. 따라서 시퀀스의 순서 정보를 명시적으로 주입해야 하며, 이것이 위치 임베딩의 역할이다.

### 기존 위치 임베딩 방법들

**절대 위치 임베딩(Absolute PE)**: 각 위치 $m$에 대해 학습 가능한 벡터 $p_m$을 입력에 더한다. BERT, GPT-2 등이 사용한다.

$$x_m' = x_m + p_m$$

이 방법에서 어텐션 점수를 전개하면:

$$\langle W_Q(x_m + p_m), W_K(x_n + p_n) \rangle = x_m^T W_Q^T W_K x_n + x_m^T W_Q^T W_K p_n + p_m^T W_Q^T W_K x_n + p_m^T W_Q^T W_K p_n$$

마지막 항 $p_m^T W_Q^T W_K p_n$은 두 절대 위치의 함수이지 상대 위치 $m - n$의 함수가 아니다. 또한 학습 시 본 최대 위치 이후로는 일반화가 불가능하다 (예: 512 위치로 학습하면 513번째 위치를 처리할 수 없다).

**Sinusoidal PE**: 원 Transformer(Vaswani et al., 2017)의 방법으로, 사인/코사인 함수로 위치를 인코딩한다:

$$PE_{(pos, 2i)} = \sin\left(\frac{pos}{10000^{2i/d}}\right), \quad PE_{(pos, 2i+1)} = \cos\left(\frac{pos}{10000^{2i/d}}\right)$$

학습 파라미터가 없고 이론적으로는 외삽 가능하지만, 어텐션 점수에 상대 위치를 직접 인코딩하지 않아 효과가 제한적이다.

**상대 위치 임베딩(Relative PE)**: Shaw et al.(2018), Transformer-XL(Dai et al., 2019) 등이 제안한 방법으로, 두 위치의 상대 거리를 직접 어텐션에 반영한다. Transformer-XL에서는 이를 4개의 항으로 분해한다:

$$e_{ij} = x_i^T W_Q^T W_{K,E} x_j + x_i^T W_Q^T W_{K,R} r_{i-j} + u^T W_{K,E} x_j + v^T W_{K,R} r_{i-j}$$

여기서 $r_{i-j}$는 상대 위치 인코딩, $u$와 $v$는 학습 가능한 편향이다. 상대 위치를 직접적으로 모델링하지만, 구현이 복잡하고 어텐션 행렬 계산에 추가 메모리와 연산이 필요하다.

**ALiBi (Attention with Linear Biases)**: Press et al.(2022)이 제안한 방법으로, 어텐션 스코어에 위치 거리에 비례하는 선형 편향을 더한다:

$$\text{Attn}(i, j) = \frac{q_i k_j^T}{\sqrt{d}} - m \cdot |i - j|$$

단순하고 외삽 성능이 좋지만, 멀리 떨어진 토큰 간의 높은 어텐션을 원천적으로 억제하므로 장거리 의존성이 중요한 태스크에서 불리할 수 있다.

### RoPE의 설계 목표

RoPE는 다음 조건을 동시에 만족하는 위치 인코딩을 목표로 한다:

1. 어텐션 점수가 상대 위치 $m - n$에만 의존
2. 추가 학습 파라미터 불필요
3. 효율적 구현 가능 ($O(d)$ 원소별 연산)
4. 외삽 가능성 확보
5. 기존 Transformer 아키텍처에 최소한의 변경으로 적용 가능

기존 방법들은 이 조건들 중 일부만 만족했다. 절대 PE는 1, 4를 만족하지 않고, 상대 PE는 2, 3을 만족하지 않으며, ALiBi는 어텐션 점수에 곱셈적(multiplicative)이 아닌 가산적(additive) 편향만 줄 수 있어 표현력이 제한된다.

---

## 핵심 아이디어

다음 다이어그램은 RoPE의 핵심 개념과 설계 원리를 한눈에 보여준다. 쿼리와 키 벡터에 위치에 비례하는 회전을 적용하면, 내적 결과가 자연스럽게 상대 위치의 함수가 되는 원리를 시각화한 것이다.

![RoPE 전체 개요 - 핵심 아이디어, 2D 회전 시각화, 주요 특성 요약](figures/architecture.png)
*Figure 5: RoPE(Rotary Position Embedding)의 전체 개요, 위치 m의 쿼리와 위치 n의 키에 각각 회전 변환을 적용하면, 내적이 상대 거리 (m-n)에만 의존하게 된다. 상대적 위치 인코딩, 시퀀스 길이 제한 없음, 원소별 곱셈으로 효율적 계산, 선형 어텐션과의 호환성 등 네 가지 핵심 특성을 갖추고 있다. (Su et al., 2021)*

RoPE의 핵심은 간단하지만 우아하다: **위치 정보를 학습 가능한 임베딩으로 추가하는 대신, 쿼리와 키 벡터에 회전 변환(rotation)을 적용한다.**

기존의 additive 방식($x + p$)과 달리, RoPE는 multiplicative 방식($R \cdot x$)을 사용한다. 덧셈 방식에서는 위치 정보와 내용 정보가 섞여서 분리가 어렵지만, 곱셈(회전) 방식에서는 위치 정보가 벡터의 **방향만 변경하고 크기는 보존**하므로 내용 정보의 손실이 없다.

목표를 수학적으로 정의하면, 위치 $m$의 쿼리와 위치 $n$의 키 사이의 어텐션 점수가 두 위치의 **상대 거리** $m - n$에만 의존하도록 하는 함수 $f_q, f_k$를 찾는 것이다:

$$\langle f_q(x_m, m), f_k(x_n, n) \rangle = g(x_m, x_n, m - n)$$

추가 조건으로, 위치 0에서는 항등 변환이 되어야 한다:

$$f_q(x_m, 0) = W_Q x_m, \quad f_k(x_n, 0) = W_K x_n$$

이 두 조건을 동시에 만족하는 해를 복소수 공간에서 도출한 것이 RoPE이다. 저자들은 2차원 케이스에서 출발하여 일반해를 구한 후, 이를 고차원으로 확장하는 전략을 취했다.

---

## 방법론

### 2D 케이스: 회전의 직관

![RoPE의 구현 과정을 보여주는 다이어그램](figures/fig_1.png)
*RoPE의 구현 과정. 2차원 벡터에 위치에 비례하는 각도만큼 회전을 적용하는 원리(상단)와, 실제 쿼리/키 벡터의 인접 차원 쌍에 독립적인 회전을 적용하는 과정(하단)을 보여준다 (Su et al., 2021).*

먼저 $d = 2$ (2차원 벡터)인 경우를 살펴보자. 위치 $m$에 있는 쿼리 벡터 $q = (q_1, q_2)$에 대해 다음 회전 변환을 적용한다:

$$f_q(x_m, m) = R(m\theta) \cdot q = \begin{pmatrix} \cos m\theta & -\sin m\theta \\ \sin m\theta & \cos m\theta \end{pmatrix} \begin{pmatrix} q_1 \\ q_2 \end{pmatrix}$$

이를 전개하면:

$$f_q(x_m, m) = \begin{pmatrix} q_1 \cos m\theta - q_2 \sin m\theta \\ q_1 \sin m\theta + q_2 \cos m\theta \end{pmatrix}$$

마찬가지로 위치 $n$의 키 벡터 $k = (k_1, k_2)$에 대해:

$$f_k(x_n, n) = R(n\theta) \cdot k = \begin{pmatrix} \cos n\theta & -\sin n\theta \\ \sin n\theta & \cos n\theta \end{pmatrix} \begin{pmatrix} k_1 \\ k_2 \end{pmatrix}$$

이 두 벡터의 내적을 전개하면:

$$f_q^T f_k = q^T R(m\theta)^T R(n\theta) k = q^T R((n-m)\theta) k$$

회전 행렬의 직교성($R(\alpha)^T = R(-\alpha)$)에 의해 결과가 **상대 거리 $(m - n)\theta$**에만 의존한다. 이것이 RoPE의 핵심 원리이다. 기하학적으로 해석하면, 각 토큰의 쿼리와 키 벡터를 위치에 비례한 각도만큼 2D 평면에서 회전시키는 것이다. 두 벡터의 내적은 이들 사이의 각도 차이에 의존하므로, 결국 상대 위치에만 의존하게 된다.

### 일반적인 d차원 확장

$d$차원 벡터의 경우, 인접한 두 차원을 쌍(pair)으로 묶어 각각 독립적인 2D 회전을 적용한다. 전체 회전 행렬은 블록 대각 행렬이 된다:

$$R_{\Theta, m}^d = \text{diag}\left(R(m\theta_1), R(m\theta_2), \ldots, R(m\theta_{d/2})\right)$$

이를 완전히 풀어 쓰면:

$$R_{\Theta, m}^d = \begin{pmatrix} \cos m\theta_1 & -\sin m\theta_1 & 0 & 0 & \cdots & 0 & 0 \\ \sin m\theta_1 & \cos m\theta_1 & 0 & 0 & \cdots & 0 & 0 \\ 0 & 0 & \cos m\theta_2 & -\sin m\theta_2 & \cdots & 0 & 0 \\ 0 & 0 & \sin m\theta_2 & \cos m\theta_2 & \cdots & 0 & 0 \\ \vdots & \vdots & \vdots & \vdots & \ddots & \vdots & \vdots \\ 0 & 0 & 0 & 0 & \cdots & \cos m\theta_{d/2} & -\sin m\theta_{d/2} \\ 0 & 0 & 0 & 0 & \cdots & \sin m\theta_{d/2} & \cos m\theta_{d/2} \end{pmatrix}$$

각 주파수 $\theta_i$는 원 Transformer의 sinusoidal PE와 동일한 공식으로 정의된다:

$$\theta_i = 10000^{-2(i-1)/d}, \quad i = 1, 2, \ldots, d/2$$

이는 낮은 인덱스($i=1$)에서 높은 주파수(세밀한 위치 구분), 높은 인덱스($i=d/2$)에서 낮은 주파수(전반적인 위치 구분)를 담당하게 하여, 다양한 스케일의 위치 정보를 동시에 인코딩한다. 구체적으로, $d = 128$일 때 $\theta_1 = 1.0$ (주기 $2\pi \approx 6.28$)부터 $\theta_{64} \approx 0.0001$ (주기 $\approx 62{,}832$)까지의 범위를 커버한다.

이 블록 대각 구조의 핵심 수학적 성질:

- **직교성**: $R_{\Theta, m}^T R_{\Theta, m} = I$ (회전은 벡터의 노름을 보존)
- **역변환**: $(R_{\Theta, m})^{-1} = R_{\Theta, -m}$ (역회전은 반대 방향 회전)
- **합성**: $R_{\Theta, m} R_{\Theta, n} = R_{\Theta, m+n}$ (회전의 합성은 각도의 덧셈)

### 복소수 표현: 오일러 공식과의 연결

RoPE는 복소수 관점에서 더욱 우아하게 표현된다. $d$차원 실수 벡터를 $d/2$차원 복소수 벡터로 해석하면:

$$\mathbf{q} = (q_1 + iq_2, q_3 + iq_4, \ldots, q_{d-1} + iq_d)$$

위치 $m$에서의 RoPE 변환은 각 복소수 성분에 단위 복소수(회전자)를 곱하는 것과 동일하다:

$$f_q(\mathbf{q}, m)_j = (q_{2j-1} + iq_{2j}) \cdot e^{im\theta_j}$$

이는 **오일러 공식** $e^{i\theta} = \cos\theta + i\sin\theta$를 적용한 복소 평면 상의 회전이다. 복소수 곱셈 $z_1 \cdot z_2$는 기하학적으로 $z_1$을 $z_2$의 각도만큼 회전시키는 연산이므로, $e^{im\theta_j}$를 곱하는 것은 정확히 $m\theta_j$ 라디안만큼의 회전에 해당한다.

두 벡터의 내적은 복소수 내적의 실수 부분으로 표현된다:

$$\langle f_q(\mathbf{q}_m), f_k(\mathbf{k}_n) \rangle = \text{Re}\left[\sum_{j=1}^{d/2} (q_{2j-1} + iq_{2j})^* (k_{2j-1} + ik_{2j}) \cdot e^{i(n-m)\theta_j}\right]$$

이 결과가 $(m - n)$에만 의존하는 함수임이 명확하다. 이 복소수 표현은 단순히 수학적 우아함을 위한 것이 아니라, 실제 구현에서도 PyTorch의 `torch.view_as_complex`를 활용하여 효율적인 코드를 작성할 수 있게 해준다.

### 거리 감쇠 특성

![RoPE의 거리에 따른 내적 상한의 감쇠를 보여주는 그래프](figures/fig_2.png)
*상대 거리(relative distance)가 증가할수록 RoPE 내적의 상대적 상한(relative upper bound)이 단조 감소하는 거리 감쇠 특성. 가까운 토큰에 자연스럽게 더 높은 어텐션을 부여하는 귀납적 편향을 형성한다 (Su et al., 2021).*

RoPE는 자연스러운 거리 감쇠(distance decay) 특성을 갖는다. 내적 $\langle f_q(\mathbf{q}_m), f_k(\mathbf{k}_n) \rangle$은 $|m - n|$이 증가할수록 평균적으로 감소하는 경향을 보인다. 이는 서로 다른 주파수 $\theta_j$의 코사인 성분들이 $|m - n|$이 클 때 **상쇄 간섭(destructive interference)**을 일으키기 때문이다.

수학적으로, 쿼리와 키가 동일한 벡터일 때 내적의 기댓값은 다음과 같이 근사된다:

$$\mathbb{E}[\langle f_q, f_k \rangle] \approx \|q\|^2 \cdot \frac{1}{d/2} \sum_{j=1}^{d/2} \cos((m-n)\theta_j)$$

이 합은 $|m - n|$이 증가하면 빠르게 감소하여, 모델이 가까운 토큰에 더 높은 어텐션을 부여하는 귀납적 편향을 자연스럽게 형성한다. 그래프에서 볼 수 있듯이, 이 감쇠는 단순한 단조 감소가 아니라 진동을 수반하면서 감소하는 패턴을 보이는데, 이는 다양한 주파수 성분들의 간섭 효과를 반영한다.

### 효율적인 구현

RoPE의 실제 구현에서는 희소한 블록 대각 행렬 곱을 직접 수행하지 않고, **원소별(element-wise) 연산**으로 효율적으로 계산한다:

$$\begin{pmatrix} q_{2j-1}' \\ q_{2j}' \end{pmatrix} = \begin{pmatrix} q_{2j-1} \cos m\theta_j - q_{2j} \sin m\theta_j \\ q_{2j-1} \sin m\theta_j + q_{2j} \cos m\theta_j \end{pmatrix}$$

이를 벡터 연산으로 표현하면:

$$q' = q \odot \cos(m\Theta) + \text{rotate\_half}(q) \odot \sin(m\Theta)$$

여기서 $\text{rotate\_half}$는 인접한 원소 쌍의 순서를 바꾸고 부호를 조정하는 연산이다. 이 방식은 $O(d)$의 시간 복잡도로 동작하며, $\cos(m\Theta)$와 $\sin(m\Theta)$ 값은 모든 레이어에서 공유할 수 있으므로 한 번만 사전 계산하면 된다.

### KV Cache와의 호환성

RoPE는 KV cache 기반 추론과 자연스럽게 호환된다. 각 위치의 쿼리/키는 해당 위치에서의 회전만 적용받으므로, 새 토큰이 추가될 때 이전 토큰의 키 캐시를 재계산할 필요가 없다. 이는 상대 위치 임베딩 방식(예: Transformer-XL)과 대비되는 장점으로, 상대 PE에서는 새 토큰이 추가되면 기존 모든 토큰과의 상대 거리가 변경되어 재계산이 필요할 수 있다.

### RoPE의 주요 특성 요약

| 특성 | 설명 |
|---|---|
| 상대 위치 인코딩 | 어텐션 점수가 $m - n$에만 의존 |
| 추가 파라미터 | 0개 (순수 수학적 변환) |
| 거리 감쇠 | 상대 거리가 멀수록 어텐션 감쇠 (장거리 의존성은 유지) |
| 구현 복잡도 | $O(d)$ 원소별 연산 |
| 메모리 오버헤드 | 사전 계산된 주파수 테이블만 저장 |
| 외삽 가능성 | 학습 범위 밖 위치에 대해 부분적 일반화 가능 |
| 노름 보존 | 회전의 직교성으로 벡터 크기 불변 |
| KV Cache 호환 | 이전 토큰의 캐시 재계산 불필요 |

---

## 실험 결과

### 사전학습 수렴 비교

![BERT와 RoFormer의 MLM 사전학습 손실 비교 그래프](figures/fig_3_1.png)
*BERT(학습 가능 PE)와 RoFormer(RoPE)의 MLM 사전학습 손실 비교. RoFormer가 초기부터 더 빠르게 수렴하며 최종 손실도 낮다 (Su et al., 2024).*

![Performer에 RoPE를 적용한 경우와 미적용 경우의 학습 손실 비교 그래프](figures/fig_3_2.png)
*Performer에 RoPE를 적용한 경우와 적용하지 않은 경우의 LM 학습 손실 비교. RoPE의 효과가 표준 어텐션뿐 아니라 선형 어텐션 구조에서도 유효함을 보여준다 (Su et al., 2024).*

원 논문에서는 RoPE의 효과를 두 가지 아키텍처에서 검증했다. 첫 번째 그래프에서 RoFormer는 BERT 대비 초기 수렴 속도가 빠르고 최종 MLM 손실도 낮았다. 특히 주목할 점은 두 번째 그래프로, 선형 어텐션 기반의 Performer에서도 RoPE 적용 시 유사한 개선이 관찰된다는 것이다. 이는 RoPE의 효과가 특정 어텐션 메커니즘에 한정되지 않는 범용적인 것임을 시사한다.

### 벤치마크 성능

원 논문에서는 중국어 기계 독해(MRC) 벤치마크와 영어 GLUE 벤치마크 양쪽에서 성능을 검증했다.

**중국어 MRC 벤치마크:**

| 모델 | 위치 임베딩 | CMRC2018 (F1) | DRCD (F1) |
|---|---|---|---|
| BERT | 학습 가능 | 78.2 | 84.4 |
| RoBERTa | 학습 가능 | 80.3 | 86.6 |
| RoFormer | **RoPE** | **80.5** | **87.2** |

**영어 GLUE 벤치마크:**

| 모델 | 위치 임베딩 | MNLI (Acc) | SST-2 (Acc) | STS-B (Corr) |
|---|---|---|---|---|
| BERT-base | 학습 가능 | 84.6 | 93.5 | 85.8 |
| RoFormer-base | **RoPE** | **84.9** | **93.7** | **86.2** |

수치 자체는 크지 않지만, RoPE가 추가 파라미터 없이 일관된 성능 향상을 달성한다는 점에서 의미가 있다. 특히 문장 유사도 태스크(STS-B)에서의 향상이 두드러지는데, 상대 위치 인코딩이 문장 간 의미적 관계 파악에 도움이 된다는 것을 시사한다.

### 위치 임베딩 방법 종합 비교

| 특성 | 학습 가능 PE | Sinusoidal | Relative PE | ALiBi | **RoPE** |
|---|---|---|---|---|---|
| 학습 파라미터 | 있음 | 없음 | 있음 | 없음 | **없음** |
| 상대 위치 | 간접적 | 간접적 | 직접적 | 직접적 | **직접적** |
| 외삽 가능성 | 불가 | 제한적 | 제한적 | 우수 | **우수** |
| 구현 복잡도 | 낮음 | 낮음 | 높음 | 낮음 | **중간** |
| 표현력 | 중간 | 중간 | 높음 | 제한적 | **높음** |
| KV Cache 호환 | 호환 | 호환 | 비호환 | 호환 | **호환** |
| 적용 방식 | 가산적 | 가산적 | 가산적 | 가산적 | **곱셈적** |
| 노름 보존 | 미보존 | 미보존 | 미보존 | 해당없음 | **보존** |
| 채택 모델 | BERT, GPT-2 | 원 Transformer | Transformer-XL | BLOOM | **LLaMA, PaLM 등** |

### 긴 시퀀스에서의 외삽

RoPE는 학습 시 보지 못한 긴 시퀀스에서도 상대적으로 안정적인 성능을 보인다. 학습 시 2048 토큰으로 훈련된 모델이 4096 토큰까지는 큰 성능 저하 없이 동작하는 것이 관찰되었다. 그러나 학습 길이의 2배를 넘어서면 perplexity가 급격히 증가하여, 순수 외삽만으로는 한계가 있다.

이 외삽 한계를 극복하기 위해 이후 다양한 컨텍스트 확장 기법들이 등장했으며, 이는 RoPE가 촉발한 가장 활발한 후속 연구 분야 중 하나가 되었다.

---

## 후속 연구: 컨텍스트 확장 기법들

RoPE의 등장은 수많은 컨텍스트 확장 연구를 직접 가능하게 했다. 이들은 모두 RoPE의 주파수 구조를 조작하여 더 긴 시퀀스를 처리하는 방법을 제안한다.

**Position Interpolation (PI)**: Chen et al.(2023)이 제안. 위치 인덱스를 원래 학습 범위로 선형 보간하여 컨텍스트를 확장한다. 핵심 아이디어는 위치 $m$을 $m' = m \cdot L_{\text{train}} / L_{\text{target}}$로 스케일링하는 것이다. 학습 범위 밖의 주파수 성분이 나타나지 않으므로 안정적이지만, 근거리 위치 구분 해상도가 저하된다.

**NTK-Aware Scaling**: Reddit 커뮤니티(2023)에서 제안. 차원별 주파수를 비균일하게 스케일링한다. 고주파 성분(근거리 위치 구분)은 유지하고 저주파 성분(장거리 위치)만 확장하여 PI의 근거리 해상도 저하 문제를 보완한다.

**YaRN (Yet another RoPE extensioN)**: Peng et al.(2023)이 제안. NTK-by-parts 보간 + 어텐션 온도 스케일링으로 128K+ 컨텍스트까지 확장한다. 주파수를 고/중/저 대역으로 나누어 차등 처리하는 것이 핵심이다.

**LongRoPE**: Ding et al.(2024)이 제안. 진화적 탐색으로 최적 주파수 스케일링 인자를 찾아 256K+ 컨텍스트를 지원한다.

**비전 RoPE (2D RoPE)**: 이미지 모델에 RoPE를 2D로 확장. 높이와 너비 각각에 독립적인 RoPE를 적용하여 2차원 위치 정보를 인코딩한다 (Heo et al., ECCV 2024).

---

## 의의 및 한계

### 의의

**현대 LLM의 기반 기술**: RoPE는 2022년 이후 등장한 대부분의 주요 LLM에 채택되어 사실상의 표준 위치 임베딩이 되었다. LLaMA 시리즈, PaLM, GPT-NeoX, Falcon, Mistral, Qwen, Yi, DeepSeek 등이 모두 RoPE를 사용하며, 이러한 광범위한 채택은 이론적 우아함과 실용적 효과를 동시에 갖추었음을 증명한다.

**수학적 우아함과 분석 용이성**: 복소수 회전이라는 단순한 수학적 아이디어로 위치 인코딩 문제를 해결한다. 회전 행렬의 직교성, 합성 법칙, 노름 보존 등의 성질이 RoPE의 동작을 예측 가능하게 만들고, 후속 연구(PI, YaRN 등)의 이론적 분석을 용이하게 했다.

**파라미터 효율**: 추가 학습 파라미터 없이 위치 정보를 인코딩하므로 모델 복잡도를 전혀 증가시키지 않는다. 수십억~수천억 파라미터 규모의 대형 모델에서 특히 중요한 장점이다.

### 한계

**순수 외삽의 한계**: RoPE 자체만으로는 학습 시 본 컨텍스트의 2~4배 이상을 안정적으로 처리하기 어렵다. 고주파 성분이 학습 범위 밖에서 빠르게 발산하기 때문이며, YaRN 등의 추가 스케일링 기법이 필요하다. 구체적으로, $\theta_1 = 1.0$인 가장 고주파 성분의 주기는 $2\pi \approx 6.28$으로, 위치 7부터 이미 첫 주기를 넘어서 학습하지 않은 패턴이 나타난다.

**기저 주파수의 경험적 선택**: $\theta_{\text{base}} = 10000$이라는 기저 주파수는 경험적으로 선택된 것으로, 최적값에 대한 이론적 근거가 부족하다. 실제로 이후 모델들은 다른 값을 사용하기도 한다 (LLaMA 3: $\theta_{\text{base}} = 500000$, CodeLlama: $\theta_{\text{base}} = 1000000$). 더 큰 $\theta_{\text{base}}$는 저주파 성분의 주기를 늘려 장거리 외삽을 돕지만, 근거리 위치 구분 능력이 저하될 수 있는 트레이드오프가 존재한다.

**2D/멀티모달 확장의 복잡성**: 1D 시퀀스에 최적화되어 있어 이미지(2D) 등 다차원 위치 정보를 다루려면 별도의 확장이 필요하다. 2D RoPE에서는 차원을 절반씩 나누어 x축과 y축에 독립적으로 회전을 적용하는데, 각 축당 사용 가능한 차원이 절반으로 줄어든다.

**Value 벡터 미적용**: RoPE는 Query와 Key에만 적용되고 Value에는 적용되지 않는다. Value에 회전을 적용하면 출력 벡터의 의미가 위치에 따라 달라져 후속 레이어의 학습이 불안정해질 수 있기 때문이다. Value에 위치 정보를 인코딩하는 것이 유익할 수 있다는 연구도 있으나, 아직 표준적 방법은 확립되지 않았다.

---

## 코드 예제

### RoPE 구현 (PyTorch)

```python
import torch
import math

def precompute_freqs_cis(dim: int, end: int, theta: float = 10000.0):
    """RoPE 주파수 사전 계산.
    각 차원 쌍에 대해 서로 다른 주파수의 회전자를 생성.
    theta_i = 10000^(-2(i-1)/d)
    """
    freqs = 1.0 / (theta ** (torch.arange(0, dim, 2).float() / dim))
    t = torch.arange(end, dtype=torch.float)  # 위치 인덱스 [0, 1, ..., end-1]
    freqs = torch.outer(t, freqs)             # [end, dim/2]: 각 위치 x 각 주파수
    # 복소수 형태: e^(i * m * theta_j) = cos(m*theta_j) + i*sin(m*theta_j)
    freqs_cis = torch.polar(torch.ones_like(freqs), freqs)
    return freqs_cis  # [end, dim/2] complex64

def apply_rotary_emb(xq, xk, freqs_cis):
    """쿼리와 키에 RoPE 적용.
    실수 벡터 -> 복소수 해석 -> 회전자 곱 -> 실수 복원
    """
    # 실수 -> 복소수: (B, T, H, D) -> (B, T, H, D/2) complex
    xq_ = torch.view_as_complex(xq.float().reshape(*xq.shape[:-1], -1, 2))
    xk_ = torch.view_as_complex(xk.float().reshape(*xk.shape[:-1], -1, 2))

    # 브로드캐스팅을 위한 차원 정렬
    freqs_cis = freqs_cis[:xq.shape[1]]  # 시퀀스 길이에 맞춤
    freqs_cis = freqs_cis.unsqueeze(0).unsqueeze(2)  # (1, T, 1, D/2)

    # 핵심: 복소수 곱 = 2D 평면에서의 회전!
    xq_out = torch.view_as_real(xq_ * freqs_cis).flatten(3)
    xk_out = torch.view_as_real(xk_ * freqs_cis).flatten(3)

    return xq_out.type_as(xq), xk_out.type_as(xk)


def apply_rotary_emb_real(xq, xk, cos, sin):
    """실수 연산만으로 RoPE 적용 (복소수 미지원 환경용).
    rotate_half 방식: q' = q * cos + rotate_half(q) * sin
    """
    def rotate_half(x):
        # (q1, q2, q3, q4, ...) -> (-q2, q1, -q4, q3, ...)
        x1 = x[..., : x.shape[-1] // 2]
        x2 = x[..., x.shape[-1] // 2 :]
        return torch.cat((-x2, x1), dim=-1)

    xq_out = xq * cos + rotate_half(xq) * sin
    xk_out = xk * cos + rotate_half(xk) * sin
    return xq_out, xk_out


class RoPEAttention(torch.nn.Module):
    """RoPE를 적용한 멀티헤드 어텐션 레이어."""
    def __init__(self, d_model=4096, num_heads=32, max_seq_len=8192, theta=10000.0):
        super().__init__()
        self.num_heads = num_heads
        self.head_dim = d_model // num_heads
        self.Wq = torch.nn.Linear(d_model, d_model, bias=False)
        self.Wk = torch.nn.Linear(d_model, d_model, bias=False)
        self.Wv = torch.nn.Linear(d_model, d_model, bias=False)
        self.Wo = torch.nn.Linear(d_model, d_model, bias=False)
        # 주파수 사전 계산 (학습 불필요)
        self.register_buffer(
            'freqs_cis',
            precompute_freqs_cis(self.head_dim, max_seq_len, theta)
        )

    def forward(self, x):
        B, T, _ = x.shape
        Q = self.Wq(x).view(B, T, self.num_heads, self.head_dim)
        K = self.Wk(x).view(B, T, self.num_heads, self.head_dim)
        V = self.Wv(x).view(B, T, self.num_heads, self.head_dim)

        # RoPE 적용 (Q, K에만 - V에는 적용하지 않음)
        Q, K = apply_rotary_emb(Q, K, self.freqs_cis[:T])

        # 표준 어텐션 계산
        Q, K, V = [t.transpose(1, 2) for t in (Q, K, V)]  # (B, H, T, D)
        scale = math.sqrt(self.head_dim)
        scores = torch.matmul(Q, K.transpose(-2, -1)) / scale
        # Causal mask
        mask = torch.tril(torch.ones(T, T, device=x.device))
        scores = scores.masked_fill(mask == 0, float('-inf'))
        attn = torch.softmax(scores, dim=-1)
        out = torch.matmul(attn, V).transpose(1, 2).contiguous().view(B, T, -1)
        return self.Wo(out)


# ===== RoPE 동작 시연 =====
print("=== RoPE 주파수 시각화 ===")
dim, seq_len = 128, 2048
freqs_cis = precompute_freqs_cis(dim, seq_len)
print(f"주파수 테이블 크기: {freqs_cis.shape}")  # [2048, 64]
print(f"위치 0의 회전각 (처음 4개): {freqs_cis[0, :4].angle()}")
print(f"위치 100의 회전각 (처음 4개): {freqs_cis[100, :4].angle()}")

# 상대 위치 의존성 검증
print("\n=== 상대 위치 의존성 검증 ===")
attn = RoPEAttention(d_model=256, num_heads=4, max_seq_len=512)
x = torch.randn(1, 10, 256)
out = attn(x)
print(f"입력: {x.shape} -> 출력: {out.shape}")

# 노름 보존 검증
print("\n=== 노름 보존 검증 ===")
q = torch.randn(1, 1, 4, 64)  # (B, T=1, H=4, D=64)
freqs = precompute_freqs_cis(64, 100)
q_rot, _ = apply_rotary_emb(q, q, freqs)
print(f"회전 전 노름: {q.norm(dim=-1).mean():.4f}")
print(f"회전 후 노름: {q_rot.norm(dim=-1).mean():.4f}")
# 회전은 직교 변환이므로 두 값은 동일

# 다양한 theta 값의 주파수 범위 비교
print("\n=== theta 값별 주파수 범위 ===")
for theta in [10000, 100000, 500000]:
    freqs = 1.0 / (theta ** (torch.arange(0, 128, 2).float() / 128))
    min_period = 2 * 3.14159 / freqs.max()
    max_period = 2 * 3.14159 / freqs.min()
    print(f"theta={theta:>7}: 최소 주기={min_period:.1f}, 최대 주기={max_period:.0f}")
    # LLaMA 3는 theta=500000으로 장거리 일반화 강화
```