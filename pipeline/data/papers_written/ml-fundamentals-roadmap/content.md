# 머신러닝 기초부터 실전까지: 학습 로드맵

## 개요

머신러닝(Machine Learning)은 데이터로부터 패턴을 학습하여 예측과 결정을 수행하는 AI의 핵심 분야입니다. 딥러닝이 각광받는 현재에도, 전통적 머신러닝 알고리즘과 이론은 데이터 과학, 산업 AI, 연구 등 다양한 영역에서 필수적인 기초 지식으로 활용됩니다.

이 가이드는 머신러닝의 **수학적 기초부터 실전 응용까지** 51개 주제를 체계적으로 정리합니다. 확률/통계, 선형대수, 최적화 이론 등 수학 기초부터 지도/비지도/강화학습의 핵심 알고리즘, 모델 평가, 인과추론, MLOps까지 단계별로 학습할 수 있는 로드맵을 제시합니다.

### 왜 머신러닝 기초가 중요한가?

딥러닝의 시대에도 머신러닝 기초가 중요한 이유는 분명합니다. 첫째, 모든 딥러닝 모델은 머신러닝 이론(경사하강법, 정규화, 편향-분산 트레이드오프 등) 위에 구축됩니다. 둘째, 많은 실무 문제에서 XGBoost, LightGBM 등 전통적 ML 알고리즘이 여전히 최고의 성능을 보입니다. 셋째, 데이터 전처리, 피처 엔지니어링, 모델 평가 등 ML 파이프라인의 핵심은 딥러닝에서도 동일하게 적용됩니다.

---

## 핵심 흐름: 머신러닝 학습 체계

### Part 1: 기초 개념 (Fundamentals)

머신러닝의 전체 그림과 핵심 개념을 이해합니다.

| 주제 | 핵심 내용 | 관련 포스트 |
|------|----------|------------|
| ML 개론 | AI/ML/DL 관계, 학습 유형, No Free Lunch | [ML 개론](/post/ml-overview) |
| ML 워크플로 | 문제 정의→데이터→학습→평가→배포 | [ML 워크플로](/post/ml-workflow) |
| 편향-분산 트레이드오프 | 과적합/과소적합, 모델 복잡도 | [편향-분산](/post/bias-variance-tradeoff) |

### Part 2: 수학적 기초 (Mathematical Foundations)

ML을 깊이 이해하기 위한 수학적 토대입니다.

| 주제 | 핵심 내용 | 관련 포스트 |
|------|----------|------------|
| 선형대수 | 벡터, 행렬, 고유값 분해, SVD | [선형대수](/post/linear-algebra-for-ml) |
| 확률과 베이즈 | 확률 분포, 베이즈 정리, MLE/MAP | [확률/베이즈](/post/probability-bayes) |
| 정보이론 | 엔트로피, KL-Divergence, Cross-Entropy | [정보이론](/post/information-theory) |
| 최적화 이론 | 경사하강법, 볼록 최적화, 라그랑주 | [최적화](/post/optimization-theory) |

### Part 3: 데이터 전처리 (Data Preprocessing)

실무에서 가장 많은 시간이 소요되는 단계입니다.

| 주제 | 핵심 내용 | 관련 포스트 |
|------|----------|------------|
| 데이터 전처리 | 결측치, 스케일링, 인코딩 | [데이터 전처리](/post/data-preprocessing) |
| 피처 엔지니어링 | 피처 생성, 선택, 변환 | [피처 엔지니어링](/post/feature-engineering) |
| 불균형 데이터 | SMOTE, 오버/언더샘플링, 비용 민감 학습 | [불균형 데이터](/post/imbalanced-data) |

### Part 4: 지도학습 — 회귀 (Supervised: Regression)

연속적인 값을 예측하는 모델입니다.

| 주제 | 핵심 내용 | 관련 포스트 |
|------|----------|------------|
| 선형 회귀 | 최소제곱법, 정규방정식 | [선형 회귀](/post/linear-regression) |
| 정규화 회귀 | Ridge, Lasso, Elastic Net | [정규화 회귀](/post/regularized-regression) |
| 다항 회귀 | 비선형 관계 모델링 | [다항 회귀](/post/polynomial-regression) |

