## 개요: AI에서 ML, 그리고 DL까지

**인공지능(Artificial Intelligence, AI)**은 인간의 지능을 모방하는 시스템을 만드는 컴퓨터 과학의 한 분야입니다. 1956년 다트머스 회의(Dartmouth Conference)에서 John McCarthy가 "인공지능"이라는 용어를 처음 사용한 이래, AI는 규칙 기반 시스템(Expert System)에서 시작하여 오늘날의 대규모 언어 모델(LLM)에 이르기까지 긴 발전 과정을 거쳐왔습니다.

**머신러닝(Machine Learning, ML)**은 AI의 하위 분야로, 명시적으로 프로그래밍하지 않고도 데이터로부터 학습하여 성능을 개선하는 알고리즘을 연구합니다. Tom Mitchell(1997)의 정의에 따르면:

> 컴퓨터 프로그램이 어떤 태스크 $T$에 대해 경험 $E$로부터 학습한다고 하는 것은, 성능 척도 $P$로 측정한 $T$에서의 성능이 $E$를 통해 개선될 때이다.

**딥러닝(Deep Learning, DL)**은 ML의 하위 분야로, 다층 신경망(Deep Neural Network)을 사용하여 데이터의 계층적 표현(Hierarchical Representation)을 자동으로 학습합니다. 2012년 AlexNet이 ImageNet 대회에서 압도적인 성능을 보여준 이후, 딥러닝은 ML의 주류 방법론으로 자리잡았습니다.

이들의 관계를 정리하면 **AI $\supset$ ML $\supset$ DL** 입니다.

### 주요 발전 타임라인

| 시기 | 사건 | 의의 |
|------|------|------|
| 1956 | 다트머스 회의 | AI라는 학문 분야의 탄생 |
| 1957 | 퍼셉트론(Perceptron) | 최초의 학습 가능한 신경망 |
| 1986 | 역전파(Backpropagation) | 다층 신경망 학습 가능 |
| 1997 | SVM, Random Forest 등장 | 전통 ML의 황금기 |
| 2001 | Random Forest | 앙상블 학습의 대중화 |
| 2012 | AlexNet | 딥러닝 혁명의 시작 |
| 2017 | Transformer | 현대 AI의 기반 아키텍처 |
| 2022 | ChatGPT | 생성형 AI의 대중화 |

---

## 학습 유형 분류

머신러닝은 학습 데이터에 레이블(Label)이 존재하는지, 환경과 상호작용하는지에 따라 크게 네 가지 유형으로 분류됩니다.

![머신러닝 유형 벤 다이어그램: AI, ML, DL의 포함 관계와 학습 유형 분류](figures/ml_types_venn.png)
*머신러닝 유형 분류: AI, ML, DL의 포함 관계와 지도학습, 비지도학습, 강화학습, 자기지도학습의 위치를 보여준다.*

### 1. 지도학습 (Supervised Learning)

입력 $\mathbf{x}$와 정답 레이블 $y$의 쌍 $\{(\mathbf{x}_i, y_i)\}_{i=1}^{N}$으로부터 매핑 함수 $f: \mathbf{x} \rightarrow y$를 학습합니다.

- **회귀(Regression)**: 연속적인 값을 예측합니다. 예) 주택 가격 예측, 주가 예측, 기온 예측
- **분류(Classification)**: 이산적인 카테고리를 예측합니다. 예) 스팸 메일 분류, 이미지 인식, 질병 진단

대표 알고리즘: 선형 회귀(Linear Regression), 로지스틱 회귀(Logistic Regression), SVM, 의사결정 나무(Decision Tree), Random Forest, XGBoost

### 2. 비지도학습 (Unsupervised Learning)

레이블 없이 입력 데이터 $\{\mathbf{x}_i\}_{i=1}^{N}$만으로 데이터의 내재된 구조(Structure)를 발견합니다.

- **클러스터링(Clustering)**: 유사한 데이터를 그룹화합니다. 예) 고객 세분화, 문서 군집화
- **차원 축소(Dimensionality Reduction)**: 고차원 데이터를 저차원으로 변환합니다. 예) PCA, t-SNE, UMAP을 이용한 시각화
- **이상 탐지(Anomaly Detection)**: 정상 패턴에서 벗어난 데이터를 식별합니다. 예) 사기 탐지, 장비 이상 감지

