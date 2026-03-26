## 개요: 왜 선형대수가 ML의 언어인가

머신러닝은 본질적으로 **고차원 데이터를 다루는 학문**입니다. 1만 개의 픽셀로 이루어진 이미지, 수백 개의 피처를 가진 테이블 데이터, 수만 개의 토큰으로 구성된 언어 모델 — 이 모든 것들은 수치(숫자)의 배열로 표현됩니다. 바로 여기서 **선형대수(Linear Algebra)**가 등장합니다.

선형대수는 벡터와 행렬을 다루는 수학 분야입니다. ML에서 선형대수가 핵심인 이유는 명확합니다:

- **데이터 표현**: 하나의 데이터 샘플은 벡터, 전체 데이터셋은 행렬로 표현됩니다.
- **모델 연산**: 신경망의 순전파(Forward Pass)는 행렬 곱의 연쇄입니다.
- **최적화**: 그래디언트(Gradient)는 벡터이며, 헤시안(Hessian)은 행렬입니다.
- **차원 축소**: PCA, SVD 같은 핵심 알고리즘의 수학적 토대입니다.

선형대수를 모르고 ML을 배우는 것은 문법을 모르고 외국어를 배우는 것과 같습니다. 표면적인 사용은 가능하지만, 깊은 이해와 응용은 불가능합니다. 이 글에서는 ML 실무에서 반드시 알아야 할 선형대수 개념을 직관과 함께 정리합니다.

---

## 벡터와 행렬 기초

### 벡터 (Vector): 데이터 포인트를 표현하는 기본 단위

**벡터(Vector)**는 숫자의 순서 있는 배열입니다. ML에서 하나의 데이터 샘플은 $n$차원 열벡터(Column Vector)로 표현합니다:

$$\mathbf{x} = \begin{bmatrix} x_1 \\ x_2 \\ \vdots \\ x_n \end{bmatrix} \in \mathbb{R}^n$$

예를 들어, 키와 몸무게로 사람을 표현하면 $\mathbf{x} = [175, 70]^T$이고, 28×28 흑백 이미지는 784차원 벡터가 됩니다. 신경망의 가중치(Weight)도 벡터 혹은 행렬로 표현됩니다.

### 내적 (Dot Product): 유사도의 수학적 표현

두 벡터 $\mathbf{a}, \mathbf{b} \in \mathbb{R}^n$의 **내적(Dot Product)**은 다음과 같이 정의됩니다:

$$\mathbf{a} \cdot \mathbf{b} = \mathbf{a}^T \mathbf{b} = \sum_{i=1}^{n} a_i b_i = \|\mathbf{a}\| \|\mathbf{b}\| \cos\theta$$

여기서 $\theta$는 두 벡터 사이의 각도입니다. 내적이 ML에서 중요한 이유는 **유사도(Similarity)**를 측정하기 때문입니다:

- 두 벡터의 방향이 같을수록($\theta \approx 0$) 내적값이 커집니다.
- 직교($\theta = 90°$)이면 내적이 0, 즉 두 벡터는 무관합니다.
- 코사인 유사도(Cosine Similarity): $\text{sim}(\mathbf{a}, \mathbf{b}) = \frac{\mathbf{a} \cdot \mathbf{b}}{\|\mathbf{a}\| \|\mathbf{b}\|}$

선형 회귀, SVM, Attention 메커니즘 등 핵심 ML 알고리즘이 모두 내적을 기반으로 동작합니다.

### 노름 (Norm): 벡터의 크기 측정

**노름(Norm)**은 벡터의 "길이" 또는 "크기"를 나타냅니다. ML에서 자주 사용되는 두 가지 노름은:

$$\|\mathbf{x}\|_1 = \sum_{i=1}^{n} |x_i| \quad \text{(L1 노름, Manhattan Distance)}$$

$$\|\mathbf{x}\|_2 = \sqrt{\sum_{i=1}^{n} x_i^2} \quad \text{(L2 노름, Euclidean Distance)}$$

L1 노름은 Lasso 정규화에, L2 노름은 Ridge 정규화와 그래디언트 계산에 사용됩니다. 규제(Regularization) 관점에서 L1은 희소성(Sparsity)을 유도하고, L2는 가중치를 고르게 작게 만듭니다.

### 행렬 (Matrix): 선형 변환의 표현

**행렬(Matrix)**은 벡터를 2차원으로 확장한 수의 직사각형 배열입니다. $m \times n$ 행렬 $A$는:

