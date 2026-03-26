## 개요

머신러닝 모델을 실제 산업 환경에 적용할 때 가장 흔히 부딪히는 장벽 중 하나는 **레이블(정답) 부족** 문제다. 의료 영상 분류를 위해 전문의가 수천 장을 직접 판독해야 하거나, 법률 문서를 도메인 전문가가 일일이 태깅해야 하는 경우처럼 레이블 획득에는 막대한 시간과 비용이 든다. 반면 레이블이 없는 원시 데이터는 인터넷, 센서, 로그 등에서 거의 무한정 수집할 수 있다.

**준지도학습(Semi-supervised Learning, SSL)**은 소량의 레이블 데이터와 대량의 비레이블 데이터를 함께 사용해 모델을 학습하는 패러다임이다. **자기지도학습(Self-supervised Learning)**은 한 발 더 나아가 레이블 자체를 데이터로부터 자동 생성하여 사전학습(pre-training)에 활용한다. 두 접근법 모두 '레이블이 없어도 데이터 자체에 구조적 정보가 있다'는 직관에서 출발한다.

이 글에서는 수학적 기반부터 sklearn 구현, 딥러닝에서의 활용까지 단계적으로 살펴본다.

---

## 수학적 배경

### 1. 그래프 기반 레이블 전파 (Label Propagation)

$n$개의 샘플 중 $l$개는 레이블 데이터 $\mathcal{L} = \{(x_i, y_i)\}_{i=1}^{l}$, 나머지 $u = n - l$개는 비레이블 데이터 $\mathcal{U} = \{x_j\}_{j=l+1}^{n}$라 하자.

유사도 그래프 $W$를 RBF 커널로 정의한다:

$$W_{ij} = \exp\left(-\frac{\|x_i - x_j\|^2}{2\sigma^2}\right)$$

행 정규화된 전이 행렬 $T$는:

$$T_{ij} = \frac{W_{ij}}{\sum_k W_{ik}}$$

레이블 행렬 $F \in \mathbb{R}^{n \times C}$를 반복 갱신한다:

$$F^{(t+1)} = \alpha T F^{(t)} + (1 - \alpha) Y$$

여기서 $\alpha \in (0, 1)$은 전파 강도, $Y$는 초기 레이블 행렬(비레이블 행은 0)이다. 수렴 시 닫힌 형태(closed-form) 해는:

$$F^* = (I - \alpha T)^{-1} Y$$

### 2. Self-training 목적함수

Self-training은 현재 모델 $\theta$로 비레이블 데이터에 **의사 레이블(pseudo-label)** $\hat{y}_j$를 부여한 뒤 레이블 데이터처럼 재학습한다:

$$\hat{y}_j = \arg\max_c P_\theta(y = c \mid x_j)$$

전체 목적함수:

$$\mathcal{L} = \underbrace{\frac{1}{l}\sum_{i=1}^{l} \ell(f_\theta(x_i), y_i)}_{\text{지도 손실}} + \lambda \underbrace{\frac{1}{u}\sum_{j=l+1}^{n} \mathbf{1}[\max_c P_\theta > \tau]\, \ell(f_\theta(x_j), \hat{y}_j)}_{\text{pseudo-label 손실}}$$

$\tau$는 신뢰도 임계값으로, 확신도가 높은 샘플만 pseudo-label로 사용해 오류 전파를 억제한다.

### 3. 대조학습 (Contrastive Learning) 목적함수 — SimCLR

같은 샘플 $x$의 두 증강(augmentation) $\tilde{x}_i, \tilde{x}_j$를 양성 쌍(positive pair)으로, 배치 내 나머지를 음성 쌍(negative pair)으로 정의한다. NT-Xent 손실:

$$\mathcal{L}_{\text{SimCLR}} = -\log \frac{\exp(\text{sim}(z_i, z_j)/\tau)}{\sum_{k \neq i} \exp(\text{sim}(z_i, z_k)/\tau)}$$

여기서 $\text{sim}(u, v) = u^\top v / (\|u\|\|v\|)$는 코사인 유사도, $\tau$는 온도 파라미터다.

---

