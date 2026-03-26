## 개요

나이브 베이즈(Naive Bayes) 분류기는 **베이즈 정리(Bayes' Theorem)**를 기반으로 한 확률적 분류 알고리즘입니다. '나이브(Naive)'라는 이름은 모델이 모든 특성(feature)이 서로 **조건부 독립(conditionally independent)**이라고 가정하기 때문에 붙여졌습니다. 현실 데이터에서 이 가정이 완전히 성립하는 경우는 드물지만, 이 단순한 가정 덕분에 계산이 매우 효율적이고 고차원 희소 데이터(sparse data)에서도 뛰어난 성능을 발휘합니다.

나이브 베이즈는 텍스트 분류, 스팸 필터링, 감성 분석, 의료 진단 등 다양한 도메인에서 강력한 베이스라인으로 자리 잡고 있습니다. 학습 데이터가 적어도 비교적 안정적이며, 온라인 학습(incremental learning)도 지원하기 때문에 실시간 스트리밍 데이터 환경에서도 유용합니다.

---

## 수학적 배경

### 베이즈 정리

베이즈 정리는 사전 확률(prior)과 우도(likelihood)를 결합하여 사후 확률(posterior)을 계산합니다.

$$P(C \mid X) = \frac{P(X \mid C) \cdot P(C)}{P(X)}$$

- $P(C \mid X)$: 특성 벡터 $X$가 주어졌을 때 클래스 $C$일 확률 (사후 확률)
- $P(X \mid C)$: 클래스 $C$에서 $X$가 관측될 우도 (likelihood)
- $P(C)$: 클래스 $C$의 사전 확률 (prior)
- $P(X)$: 특성 벡터 $X$의 주변 확률 (모든 클래스에 대해 동일하므로 분류 시 무시 가능)

분류 목적에서는 분모 $P(X)$가 모든 클래스에 대해 동일하므로 다음과 같이 비례 관계만 사용합니다.

$$P(C \mid X) \propto P(X \mid C) \cdot P(C)$$

### 조건부 독립 가정

특성 벡터 $X = (x_1, x_2, \ldots, x_n)$에 대해 나이브 베이즈는 다음을 가정합니다.

$$P(X \mid C) = \prod_{i=1}^{n} P(x_i \mid C)$$

따라서 최종 분류 규칙은 다음과 같습니다.

$$\hat{C} = \arg\max_{C} \left[ P(C) \cdot \prod_{i=1}^{n} P(x_i \mid C) \right]$$

실제 구현에서는 수치 언더플로(underflow)를 방지하기 위해 로그를 취해 덧셈으로 변환합니다.

$$\hat{C} = \arg\max_{C} \left[ \log P(C) + \sum_{i=1}^{n} \log P(x_i \mid C) \right]$$

### 분포별 우도 모델

#### 가우시안 NB (Gaussian Naive Bayes)

연속형 특성에 사용하며, 클래스 $C$ 내 특성 $x_i$가 정규분포를 따른다고 가정합니다.

$$P(x_i \mid C) = \frac{1}{\sqrt{2\pi\sigma_{C,i}^2}} \exp\!\left(-\frac{(x_i - \mu_{C,i})^2}{2\sigma_{C,i}^2}\right)$$

#### 다항 NB (Multinomial Naive Bayes)

단어 빈도처럼 이산형 횟수 데이터에 사용합니다.

$$P(x_i \mid C) = \frac{\text{count}(x_i, C) + \alpha}{\sum_{j} \text{count}(x_j, C) + \alpha \cdot |V|}$$

$\alpha$는 라플라스 스무딩 파라미터이며, $|V|$는 어휘 크기입니다.

#### 베르누이 NB (Bernoulli Naive Bayes)

특성이 존재(1) 또는 부재(0)의 이진값일 때 사용합니다.

$$P(x_i \mid C) = P(x_i=1 \mid C)^{x_i} \cdot (1 - P(x_i=1 \mid C))^{1-x_i}$$

---

## 알고리즘 비교

| 모델 | 특성 유형 | 우도 분포 | 주요 용도 |
|---|---|---|---|
| Gaussian NB | 연속형 실수 | 정규 분포 | 붓꽃 분류, 의료 진단 |
| Multinomial NB | 이산형 횟수 | 다항 분포 | 텍스트 분류, TF 기반 특성 |
| Bernoulli NB | 이진형 (0/1) | 베르누이 분포 | 이진 BOW, 스팸 필터링 |

### Laplace Smoothing (라플라스 스무딩)

훈련 데이터에서 특정 특성-클래스 조합이 한 번도 등장하지 않으면 $P(x_i \mid C) = 0$이 되어 전체 곱이 0이 되는 문제(zero probability)가 발생합니다. 이를 방지하기 위해 스무딩 파라미터 $\alpha$ (보통 1)를 분자에 더합니다.

$$P(x_i \mid C) = \frac{\text{count}(x_i, C) + \alpha}{\sum_{j} \text{count}(x_j, C) + \alpha \cdot |V|}$$

$\alpha = 1$이면 라플라스 스무딩, $0 < \alpha < 1$이면 리드스톤(Lidstone) 스무딩이라 부릅니다.

---

## Python 구현

### Gaussian Naive Bayes — Iris 데이터셋

```python
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import accuracy_score, classification_report

# 데이터 로드
X, y = load_iris(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 모델 학습
gnb = GaussianNB()
gnb.fit(X_train, y_train)

# 평가
y_pred = gnb.predict(X_test)
print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
print(classification_report(y_test, y_pred, target_names=load_iris().target_names))

# 사전 확률 및 클래스별 평균·분산 확인
print("클래스별 사전 확률:", gnb.class_prior_)
print("클래스별 특성 평균:\n", gnb.theta_)  # shape: (n_classes, n_features)
```

```output
Accuracy: 0.9667
              precision    recall  f1-score   support

      setosa       1.00      1.00      1.00        10
  versicolor       1.00      0.90      0.95        10
   virginica       0.91      1.00      0.95        10

    accuracy                           0.97        30
   macro avg       0.97      0.97      0.97        30
weighted avg       0.97      0.97      0.97        30

클래스별 사전 확률: [0.33333333 0.33333333 0.33333333]
클래스별 특성 평균:
 [[4.985  3.415  1.4775 0.255 ]
 [5.93   2.75   4.2525 1.32  ]
 [6.61   2.98   5.58   2.04  ]]
```

### Multinomial Naive Bayes — 텍스트 분류

```python
from sklearn.datasets import fetch_20newsgroups
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score

# 데이터 로드 (4개 카테고리)
categories = ['rec.sport.hockey', 'sci.med', 'comp.graphics', 'talk.politics.guns']
train = fetch_20newsgroups(subset='train', categories=categories)
test  = fetch_20newsgroups(subset='test',  categories=categories)

# Pipeline: TF-IDF 벡터화 + Multinomial NB
pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(max_features=10000, stop_words='english')),
    ('nb',    MultinomialNB(alpha=0.1))  # alpha: 라플라스 스무딩 파라미터
])

pipeline.fit(train.data, train.target)
y_pred = pipeline.predict(test.data)
print(f"Accuracy: {accuracy_score(test.target, y_pred):.4f}")
```

```output
Accuracy: 0.9606
```

### Bernoulli Naive Bayes — 이진 특성

```python
from sklearn.naive_bayes import BernoulliNB
from sklearn.feature_extraction.text import CountVectorizer

# 이진 BOW (단어 존재 여부만)
vectorizer = CountVectorizer(binary=True, max_features=5000)
X_train_bin = vectorizer.fit_transform(train.data)
X_test_bin  = vectorizer.transform(test.data)

bnb = BernoulliNB(alpha=1.0)
bnb.fit(X_train_bin, train.target)
y_pred_bnb = bnb.predict(X_test_bin)
print(f"Bernoulli NB Accuracy: {accuracy_score(test.target, y_pred_bnb):.4f}")
```

```output
Bernoulli NB Accuracy: 0.8101
```

---

## 시각화 — Decision Boundary

2개의 특성을 선택하여 Gaussian NB의 결정 경계를 시각화합니다.

```python
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import load_iris
from sklearn.naive_bayes import GaussianNB

# Iris 데이터에서 특성 2개만 사용
X, y = load_iris(return_X_y=True)
X2 = X[:, :2]  # sepal length, sepal width

gnb = GaussianNB()
gnb.fit(X2, y)

# 메시 그리드 생성
x_min, x_max = X2[:, 0].min() - 0.5, X2[:, 0].max() + 0.5
y_min, y_max = X2[:, 1].min() - 0.5, X2[:, 1].max() + 0.5
xx, yy = np.meshgrid(
    np.linspace(x_min, x_max, 300),
    np.linspace(y_min, y_max, 300)
)

# 예측 확률 계산
Z = gnb.predict(np.c_[xx.ravel(), yy.ravel()])
Z = Z.reshape(xx.shape)

# 시각화
fig, ax = plt.subplots(figsize=(8, 6))
cmap_bg = plt.cm.Pastel1
cmap_pt = plt.cm.Set1

ax.contourf(xx, yy, Z, alpha=0.4, cmap=cmap_bg)
scatter = ax.scatter(X2[:, 0], X2[:, 1], c=y, cmap=cmap_pt,
                     edgecolors='k', s=60, linewidths=0.8)

ax.set_xlabel('Sepal Length (cm)', fontsize=12)
ax.set_ylabel('Sepal Width (cm)',  fontsize=12)
ax.set_title('Gaussian Naive Bayes — Decision Boundary (Iris)', fontsize=14)
legend = ax.legend(*scatter.legend_elements(),
                   title='Species', loc='upper right')
ax.add_artist(legend)
plt.tight_layout()
plt.savefig('gnb_decision_boundary.png', dpi=150)
plt.show()
```

![Naive-Bayes Fig 1](/media/figures/outputs/naive-bayes/naive-bayes_fig_1.png)

위 코드는 배경 색상으로 각 클래스의 결정 영역을, 점으로 실제 샘플을 표시합니다. 나이브 베이즈의 결정 경계는 가우시안 분포의 등고선 형태로 나타나며, 선형 모델(로지스틱 회귀)과 달리 곡선형 경계를 형성할 수 있습니다.

---

## 실전 팁

### 언제 나이브 베이즈를 써야 할까?

- **텍스트·NLP 태스크**: 단어 빈도 기반 특성이 많고 희소한 경우 Multinomial/Bernoulli NB가 강력합니다.
- **빠른 베이스라인이 필요할 때**: 데이터 탐색 초기 단계에서 빠르게 성능 가늠자를 세울 수 있습니다.
- **소규모 데이터**: 파라미터 수가 적어 과적합(overfitting) 위험이 낮습니다.
- **온라인(실시간) 학습**: `partial_fit()` API로 배치 없이 증분 학습이 가능합니다.
- **실시간 추론**: 학습된 모델의 추론이 극도로 빠릅니다.

### 장점

1. **학습·추론 속도**: $O(nd)$ 복잡도로 대규모 데이터에서도 빠릅니다.
2. **고차원 희소 데이터 강건성**: 특성 수가 샘플 수보다 많아도 잘 동작합니다.
3. **해석 가능성**: 각 클래스·특성별 확률을 직접 확인할 수 있습니다.
4. **소량 데이터**: 데이터가 적어도 비교적 안정적입니다.

### 단점

1. **조건부 독립 가정**: 특성 간 상관관계가 높으면 성능이 급격히 떨어집니다.
2. **수치 특성 분포 가정**: Gaussian NB는 정규 분포를 가정하므로 왜도(skewness)가 큰 데이터엔 부적합합니다.
3. **zero probability**: 스무딩 없이는 훈련에 없던 특성 조합에서 확률이 0이 됩니다.
4. **확률 추정 신뢰도**: 독립 가정 위반 시 클래스 확률 값 자체의 신뢰도가 낮아집니다.

### 조건부 독립 가정의 현실적 의미

텍스트에서 'machine'과 'learning'은 함께 등장할 가능성이 높지만, 나이브 베이즈는 이 두 단어를 독립적으로 처리합니다. 놀랍게도 이런 가정이 틀렸더라도 **분류 결과 자체는 올바른 경우가 많습니다**. 이는 나이브 베이즈가 확률 추정은 부정확하더라도 상대적 순위(ranking)는 잘 유지하기 때문입니다. 실제로 Domingos & Pazzani(1997)는 나이브 베이즈가 독립 가정 위반에도 최적 베이즈 분류기와 동일한 결정 경계를 만들 수 있음을 보였습니다.

### 하이퍼파라미터 튜닝

```python
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import TfidfVectorizer

pipeline = Pipeline([
    ('tfidf', TfidfVectorizer()),
    ('nb',    MultinomialNB())
])

param_grid = {
    'tfidf__max_features': [5000, 10000, None],
    'tfidf__ngram_range':  [(1, 1), (1, 2)],
    'nb__alpha':           [0.01, 0.1, 0.5, 1.0]
}

grid = GridSearchCV(pipeline, param_grid, cv=5, scoring='accuracy', n_jobs=-1)
grid.fit(train.data, train.target)
print("최적 파라미터:", grid.best_params_)
print(f"CV Accuracy: {grid.best_score_:.4f}")
```

```output
최적 파라미터: {'nb__alpha': 0.1, 'tfidf__max_features': None, 'tfidf__ngram_range': (1, 2)}
CV Accuracy: 0.9880
```

---

## 정리

나이브 베이즈는 '단순하지만 강력한' 알고리즘의 대표 사례입니다. 조건부 독립이라는 강한 가정에도 불구하고, 텍스트 분류 등 현실 문제에서 SVM이나 딥러닝과 견줄 만한 성능을 보일 때가 많습니다. 특히 빠른 프로토타입, 데이터가 부족한 환경, 고차원 희소 특성을 다룰 때 첫 번째 선택지로 고려할 만한 알고리즘입니다.