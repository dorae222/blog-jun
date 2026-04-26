<!-- infographic-hero -->
![ML Interview Guide 핵심 요약](figures/infographic.svg)

*Figure: ML Interview Guide 한 장 요약 인포그래픽*

## 개요

ML 면접은 단순히 알고리즘 이름을 외우는 것으로는 통과할 수 없습니다. 면접관은 세 가지 축을 통해 지원자를 평가합니다.

1. **이론 이해**: 수식과 직관적 설명을 동시에 요구합니다.
2. **코딩 능력**: 알고리즘을 직접 구현하거나 라이브러리를 능숙하게 다룰 수 있는지 봅니다.
3. **케이스 스터디**: 실제 비즈니스 문제를 ML로 어떻게 풀지 설계하는 능력을 평가합니다.

이 세 축을 균형 있게 준비하는 것이 핵심입니다. 이 글에서는 자주 나오는 질문과 모범 답안, 알고리즘 선택 전략, 실전 케이스 스터디 프레임워크를 정리합니다.

---

## 수학적 배경

면접에서 수식 설명을 요구하는 경우가 많습니다. 다음 네 가지는 반드시 손으로 쓸 수 있어야 합니다.

### 편향-분산 분해 (Bias-Variance Decomposition)

모델의 예측 오류는 세 가지 성분으로 분해됩니다.

$$E[(y - \hat{f}(x))^2] = \text{Bias}[\hat{f}(x)]^2 + \text{Var}[\hat{f}(x)] + \sigma^2$$

- **Bias**: 모델이 평균적으로 얼마나 틀리는지 (단순한 모델 → 높은 편향)
- **Variance**: 학습 데이터가 달라질 때 예측이 얼마나 흔들리는지 (복잡한 모델 → 높은 분산)
- **$\sigma^2$**: 줄일 수 없는 노이즈

### 경사하강법 (Gradient Descent)

$$\theta_{t+1} = \theta_t - \eta \cdot \nabla_{\theta} L(\theta_t)$$

- $\eta$: 학습률 (너무 크면 발산, 너무 작으면 수렴 느림)
- $\nabla_{\theta} L$: 손실 함수의 기울기
- Stochastic GD는 미니배치 단위로 기울기를 근사합니다.

### 정보 이득 (Information Gain)

결정 트리의 분할 기준으로 사용됩니다.

$$IG(D, A) = H(D) - \sum_{v \in Values(A)} \frac{|D_v|}{|D|} H(D_v)$$

여기서 $H(D) = -\sum_{k} p_k \log_2 p_k$ 는 엔트로피입니다.

### 소프트맥스 (Softmax)

다중 클래스 분류의 출력층에 사용됩니다.

$$\text{softmax}(z_i) = \frac{e^{z_i}}{\sum_{j=1}^{K} e^{z_j}}$$

수치 안정성을 위해 구현 시 $z_i - \max(z)$ 를 빼는 로그-합-지수 트릭을 사용합니다.

```python
import numpy as np

def softmax(z):
    z_stable = z - np.max(z)  # 수치 안정성
    exp_z = np.exp(z_stable)
    return exp_z / np.sum(exp_z)
```

---

![ML 개념 맵: 머신러닝 핵심 개념들의 관계를 정리한 마인드맵](figures/ml_concept_map.png)
*ML 개념 맵: 지도학습, 비지도학습, 강화학습의 주요 알고리즘과 개념 간 관계를 한눈에 파악할 수 있다.*

## 알고리즘 선택 가이드

"어떤 알고리즘을 쓸 건가요?"라는 질문에는 무조건 맥락을 먼저 파악해야 합니다.

### 선택 흐름도

```
문제 유형 확인
├── 지도 학습
│   ├── 분류
│   │   ├── 데이터 소규모 + 해석 필요  → Logistic Regression, Decision Tree
│   │   ├── 비선형 경계 + 중간 규모   → Random Forest, SVM
│   │   └── 대규모 + 고성능            → XGBoost/LightGBM, Neural Network
│   └── 회귀
│       ├── 선형 관계                 → Linear Regression, Ridge/Lasso
│       └── 비선형 관계               → Gradient Boosting, SVR
├── 비지도 학습
│   ├── 클러스터링
│   │   ├── 구형 클러스터              → K-Means
│   │   ├── 임의 형태                 → DBSCAN
│   │   └── 계층적 구조               → Hierarchical Clustering
│   └── 차원 축소
│       ├── 선형                      → PCA
│       └── 비선형                    → t-SNE, UMAP
└── 강화 학습                          → Q-Learning, Policy Gradient
```

