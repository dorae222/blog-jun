<!-- infographic-hero -->
![Information Theory for ML 핵심 요약](figures/infographic.svg)

*Figure: Information Theory for ML 한 장 요약 인포그래픽*

# 정보 이론: 엔트로피에서 KL Divergence까지

## 1. 개요: 정보 이론이 ML과 만나는 지점

**정보 이론(Information Theory)**은 1948년 클로드 섀넌(Claude Shannon)이 통신 시스템에서 정보를 얼마나 효율적으로 전달할 수 있는지를 수학적으로 정립한 분야입니다. 처음에는 전신·전화 신호의 압축과 오류 정정을 위한 이론이었지만, 오늘날 머신러닝의 여러 핵심 개념에 깊이 뿌리내리고 있습니다.

정보 이론이 ML에서 중요한 이유를 세 가지로 정리할 수 있습니다:

- **손실 함수의 수학적 근거**: 분류 문제에서 널리 쓰이는 **크로스 엔트로피 손실(Cross-Entropy Loss)**은 사실 정보 이론의 교차 엔트로피 개념을 그대로 가져온 것입니다. 왜 MSE 대신 크로스 엔트로피를 쓰는지 이해하려면 정보 이론이 필요합니다.
- **모델 평가 및 분포 비교**: **KL Divergence**는 모델이 예측한 분포와 실제 분포가 얼마나 다른지를 측정합니다. VAE(Variational Autoencoder), GAN 등 생성 모델에서 필수적인 개념입니다.
- **피처 선택(Feature Selection)**: **상호 정보량(Mutual Information)**은 두 변수 사이의 의존성을 측정하여, 어떤 피처가 예측에 유용한지 판별하는 데 활용됩니다.

이 글에서는 정보량 → 엔트로피 → 교차 엔트로피 → KL Divergence → 상호 정보량 순서로 개념을 쌓아올리며, Python 코드로 각 개념을 직접 계산해 보겠습니다.

---

## 2. 정보량(Self-Information): 드문 사건일수록 정보가 많다

### 2.1 직관적 이해

뉴스를 생각해 봅시다. "오늘도 해가 동쪽에서 떴습니다"라는 문장은 아무도 놀라지 않습니다. 반면 "서울에 7월에 눈이 내렸습니다"라는 소식은 매우 놀랍고, 그만큼 많은 정보를 담고 있습니다.

- **맑은 날**: 서울 여름에 매우 흔함. 발생 확률 $P(\text{맑음}) = 0.9$. 정보량은 작음.
- **눈 오는 날**: 서울 7월에 극히 드묾. 발생 확률 $P(\text{눈}) = 0.001$. 정보량은 큼.

이 직관을 수식으로 표현한 것이 **자기 정보량(Self-Information)** 또는 **정보량**입니다.

### 2.2 수식 정의

$$
I(x) = -\log P(x)
$$

로그의 밑은 보통 2(비트 단위) 또는 $e$(nat 단위)를 사용합니다. ML에서는 자연로그를 많이 씁니다.

이 정의가 가지는 세 가지 핵심 성질:

1. **확률이 1인 사건**: $I(x) = -\log 1 = 0$. 반드시 일어나는 사건은 정보량이 0.
2. **확률이 낮을수록**: $P(x) \to 0$이면 $I(x) \to \infty$. 드문 사건일수록 정보량이 큼.
3. **독립 사건의 결합**: $I(x, y) = I(x) + I(y)$ (독립일 때). 정보량은 더해지는 성질(additive).

| 사건 | $P(x)$ | $I(x) = -\log_2 P(x)$ (비트) |
|------|--------|-------------------------------|
| 동전 앞면 (공정한 동전) | 0.5 | 1.0 |
| 주사위 1 | 1/6 ≈ 0.167 | 2.58 |
| 복권 당첨 (100만 분의 1) | $10^{-6}$ | 19.93 |

---

