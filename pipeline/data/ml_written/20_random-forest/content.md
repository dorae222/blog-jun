# Random Forest: 나무들의 민주주의

## 1. 개요: 왜 숲이 나무보다 강한가

결정 트리(Decision Tree)는 직관적이고 해석하기 쉽지만, 한 가지 치명적인 약점이 있습니다. **분산(Variance)이 매우 높다**는 것입니다. 학습 데이터가 조금만 달라져도 트리 구조가 크게 바뀌고, 깊이 자란 트리는 학습 데이터의 노이즈까지 암기하는 과적합(Overfitting)에 빠지기 쉽습니다.

**Random Forest**는 이 문제를 "혼자 판단하지 말고, 여럿이 함께 결정하자"는 아이디어로 해결합니다. 수백 개의 결정 트리를 각기 다른 데이터와 다른 특성 조합으로 학습시킨 뒤, 각자의 예측을 모아 다수결(분류) 또는 평균(회귀)으로 최종 답을 냅니다.

이 접근법이 강력한 이유는 통계학의 핵심 원리에 기반합니다. 서로 독립적인 예측기 $n$개의 평균을 취하면, 분산이 $\frac{1}{n}$ 수준으로 줄어듭니다:

$$
\text{Var}\left(\frac{1}{n}\sum_{i=1}^{n} X_i\right) = \frac{\sigma^2}{n} \quad (\text{독립인 경우})
$$

물론 트리들이 완전히 독립적이지는 않지만, Random Forest는 **Bootstrap Sampling**과 **Random Feature Subspace**라는 두 가지 무기로 트리 간 상관도를 의도적으로 낮춥니다. 그 결과, 개별 트리보다 분산이 크게 감소하면서도 편향은 거의 유지되는 강력한 모델이 만들어집니다.

Random Forest가 실전에서 사랑받는 이유는 분명합니다:
- 하이퍼파라미터 조정 없이도 준수한 기본 성능
- 과적합에 강한 자연스러운 내성
- OOB 오차로 별도 검증셋 없이 모델 평가 가능
- Feature Importance로 변수 해석 제공

---

## 2. 배깅(Bagging) 기반 구조

Random Forest의 뼈대는 **Bagging(Bootstrap Aggregating)**입니다. Bagging은 Leo Breiman이 1996년에 제안한 앙상블 기법으로, 같은 데이터에서 여러 서브셋을 만들어 각각 독립적인 모델을 학습시킵니다.

### 2.1 Bootstrap Sampling: 복원 추출로 n개 서브셋

**Bootstrap**은 원본 학습 데이터 $D = \{(x_1, y_1), \ldots, (x_N, y_N)\}$에서 **복원 추출(Sampling with Replacement)**로 크기 $N$의 서브셋을 만드는 과정입니다.

복원 추출이므로 같은 샘플이 여러 번 선택될 수 있고, 반대로 한 번도 선택되지 않는 샘플도 존재합니다. 하나의 샘플이 특정 Bootstrap 서브셋에 포함되지 않을 확률은:

$$
P(\text{미선택}) = \left(1 - \frac{1}{N}\right)^N \xrightarrow{N \to \infty} e^{-1} \approx 0.368
$$

즉, **매 Bootstrap마다 원본 데이터의 약 36.8%는 선택되지 않습니다.** 이 선택되지 않은 샘플들이 OOB(Out-Of-Bag) 샘플이 됩니다.

### 2.2 각 트리: Bootstrap 데이터로 독립 학습

$B$개의 Bootstrap 서브셋 $D^{(1)}, D^{(2)}, \ldots, D^{(B)}$를 만들어, 각각에 결정 트리 $T^{(1)}, T^{(2)}, \ldots, T^{(B)}$를 학습시킵니다. 각 트리는 서로 다른 데이터를 보기 때문에 서로 다른 구조를 가지게 됩니다.

### 2.3 예측 집계

새로운 샘플 $x$에 대한 예측은 모든 트리의 출력을 집계합니다:

