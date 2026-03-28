# 정규화 회귀: Ridge, Lasso, ElasticNet 완전 정리

## 1. 개요: 왜 정규화가 필요한가

선형 회귀는 훈련 데이터에 대한 잔차 제곱합(RSS)을 최소화한다. 특성이 많거나 서로 상관관계가 높을 때 OLS(최소제곱법) 추정량은 훈련 데이터에 **과적합(Overfitting)**되는 경향이 있다. 즉, 학습 오차는 매우 낮지만 새로운 데이터에 대한 예측 오차는 크게 커진다.

이 문제의 근본 원인은 **편향-분산 트레이드오프(Bias-Variance Tradeoff)**에 있다. OLS는 불편추정량(Unbiased Estimator)이지만 분산이 크다. 조금의 편향을 허용하는 대신 분산을 크게 낮추면 전체 예측 오차(MSE)를 줄일 수 있다.

$$
\text{MSE}(\hat{w}) = \text{Bias}^2(\hat{w}) + \text{Var}(\hat{w})
$$

**정규화(Regularization)**는 손실 함수에 가중치 크기에 대한 **페널티(Penalty)** 항을 추가하여 가중치가 지나치게 커지는 것을 억제한다. 이를 통해 분산을 줄이고 일반화 성능을 높인다.

특히 다음 상황에서 정규화는 필수적이다:

- **고차원 데이터**: 특성 수 $p$가 샘플 수 $n$보다 크거나 비슷할 때 ($p \geq n$)
- **다중공선성(Multicollinearity)**: 특성 간 상관관계가 높아 $X^TX$가 역행렬을 갖지 못할 때
- **희소 신호**: 실제로 의미 있는 특성이 소수일 때

---

## 2. Ridge 회귀 (L2 정규화)

### 2.1 목적함수

Ridge 회귀는 RSS에 가중치의 **제곱합(L2 노름의 제곱)**을 페널티로 추가한다:

$$
\mathcal{L}_{\text{Ridge}} = \sum_{i=1}^{n}(y_i - \hat{y}_i)^2 + \lambda \sum_{j=1}^{p} w_j^2 = \|\mathbf{y} - X\mathbf{w}\|_2^2 + \lambda \|\mathbf{w}\|_2^2
$$

여기서 $\lambda \geq 0$는 정규화 강도를 조절하는 하이퍼파라미터다. $\lambda = 0$이면 OLS와 동일하고, $\lambda \to \infty$이면 모든 가중치가 0에 수렴한다.

### 2.2 해석적 해 (Closed-form Solution)

Ridge의 목적함수는 볼록(Convex)하고 미분 가능하므로 해석적 해가 존재한다. $\mathcal{L}_{\text{Ridge}}$를 $\mathbf{w}$에 대해 미분하고 0으로 놓으면:

$$
\hat{\mathbf{w}}_{\text{Ridge}} = (X^TX + \lambda I)^{-1}X^T\mathbf{y}
$$

OLS 해 $(X^TX)^{-1}X^T\mathbf{y}$와 비교하면 $X^TX$에 $\lambda I$가 더해진 형태다. 이 덕분에:

- **역행렬 문제 해결**: $X^TX$가 특이 행렬(Singular Matrix)이더라도 $\lambda > 0$이면 항상 역행렬이 존재한다
- **수치 안정성**: 다중공선성이 있는 경우에도 안정적인 해를 구할 수 있다

### 2.3 Ridge의 특성

- 가중치를 **0에 가깝게 수축(Shrinkage)**시키지만, 정확히 0으로 만들지는 않는다
- 상관된 특성들의 가중치를 **고르게 분배**한다
- 모든 특성을 유지한 채 영향력만 줄이므로 **피처 선택(Feature Selection)** 기능은 없다

---

## 3. Lasso 회귀 (L1 정규화)

### 3.1 목적함수

Lasso(Least Absolute Shrinkage and Selection Operator)는 가중치의 **절댓값 합(L1 노름)**을 페널티로 사용한다:

$$
\mathcal{L}_{\text{Lasso}} = \sum_{i=1}^{n}(y_i - \hat{y}_i)^2 + \lambda \sum_{j=1}^{p} |w_j| = \|\mathbf{y} - X\mathbf{w}\|_2^2 + \lambda \|\mathbf{w}\|_1
$$