### 답변 템플릿

> "저는 우선 데이터 규모, 피처 유형, 해석 가능성 요구 여부를 확인합니다. 이 문제의 경우 [조건]이므로 [알고리즘]을 첫 번째 선택으로 고려하겠습니다. 베이스라인으로 먼저 단순 모델을 시도하고, 성능이 부족하면 [대안]으로 이동하겠습니다."

---

![알고리즘 선택 가이드: 데이터 특성과 문제 유형에 따른 최적 알고리즘 선택 플로차트](figures/algorithm_selection_guide.png)
*알고리즘 선택 가이드: 데이터 크기, 피처 수, 해석 가능성 요구사항 등을 기준으로 적합한 알고리즘을 체계적으로 선택할 수 있다.*

## 자주 묻는 질문 & 모범 답안

### Q1. L1 vs L2 정규화의 차이는?

**L1 (Lasso)**: $\lambda \sum |w_i|$ ( 가중치를 완전히 0으로 만들어 **피처 선택** 효과가 있습니다. 희소(sparse) 모델에 적합합니다.

**L2 (Ridge)**: $\lambda \sum w_i^2$ ) 가중치를 0에 가깝게 줄이지만 0이 되진 않습니다. 모든 피처를 유지하면서 **과적합을 완화**합니다.

### Q2. Random Forest와 GBM의 차이는?

| 항목 | Random Forest | Gradient Boosting |
|------|--------------|-------------------|
| 학습 방식 | 병렬 (독립적 트리) | 순차 (이전 오류 보정) |
| 과적합 위험 | 낮음 | 높음 (튜닝 필요) |
| 속도 | 빠름 | 느림 (XGBoost는 최적화됨) |
| 성능 | 안정적 | 일반적으로 더 높음 |

### Q3. 클래스 불균형 처리법은?

1. **리샘플링**: 과소 표본 오버샘플링(SMOTE) 또는 다수 클래스 언더샘플링
2. **가중치 부여**: `class_weight='balanced'` 파라미터 사용
3. **평가 지표 변경**: Accuracy 대신 F1-score, AUC-ROC, PR-AUC 사용
4. **임계값 조정**: 기본 0.5 대신 도메인에 맞는 임계값 설정

### Q4. 과적합 방지법은?

- **데이터**: 더 많은 학습 데이터 수집, 데이터 증강
- **모델 구조**: 복잡도 감소 (레이어/노드 수 줄이기)
- **정규화**: L1/L2, Dropout, Batch Normalization
- **조기 종료**: 검증 손실이 증가하면 학습 중단
- **앙상블**: 여러 모델의 예측을 평균하여 분산 감소

### Q5. 교차 검증(Cross-Validation)이란?

k-fold CV는 데이터를 k개 폴드로 나눠, 각 폴드를 한 번씩 검증 세트로 사용합니다.

```python
from sklearn.model_selection import cross_val_score
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier(n_estimators=100)
scores = cross_val_score(model, X, y, cv=5, scoring='f1_macro')
print(f"평균 F1: {scores.mean():.4f} ± {scores.std():.4f}")
```

<!-- Execution error: NameError: name 'X' is not defined -->

**장점**: 데이터 전체를 학습/검증에 활용, 편향 없는 성능 추정
**단점**: 학습 시간 k배 증가

### Q6. 배치(Batch) / 에포크(Epoch) / 반복(Iteration)의 차이?

- **Epoch**: 전체 학습 데이터를 한 번 모두 통과한 것
- **Batch**: 한 번의 가중치 업데이트에 사용되는 데이터 묶음
- **Iteration**: 한 에포크를 완료하기 위한 배치 업데이트 횟수

예: 데이터 1000개, 배치 크기 100 → 1 Epoch = 10 Iterations

### Q7. Precision vs Recall 트레이드오프?