![엔트로피와 KL Divergence 시각화: 분포의 불확실성과 분포 간 거리 측정](figures/entropy_kl_divergence.png)
*엔트로피와 KL Divergence: 균일 분포에서 엔트로피가 최대이며, 두 분포가 멀어질수록 KL Divergence가 증가하는 관계를 보여준다.*

## 3. 엔트로피(Entropy): 불확실성의 척도

### 3.1 개념과 수식

정보량은 특정 사건 하나에 대한 값입니다. 반면 **엔트로피(Entropy)**는 확률 분포 전체의 평균 정보량, 즉 그 분포에서 뽑은 사건이 얼마나 불확실한지를 나타냅니다.

$$
H(X) = -\sum_{x \in \mathcal{X}} P(x) \log P(x)
$$

기댓값의 관점에서 보면 $H(X) = \mathbb{E}[-\log P(X)]$입니다.

### 3.2 엔트로피의 성질

**균일 분포에서 최대, 결정론적 분포에서 0**입니다.

동전 던지기를 예로 들겠습니다:
- **공정한 동전** ($P(\text{앞}) = P(\text{뒤}) = 0.5$): $H = -(0.5 \log 0.5 + 0.5 \log 0.5) = \log 2 \approx 0.693$ nat
- **앞면만 나오는 동전** ($P(\text{앞}) = 1$): $H = -(1 \cdot \log 1) = 0$
- **편향된 동전** ($P(\text{앞}) = 0.9$): $H = -(0.9 \log 0.9 + 0.1 \log 0.1) \approx 0.325$ nat

불확실성이 클수록 엔트로피가 높습니다. $n$개의 균일한 결과를 가지는 분포의 최대 엔트로피는 $H = \log n$입니다.

### 3.3 결정 트리에서의 활용: 정보 이득

**결정 트리(Decision Tree)**는 노드를 분할할 때 **정보 이득(Information Gain)**을 최대화하는 피처를 선택합니다.

$$
\text{IG}(Y, X) = H(Y) - H(Y | X)
$$

여기서 $H(Y|X) = \sum_x P(x) H(Y|X=x)$는 조건부 엔트로피입니다. 분할 후 불확실성이 얼마나 줄었는지를 측정하여, 가장 효과적으로 클래스를 나누는 피처를 선택합니다. ID3, C4.5 알고리즘이 이 방식을 사용하고, CART 알고리즘은 지니 불순도(Gini Impurity)를 대안으로 사용합니다.

---

![교차 엔트로피 시각화: 예측 분포와 실제 분포의 차이에 따른 손실](figures/cross_entropy.png)
*교차 엔트로피: 모델의 예측 분포가 실제 분포에 가까울수록 교차 엔트로피 값이 낮아지며, 이것이 분류 손실 함수의 기반이다.*

## 4. 교차 엔트로피(Cross-Entropy): 분류 손실 함수의 정체

### 4.1 개념과 수식

**교차 엔트로피(Cross-Entropy)**는 두 확률 분포 $P$(실제 분포)와 $Q$(모델이 예측한 분포)가 주어졌을 때, $Q$를 사용하여 $P$를 인코딩하는 데 필요한 평균 비트 수입니다.

$$
H(P, Q) = -\sum_{x} P(x) \log Q(x)
$$

$P = Q$이면 $H(P, Q) = H(P)$가 되어 최솟값을 달성합니다. $Q$가 $P$에서 멀수록 교차 엔트로피는 커집니다.

### 4.2 분류 손실 함수로서의 역할

분류 문제에서 실제 레이블 분포 $P$는 원-핫(one-hot) 벡터입니다. 클래스가 $c$이면 $P(c) = 1$, 나머지 $P(k) = 0$입니다. 모델이 예측한 소프트맥스 확률을 $Q$라 할 때:

$$
H(P, Q) = -\sum_{k} P(k) \log Q(k) = -\log Q(c)
$$

즉 **정답 클래스에 할당된 확률의 음의 로그**만 남습니다. 이것이 분류 모델의 크로스 엔트로피 손실입니다. 모델이 정답 클래스에 높은 확률을 줄수록 손실이 줄어드는 직관과 일치합니다.