- **분류(Classification)**: 다수결 투표
$$\hat{y} = \text{mode}\left(T^{(1)}(x),\ T^{(2)}(x),\ \ldots,\ T^{(B)}(x)\right)$$

- **회귀(Regression)**: 평균
$$\hat{y} = \frac{1}{B}\sum_{b=1}^{B} T^{(b)}(x)$$

트리 수 $B$가 많을수록 분산이 줄어들지만, 어느 수준 이상에서는 수렴합니다. 일반적으로 분류에서는 100~500, 회귀에서는 300~1000 정도를 사용합니다.

---

## 3. Random Feature Subspace

Bagging만으로는 트리 간 상관도를 충분히 낮추기 어렵습니다. 강한 예측 변수가 있으면 모든 트리가 그 변수를 최상단 분기에 사용하게 되어, 트리들이 서로 비슷해지기 때문입니다.

Random Forest의 핵심 혁신은 **각 분기(Split) 노드에서 무작위로 일부 특성만 고려**하는 것입니다. 전체 특성 수가 $p$일 때:

- **분류**: 각 노드에서 $\sqrt{p}$개의 특성을 무작위 선택
- **회귀**: 각 노드에서 $p/3$개의 특성을 무작위 선택

이 Random Feature Subspace의 효과를 수식으로 이해할 수 있습니다. 상관도가 $\rho$이고 분산이 $\sigma^2$인 트리 $B$개를 앙상블하면:

$$
\text{Var}(\text{앙상블}) = \rho \cdot \sigma^2 + \frac{1 - \rho}{B} \cdot \sigma^2
$$

$B \to \infty$이더라도 $\rho \cdot \sigma^2$이 남기 때문에, **트리 간 상관도 $\rho$를 낮추는 것이 분산 감소의 핵심**입니다. Random Feature Subspace는 강한 특성이 매번 선택되지 않도록 강제함으로써 $\rho$를 효과적으로 낮춥니다.

결과적으로 각 트리는 개별적으로는 다소 약한(각 노드에서 최선의 특성을 고르지 못하므로) 대신, 서로 다양한 관점을 가지게 됩니다. 이 다양성이 앙상블 전체의 강점이 됩니다.

---

![OOB 오차 수렴: 트리 수 증가에 따른 OOB 오류율의 변화](figures/oob_error_vs_n_estimators.png)
*OOB 오차 수렴: 트리 수가 증가할수록 OOB 오류율이 감소하다가 일정 수준에서 수렴하는 과정을 보여준다.*

## 4. OOB (Out-Of-Bag) 오차

Random Forest의 실용적인 장점 중 하나는 **별도의 검증 세트 없이도 모델 성능을 추정**할 수 있다는 것입니다.

각 트리 $T^{(b)}$는 Bootstrap 서브셋 $D^{(b)}$로 학습되기 때문에, 해당 Bootstrap에 포함되지 않은 OOB 샘플들에 대해서는 완전히 새로운 데이터처럼 예측할 수 있습니다.

**OOB 예측 생성 과정:**
1. 각 학습 샘플 $(x_i, y_i)$에 대해, $i$가 OOB 샘플인 트리들만 모읍니다
2. 해당 트리들의 예측을 집계하여 $\hat{y}_i^{\text{OOB}}$를 계산합니다
3. 모든 샘플의 OOB 예측과 실제 값을 비교하여 OOB 오차를 계산합니다

$$
\text{OOB Error} = \frac{1}{N}\sum_{i=1}^{N} \mathcal{L}\left(y_i,\ \hat{y}_i^{\text{OOB}}\right)
$$

각 샘플은 평균적으로 약 $B \times 0.368$개의 트리에서 OOB 샘플이 되므로, 충분한 수의 트리로 안정적인 추정이 가능합니다. 실제로 OOB 오차는 $k$-폴드 교차 검증과 유사한 수준의 추정 정확도를 보이면서도, 계산 비용은 훨씬 적습니다.

---

![Random Forest 특성 중요도: Gini Importance와 Permutation Importance 비교](figures/rf_feature_importance.png)
*Random Forest 특성 중요도: Gini 기반 중요도와 Permutation 기반 중요도를 비교하여 각 특성의 예측 기여도를 시각화한다.*