## 알고리즘

### Label Propagation vs Label Spreading

| 항목 | Label Propagation | Label Spreading |
|---|---|---||
| 갱신 식 | $F = TF_0$ (레이블 고정) | $F^{(t+1)} = \alpha T F^{(t)} + (1-\alpha)Y$ |
| 레이블 변경 | 불가 | 가능 (노이즈 허용) |
| 정규화 | 행 정규화 | 대칭 정규화 $D^{-1/2}WD^{-1/2}$ |
| 적합 상황 | 레이블 신뢰도 높을 때 | 레이블에 노이즈 있을 때 |

### Self-training

1. 레이블 데이터로 초기 모델 학습
2. 비레이블 데이터에 예측 후 신뢰도 $\tau$ 이상인 샘플 pseudo-label 부여
3. 해당 샘플을 레이블 셋에 추가해 재학습
4. 수렴할 때까지 반복

### Co-training

두 개의 독립적 특징 뷰(view) $X^{(1)}, X^{(2)}$를 사용해 두 모델이 서로의 pseudo-label로 학습하는 방식이다. 예: 텍스트 분류에서 제목(뷰1)과 본문(뷰2)을 분리해 사용.

### Active Learning

모든 비레이블 데이터에 pseudo-label을 부여하는 대신, **레이블을 물어볼 가치가 높은 샘플**을 선별해 전문가에게 질의한다. 쿼리 전략:

- **Uncertainty Sampling**: 예측 엔트로피가 가장 높은 샘플 선택
  $$x^* = \arg\max_x H(P_\theta(y|x)) = -\sum_c P_\theta(y=c|x)\log P_\theta(y=c|x)$$
- **Query by Committee**: 여러 모델의 의견 불일치가 큰 샘플 선택
- **Core-set**: 특징 공간에서 커버리지를 최대화하는 샘플 선택

### Self-supervised Learning: SimCLR과 MoCo

**SimCLR (Simple Framework for Contrastive Learning)**은 같은 이미지에 두 가지 증강(random crop, color jitter, Gaussian blur 등)을 적용한 뒤 두 뷰의 표현이 가까워지도록 인코더를 학습한다. 핵심은 대형 배치(~4096)와 projection head다.

**MoCo (Momentum Contrast)**는 큰 배치 없이도 동작하도록 **모멘텀 인코더**와 **큐(queue)** 방식의 음성 샘플 저장소를 사용한다. 인코더 파라미터 $\theta_q$, 모멘텀 인코더 파라미터 $\theta_k$의 갱신:

$$\theta_k \leftarrow m \cdot \theta_k + (1-m) \cdot \theta_q \quad (m \approx 0.999)$$

두 방법 모두 사전학습 후 소량의 레이블 데이터로 파인튜닝하면 완전 지도학습과 대등하거나 더 나은 성능을 달성할 수 있다.

---

## Python 구현

### sklearn Label Propagation / Label Spreading

```python
import numpy as np
from sklearn.datasets import make_moons
from sklearn.semi_supervised import LabelPropagation, LabelSpreading
from sklearn.metrics import accuracy_score

# 데이터 생성
X, y_true = make_moons(n_samples=300, noise=0.1, random_state=42)

# 소량 레이블만 노출 (10%)
np.random.seed(42)
labeled_idx = np.random.choice(len(X), size=30, replace=False)
y = np.full(len(X), -1)  # -1 = 비레이블
y[labeled_idx] = y_true[labeled_idx]

# Label Propagation
lp = LabelPropagation(kernel='rbf', gamma=20, max_iter=1000)
lp.fit(X, y)
y_pred_lp = lp.predict(X)
print(f"Label Propagation 정확도: {accuracy_score(y_true, y_pred_lp):.4f}")

# Label Spreading (노이즈에 더 강건)
ls = LabelSpreading(kernel='rbf', gamma=20, alpha=0.2, max_iter=1000)
ls.fit(X, y)
y_pred_ls = ls.predict(X)
print(f"Label Spreading 정확도:   {accuracy_score(y_true, y_pred_ls):.4f}")
```