### 3.2 희소 해 (Sparse Solution)

Lasso의 가장 중요한 특성은 **일부 계수를 정확히 0으로 만든다**는 것이다. 이를 **희소 해(Sparse Solution)**라 하며, 자동으로 **피처 선택(Feature Selection)**을 수행하는 효과가 있다.

L1 페널티는 $w_j = 0$에서 미분 불가능하므로 Ridge처럼 해석적 해가 존재하지 않는다. 대신 **좌표 강하법(Coordinate Descent)** 또는 **서브그래디언트(Subgradient)** 방법으로 최적해를 구한다.

단일 특성에 대한 좌표 강하 업데이트는 **Soft Thresholding** 연산으로 표현된다:

$$
\hat{w}_j = \text{sign}(z_j) \cdot \max(|z_j| - \lambda, 0)
$$

여기서 $z_j$는 $j$번째 특성에 대한 편잔차(Partial Residual) 기반 OLS 추정량이다. $|z_j| \leq \lambda$이면 $\hat{w}_j = 0$이 되어 희소성이 발생한다.

### 3.3 Lasso의 특성

- 중요하지 않은 특성의 계수를 **정확히 0**으로 만들어 자동 피처 선택
- 상관된 특성 중 **하나만 선택**하고 나머지는 0으로 만드는 경향 (Ridge는 가중치를 분산)
- 진짜 중요한 특성이 소수일 때(**희소 신호**) 특히 효과적

---

![정규화 효과 시각화: Ridge와 Lasso가 계수를 수축시키는 과정](figures/regularization_effect.png)
*정규화 효과: 정규화 강도(lambda)가 증가할수록 Ridge는 계수를 0에 가깝게 수축시키고, Lasso는 일부 계수를 정확히 0으로 만든다.*

## 4. 기하학적 해석

정규화 회귀를 **제약 최적화(Constrained Optimization)** 관점으로 보면 기하학적 직관을 얻을 수 있다.

### 4.1 제약 최적화 공식

Ridge와 Lasso는 각각 다음과 같은 제약 최적화 문제와 동치다:

- **Ridge**: $\min_{\mathbf{w}} \text{RSS}(\mathbf{w})$ subject to $\sum_j w_j^2 \leq t$
- **Lasso**: $\min_{\mathbf{w}} \text{RSS}(\mathbf{w})$ subject to $\sum_j |w_j| \leq t$

여기서 $t$는 $\lambda$와 반비례 관계다 ($\lambda$가 크면 $t$가 작다).

### 4.2 L2 제약: 구(Sphere)

Ridge의 제약 영역 $\sum_j w_j^2 \leq t$는 2차원에서 **원(Circle)**, 고차원에서 **구(Sphere)**다. RSS 등고선(타원)이 이 원 영역과 접하는 지점이 Ridge 해다.

구는 **코너(Corner)가 없으므로** 타원 등고선이 축 위에서 접할 가능성이 낮다. 따라서 해가 정확히 0이 되는 경우는 거의 없다.

### 4.3 L1 제약: 다이아몬드(Diamond)

Lasso의 제약 영역 $\sum_j |w_j| \leq t$는 2차원에서 **마름모(Diamond)**, 고차원에서 **정팔면체(Octahedron)**다. 이 도형은 **코너(Corner)가 있으며**, 코너는 축 위($w_j = 0$)에 위치한다.

RSS 등고선이 이 다이아몬드와 접할 때 **코너에서 접할 가능성이 높다**. 특히 특성 수가 많을수록 코너의 수도 많아지므로, 많은 계수가 0이 되는 희소 해가 자연스럽게 발생한다.

이것이 L1과 L2의 근본적인 차이다: **제약 공간의 기하학적 형태**가 해의 희소성을 결정한다.

---

## 5. ElasticNet: L1 + L2의 결합

### 5.1 목적함수

ElasticNet은 L1과 L2 페널티를 동시에 사용한다:

$$
\mathcal{L}_{\text{ElasticNet}} = \|\mathbf{y} - X\mathbf{w}\|_2^2 + \lambda_1 \sum_{j=1}^{p} |w_j| + \lambda_2 \sum_{j=1}^{p} w_j^2
$$