## 5. Feature Importance

Random Forest는 블랙박스 모델이지만, 두 가지 방식으로 **특성 중요도(Feature Importance)**를 제공합니다.

### 5.1 불순도 기반 중요도 (Gini Importance)

가장 널리 사용되는 방식으로, **Mean Decrease in Impurity(MDI)**라고도 합니다. 특성 $j$의 중요도는 모든 트리에서 해당 특성이 분기에 사용될 때 불순도가 얼마나 감소했는지의 합산입니다:

$$
\text{Importance}(j) = \frac{1}{B}\sum_{b=1}^{B} \sum_{t \in T^{(b)}: v(t)=j} p(t) \cdot \Delta I(t)
$$

여기서 $p(t)$는 노드 $t$에 도달하는 샘플 비율, $\Delta I(t)$는 불순도 감소량입니다. 분류에서는 지니 불순도(Gini Impurity), 회귀에서는 분산을 사용합니다.

**주의사항**: Gini Importance는 **고카디널리티 특성(값의 종류가 많은 변수)에 편향**되어 있습니다. 예를 들어 ID처럼 고유값이 많은 변수는 분기를 많이 만들 기회가 많아 중요도가 과대평가될 수 있습니다.

### 5.2 Permutation Importance (더 신뢰할 수 있음)

**Mean Decrease in Accuracy(MDA)**라고도 하며, 실제 예측 성능에 기반합니다:

1. OOB 샘플(또는 별도 검증셋)에서 기본 성능 $S_0$를 측정합니다
2. 특성 $j$의 값을 무작위로 섞어(Permute) 해당 특성과 타깃 간의 관계를 끊습니다
3. 섞은 후의 성능 $S_j$를 측정합니다
4. 중요도 = $S_0 - S_j$ (성능 저하가 클수록 중요한 특성)

$$
\text{Importance}_j = S_0 - \frac{1}{B}\sum_{b=1}^{B} S_j^{(b)}
$$

Permutation Importance는 고카디널리티 편향이 없고 실제 예측에 미치는 영향을 직접 측정하기 때문에 더 신뢰할 수 있습니다. 단, 계산 비용이 더 높고 상관된 특성이 있을 때 중요도가 분산될 수 있습니다.

---

## 6. 주요 하이퍼파라미터

| 파라미터 | 기본값 | 설명 | 조정 방향 |
|----------|--------|------|----------|
| `n_estimators` | 100 | 트리 수 | 클수록 좋지만 수렴. 보통 100~500 |
| `max_depth` | None | 트리 최대 깊이 | 과적합 시 줄이기 |
| `min_samples_split` | 2 | 노드 분기 최소 샘플 수 | 과적합 시 늘리기 |
| `min_samples_leaf` | 1 | 리프 노드 최소 샘플 수 | 과적합 시 늘리기 |
| `max_features` | `"sqrt"` | 분기 시 고려할 특성 수 | 분류: `"sqrt"`, 회귀: `1.0` |
| `bootstrap` | True | Bootstrap 사용 여부 | False면 Pasting |
| `oob_score` | False | OOB 오차 계산 여부 | 검증셋 대체 시 True |
| `n_jobs` | 1 | 병렬 처리 수 | `-1`이면 모든 CPU 사용 |

**실전 팁:**
- `n_estimators`는 충분히 크게 잡고(500~1000) 수렴을 확인한 후 줄이는 방식이 안전합니다
- `max_depth`를 제한하는 것보다 `min_samples_leaf`를 늘리는 편이 더 자연스러운 과적합 억제 효과를 냅니다
- `max_features`를 줄이면 트리 간 다양성이 높아져 분산이 감소하지만, 개별 트리 성능이 떨어질 수 있습니다

---

## 7. 장단점

### 장점