- **Precision** = $\frac{TP}{TP+FP}$: 양성 예측 중 실제 양성 비율 (스팸 필터에서 중요)
- **Recall** = $\frac{TP}{TP+FN}$: 실제 양성 중 감지한 비율 (암 진단에서 중요)
- F1-score는 두 지표의 조화 평균: $F1 = 2 \cdot \frac{P \cdot R}{P + R}$

### Q8. PCA는 어떻게 동작하나요?

1. 데이터 표준화
2. 공분산 행렬 계산: $C = \frac{1}{n} X^T X$
3. 고유값 분해로 주성분(고유벡터) 추출
4. 분산 설명 비율이 높은 k개의 성분 선택

### Q9. 경사소실/폭발 문제 해결법?

- **소실**: ReLU 활성화 함수, 배치 정규화, ResNet의 스킵 연결
- **폭발**: 그래디언트 클리핑 (`torch.nn.utils.clip_grad_norm_`)

### Q10. 하이퍼파라미터 튜닝 전략?

1. **Grid Search**: 모든 조합 탐색 (소규모에 적합)
2. **Random Search**: 무작위 샘플링 (효율적)
3. **Bayesian Optimization**: 이전 결과를 참고해 다음 탐색 지점 결정 (최고 효율)

---

## 케이스 스터디 접근법

실전 ML 문제 풀이에는 구조화된 프레임워크가 필수입니다.

### 6단계 프레임워크

**1단계: 문제 정의**
> "추천 시스템을 만들고 싶다"가 아니라 "사용자의 클릭률을 15% 향상시킨다"처럼 측정 가능한 목표로 변환합니다.

**2단계: 지표 선택**
- 오프라인 지표: AUC-ROC, NDCG, RMSE
- 온라인 지표: CTR, 전환율, 매출
- 가드레일 지표: 사용자 이탈률, 응답 속도

**3단계: 데이터 전략**
- 사용 가능한 데이터 소스 파악
- 피처 엔지니어링 계획
- 데이터 불균형/편향 처리

**4단계: 모델 선택 및 학습**
- 베이스라인 → 복잡한 모델 순서로 진행
- 빠른 실험을 위한 피처 중요도 분석

**5단계: 평가 및 개선**
- 오류 분석: 어떤 케이스에서 틀리는가?
- 에러 분포 확인 (체계적 오류 vs 랜덤 오류)

**6단계: 배포 및 모니터링**
- A/B 테스트 설계
- 모델 드리프트 모니터링
- 롤백 전략

---

## 실전 팁

### 화이트보드 코딩 팁

- 먼저 접근 방식을 말로 설명하고 코딩을 시작합니다.
- 완벽한 코드보다 **논리 흐름**이 중요합니다.
- 엣지 케이스(빈 입력, 단일 클래스 등)를 언급하면 가산점입니다.

```python
# 면접 예시: 경사하강법 직접 구현
def gradient_descent(X, y, lr=0.01, epochs=100):
    n, d = X.shape
    w = np.zeros(d)
    for _ in range(epochs):
        y_pred = X @ w
        grad = (2 / n) * X.T @ (y_pred - y)  # MSE 기울기
        w -= lr * grad
    return w
```

### 모르는 문제 대처법

> "정확한 답은 기억나지 않지만, 관련 원리로 추론해보면..."으로 시작하세요. 모른다고 침묵하는 것보다 추론 과정을 보여주는 것이 훨씬 좋은 인상을 줍니다.

### 비즈니스 맥락 연결하기

기술적 답변 후 항상 비즈니스 임팩트를 덧붙이세요.

> "L1 정규화로 불필요한 피처를 제거하면 모델이 더 해석 가능해지고, 추론 속도도 빨라져 운영 비용이 줄어듭니다."

이 한 문장이 단순 암기와 실무 경험을 구분짓는 차이입니다.

---

## 마무리

ML 면접 준비는 마라톤입니다. 핵심 수식 5개를 완벽히 이해하고, 알고리즘 선택 논리를 내 것으로 만들고, 케이스 스터디를 소리내어 연습하는 것이 가장 효과적입니다. 완벽한 답을 외우기보다 **사고 과정을 명확히 전달하는 연습**에 집중하세요.