$$A = \begin{bmatrix} a_{11} & a_{12} & \cdots & a_{1n} \\ a_{21} & a_{22} & \cdots & a_{2n} \\ \vdots & \vdots & \ddots & \vdots \\ a_{m1} & a_{m2} & \cdots & a_{mn} \end{bmatrix} \in \mathbb{R}^{m \times n}$$

ML 데이터셋 $X \in \mathbb{R}^{N \times d}$는 $N$개의 샘플과 $d$개의 피처를 가진 행렬입니다.

**행렬 곱(Matrix Multiplication)**은 선형 변환의 합성을 표현합니다. $A \in \mathbb{R}^{m \times k}$, $B \in \mathbb{R}^{k \times n}$일 때 $C = AB \in \mathbb{R}^{m \times n}$이며:

$$c_{ij} = \sum_{l=1}^{k} a_{il} b_{lj}$$

직관적으로, 행렬 곱은 공간을 늘리고, 회전시키고, 투영하는 변환의 연속입니다. 신경망의 각 레이어는 이러한 선형 변환을 수행합니다.

---

## 행렬 분해 (Matrix Decomposition)

행렬 분해는 복잡한 행렬을 의미 있는 구성 요소로 분리하는 기법입니다. ML에서 특히 중요한 세 가지를 살펴봅니다.

### 고유값 분해 (Eigendecomposition)

정방 행렬(Square Matrix) $A \in \mathbb{R}^{n \times n}$에 대해, 다음을 만족하는 벡터 $\mathbf{v}$와 스칼라 $\lambda$가 존재합니다:

$$A\mathbf{v} = \lambda \mathbf{v}$$

$\mathbf{v}$를 **고유벡터(Eigenvector)**, $\lambda$를 **고유값(Eigenvalue)**이라 합니다. 직관적으로, 고유벡터는 행렬 $A$가 표현하는 선형 변환에 의해 방향이 변하지 않는 벡터이고, 고유값은 그 방향으로의 스케일(크기 변화)을 나타냅니다.

$A$가 $n$개의 선형 독립적인 고유벡터를 가지면, **고유값 분해(Eigendecomposition)**가 가능합니다:

$$A = Q \Lambda Q^{-1}$$

여기서 $Q$의 열들은 고유벡터들, $\Lambda$는 대각선에 고유값이 있는 대각 행렬입니다. 대칭 행렬(Symmetric Matrix, $A = A^T$)의 경우 $Q^{-1} = Q^T$가 되어 $A = Q \Lambda Q^T$가 됩니다.

**ML에서의 활용**: 공분산 행렬의 고유값 분해는 PCA의 수학적 토대입니다. 큰 고유값에 대응하는 고유벡터가 데이터의 주요 분산 방향(주성분)을 나타냅니다.

### 특이값 분해 (Singular Value Decomposition, SVD)

고유값 분해는 정방 행렬에만 적용 가능하지만, **SVD(Singular Value Decomposition)**는 임의의 행렬 $A \in \mathbb{R}^{m \times n}$에 적용할 수 있는 더 일반적인 분해입니다:

$$A = U \Sigma V^T$$

각 행렬의 의미:
- $U \in \mathbb{R}^{m \times m}$: 좌 특이벡터(Left Singular Vectors), 열이 정규직교 기저
- $\Sigma \in \mathbb{R}^{m \times n}$: 특이값(Singular Values) $\sigma_1 \geq \sigma_2 \geq \cdots \geq 0$이 대각선에 위치
- $V^T \in \mathbb{R}^{n \times n}$: 우 특이벡터(Right Singular Vectors)의 전치

특이값 $\sigma_i$는 해당 성분이 데이터를 얼마나 잘 설명하는지를 나타냅니다. 상위 $k$개의 특이값만 사용하면 **절단 SVD(Truncated SVD)**를 통해 차원 축소를 달성할 수 있습니다:

$$A \approx U_k \Sigma_k V_k^T$$

이것이 PCA와 정확히 같은 결과를 만들어냅니다. 사실 PCA는 데이터 행렬의 SVD를 통해 구현됩니다.

**ML에서의 활용**:
- 차원 축소(PCA와 동치)
- 추천 시스템의 행렬 인수분해(Matrix Factorization)
- 이미지 압축: 상위 $k$개 특이값만 보존
- 노이즈 제거(Denoising)

### 양의 정부호 행렬 (Positive Definite Matrix)

**양의 정부호 행렬(Positive Definite Matrix)**은 임의의 영벡터가 아닌 벡터 $\mathbf{z}$에 대해 다음을 만족하는 대칭 행렬입니다:

$$\mathbf{z}^T A \mathbf{z} > 0 \quad \forall \mathbf{z} \neq \mathbf{0}$$