대표 알고리즘: K-Means, DBSCAN, GMM, PCA, Autoencoder

### 3. 강화학습 (Reinforcement Learning)

에이전트(Agent)가 환경(Environment)과 상호작용하며, 보상(Reward)을 최대화하는 정책(Policy) $\pi$를 학습합니다.

$$\pi^* = \arg\max_{\pi} \mathbb{E}\left[\sum_{t=0}^{\infty} \gamma^t r_t \mid \pi\right]$$

여기서 $\gamma$는 할인율(Discount Factor), $r_t$는 시점 $t$의 보상입니다.

활용 예시: 게임 AI(AlphaGo, Atari), 로봇 제어, 추천 시스템 최적화, LLM 정렬(RLHF)

### 4. 자기지도학습 (Self-Supervised Learning)

레이블이 없는 데이터에서 **프리텍스트 태스크(Pretext Task)**를 스스로 생성하여 표현(Representation)을 학습합니다. 최근 대규모 사전학습(Pre-training)의 핵심 패러다임입니다.

- **언어 모델**: 다음 토큰 예측(GPT), 마스킹된 토큰 예측(BERT)
- **비전 모델**: 마스킹된 패치 복원(MAE), 대조 학습(SimCLR, CLIP)

자기지도학습은 지도학습과 비지도학습의 경계에 위치하며, 레이블 없는 방대한 데이터를 활용할 수 있다는 점에서 현대 AI의 핵심 학습 전략입니다.

---

## ML의 핵심 개념

### 학습이란 무엇인가: 데이터에서 패턴 발견

머신러닝에서 "학습"이란, 주어진 데이터셋 $\mathcal{D}$에서 손실 함수(Loss Function) $\mathcal{L}$을 최소화하는 모델 파라미터 $\theta$를 찾는 과정입니다:

$$\hat{\theta} = \arg\min_{\theta} \frac{1}{N}\sum_{i=1}^{N} \mathcal{L}(f_{\theta}(\mathbf{x}_i), y_i)$$

예를 들어, 회귀 문제에서 평균제곱오차(MSE)를 사용하면:

$$\mathcal{L}_{\text{MSE}} = \frac{1}{N}\sum_{i=1}^{N}(f_{\theta}(\mathbf{x}_i) - y_i)^2$$

분류 문제에서 교차 엔트로피(Cross-Entropy)를 사용하면:

$$\mathcal{L}_{\text{CE}} = -\frac{1}{N}\sum_{i=1}^{N}\sum_{c=1}^{C} y_{i,c} \log(\hat{y}_{i,c})$$

이 최적화 과정을 통해 모델은 데이터의 패턴을 포착하게 됩니다.

### 일반화 (Generalization): 학습 데이터를 넘어서

ML의 궁극적 목표는 학습 데이터에서만 잘 동작하는 것이 아니라, **처음 보는 데이터(Unseen Data)**에서도 좋은 성능을 보이는 것입니다. 이를 **일반화(Generalization)**라 합니다.

일반화 오차(Generalization Error)는 다음과 같이 분해할 수 있습니다:

$$\text{Error} = \text{Bias}^2 + \text{Variance} + \text{Irreducible Noise}$$

- **편향(Bias)**: 모델이 너무 단순하여 데이터의 패턴을 충분히 포착하지 못하는 오차 (과소적합, Underfitting)
- **분산(Variance)**: 모델이 학습 데이터의 노이즈까지 학습하여 새로운 데이터에 민감하게 반응하는 오차 (과적합, Overfitting)

이 두 요소 사이의 균형을 맞추는 것이 ML 모델 설계의 핵심이며, 이를 **편향-분산 트레이드오프(Bias-Variance Tradeoff)**라 합니다. 자세한 내용은 [[bias-variance-tradeoff]]에서 다룹니다.

### No Free Lunch 정리: 만능 알고리즘은 없다

Wolpert(1996)의 **No Free Lunch (NFL) 정리**는, 모든 가능한 문제에 대해 평균적으로 다른 모든 알고리즘보다 우수한 알고리즘은 존재하지 않음을 수학적으로 증명합니다.