실무에서는 종종 총 페널티 강도 $\alpha$와 L1 비율 $\rho \in [0, 1]$로 재매개변수화한다:

$$
\mathcal{L} = \text{RSS} + \alpha \left[ \rho \|\mathbf{w}\|_1 + \frac{1-\rho}{2} \|\mathbf{w}\|_2^2 \right]
$$

- $\rho = 1$: 순수 Lasso
- $\rho = 0$: 순수 Ridge
- $0 < \rho < 1$: ElasticNet

### 5.2 ElasticNet이 필요한 상황

**Lasso의 한계**: 상관된 특성이 여러 개 있을 때, Lasso는 그 중 임의의 하나만 선택하고 나머지는 버린다. 어떤 특성이 선택될지 불안정하고, 중요한 정보를 가진 특성이 제거될 수 있다.

**ElasticNet의 장점**:
- L2 성분이 상관된 특성들을 **함께 선택**하거나 **그룹으로 처리**하는 효과를 줌
- L1 성분이 희소성을 유지하여 자동 피처 선택 기능을 보존
- 특성 수가 샘플 수보다 많은 고차원 문제에서 Ridge보다 해석 가능성이 높음

| 특성 | Ridge | Lasso | ElasticNet |
|------|-------|-------|------------|
| 희소 해 | X | O | O (조절 가능) |
| 상관 특성 처리 | 가중치 분산 | 하나만 선택 | 그룹 선택 |
| 해석적 해 | O | X | X |
| 피처 선택 | X | O | O (부분적) |
| 적합 상황 | 모든 특성 기여 | 희소 신호 | 상관 특성 많음 |

---

## 6. 베이지안 해석

정규화 회귀는 **베이지안 통계(Bayesian Statistics)** 관점에서 자연스럽게 도출된다. 사전 분포(Prior)를 달리하면 다른 정규화 방법이 나온다.

### 6.1 Ridge = 가우시안 Prior의 MAP 추정

가중치에 가우시안 사전 분포를 부여한다:

$$
p(\mathbf{w}) \propto \exp\left(-\frac{\lambda}{2\sigma^2} \|\mathbf{w}\|_2^2\right) \quad \Leftrightarrow \quad w_j \sim \mathcal{N}\left(0, \frac{\sigma^2}{\lambda}\right)
$$

이때 **MAP(Maximum A Posteriori) 추정**은:

$$
\hat{\mathbf{w}}_{\text{MAP}} = \arg\max_{\mathbf{w}} \left[ \log p(\mathbf{y}|\mathbf{w}) + \log p(\mathbf{w}) \right] = \arg\min_{\mathbf{w}} \left[ \text{RSS} + \lambda \|\mathbf{w}\|_2^2 \right]
$$

Ridge 회귀와 동일하다. 가우시안 사전 분포는 가중치를 0 주변으로 부드럽게 당기므로, Ridge는 가중치를 작지만 0이 아닌 값으로 유지한다.

### 6.2 Lasso = 라플라스 Prior의 MAP 추정

가중치에 **라플라스(이중 지수) 사전 분포**를 부여한다:

$$
p(\mathbf{w}) \propto \exp\left(-\frac{\lambda}{\sigma^2} \|\mathbf{w}\|_1\right) \quad \Leftrightarrow \quad w_j \sim \text{Laplace}\left(0, \frac{\sigma^2}{\lambda}\right)
$$

MAP 추정은 Lasso 회귀와 동일하다. 라플라스 분포는 가우시안보다 **꼬리가 두껍고(Heavy-tailed) 0에서 뾰족한(Spike at zero)** 형태다. 이 특성이 가중치를 정확히 0으로 만드는 경향을 만든다.

이 베이지안 해석은 정규화의 통계적 근거를 제공하고, 불확실성 정량화를 위한 완전 베이지안 추론(Full Bayesian Inference)으로 자연스럽게 확장된다.

---

![L1/L2 계수 경로: 정규화 강도에 따른 계수 변화 추이](figures/l1_l2_coefficient_paths.png)
*L1/L2 정규화 경로: Lasso(L1)는 계수들이 차례로 0이 되는 명확한 패턴을 보이고, Ridge(L2)는 모든 계수가 부드럽게 0에 수렴한다.*

## 7. 하이퍼파라미터 $\lambda$ 튜닝