```output
Label Propagation 정확도: 1.0000
Label Spreading 정확도:   1.0000
```

### Self-training with Logistic Regression

```python
from sklearn.linear_model import LogisticRegression
from sklearn.semi_supervised import SelfTrainingClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# SelfTrainingClassifier: sklearn 0.24+ 지원
base_clf = LogisticRegression(max_iter=500, random_state=42)
self_training = SelfTrainingClassifier(
    base_estimator=base_clf,
    threshold=0.9,      # 신뢰도 임계값 τ
    criterion='threshold',
    max_iter=10,
    verbose=True
)

pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('clf', self_training)
])

pipeline.fit(X, y)  # y에서 -1은 비레이블로 자동 인식
y_pred_st = pipeline.predict(X)
print(f"Self-training 정확도: {accuracy_score(y_true, y_pred_st):.4f}")
```

<!-- Execution error: TypeError: SelfTrainingClassifier.__init__() got an unexpected keyword argument 'base_estimator' -->

### Pseudo-labeling 수동 구현 (신뢰도 필터링)

```python
from sklearn.ensemble import RandomForestClassifier

def pseudo_label_train(X, y_partial, threshold=0.85, n_iter=5):
    """
    threshold: pseudo-label로 채택할 최소 확신도
    """
    X_labeled = X[y_partial != -1]
    y_labeled = y_partial[y_partial != -1]
    X_unlabeled = X[y_partial == -1]

    clf = RandomForestClassifier(n_estimators=100, random_state=42)

    for i in range(n_iter):
        clf.fit(X_labeled, y_labeled)
        proba = clf.predict_proba(X_unlabeled)          # shape: (u, C)
        confidence = proba.max(axis=1)                  # 최대 확률값
        pseudo_labels = proba.argmax(axis=1)            # 예측 클래스

        # 신뢰도 높은 샘플만 추가
        mask = confidence >= threshold
        if mask.sum() == 0:
            print(f"Iter {i+1}: 추가할 샘플 없음. 종료.")
            break

        X_labeled = np.vstack([X_labeled, X_unlabeled[mask]])
        y_labeled = np.hstack([y_labeled, pseudo_labels[mask]])
        X_unlabeled = X_unlabeled[~mask]
        print(f"Iter {i+1}: {mask.sum()}개 추가 → 총 레이블 {len(y_labeled)}개")

    return clf

clf_pl = pseudo_label_train(X, y, threshold=0.85)
y_pred_pl = clf_pl.predict(X)
print(f"Pseudo-labeling 정확도: {accuracy_score(y_true, y_pred_pl):.4f}")
```

```output
Iter 1: 188개 추가 → 총 레이블 218개
Iter 2: 34개 추가 → 총 레이블 252개
Iter 3: 5개 추가 → 총 레이블 257개
Iter 4: 6개 추가 → 총 레이블 263개
Iter 5: 6개 추가 → 총 레이블 269개
Pseudo-labeling 정확도: 0.8933
```

---

## 시각화

```python
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

fig, axes = plt.subplots(1, 3, figsize=(15, 4))

# --- 공통 설정 ---
cmap_bg = plt.cm.RdYlBu
titles = ['초기 레이블 상태', 'Label Propagation 예측', 'Label Spreading 예측']
predictions = [None, y_pred_lp, y_pred_ls]

for ax, title, pred in zip(axes, titles, predictions):
    # 배경 결정 경계
    if pred is not None:
        xx, yy = np.meshgrid(
            np.linspace(X[:, 0].min() - 0.5, X[:, 0].max() + 0.5, 200),
            np.linspace(X[:, 1].min() - 0.5, X[:, 1].max() + 0.5, 200)
        )
        Z = lp.predict(np.c_[xx.ravel(), yy.ravel()]).reshape(xx.shape)
        ax.contourf(xx, yy, Z, alpha=0.2, cmap=cmap_bg)

    # 비레이블 샘플
    unlabeled_mask = (y == -1)
    ax.scatter(X[unlabeled_mask, 0], X[unlabeled_mask, 1],
               c='lightgray', s=20, alpha=0.6, label='비레이블')

    # 레이블 샘플
    for cls, color, name in [(0, 'blue', 'Class 0'), (1, 'red', 'Class 1')]:
        mask = (y == cls)
        ax.scatter(X[mask, 0], X[mask, 1],
                   c=color, s=80, edgecolors='black', linewidths=0.8,
                   zorder=5, label=name)

    ax.set_title(title, fontsize=12, fontweight='bold')
    ax.legend(loc='upper right', fontsize=8)
    ax.set_xlabel('Feature 1')
    ax.set_ylabel('Feature 2')

plt.suptitle('준지도학습 레이블 전파 시각화', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('ssl_visualization.png', dpi=150, bbox_inches='tight')
plt.show()
```