- **과적합에 강건**: 배깅과 랜덤 특성 선택이 자연스럽게 과적합을 억제합니다. 깊이 제한 없이 완전히 성장한 트리도 앙상블 효과로 일반화 성능이 유지됩니다
- **Feature Importance 제공**: 어떤 변수가 예측에 중요한지 정량적으로 파악할 수 있어 탐색적 분석에 유용합니다
- **이상치(Outlier)에 강건**: 결정 트리는 분기 기준이 상대적 순서에 기반하므로 극단값에 덜 민감하며, 앙상블 효과로 이상치의 영향이 더욱 희석됩니다
- **결측치 처리**: 일부 구현에서 결측치를 내부적으로 처리합니다
- **병렬화 가능**: 각 트리가 독립적으로 학습되므로 `n_jobs=-1`로 손쉽게 병렬화할 수 있습니다
- **하이퍼파라미터 비민감**: 기본값으로도 준수한 성능을 내는 경우가 많아, 빠른 베이스라인 구축에 적합합니다

### 단점

- **해석 어려움**: 수백 개의 트리를 종합한 결과이므로 단일 결정 트리처럼 "왜 이런 예측을 했는가"를 직관적으로 설명하기 어렵습니다
- **메모리 사용량**: 트리 수가 많아질수록 메모리 사용량이 선형적으로 증가합니다. 대규모 데이터셋에서는 부담이 될 수 있습니다
- **느린 예측**: 학습은 병렬화되지만, 예측 시 모든 트리를 통과해야 하므로 실시간 예측이 필요한 환경에서는 지연이 발생할 수 있습니다
- **범주형 변수 처리**: scikit-learn 구현에서는 범주형 변수를 직접 처리하지 않아 One-Hot Encoding이 필요하며, 이로 인해 고카디널리티 특성 처리가 번거롭습니다
- **외삽(Extrapolation) 불가**: 트리 기반 모델의 한계로, 학습 데이터 범위를 벗어난 값 예측에 취약합니다

---

## 8. Python 코드: RandomForestClassifier + Feature Importance 시각화

```python
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.inspection import permutation_importance

# ── 1. 데이터 준비 ──────────────────────────────────────────
dataset = load_breast_cancer()
X, y = dataset.data, dataset.target
feature_names = dataset.feature_names

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ── 2. Random Forest 학습 ───────────────────────────────────
rf = RandomForestClassifier(
    n_estimators=300,
    max_depth=None,          # 완전히 성장시킨 트리
    min_samples_leaf=2,
    max_features='sqrt',     # 분류 기본값
    oob_score=True,          # OOB 오차 계산
    n_jobs=-1,
    random_state=42
)
rf.fit(X_train, y_train)

# ── 3. 성능 평가 ────────────────────────────────────────────
y_pred = rf.predict(X_test)
print(f"Test Accuracy  : {accuracy_score(y_test, y_pred):.4f}")
print(f"OOB Score      : {rf.oob_score_:.4f}")
print("\n분류 보고서:")
print(classification_report(y_test, y_pred,
                             target_names=dataset.target_names))

# ── 4. Gini Importance 시각화 ───────────────────────────────
gini_imp = rf.feature_importances_
indices = np.argsort(gini_imp)[::-1][:15]  # 상위 15개

fig, axes = plt.subplots(1, 2, figsize=(16, 6))

axes[0].barh(
    range(15),
    gini_imp[indices][::-1],
    color='steelblue', alpha=0.8
)
axes[0].set_yticks(range(15))
axes[0].set_yticklabels([feature_names[i] for i in indices[::-1]], fontsize=9)
axes[0].set_xlabel('Gini Importance (Mean Decrease in Impurity)')
axes[0].set_title('Top 15 Features: Gini Importance', fontsize=12)
axes[0].axvline(x=gini_imp[indices].mean(), color='red',
                linestyle='--', alpha=0.7, label='Mean')
axes[0].legend()

# ── 5. Permutation Importance 시각화 ───────────────────────
perm_imp = permutation_importance(
    rf, X_test, y_test,
    n_repeats=30,
    random_state=42,
    n_jobs=-1
)
perm_mean = perm_imp.importances_mean
perm_std  = perm_imp.importances_std

perm_indices = np.argsort(perm_mean)[::-1][:15]

axes[1].barh(
    range(15),
    perm_mean[perm_indices][::-1],
    xerr=perm_std[perm_indices][::-1],
    color='coral', alpha=0.8, capsize=3
)
axes[1].set_yticks(range(15))
axes[1].set_yticklabels(
    [feature_names[i] for i in perm_indices[::-1]], fontsize=9
)
axes[1].set_xlabel('Permutation Importance (Mean Decrease in Accuracy)')
axes[1].set_title('Top 15 Features: Permutation Importance', fontsize=12)
axes[1].axvline(x=0, color='black', linewidth=0.8)

plt.suptitle('Random Forest Feature Importance Comparison', fontsize=14, y=1.02)
plt.tight_layout()
plt.savefig('rf_feature_importance.png', dpi=150, bbox_inches='tight')
plt.show()

# ── 6. OOB 오차 수렴 확인 (n_estimators 효과) ───────────────
oob_errors = []
n_range = range(10, 310, 10)

for n in n_range:
    clf = RandomForestClassifier(
        n_estimators=n,
        oob_score=True,
        n_jobs=-1,
        random_state=42
    )
    clf.fit(X_train, y_train)
    oob_errors.append(1 - clf.oob_score_)

fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(list(n_range), oob_errors, 'b-o', markersize=4, linewidth=1.5)
ax.set_xlabel('n_estimators (트리 수)', fontsize=12)
ax.set_ylabel('OOB Error Rate', fontsize=12)
ax.set_title('OOB 오차의 수렴: 트리 수가 많아질수록 안정', fontsize=13)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('rf_oob_convergence.png', dpi=150, bbox_inches='tight')
plt.show()
```