정규화 강도 $\lambda$는 데이터에서 직접 학습할 수 없으며, 교차 검증(Cross-Validation)으로 선택해야 한다.

### 7.1 Regularization Path

$\lambda$를 크게 늘릴수록 가중치가 수축(Shrink)된다. 모든 $\lambda$ 값에 대한 계수 변화를 추적한 것을 **정규화 경로(Regularization Path)**라 한다.

- **Lasso 경로**: $\lambda$가 커질수록 계수들이 차례로 0이 되는 명확한 패턴
- **Ridge 경로**: $\lambda$가 커질수록 계수들이 부드럽게 0에 수렴

### 7.2 LassoCV / RidgeCV

scikit-learn은 효율적인 교차 검증 탐색을 위한 전용 클래스를 제공한다:

- `LassoCV`: LARS 알고리즘으로 정규화 경로 전체를 효율적으로 탐색
- `RidgeCV`: 각 $\lambda$에 대해 해석적 해를 사용하여 빠른 CV 수행
- `ElasticNetCV`: $\alpha$와 `l1_ratio` 동시 탐색

### 7.3 $\lambda$ 선택 기준

- **최소 CV 오차**: 검증 오차가 가장 낮은 $\lambda$ 선택 (`lambda_min`)
- **1-SE 규칙(1-Standard Error Rule)**: 최소 오차에서 1 표준오차 내에 있는 **가장 단순한 모델** 선택 (`lambda_1se`). 과적합 위험을 줄이고 더 희소한 모델을 얻을 수 있어 실무에서 선호되는 경우가 많다.

---

## 8. Python 코드: scikit-learn 실전 예제

```python
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import make_regression
from sklearn.linear_model import Ridge, Lasso, ElasticNet, LassoCV, RidgeCV
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

# -------------------------------------------------------
# 1. 데이터 생성 (희소 신호: 100개 특성 중 10개만 유효)
# -------------------------------------------------------
np.random.seed(42)
X, y, true_coef = make_regression(
    n_samples=200,
    n_features=100,
    n_informative=10,  # 실제 유효 특성
    noise=20,
    coef=True
)

# 특성 스케일링 (정규화 회귀는 스케일에 민감)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42
)

# -------------------------------------------------------
# 2. 모델 학습
# -------------------------------------------------------
models = {
    'Ridge (λ=1.0)': Ridge(alpha=1.0),
    'Lasso (λ=1.0)': Lasso(alpha=1.0),
    'ElasticNet (λ=1.0, l1=0.5)': ElasticNet(alpha=1.0, l1_ratio=0.5),
}

for name, model in models.items():
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    n_zero = np.sum(np.abs(model.coef_) < 1e-6)  # 0에 가까운 계수 수
    print(f"{name}: RMSE={rmse:.2f}, 0 계수={n_zero}/100")

# -------------------------------------------------------
# 3. LassoCV: 교차 검증으로 최적 λ 자동 탐색
# -------------------------------------------------------
lasso_cv = LassoCV(
    alphas=np.logspace(-3, 2, 100),  # 탐색할 λ 범위
    cv=5,
    max_iter=10000,
    random_state=42
)
lasso_cv.fit(X_train, y_train)

print(f"\nLassoCV 최적 λ: {lasso_cv.alpha_:.4f}")
y_pred_cv = lasso_cv.predict(X_test)
rmse_cv = np.sqrt(mean_squared_error(y_test, y_pred_cv))
n_zero_cv = np.sum(np.abs(lasso_cv.coef_) < 1e-6)
print(f"LassoCV: RMSE={rmse_cv:.2f}, 0 계수={n_zero_cv}/100")

# -------------------------------------------------------
# 4. 정규화 경로 시각화 (Lasso)
# -------------------------------------------------------
alphas = np.logspace(-2, 2, 100)
coefs_lasso = []
coefs_ridge = []

for a in alphas:
    lasso = Lasso(alpha=a, max_iter=10000)
    lasso.fit(X_train, y_train)
    coefs_lasso.append(lasso.coef_)

    ridge = Ridge(alpha=a)
    ridge.fit(X_train, y_train)
    coefs_ridge.append(ridge.coef_)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Lasso 경로
axes[0].plot(alphas, coefs_lasso)
axes[0].set_xscale('log')
axes[0].axvline(lasso_cv.alpha_, color='red', linestyle='--',
                label=f'CV 최적 λ={lasso_cv.alpha_:.3f}')
axes[0].set_xlabel('λ (alpha)', fontsize=12)
axes[0].set_ylabel('계수 값', fontsize=12)
axes[0].set_title('Lasso 정규화 경로', fontsize=13)
axes[0].legend()

# Ridge 경로
axes[1].plot(alphas, coefs_ridge)
axes[1].set_xscale('log')
axes[1].set_xlabel('λ (alpha)', fontsize=12)
axes[1].set_ylabel('계수 값', fontsize=12)
axes[1].set_title('Ridge 정규화 경로', fontsize=13)

plt.tight_layout()
plt.savefig('regularization_path.png', dpi=150, bbox_inches='tight')
plt.show()

# -------------------------------------------------------
# 5. 계수 비교 시각화
# -------------------------------------------------------
best_lasso = Lasso(alpha=lasso_cv.alpha_, max_iter=10000).fit(X_train, y_train)
best_ridge = Ridge(alpha=1.0).fit(X_train, y_train)

fig, axes = plt.subplots(1, 3, figsize=(15, 4))
for ax, coef, title in zip(
    axes,
    [true_coef, best_ridge.coef_, best_lasso.coef_],
    ['True Coefficients', 'Ridge 계수', 'Lasso 계수']
):
    ax.bar(range(len(coef)), coef, color='steelblue', alpha=0.7)
    ax.set_title(title, fontsize=12)
    ax.set_xlabel('특성 인덱스')
    ax.set_ylabel('계수 값')
    ax.axhline(0, color='black', linewidth=0.8)

plt.tight_layout()
plt.savefig('coef_comparison.png', dpi=150, bbox_inches='tight')
plt.show()
```