동치 조건: 모든 고유값이 양수($\lambda_i > 0$)입니다.

**공분산 행렬(Covariance Matrix)**은 항상 양의 반정부호(Positive Semi-Definite, PSD) 행렬입니다. 데이터 행렬 $X$에서 공분산 행렬은:

$$\Sigma = \frac{1}{N-1} (X - \bar{X})^T (X - \bar{X})$$

양의 정부호 성질은 머신러닝의 손실 함수가 볼록(Convex)임을 보장하고, 고유값 분해 시 항상 실수 고유값을 갖도록 보장합니다.

---

## 그래디언트와 행렬 미분

최적화를 위해서는 파라미터에 대한 손실 함수의 미분이 필요합니다. 벡터와 행렬로 확장된 미분이 **행렬 미분(Matrix Calculus)**입니다.

### 그래디언트 (Gradient)

스칼라 함수 $f(\mathbf{w})$의 벡터 $\mathbf{w} \in \mathbb{R}^n$에 대한 **그래디언트(Gradient)**는 각 성분의 편미분으로 구성된 벡터입니다:

$$\nabla_{\mathbf{w}} f = \frac{\partial f}{\partial \mathbf{w}} = \begin{bmatrix} \frac{\partial f}{\partial w_1} \\ \frac{\partial f}{\partial w_2} \\ \vdots \\ \frac{\partial f}{\partial w_n} \end{bmatrix}$$

그래디언트는 함수가 가장 가파르게 증가하는 방향을 가리킵니다. 경사하강법(Gradient Descent)은 그래디언트의 반대 방향으로 파라미터를 업데이트하여 손실을 최소화합니다:

$$\mathbf{w}_{t+1} = \mathbf{w}_t - \eta \nabla_{\mathbf{w}} \mathcal{L}(\mathbf{w}_t)$$

### 선형 회귀 손실의 그래디언트 유도

선형 회귀의 MSE 손실 $\mathcal{L} = \|\mathbf{y} - X\mathbf{w}\|^2$의 그래디언트를 유도하면:

$$\frac{\partial}{\partial \mathbf{w}} \|\mathbf{y} - X\mathbf{w}\|^2 = \frac{\partial}{\partial \mathbf{w}} (\mathbf{y} - X\mathbf{w})^T(\mathbf{y} - X\mathbf{w}) = -2X^T(\mathbf{y} - X\mathbf{w})$$

이 그래디언트를 0으로 놓으면 닫힌형(Closed-form) 해를 구할 수 있습니다(정규 방정식):

$$X^T(\mathbf{y} - X\hat{\mathbf{w}}) = 0 \implies \hat{\mathbf{w}} = (X^TX)^{-1}X^T\mathbf{y}$$

### 야코비안과 헤시안 (Jacobian & Hessian)

**야코비안(Jacobian)**: 벡터 함수 $\mathbf{f}: \mathbb{R}^n \rightarrow \mathbb{R}^m$의 1차 편미분으로 구성된 $m \times n$ 행렬입니다.

$$J = \frac{\partial \mathbf{f}}{\partial \mathbf{x}} = \begin{bmatrix} \frac{\partial f_1}{\partial x_1} & \cdots & \frac{\partial f_1}{\partial x_n} \\ \vdots & \ddots & \vdots \\ \frac{\partial f_m}{\partial x_1} & \cdots & \frac{\partial f_m}{\partial x_n} \end{bmatrix}$$

신경망의 역전파(Backpropagation)는 연쇄 법칙(Chain Rule)을 야코비안의 곱으로 표현합니다.

**헤시안(Hessian)**: 스칼라 함수의 2차 편미분으로 구성된 $n \times n$ 대칭 행렬입니다.

$$H = \nabla^2 f = \begin{bmatrix} \frac{\partial^2 f}{\partial x_1^2} & \cdots & \frac{\partial^2 f}{\partial x_1 \partial x_n} \\ \vdots & \ddots & \vdots \\ \frac{\partial^2 f}{\partial x_n \partial x_1} & \cdots & \frac{\partial^2 f}{\partial x_n^2} \end{bmatrix}$$