### Part 5: 지도학습 — 분류 (Supervised: Classification)

범주를 예측하는 모델입니다.

| 주제 | 핵심 내용 | 관련 포스트 |
|------|----------|------------|
| 로지스틱 회귀 | 시그모이드 함수, 이진 분류 | [로지스틱 회귀](/post/logistic-regression) |
| 나이브 베이즈 | 베이즈 정리 기반 분류 | [나이브 베이즈](/post/naive-bayes) |
| KNN | 거리 기반 분류/회귀 | [KNN](/post/knn) |
| SVM | 최대 마진 분류, 커널 트릭 | [SVM](/post/svm) |
| 결정 트리 | 정보 이득, 지니 계수 | [결정 트리](/post/decision-tree) |

### Part 6: 앙상블 학습 (Ensemble Methods)

여러 모델을 결합하여 성능을 높이는 기법입니다. 실무에서 가장 많이 사용되는 모델군입니다.

| 주제 | 핵심 내용 | 관련 포스트 |
|------|----------|------------|
| 앙상블 개요 | 배깅, 부스팅, 스태킹 | [앙상블 개요](/post/ensemble-overview) |
| 랜덤 포레스트 | 배깅 + 피처 랜덤 선택 | [랜덤 포레스트](/post/random-forest) |
| 그래디언트 부스팅 | 잔차 학습, 순차적 모델 추가 | [그래디언트 부스팅](/post/gradient-boosting) |
| XGBoost/LightGBM | 산업 표준 부스팅 라이브러리 | [XGBoost/LightGBM](/post/xgboost-lightgbm) |

### Part 7: 비지도학습 (Unsupervised Learning)

레이블 없이 데이터의 구조를 발견합니다.

| 주제 | 핵심 내용 | 관련 포스트 |
|------|----------|------------|
| K-Means | 중심점 기반 군집화 | [K-Means](/post/kmeans-clustering) |
| 고급 클러스터링 | DBSCAN, 계층적 클러스터링 | [고급 클러스터링](/post/advanced-clustering) |
| GMM | 가우시안 혼합 모델, EM 알고리즘 | [GMM](/post/gmm) |
| PCA | 주성분 분석, 차원 축소 | [PCA](/post/pca) |
| t-SNE/UMAP | 비선형 차원 축소, 시각화 | [t-SNE/UMAP](/post/tsne-umap) |

### Part 8: 모델 평가 (Model Evaluation)

모델의 성능을 정확히 측정하고 비교하는 방법입니다.

| 주제 | 핵심 내용 | 관련 포스트 |
|------|----------|------------|
| 분류 메트릭 | Accuracy, Precision, Recall, F1, AUC | [분류 메트릭](/post/classification-metrics) |
| 회귀 메트릭 | MSE, RMSE, MAE, R^2 | [회귀 메트릭](/post/regression-metrics) |
| 교차 검증 | K-Fold, Stratified, Time Series Split | [교차 검증](/post/cross-validation) |
| 모델 해석력 | SHAP, LIME, Feature Importance | [모델 해석력](/post/model-interpretability) |

### Part 9: 인과추론 (Causal Inference)

상관관계를 넘어 인과관계를 추론하는 방법론입니다.

| 주제 | 핵심 내용 | 관련 포스트 |
|------|----------|------------|
| 인과추론 개요 | 잠재 결과 프레임워크, ATE | [인과추론 개요](/post/causal-inference-overview) |
| 패널 데이터/고정효과 | 개체 고정효과, 시간 고정효과 | [패널 데이터](/post/panel-data-fixed-effects) |
| 이중차분법(DID) | 처치-대조 그룹 비교 | [DID](/post/did) |
| RD/IV | 회귀불연속, 도구변수 | [RD/IV](/post/rd-iv) |
| PSM/합성통제 | 성향점수 매칭, 합성통제법 | [PSM/합성통제](/post/psm-synthetic-control) |