```output
Ridge (λ=1.0): RMSE=42.56, 0 계수=0/100
Lasso (λ=1.0): RMSE=25.87, 0 계수=44/100
ElasticNet (λ=1.0, l1=0.5): RMSE=95.24, 0 계수=8/100

LassoCV 최적 λ: 1.7074
LassoCV: RMSE=24.89, 0 계수=69/100
```

![정규화 효과 시각화](figures/regularization_effect.png)

*Figure 1: 정규화 효과: Ridge와 Lasso가 계수를 수축시키는 과정을 시각화하며, Lasso는 유효하지 않은 계수를 0으로 만든다.*

![L1/L2 계수 경로](figures/l1_l2_coefficient_paths.png)

*Figure 2: L1/L2 계수 경로: 정규화 강도(λ)에 따른 계수 변화 추이를 비교하여 Ridge와 Lasso의 수축 패턴 차이를 보여준다.*

위 코드에서 주목할 점:

- **StandardScaler 필수**: 정규화 회귀는 각 특성의 스케일에 민감하다. 스케일링 없이 적용하면 단위가 큰 특성에 불공평하게 큰 페널티가 부과된다.
- **LassoCV의 alphas 범위**: 로그 스케일(`np.logspace`)로 탐색해야 넓은 범위를 균등하게 커버할 수 있다.
- **Lasso vs Ridge 계수 패턴**: Lasso는 유효하지 않은 90개 특성의 계수를 0으로 만들어 True Coefficients의 희소 패턴을 잘 복원하는 반면, Ridge는 모든 계수를 작게 유지한다.

---

## 정리

정규화 회귀는 OLS의 과적합 문제를 해결하기 위해 손실 함수에 가중치 크기 페널티를 추가한다:

- **Ridge (L2)**: 가중치를 0에 가깝게 수축. 다중공선성 해결에 탁월. 모든 특성을 유지.
- **Lasso (L1)**: 일부 가중치를 정확히 0으로 만들어 자동 피처 선택. 희소 신호에 최적.
- **ElasticNet**: L1+L2 혼합으로 상관된 특성을 그룹으로 처리하며 희소성도 유지.
- **베이지안 관점**: Ridge = 가우시안 Prior MAP, Lasso = 라플라스 Prior MAP으로 통계적 근거가 명확하다.
- **실전 팁**: 반드시 특성을 표준화하고, `LassoCV` / `RidgeCV`로 교차 검증 기반 $\lambda$ 선택을 자동화한다.