헤시안의 고유값이 모두 양수이면 해당 점이 극솟값(Local Minimum)임을 나타냅니다. 2차 최적화 방법(Newton's Method)에서 핵심적으로 사용됩니다.

---

## ML에서의 활용 예시

### 1. 선형 회귀: 정규 방정식

$N$개의 데이터 포인트 $\{(\mathbf{x}_i, y_i)\}$에 대해, 선형 회귀 모델은 $\hat{y} = \mathbf{w}^T \mathbf{x}$로 예측합니다. 행렬 형태로 쓰면 $\hat{\mathbf{y}} = X\mathbf{w}$이고, MSE를 최소화하는 해석적 해(Analytical Solution)는:

$$\hat{\mathbf{w}} = (X^TX)^{-1}X^T\mathbf{y}$$

여기서 $(X^TX)^{-1}X^T$를 **무어-펜로즈 유사역행렬(Moore-Penrose Pseudoinverse)**이라 합니다. $X^TX$가 역행렬을 가지려면 열들이 선형 독립이어야 하며, 그렇지 않으면 정규화(Regularization)가 필요합니다.

### 2. PCA: 공분산 행렬 고유값 분해

**주성분 분석(Principal Component Analysis, PCA)**의 알고리즘:

1. 데이터 중심화: $\tilde{X} = X - \bar{X}$
2. 공분산 행렬 계산: $\Sigma = \frac{1}{N-1} \tilde{X}^T \tilde{X}$
3. 고유값 분해: $\Sigma = Q \Lambda Q^T$
4. 상위 $k$개 고유벡터 선택: $Q_k = [\mathbf{q}_1, \mathbf{q}_2, \ldots, \mathbf{q}_k]$
5. 차원 축소: $Z = \tilde{X} Q_k \in \mathbb{R}^{N \times k}$

고유값이 클수록 해당 주성분이 데이터의 분산을 더 많이 설명합니다. **설명된 분산 비율(Explained Variance Ratio)**:

$$\text{EVR}_k = \frac{\lambda_k}{\sum_{i=1}^{n} \lambda_i}$$

### 3. 신경망: 행렬 곱의 연쇄

$L$개의 레이어를 가진 신경망의 순전파(Forward Pass)는 행렬 곱의 연쇄입니다. $l$번째 레이어의 출력:

$$\mathbf{h}^{(l)} = \sigma(W^{(l)} \mathbf{h}^{(l-1)} + \mathbf{b}^{(l)})$$

여기서 $W^{(l)}$은 가중치 행렬, $\mathbf{b}^{(l)}$은 편향 벡터, $\sigma$는 비선형 활성화 함수입니다. 가중치 행렬의 특이값 분포는 학습 안정성(Training Stability)과 직결됩니다. 특이값이 너무 크면 그래디언트 폭발(Gradient Explosion), 너무 작으면 그래디언트 소실(Gradient Vanishing)이 발생합니다.

---

## Python NumPy 코드 예시

```python
import numpy as np
from numpy import linalg as LA

# --- 고유값 분해 예시 ---
# 대칭 행렬(공분산 행렬 역할) 생성
np.random.seed(42)
X = np.random.randn(100, 3)  # 100개 샘플, 3개 피처

# 공분산 행렬 계산
X_centered = X - X.mean(axis=0)
cov_matrix = (X_centered.T @ X_centered) / (len(X) - 1)
print("공분산 행렬 (Covariance Matrix):")
print(cov_matrix)

# 고유값 분해 수행
eigenvalues, eigenvectors = LA.eigh(cov_matrix)  # 대칭 행렬엔 eigh 사용
# eigh는 고유값을 오름차순으로 반환하므로 뒤집기
eigenvalues = eigenvalues[::-1]
eigenvectors = eigenvectors[:, ::-1]

print("\n고유값 (Eigenvalues):", eigenvalues)
print("설명된 분산 비율 (EVR):",
      eigenvalues / eigenvalues.sum())

# 상위 2개 주성분으로 차원 축소
k = 2
Z_pca = X_centered @ eigenvectors[:, :k]  # (100, 3) @ (3, 2) = (100, 2)
print(f"\nPCA 후 데이터 형태: {X_centered.shape} → {Z_pca.shape}")

# --- SVD 예시 ---
# 직사각형 행렬에도 적용 가능
A = np.random.randn(5, 4)  # 5행 4열 행렬
U, sigma, Vt = LA.svd(A, full_matrices=True)

print("\n원본 행렬 A:")
print(A)
print("\n특이값 (Singular Values):", sigma)

# 절단 SVD로 행렬 근사 (k=2)
k = 2
A_approx = U[:, :k] @ np.diag(sigma[:k]) @ Vt[:k, :]
print(f"\n상위 {k}개 특이값으로 근사한 A:")
print(A_approx)
print(f"근사 오차 (Frobenius Norm): {LA.norm(A - A_approx):.4f}")

# --- 내적과 코사인 유사도 ---
a = np.array([1.0, 2.0, 3.0])
b = np.array([4.0, 5.0, 6.0])

dot_product = np.dot(a, b)
cosine_sim = dot_product / (LA.norm(a) * LA.norm(b))
print(f"\n내적 (Dot Product): {dot_product:.2f}")
print(f"코사인 유사도 (Cosine Similarity): {cosine_sim:.4f}")

# --- 정규 방정식으로 선형 회귀 ---
# 데이터 생성: y = 2x_1 + 3x_2 + 노이즈
X_reg = np.column_stack([
    np.ones(100),          # 편향 항
    np.random.randn(100),  # 특성 1
    np.random.randn(100),  # 특성 2
])
true_w = np.array([1.0, 2.0, 3.0])
y_reg = X_reg @ true_w + 0.1 * np.random.randn(100)

# 정규 방정식: w_hat = (X^T X)^{-1} X^T y
w_hat = LA.pinv(X_reg.T @ X_reg) @ X_reg.T @ y_reg
print(f"\n정규 방정식으로 추정한 가중치: {w_hat}")
print(f"실제 가중치:                  {true_w}")
```

```output
공분산 행렬 (Covariance Matrix):
[[ 0.68029352 -0.03927641 -0.1108006 ]
 [-0.03927641  0.9586369  -0.1348594 ]
 [-0.1108006  -0.1348594   1.23856849]]

고유값 (Eigenvalues): [1.30567458 0.92688528 0.64493904]
설명된 분산 비율 (EVR): [0.45375329 0.3221149  0.22413181]

PCA 후 데이터 형태: (100, 3) → (100, 2)

원본 행렬 A:
[[-0.82899501 -0.56018104  0.74729361  0.61037027]
 [-0.02090159  0.11732738  1.2776649  -0.59157139]
 [ 0.54709738 -0.20219265 -0.2176812   1.09877685]
 [ 0.82541635  0.81350964  1.30547881  0.02100384]
 [ 0.68195297 -0.31026676  0.32416635 -0.13014305]]

특이값 (Singular Values): [2.14797831 1.49484157 1.39080549 0.68701204]

상위 2개 특이값으로 근사한 A:
[[-0.91653207 -0.33490014  0.48955608 -0.1579898 ]
 [-0.06866921  0.21018291  1.32197439 -0.37399277]
 [ 0.42775181  0.0997765  -0.5372658   0.16074125]
 [ 0.90978596  0.64787056  1.23725818 -0.32871956]
 [ 0.42491854  0.24132542  0.24317919 -0.05922551]]
근사 오차 (Frobenius Norm): 1.5512

내적 (Dot Product): 32.00
코사인 유사도 (Cosine Similarity): 0.9746

정규 방정식으로 추정한 가중치: [0.99480991 2.01478173 2.98993248]
실제 가중치:                  [1. 2. 3.]
```

위 코드는 선형대수의 핵심 연산을 NumPy로 직접 구현하는 방법을 보여줍니다. 실무에서는 `sklearn.decomposition.PCA` 같은 라이브러리를 사용하지만, 내부 동작을 이해하면 파라미터 튜닝과 디버깅이 훨씬 쉬워집니다.

---

## 정리

선형대수는 ML 알고리즘의 언어입니다. 이 글에서 다룬 핵심 내용을 정리하면:

1. **벡터와 내적**: 데이터를 표현하고 유사도를 측정하는 기본 도구
2. **노름**: 벡터의 크기를 측정하며, 정규화 기법의 수학적 토대
3. **행렬 곱**: 선형 변환의 합성, 신경망 순전파의 본질
4. **고유값 분해**: 행렬이 표현하는 변환의 "주요 방향"을 찾는 것 → PCA의 핵심
5. **SVD**: 임의 행렬을 분해하는 가장 일반적인 방법 → 차원 축소, 추천 시스템
6. **행렬 미분**: 경사하강법의 수학적 토대, 역전파 알고리즘의 언어

> **다음 글 안내**: 확률론과 베이즈 정리를 중심으로 ML의 또 다른 수학적 기둥을 살펴보려면 [[probability-bayes]]를 참고하세요. 선형대수의 대표적 응용인 PCA는 [[pca]]에서 더 깊이 다룹니다.

## 관련 문서

- [[probability-bayes]] - 확률론과 베이즈 정리
- [[pca]] - 주성분 분석 (PCA)
- [[optimization-theory]] - 최적화 이론
- [[linear-regression]] - 선형 회귀
- [[regularized-regression]] - 정규화 회귀 (Ridge/Lasso)
- [[kernel-methods]] - 커널 방법론
- [[tsne-umap]] - t-SNE와 UMAP