### Part 10: 고급 주제 (Advanced Topics)

특수한 문제 영역과 고급 기법을 다룹니다.

| 주제 | 핵심 내용 | 관련 포스트 |
|------|----------|------------|
| 베이지안 ML | 사전/사후 분포, MCMC | [베이지안 ML](/post/bayesian-ml) |
| 준지도학습 | 레이블 부족 문제 해결 | [준지도학습](/post/semi-supervised-learning) |
| 토픽 모델링 | LDA, 문서 주제 분류 | [토픽 모델링](/post/topic-modeling) |
| 커널 방법 | 커널 트릭, RKHS | [커널 방법](/post/kernel-methods) |
| 시계열 ML | ARIMA, Prophet, 시계열 특징 | [시계열 ML](/post/time-series-ml) |
| 추천 시스템 | 협업 필터링, 콘텐츠 기반 | [추천 시스템](/post/recommendation-systems) |
| NLP 전통 ML | TF-IDF, Word2Vec, 감성분석 | [NLP 전통 ML](/post/nlp-traditional-ml) |
| 이상 탐지 | Isolation Forest, LOF | [이상 탐지](/post/anomaly-detection) |
| 강화학습 기초 | MDP, Q-Learning, Policy Gradient | [강화학습](/post/reinforcement-learning-basics) |

### Part 11: 실전과 MLOps (Practice & MLOps)

ML을 실무에 적용하고 운영하는 방법입니다.

| 주제 | 핵심 내용 | 관련 포스트 |
|------|----------|------------|
| Scikit-learn Pipeline | 파이프라인 구축, 재현 가능한 ML | [sklearn Pipeline](/post/sklearn-pipeline) |
| A/B 테스트 | 가설 검정, 통계적 유의성 | [A/B 테스트](/post/ab-testing) |
| ML 시스템 설계 | 대규모 ML 시스템 설계 원칙 | [ML 시스템 설계](/post/ml-system-design) |
| MLOps 기초 | CI/CD for ML, 모니터링, 재학습 | [MLOps](/post/mlops-fundamentals) |
| AutoML | 자동화된 ML 파이프라인 | [AutoML](/post/automl) |
| ML 인터뷰 가이드 | ML 면접 준비 전략 | [ML 인터뷰](/post/ml-interview-guide) |

---

## 주요 알고리즘 요약 테이블

| 알고리즘 | 유형 | 장점 | 단점 | 적합한 문제 |
|---------|------|------|------|------------|
| [선형 회귀](/post/linear-regression) | 회귀 | 해석 용이, 빠름 | 비선형 관계 표현 불가 | 연속값 예측 |
| [로지스틱 회귀](/post/logistic-regression) | 분류 | 확률 출력, 해석 용이 | 비선형 경계 어려움 | 이진 분류 |
| [SVM](/post/svm) | 분류/회귀 | 고차원에 강함 | 대규모 데이터 느림 | 소규모 고차원 |
| [결정 트리](/post/decision-tree) | 분류/회귀 | 해석 최고 | 과적합 경향 | 설명 필요한 문제 |
| [랜덤 포레스트](/post/random-forest) | 앙상블 | 안정적, 과적합 적음 | 느린 추론 | 범용 |
| [XGBoost](/post/xgboost-lightgbm) | 앙상블 | 최고 성능 (테이블) | 하이퍼파라미터 많음 | 테이블 데이터 |
| [K-Means](/post/kmeans-clustering) | 군집화 | 빠름, 단순 | 클러스터 수 지정 필요 | 구형 클러스터 |
| [PCA](/post/pca) | 차원 축소 | 분산 최대 보존 | 선형 변환만 가능 | 차원 축소/시각화 |
| [KNN](/post/knn) | 분류/회귀 | 학습 불필요 | 추론 느림, 고차원 약함 | 소규모 데이터 |
| [나이브 베이즈](/post/naive-bayes) | 분류 | 매우 빠름 | 독립 가정 | 텍스트 분류 |

---

## 추천 학습 경로

### 초심자 (ML 입문)