![Semi-Supervised-Learning Fig 1](/media/figures/outputs/semi-supervised-learning/semi-supervised-learning_fig_1.png)

---

## 실전 팁

### 언제 준지도학습을 쓸까?

| 상황 | 권장 방법 |
|---|---|
| 레이블 < 5%, 비레이블 풍부 | Label Propagation / Self-training |
| 레이블 취득 비용이 매우 높음 | Active Learning + 준지도학습 혼합 |
| 이미지·텍스트 대규모 데이터 | Self-supervised pre-training (SimCLR, BERT) |
| 레이블에 노이즈 존재 | Label Spreading (α 조정으로 유연성 확보) |
| 뷰 분리 가능한 멀티모달 | Co-training |

**주의할 점:**
- **확증 편향(Confirmation Bias)**: Self-training에서 초기 모델이 틀리면 오류가 증폭된다. 낮은 초기 임계값 $\tau$를 점차 높이는 **커리큘럼 전략**이 효과적이다.
- **클러스터 가정(Cluster Assumption)**: 준지도학습은 같은 클러스터 내 샘플이 같은 클래스라 가정한다. 이 가정이 성립하지 않으면 성능이 오히려 저하될 수 있다.
- **클래스 불균형**: pseudo-label 생성 시 다수 클래스 편향이 심화될 수 있으므로 클래스별 임계값을 다르게 설정하는 것이 좋다.

### Active Learning 실전 적용

1. 소량의 레이블 데이터(예: 100개)로 초기 모델 학습
2. 비레이블 풀(pool)에서 불확실성이 가장 높은 샘플 $k$개를 선택
3. 전문가(오라클)에게 해당 샘플 레이블 요청
4. 레이블 풀에 추가 후 모델 재학습
5. 예산 소진 또는 성능 수렴까지 반복

라벨링 예산이 고정된 상황에서 랜덤 샘플링보다 **2~5배 적은 레이블**로 동일 성능을 달성하는 사례가 많다.

### Self-supervised Learning의 딥러닝에서의 역할

자기지도학습은 현대 딥러닝에서 **사전학습(pre-training)**의 표준 패러다임이 되었다:

- **NLP**: BERT의 Masked Language Modeling, GPT의 다음 토큰 예측은 모두 자기지도학습의 일종이다.
- **Vision**: SimCLR, MoCo, MAE(Masked Autoencoder)는 ImageNet 레이블 없이 강력한 표현을 학습한다.
- **멀티모달**: CLIP은 이미지-텍스트 쌍의 대조학습으로 제로샷 분류를 가능하게 한다.

사전학습된 모델을 소량의 레이블로 **파인튜닝**하는 전략은 준지도학습과 자기지도학습의 시너지를 극대화하며, 의료·법률·과학 도메인처럼 레이블 획득이 어려운 분야에서 특히 강력하다.

---

## 정리

준지도학습과 자기지도학습은 레이블 부족이라는 현실적 제약을 데이터 구조에서 답을 찾아 극복한다. 그래프 기반의 Label Propagation부터 딥러닝 시대의 SimCLR까지, 핵심 아이디어는 동일하다: **레이블 없는 데이터도 구조 정보를 가지며, 이를 잘 활용하면 훨씬 적은 비용으로 강력한 모델을 만들 수 있다.** 실무에서는 데이터 규모, 레이블 예산, 도메인 특성에 맞게 위 기법들을 조합해 사용하는 것이 최선이다.