```output
Test Accuracy  : 0.9561
OOB Score      : 0.9560

분류 보고서:
              precision    recall  f1-score   support

   malignant       0.95      0.93      0.94        42
      benign       0.96      0.97      0.97        72

    accuracy                           0.96       114
   macro avg       0.96      0.95      0.95       114
weighted avg       0.96      0.96      0.96       114
```

![Random Forest 특성 중요도](figures/rf_feature_importance.png)

*Figure 1: 특성 중요도 비교: Gini Importance와 Permutation Importance 두 가지 방법으로 측정한 특성 중요도를 비교한다.*

![OOB 오차 수렴 곡선](figures/oob_error_vs_n_estimators.png)

*Figure 2: OOB 오차 수렴: 트리 수 증가에 따른 OOB 오류율 변화를 보여주며, 수렴 지점을 통해 최적 트리 수를 결정한다.*

**코드 설명:**
- **OOB Score**: `oob_score=True` 설정으로 별도 검증셋 없이 일반화 성능을 추정합니다. 반환값이 1에 가까울수록 좋습니다.
- **Gini vs Permutation**: 두 방식은 순위가 다를 수 있습니다. 고카디널리티 특성이 있거나 특성 간 상관관계가 있을 때 Permutation Importance가 더 신뢰할 수 있습니다.
- **수렴 확인**: OOB 오차는 트리 수가 늘어날수록 감소하다가 수렴합니다. 수렴점을 확인하면 불필요하게 많은 트리를 사용하는 낭비를 줄일 수 있습니다.

---

## 정리

Random Forest는 **"여럿이 힘을 합치면 하나보다 낫다"**는 단순한 원리를 수학적으로 정교하게 구현한 모델입니다:

- **Bootstrap Sampling**으로 서로 다른 데이터를 보는 다양한 트리를 만들고
- **Random Feature Subspace**로 트리 간 상관도를 낮춰 분산 감소 효과를 극대화하며
- **OOB 오차**로 추가 비용 없이 모델 성능을 검증하고
- **Feature Importance**로 데이터에 대한 인사이트를 제공합니다

실무에서 Random Forest는 종종 "첫 번째로 시도해볼 모델"로 추천됩니다. XGBoost나 LightGBM 같은 부스팅 계열이 대부분의 벤치마크에서 더 높은 성능을 보이지만, Random Forest는 조정이 적고 안정적이며 병렬화가 쉬운 특성 덕분에 빠른 베이스라인 수립과 특성 분석에 여전히 높은 가치를 지닙니다.