ML의 기본 개념과 핵심 알고리즘을 이해합니다.

**1단계: 개념 잡기**
1. [ML 개론](/post/ml-overview) — AI/ML/DL의 관계
2. [ML 워크플로](/post/ml-workflow) — 전체 프로세스 이해
3. [편향-분산 트레이드오프](/post/bias-variance-tradeoff) — 모델 복잡도의 핵심

**2단계: 핵심 알고리즘**
4. [선형 회귀](/post/linear-regression) → [로지스틱 회귀](/post/logistic-regression)
5. [결정 트리](/post/decision-tree) → [랜덤 포레스트](/post/random-forest)
6. [K-Means](/post/kmeans-clustering) → [PCA](/post/pca)

**3단계: 평가**
7. [분류 메트릭](/post/classification-metrics) + [회귀 메트릭](/post/regression-metrics)
8. [교차 검증](/post/cross-validation)

### 중급 (실무 역량)

고급 알고리즘과 실무 기법을 학습합니다.

**1단계: 수학 기초**
1. [선형대수](/post/linear-algebra-for-ml)
2. [확률/베이즈](/post/probability-bayes)
3. [최적화 이론](/post/optimization-theory)

**2단계: 고급 알고리즘**
4. [SVM](/post/svm) + [커널 방법](/post/kernel-methods)
5. [그래디언트 부스팅](/post/gradient-boosting) → [XGBoost/LightGBM](/post/xgboost-lightgbm)
6. [GMM](/post/gmm) + [고급 클러스터링](/post/advanced-clustering)

**3단계: 실전 기법**
7. [데이터 전처리](/post/data-preprocessing) + [피처 엔지니어링](/post/feature-engineering)
8. [불균형 데이터](/post/imbalanced-data) 처리
9. [모델 해석력](/post/model-interpretability) — SHAP, LIME
10. [sklearn Pipeline](/post/sklearn-pipeline)

### 고급 (전문가 역량)

특수 문제와 MLOps를 마스터합니다.

**1단계: 특수 문제**
1. [시계열 ML](/post/time-series-ml)
2. [추천 시스템](/post/recommendation-systems)
3. [이상 탐지](/post/anomaly-detection)

**2단계: 통계적 기법**
4. [인과추론 개요](/post/causal-inference-overview) → [DID](/post/did) → [PSM/합성통제](/post/psm-synthetic-control)
5. [A/B 테스트](/post/ab-testing)
6. [베이지안 ML](/post/bayesian-ml)

**3단계: 시스템과 운영**
7. [ML 시스템 설계](/post/ml-system-design)
8. [MLOps](/post/mlops-fundamentals)
9. [AutoML](/post/automl)
10. [ML 인터뷰 가이드](/post/ml-interview-guide)

---

## ML과 딥러닝의 교차점

머신러닝 기초는 딥러닝 이해의 필수 전제입니다.

| ML 기초 | 딥러닝 연결 | 관련 포스트 |
|---------|------------|------------|
| 경사하강법 | Optimizer (Adam, SGD) | [최적화](/post/optimization-theory) |
| 정규화 | Dropout, Weight Decay | [정규화 회귀](/post/regularized-regression) |
| 앙상블 | MoE (Mixture of Experts) | [앙상블 개요](/post/ensemble-overview) |
| PCA/차원축소 | AutoEncoder, VAE | [PCA](/post/pca) |
| 교차 검증 | 학습/검증/테스트 분리 | [교차 검증](/post/cross-validation) |
| 강화학습 | RLHF, PPO, DPO | [강화학습](/post/reinforcement-learning-basics) |

---

## 관련 카테고리

- [AI/ML 아키텍처 로드맵](/post/ai-ml-architecture-roadmap) — 전체 AI/ML 지형도
- [AI 핵심 기법 총정리](/post/ai-core-techniques-guide) — 딥러닝 기법으로의 확장
- [AWS & Cloud 인프라 학습 가이드](/post/aws-cloud-infrastructure-guide) — SageMaker, Bedrock 등 ML 인프라