### 4.3 이진 분류의 경우

이진 분류에서 실제 레이블 $y \in \{0, 1\}$이고 모델 예측값이 $\hat{y} = Q(y=1)$일 때:

$$
\mathcal{L} = -\left[ y \log \hat{y} + (1 - y) \log (1 - \hat{y}) \right]
$$

- $y = 1$이면 $\mathcal{L} = -\log \hat{y}$: 모델이 1을 높게 예측할수록 손실 감소
- $y = 0$이면 $\mathcal{L} = -\log(1 - \hat{y})$: 모델이 0을 높게 예측(즉, 1을 낮게 예측)할수록 손실 감소

이것이 로지스틱 회귀와 딥러닝 이진 분류에서 쓰는 **Binary Cross-Entropy(BCE) Loss**입니다.

---

## 5. KL Divergence: 두 분포의 차이를 측정하다

### 5.1 개념과 수식

**KL Divergence(Kullback-Leibler Divergence)**는 분포 $Q$가 분포 $P$를 얼마나 잘 근사하는지 측정합니다. 달리 말하면, $P$ 대신 $Q$를 사용할 때 발생하는 평균 정보 손실량입니다.

$$
D_{KL}(P \| Q) = \sum_{x} P(x) \log \frac{P(x)}{Q(x)}
$$

연속 분포의 경우:

$$
D_{KL}(P \| Q) = \int_{-\infty}^{\infty} p(x) \log \frac{p(x)}{q(x)} \, dx
$$

### 5.2 핵심 성질