이것이 의미하는 바는 명확합니다:

- 특정 문제에 최적인 알고리즘이 다른 문제에도 최적이라는 보장은 없음
- **데이터의 특성과 문제의 구조**에 따라 적절한 알고리즘을 선택해야 함
- 실무에서는 여러 알고리즘을 실험하고 비교하는 과정이 필수적

따라서 ML 실무자에게 다양한 알고리즘의 장단점과 적용 조건을 이해하는 것은 매우 중요합니다.

---

## ML 알고리즘 지도 (Landscape)

주요 ML 알고리즘을 체계적으로 분류하면 다음과 같습니다:

### 지도학습 알고리즘

| 분류 | 알고리즘 | 특징 |
|------|---------|------|
| 선형 모델 | Linear/Logistic Regression, Ridge, Lasso | 해석 가능, 빠른 학습 |
| 트리 기반 | Decision Tree, Random Forest, XGBoost, LightGBM | 비선형 관계 포착, 정형 데이터에 강함 |
| 커널 기반 | SVM, Kernel Ridge Regression | 고차원 공간에서의 분류 |
| 거리 기반 | KNN, Radius Neighbors | 단순하지만 직관적 |
| 확률 기반 | Naive Bayes, Gaussian Process | 불확실성 추정 가능 |
| 신경망 | MLP, CNN, RNN, Transformer | 대규모 데이터에서 높은 성능 |

### 비지도학습 알고리즘

| 분류 | 알고리즘 | 특징 |
|------|---------|------|
| 클러스터링 | K-Means, DBSCAN, 계층적 군집화 | 데이터 그룹화 |
| 차원 축소 | PCA, t-SNE, UMAP, LDA | 시각화 및 특성 압축 |
| 밀도 추정 | GMM, KDE | 데이터 분포 모델링 |
| 이상 탐지 | Isolation Forest, One-Class SVM | 비정상 데이터 식별 |

실무에서 **정형 데이터(Tabular Data)**에는 여전히 XGBoost, LightGBM 같은 그래디언트 부스팅 모델이 강력한 성능을 보이며, **비정형 데이터(이미지, 텍스트, 음성)**에는 딥러닝이 압도적인 우위를 보입니다.

---

## DL과의 차이점: 전통 ML vs 딥러닝

![모델 복잡도와 오차의 관계: 과소적합에서 과적합까지의 U자형 곡선](figures/complexity_vs_error.png)
*모델 복잡도에 따른 오차 변화: 복잡도가 너무 낮으면 과소적합, 너무 높으면 과적합이 발생하며, 최적 지점에서 일반화 성능이 가장 좋다.*

### Feature Engineering vs Feature Learning

전통 ML과 딥러닝의 가장 근본적인 차이는 **특성(Feature)**을 다루는 방식입니다:

- **전통 ML**: 도메인 전문가가 수동으로 특성을 설계합니다 (Feature Engineering). 예를 들어, 이미지 분류를 위해 HOG, SIFT 같은 수작업 특성 추출기를 사용합니다.
- **딥러닝**: 원시 데이터(Raw Data)로부터 유용한 특성을 자동으로 학습합니다 (Feature Learning / Representation Learning). 신경망의 각 층이 점진적으로 더 추상적인 특성을 학습합니다.

### 비교 정리

| 기준 | 전통 ML | 딥러닝 |
|------|---------|--------|
| 특성 추출 | 수동 (Feature Engineering) | 자동 (Feature Learning) |
| 데이터 요구량 | 상대적으로 적음 | 대규모 데이터 필요 |
| 해석 가능성 | 높음 (Decision Tree 등) | 낮음 (Black Box) |
| 계산 비용 | 낮음 (CPU로 충분) | 높음 (GPU/TPU 필요) |
| 정형 데이터 | 강함 (XGBoost 등) | 상대적으로 약함 |
| 비정형 데이터 | 약함 | 매우 강함 (이미지, 텍스트 등) |
| 학습 곡선 | 빠른 프로토타이핑 | 설정과 튜닝에 시간 필요 |

중요한 점은, 딥러닝이 등장했다고 해서 전통 ML이 불필요해진 것이 아니라는 것입니다. **문제의 특성, 데이터의 크기와 종류, 해석 가능성의 요구 수준**에 따라 적절한 방법론을 선택해야 합니다.

---

## 코드 예제: scikit-learn으로 보는 ML 워크플로우

다음은 sklearn을 사용하여 간단한 분류 문제를 풀어보는 예제입니다:

```python
import numpy as np
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

# 1. 데이터 로드
iris = load_iris()
X, y = iris.data, iris.target
print(f"데이터 크기: {X.shape}, 클래스 수: {len(np.unique(y))}")

# 2. 학습/테스트 분할
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 3. 전처리 (특성 스케일링)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# 4. 여러 모델 비교 (No Free Lunch: 최적 모델은 실험으로 찾아야 함)
models = {
    "Logistic Regression": LogisticRegression(max_iter=200),
    "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42),
}

for name, model in models.items():
    # 교차 검증으로 일반화 성능 추정
    cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5)
    print(f"\n[{name}]")
    print(f"  교차검증 정확도: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

    # 최종 학습 및 테스트 평가
    model.fit(X_train_scaled, y_train)
    y_pred = model.predict(X_test_scaled)
    print(f"  테스트 정확도: {accuracy_score(y_test, y_pred):.4f}")

# 5. 최종 모델 상세 평가
best_model = models["Random Forest"]
y_pred = best_model.predict(X_test_scaled)
print("\n=== 최종 분류 리포트 ===")
print(classification_report(y_test, y_pred, target_names=iris.target_names))
```

```output
데이터 크기: (150, 4), 클래스 수: 3

[Logistic Regression]
  교차검증 정확도: 0.9583 (+/- 0.0264)
  테스트 정확도: 0.9333

[Random Forest]
  교차검증 정확도: 0.9500 (+/- 0.0167)
  테스트 정확도: 0.9000

=== 최종 분류 리포트 ===
              precision    recall  f1-score   support

      setosa       1.00      1.00      1.00        10
  versicolor       0.82      0.90      0.86        10
   virginica       0.89      0.80      0.84        10

    accuracy                           0.90        30
   macro avg       0.90      0.90      0.90        30
weighted avg       0.90      0.90      0.90        30
```

이 예제는 ML의 기본 워크플로우인 **데이터 로드 -> 전처리 -> 모델 학습 -> 평가**의 흐름을 보여줍니다. 더 상세한 워크플로우는 [[ml-workflow]]에서 다룹니다.

---

## 정리

머신러닝은 데이터에서 패턴을 발견하여 예측과 의사결정을 자동화하는 강력한 도구입니다. 이 글에서 다룬 핵심 내용을 정리하면:

1. **AI $\supset$ ML $\supset$ DL**의 포함 관계를 이해하고, 각각의 역할을 구분할 것
2. **학습 유형**(지도/비지도/강화/자기지도)에 따른 문제 정의와 접근법을 파악할 것
3. **일반화**가 ML의 궁극적 목표이며, 편향-분산 트레이드오프를 이해할 것
4. **No Free Lunch 정리**에 따라 만능 알고리즘은 없으므로, 문제에 맞는 알고리즘을 실험적으로 선택할 것
5. 전통 ML과 딥러닝은 **대체 관계가 아닌 상호 보완 관계**임을 인식할 것

> **다음 글 안내**: ML의 전체적인 작업 흐름(문제 정의부터 배포까지)에 대해서는 [[ml-workflow]]를 참고하세요. 모델의 복잡도를 조절하는 핵심 원리인 편향-분산 트레이드오프는 [[bias-variance-tradeoff]]에서 깊이 다룹니다.

## 관련 문서

- [[ml-workflow]] - ML 워크플로우: 문제 정의에서 배포까지
- [[bias-variance-tradeoff]] - 편향-분산 트레이드오프
- [[data-preprocessing]] - 데이터 전처리
- [[feature-engineering]] - 특성 공학
- [[ensemble-overview]] - 앙상블 학습 개요
- [[reinforcement-learning-basics]] - 강화학습 기초
- [[sklearn-pipeline]] - scikit-learn 파이프라인