1. **비음수성**: $D_{KL}(P \| Q) \geq 0$. 등호는 $P = Q$일 때만 성립합니다(깁스 부등식, Gibbs' Inequality).
2. **비대칭성**: $D_{KL}(P \| Q) \neq D_{KL}(Q \| P)$. 이 점 때문에 KL Divergence는 엄밀한 의미의 거리(metric)가 아닙니다.
   - $D_{KL}(P \| Q)$: $P$를 기준으로 $Q$의 부족함을 측정. **forward KL**.
   - $D_{KL}(Q \| P)$: $Q$를 기준으로 $P$의 부족함을 측정. **reverse KL**.
3. **$Q(x)=0$인 지점에서 $P(x)>0$이면 무한대**: 실제 분포에서 일어나는 사건을 모델 분포가 전혀 지원하지 않으면 KL Divergence는 무한해집니다.

### 5.3 교차 엔트로피와의 관계

$$
H(P, Q) = H(P) + D_{KL}(P \| Q)
$$

교차 엔트로피는 실제 분포의 엔트로피(상수)에 KL Divergence를 더한 값입니다. 따라서 **교차 엔트로피를 최소화하는 것은 KL Divergence를 최소화하는 것과 동치**입니다. 학습 레이블 $P$의 엔트로피는 학습 과정에서 변하지 않으므로, 모델을 학습할 때 크로스 엔트로피 손실을 줄이는 것이 곧 예측 분포를 실제 분포에 가깝게 만드는 것입니다.

### 5.4 ML에서의 활용

- **VAE(Variational Autoencoder)**: ELBO(Evidence Lower Bound) 목적함수에서 잠재 변수 분포 $q(z|x)$를 사전 분포 $p(z)$에 가깝게 만들기 위해 $D_{KL}(q(z|x) \| p(z))$를 최소화합니다.
- **정책 최적화(Policy Optimization)**: PPO(Proximal Policy Optimization) 등 강화학습 알고리즘에서 새로운 정책이 이전 정책에서 너무 멀리 벗어나지 않도록 KL Divergence로 제약을 줍니다.
- **지식 증류(Knowledge Distillation)**: 교사 모델 출력 분포와 학생 모델 출력 분포 사이의 KL Divergence를 최소화합니다.

---

## 6. 상호 정보량(Mutual Information): 두 변수가 서로 얼마나 많은 정보를 공유하는가

### 6.1 개념과 수식

**상호 정보량(Mutual Information, MI)**은 한 확률변수를 알았을 때 다른 확률변수의 불확실성이 얼마나 줄어드는지를 측정합니다.

$$
I(X; Y) = H(X) - H(X | Y) = H(Y) - H(Y | X)
$$

또는 KL Divergence를 사용한 동치 표현:

$$
I(X; Y) = D_{KL}(P(X, Y) \| P(X) P(Y))
$$

결합 분포 $P(X, Y)$와 두 주변 분포의 곱 $P(X)P(Y)$ 사이의 KL Divergence로도 해석됩니다. $X$와 $Y$가 독립이면 $P(X,Y) = P(X)P(Y)$이므로 $I(X;Y) = 0$입니다.

### 6.2 성질

- **비음수성**: $I(X; Y) \geq 0$
- **대칭성**: $I(X; Y) = I(Y; X)$ (엔트로피와 달리 대칭)
- **상한**: $I(X; Y) \leq \min(H(X), H(Y))$

### 6.3 피처 선택에서의 활용

피처 $X_i$와 타겟 $Y$ 사이의 상호 정보량 $I(X_i; Y)$를 계산하면, 해당 피처가 타겟 예측에 얼마나 유용한지를 측정할 수 있습니다.

- $I(X_i; Y) = 0$: 피처와 타겟이 완전히 독립 → 해당 피처는 예측에 도움이 안 됨
- $I(X_i; Y)$가 클수록: 피처가 타겟에 대한 정보를 많이 담고 있음 → 중요한 피처

`sklearn.feature_selection`의 `mutual_info_classif`, `mutual_info_regression` 함수가 이 방법을 구현하고 있습니다. 선형 상관관계를 잡지 못하는 피어슨 상관계수와 달리, 상호 정보량은 **비선형 의존성**도 탐지할 수 있습니다.

---

## 7. Python 코드: numpy와 scipy로 직접 계산하기

```python
import numpy as np
from scipy.stats import entropy as scipy_entropy
from scipy.special import kl_div

# ── 1. 정보량(Self-Information) ──────────────────────────────────────────
def self_information(p):
    """단일 사건의 정보량 (nat 단위, 자연로그 사용)"""
    assert 0 < p <= 1, "확률은 (0, 1] 범위여야 합니다"
    return -np.log(p)

print("=== 정보량 ===")
print(f"맑은 날 (P=0.9):  I = {self_information(0.9):.4f} nat")
print(f"비 오는 날 (P=0.3): I = {self_information(0.3):.4f} nat")
print(f"눈 오는 날 (P=0.01): I = {self_information(0.01):.4f} nat")

# ── 2. 엔트로피(Entropy) ──────────────────────────────────────────────────
def entropy(probs):
    """이산 분포의 엔트로피"""
    probs = np.array(probs, dtype=float)
    probs = probs[probs > 0]  # log(0) 방지
    return -np.sum(probs * np.log(probs))

print("\n=== 엔트로피 ===")
# 균일 분포 (최대 엔트로피)
uniform_4 = [0.25, 0.25, 0.25, 0.25]
print(f"균일 분포 [0.25, 0.25, 0.25, 0.25]: H = {entropy(uniform_4):.4f} nat")
print(f"이론값 log(4):                       H = {np.log(4):.4f} nat")

# 편향된 분포
skewed = [0.7, 0.1, 0.1, 0.1]
print(f"편향 분포 [0.7, 0.1, 0.1, 0.1]:     H = {entropy(skewed):.4f} nat")

# 결정론적 분포 (최소 엔트로피)
deterministic = [1.0, 0.0, 0.0, 0.0]
print(f"결정론적 분포 [1, 0, 0, 0]:           H = {entropy(deterministic):.4f} nat")

# scipy 검증
print(f"\n[scipy 검증] 균일 분포 H = {scipy_entropy(uniform_4):.4f} nat")

# ── 3. 교차 엔트로피(Cross-Entropy) ─────────────────────────────────────
def cross_entropy(p, q):
    """
    H(P, Q) = -sum P(x) log Q(x)
    P: 실제 분포 (레이블)
    Q: 예측 분포 (모델 출력)
    """
    p, q = np.array(p, dtype=float), np.array(q, dtype=float)
    # q가 0인 곳에서 p가 0이어야 유한값을 보장
    mask = p > 0
    return -np.sum(p[mask] * np.log(q[mask]))

print("\n=== 교차 엔트로피 ===")
# 실제 레이블: 클래스 2가 정답 (원-핫)
p_true = [0.0, 0.0, 1.0, 0.0]

# 좋은 예측: 클래스 2에 높은 확률
q_good = [0.05, 0.05, 0.85, 0.05]
# 나쁜 예측: 클래스 0에 높은 확률
q_bad  = [0.80, 0.05, 0.10, 0.05]

print(f"좋은 예측 H(P, Q_good) = {cross_entropy(p_true, q_good):.4f} nat")
print(f"나쁜 예측 H(P, Q_bad)  = {cross_entropy(p_true, q_bad):.4f} nat")

# 이진 분류 BCE Loss
def binary_cross_entropy(y_true, y_pred, eps=1e-15):
    y_pred = np.clip(y_pred, eps, 1 - eps)
    return -np.mean(y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred))

y_true = np.array([1, 0, 1, 1, 0])
y_pred_good = np.array([0.9, 0.1, 0.8, 0.95, 0.05])
y_pred_bad  = np.array([0.3, 0.7, 0.4, 0.2, 0.6])

print(f"\n이진 BCE (좋은 예측): {binary_cross_entropy(y_true, y_pred_good):.4f}")
print(f"이진 BCE (나쁜 예측): {binary_cross_entropy(y_true, y_pred_bad):.4f}")

# ── 4. KL Divergence ──────────────────────────────────────────────────────
def kl_divergence(p, q, eps=1e-15):
    """
    D_KL(P || Q) = sum P(x) log(P(x)/Q(x))
    """
    p, q = np.array(p, dtype=float), np.array(q, dtype=float)
    q = np.clip(q, eps, None)  # log(0) 방지
    mask = p > 0
    return np.sum(p[mask] * np.log(p[mask] / q[mask]))

print("\n=== KL Divergence ===")
P = [0.4, 0.3, 0.2, 0.1]
Q = [0.25, 0.25, 0.25, 0.25]  # 균일 분포

kl_pq = kl_divergence(P, Q)
kl_qp = kl_divergence(Q, P)
print(f"D_KL(P || Q) = {kl_pq:.4f} nat")
print(f"D_KL(Q || P) = {kl_qp:.4f} nat")
print(f"비대칭성 확인: D_KL(P||Q) != D_KL(Q||P) => {kl_pq:.4f} != {kl_qp:.4f}")

# 교차 엔트로피 = 엔트로피 + KL Divergence 검증
h_p  = entropy(P)
ce_pq = cross_entropy(P, Q)
print(f"\nH(P)               = {h_p:.4f}")
print(f"D_KL(P || Q)       = {kl_pq:.4f}")
print(f"H(P) + D_KL(P||Q)  = {h_p + kl_pq:.4f}")
print(f"H(P, Q) (직접 계산) = {ce_pq:.4f}")
print("=> H(P, Q) = H(P) + D_KL(P || Q) 성립!")

# scipy로 검증
print(f"\n[scipy 검증] D_KL(P||Q) = {scipy_entropy(P, Q):.4f}")

# ── 5. 상호 정보량(Mutual Information) ───────────────────────────────────
from sklearn.feature_selection import mutual_info_classif
from sklearn.datasets import load_iris

print("\n=== 상호 정보량 (Iris 데이터셋) ===")
iris = load_iris()
X, y = iris.data, iris.target
feature_names = iris.feature_names

mi_scores = mutual_info_classif(X, y, random_state=42)
for name, score in zip(feature_names, mi_scores):
    print(f"{name:30s}: I(X;Y) = {score:.4f}")

print("\n=> I(X;Y)가 클수록 해당 피처가 타겟 분류에 더 유용")
```

```output
=== 정보량 ===
맑은 날 (P=0.9):  I = 0.1054 nat
비 오는 날 (P=0.3): I = 1.2040 nat
눈 오는 날 (P=0.01): I = 4.6052 nat

=== 엔트로피 ===
균일 분포 [0.25, 0.25, 0.25, 0.25]: H = 1.3863 nat
이론값 log(4):                       H = 1.3863 nat
편향 분포 [0.7, 0.1, 0.1, 0.1]:     H = 0.9404 nat
결정론적 분포 [1, 0, 0, 0]:           H = -0.0000 nat

[scipy 검증] 균일 분포 H = 1.3863 nat

=== 교차 엔트로피 ===
좋은 예측 H(P, Q_good) = 0.1625 nat
나쁜 예측 H(P, Q_bad)  = 2.3026 nat

이진 BCE (좋은 예측): 0.1073
이진 BCE (나쁜 예측): 1.1700

=== KL Divergence ===
D_KL(P || Q) = 0.1064 nat
D_KL(Q || P) = 0.1218 nat
비대칭성 확인: D_KL(P||Q) != D_KL(Q||P) => 0.1064 != 0.1218

H(P)               = 1.2799
D_KL(P || Q)       = 0.1064
H(P) + D_KL(P||Q)  = 1.3863
H(P, Q) (직접 계산) = 1.3863
=> H(P, Q) = H(P) + D_KL(P || Q) 성립!

[scipy 검증] D_KL(P||Q) = 0.1064

=== 상호 정보량 (Iris 데이터셋) ===
sepal length (cm)             : I(X;Y) = 0.5114
sepal width (cm)              : I(X;Y) = 0.2994
petal length (cm)             : I(X;Y) = 0.9926
petal width (cm)              : I(X;Y) = 0.9856

=> I(X;Y)가 클수록 해당 피처가 타겟 분류에 더 유용
```

위 코드를 실행하면 다음과 같은 결과를 확인할 수 있습니다:

- **정보량**: 눈 오는 날($P=0.01$)의 정보량이 맑은 날($P=0.9$)보다 약 13배 큼
- **엔트로피**: 균일 분포의 엔트로피($\log 4 \approx 1.386$)가 가장 크고, 결정론적 분포는 0
- **교차 엔트로피**: 나쁜 예측의 손실값이 좋은 예측보다 훨씬 큼
- **KL Divergence 비대칭성**: $D_{KL}(P\|Q) \neq D_{KL}(Q\|P)$ 직접 확인
- **$H(P,Q) = H(P) + D_{KL}(P\|Q)$** 관계가 수치적으로 정확히 성립
- **Iris 상호 정보량**: petal length/width가 sepal features보다 클래스 구분에 더 유용

---

## 정리

정보 이론의 핵심 개념과 ML에서의 활용을 정리하면 다음과 같습니다:

| 개념 | 수식 | ML 활용 |
|------|------|----------|
| 정보량 | $I(x) = -\log P(x)$ | 드문 사건의 중요성 모델링 |
| 엔트로피 | $H(X) = -\sum P(x) \log P(x)$ | 결정 트리 분할 기준(정보 이득) |
| 교차 엔트로피 | $H(P,Q) = -\sum P(x)\log Q(x)$ | 분류 손실 함수 |
| KL Divergence | $D_{KL}(P\|Q) = \sum P(x)\log\frac{P(x)}{Q(x)}$ | 분포 비교, VAE, 지식 증류 |
| 상호 정보량 | $I(X;Y) = H(X) - H(X\|Y)$ | 피처 선택, 의존성 측정 |

가장 중요한 통찰은 **교차 엔트로피 최소화 = KL Divergence 최소화**라는 점입니다. 딥러닝 분류 모델을 학습할 때 크로스 엔트로피 손실을 줄이는 행위는, 수학적으로 모델의 예측 분포를 실제 데이터 분포에 최대한 가깝게 만드는 것입니다. 정보 이론의 언어로 이 사실을 이해하면, 손실 함수 설계에서 더 근거 있는 선택을 할 수 있습니다.