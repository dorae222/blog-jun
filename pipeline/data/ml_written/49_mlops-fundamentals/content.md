## 개요

MLOps(Machine Learning Operations)는 **ML + DevOps**의 합성어로, 머신러닝 모델을 단순히 실험 노트북 수준에서 끝내지 않고 프로덕션 환경에서 안정적으로 운영하기 위한 일련의 실천 방법론입니다. 전통적인 소프트웨어 DevOps가 코드 빌드·테스트·배포·모니터링을 자동화하듯, MLOps는 **데이터 수집 → 피처 엔지니어링 → 모델 학습 → 평가 → 배포 → 모니터링 → 재학습** 사이클 전체를 자동화하고 재현 가능하게 만드는 것을 목표로 합니다.

아직 MLOps 없이 운영하고 있다면 다음과 같은 고통이 익숙할 것입니다.

- "지난달에 학습한 모델 파라미터가 뭐였지?"
- "같은 코드인데 왜 재현이 안 되지?"
- "모델을 배포했더니 정확도가 갑자기 떨어졌어."

MLOps는 이 모든 문제를 시스템적으로 해결합니다.

---

## 수학적 배경: SLO/SLA와 드리프트 지표

### 가용성(Availability) 계산

프로덕션 ML 서비스에서는 **SLO(Service Level Objective)**와 **SLA(Service Level Agreement)**가 중요합니다.

$$\text{Availability} = \frac{\text{MTBF}}{\text{MTBF} + \text{MTTR}} \times 100\%$$

- **MTBF**: Mean Time Between Failures (평균 고장 간격)
- **MTTR**: Mean Time To Recovery (평균 복구 시간)

예를 들어 MTBF = 720시간, MTTR = 1시간이면 가용성은 약 $\frac{720}{721} \approx 99.86\%$입니다. ML 서비스에서는 모델 성능 저하(드리프트)도 "장애"의 일종으로 간주해야 합니다.

### 데이터 드리프트 감지: PSI

Data drift는 입력 분포 $P_{train}(X)$와 서빙 분포 $P_{serve}(X)$가 달라지는 현상, Concept drift는 $P(Y|X)$ 자체가 변하는 현상입니다. Population Stability Index(PSI)는 흔히 사용되는 드리프트 지표입니다.

$$\text{PSI} = \sum_{i=1}^{n} (A_i - E_i) \ln\left(\frac{A_i}{E_i}\right)$$

$PSI < 0.1$이면 안정, $0.1 \leq PSI < 0.2$이면 경고, $PSI \geq 0.2$이면 재학습이 필요하다는 경험적 기준을 많이 사용합니다.

---

![MLOps 라이프사이클: 데이터 수집부터 모델 배포, 모니터링, 재학습까지의 순환 구조](figures/mlops_lifecycle.png)
*MLOps 라이프사이클: 데이터 준비, 모델 학습, 평가, 배포, 모니터링, 재학습의 순환 구조를 통해 지속적인 모델 개선이 이루어진다.*

## ML 라이프사이클과 핵심 패턴

### ML 파이프라인 전체 흐름

```
데이터 수집/검증
      ↓
피처 엔지니어링 (Feature Store)
      ↓
실험 추적 (MLflow / Weights & Biases)  ←── 반복
      ↓
모델 레지스트리 (DVC / MLflow Registry)
      ↓
CI/CD for ML (GitHub Actions)
      ↓
배포 전략 (Blue-Green / Canary / Shadow)
      ↓
모니터링 (Prometheus / Grafana / Evidently)
      ↓
자동 재학습 트리거 ──────────────────────┘
```

### 실험 추적: MLflow vs Weights & Biases

**MLflow**는 오픈소스 실험 추적 플랫폼입니다. 핵심 개념은 다음과 같습니다.

- **Experiment**: 같은 목표를 가진 실험들의 묶음
- **Run**: 단일 학습 실행 (파라미터, 메트릭, 아티팩트 기록)
- **Model Registry**: 스테이징/프로덕션 모델 버전 관리

**Weights & Biases(W&B)**는 시각화와 팀 협업에 강점이 있는 클라우드 기반 실험 추적 도구입니다. 딥러닝 팀에서 특히 인기가 높으며, 하이퍼파라미터 탐색(Sweeps)과 실시간 학습 곡선 시각화가 뛰어납니다.

**선택 기준**: 소규모 팀이나 온프레미스 환경이라면 MLflow, 빠른 시각화와 팀 협업이 중요하다면 W&B를 고려합니다.

### 모델 버전 관리: DVC

DVC(Data Version Control)는 Git과 연동하여 대용량 데이터셋과 모델 파일을 버전 관리합니다. `.dvc` 파일을 Git에 커밋하고 실제 바이너리는 S3/GCS 등 원격 스토리지에 저장합니다.

```bash
# DVC 초기화 및 원격 스토리지 설정
dvc init
dvc remote add -d s3remote s3://my-ml-bucket/dvc

# 데이터셋 버전 관리 시작
dvc add data/train.csv
git add data/train.csv.dvc .gitignore
git commit -m "데이터셋 v1 추가"
dvc push

# 이전 데이터셋으로 되돌리기
git checkout v1.0
dvc pull
```

### CI/CD for ML

전통적인 CI/CD에 ML 특화 단계를 추가합니다.

1. **코드 품질**: flake8, black, mypy
2. **데이터 검증**: Great Expectations
3. **모델 학습 및 평가**: 기준 모델 대비 성능 비교
4. **모델 등록**: MLflow Registry 자동 등록
5. **배포**: 컨테이너 빌드 및 쿠버네티스 배포

### 배포 전략 비교

| 전략 | 설명 | 장점 | 단점 |
|------|------|------|------|
| **Blue-Green** | 구 버전(Blue)과 신 버전(Green)을 동시 유지, 트래픽 전환 | 빠른 롤백 | 인프라 비용 2배 |
| **Canary** | 신 버전에 트래픽 일부(예: 5%)만 점진적 전달 | 위험 최소화 | 모니터링 복잡 |
| **Shadow** | 신 버전이 실제 트래픽을 미러링해 예측만 수행 | 프로덕션 영향 없음 | 실제 피드백 없음 |

---

## Python 구현: MLflow 실험 추적

```python
import mlflow
import mlflow.sklearn
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
from sklearn.datasets import load_breast_cancer

# 데이터 준비
data = load_breast_cancer()
X_train, X_test, y_train, y_test = train_test_split(
    data.data, data.target, test_size=0.2, random_state=42
)

# MLflow 실험 설정
mlflow.set_tracking_uri("http://localhost:5000")  # MLflow 서버 주소
mlflow.set_experiment("breast-cancer-classification")

# 하이퍼파라미터 탐색
for n_estimators in [50, 100, 200]:
    for max_depth in [3, 5, None]:
        with mlflow.start_run(run_name=f"rf_n{n_estimators}_d{max_depth}"):
            # 파라미터 기록
            mlflow.log_param("n_estimators", n_estimators)
            mlflow.log_param("max_depth", max_depth)
            mlflow.log_param("random_state", 42)

            # 모델 학습
            model = RandomForestClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                random_state=42
            )
            model.fit(X_train, y_train)

            # 평가 및 메트릭 기록
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred, average="weighted")

            mlflow.log_metric("accuracy", accuracy)
            mlflow.log_metric("f1_score", f1)

            # 모델 아티팩트 저장 (sklearn 포맷, 레지스트리에 자동 등록)
            mlflow.sklearn.log_model(
                sk_model=model,
                artifact_path="random_forest_model",
                registered_model_name="BreastCancerClassifier"
            )

            print(f"n_estimators={n_estimators}, max_depth={max_depth} "
                  f"-> accuracy={accuracy:.4f}, f1={f1:.4f}")

print("실험 완료! MLflow UI(http://localhost:5000)에서 결과를 확인하세요.")
```

```output
<!-- Pre-computed result needed -->
```

### 모델 레지스트리 스테이지 전환

```python
from mlflow.tracking import MlflowClient

client = MlflowClient()

# Staging으로 전환 (QA 검증 단계)
client.transition_model_version_stage(
    name="BreastCancerClassifier",
    version=1,
    stage="Staging"
)

# 검증 통과 후 Production으로 승격
client.transition_model_version_stage(
    name="BreastCancerClassifier",
    version=1,
    stage="Production"
)

# Production 모델 불러오기
production_model = mlflow.sklearn.load_model(
    model_uri="models:/BreastCancerClassifier/Production"
)
```

### GitHub Actions를 활용한 ML CI/CD

```yaml
# .github/workflows/ml-ci.yml
name: ML CI Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  train-and-evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Python 환경 설정
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: 의존성 설치
        run: pip install -r requirements.txt

      - name: 데이터 검증
        run: python scripts/validate_data.py

      - name: 모델 학습 및 평가
        run: python scripts/train.py
        env:
          MLFLOW_TRACKING_URI: ${{ secrets.MLFLOW_TRACKING_URI }}

      - name: 성능 기준 검사 (accuracy >= 0.90)
        run: python scripts/check_model_performance.py --threshold 0.90

      - name: Docker 이미지 빌드 및 푸시
        if: github.ref == 'refs/heads/main'
        run: |
          docker build -t dorae222/ml-model:${{ github.sha }} .
          docker push dorae222/ml-model:${{ github.sha }}
```

---

![MLOps 성숙도 단계: 수동 프로세스에서 완전 자동화까지의 MLOps 성숙도 모델](figures/mlops_maturity_levels.png)
*MLOps 성숙도 단계: Level 0(수동)부터 Level 2(완전 자동화)까지 조직의 MLOps 성숙도를 단계적으로 보여준다.*

## 시각화: MLOps 파이프라인 다이어그램

```python
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

fig, ax = plt.subplots(figsize=(14, 5))
ax.set_xlim(0, 14)
ax.set_ylim(0, 5)
ax.axis("off")

# 파이프라인 단계 정의 (x좌표, 레이블, 색상)
stages = [
    (1.0, "데이터\n수집",   "#4A90D9"),
    (3.0, "피처\n엔지니어링", "#7B68EE"),
    (5.0, "모델\n학습",   "#50C878"),
    (7.0, "실험\n추적",   "#FFD700"),
    (9.0, "CI/CD",      "#FF8C00"),
    (11.0, "배포",       "#FF6B6B"),
    (13.0, "모니터링",    "#20B2AA")
]

for x, label, color in stages:
    rect = mpatches.FancyBboxPatch(
        (x - 0.7, 1.5), 1.4, 1.5,
        boxstyle="round,pad=0.1",
        facecolor=color, edgecolor="white", linewidth=2, alpha=0.85
    )
    ax.add_patch(rect)
    ax.text(x, 2.25, label, ha="center", va="center",
            fontsize=9, fontweight="bold", color="white")

# 단계 간 화살표
for i in range(len(stages) - 1):
    x1 = stages[i][0] + 0.7
    x2 = stages[i + 1][0] - 0.7
    ax.annotate("", xy=(x2, 2.25), xytext=(x1, 2.25),
                arrowprops=dict(arrowstyle="->", color="#555", lw=1.5))

# 모니터링 → 재학습 피드백 루프
ax.annotate("", xy=(5.0, 1.5), xytext=(13.0, 1.5),
            arrowprops=dict(arrowstyle="->", color="#FF6B6B",
                            lw=1.5, connectionstyle="arc3,rad=-0.3"))
ax.text(9.0, 0.5, "드리프트 감지 시 자동 재학습 트리거",
        ha="center", fontsize=8, color="#FF6B6B", style="italic")

ax.set_title("MLOps 파이프라인 전체 흐름",
             fontsize=13, fontweight="bold", pad=15)
plt.tight_layout()
plt.savefig("mlops_pipeline.png", dpi=150, bbox_inches="tight")
plt.show()
```

![Mlops-Fundamentals Fig 1](/media/figures/outputs/mlops-fundamentals/mlops-fundamentals_fig_1.png)

### 실험 추적 대시보드 개념도

MLflow UI(`mlflow ui` 실행 후 `http://localhost:5000`)에서 볼 수 있는 주요 화면 구성은 다음과 같습니다.

```
[Experiments 탭]
  └─ breast-cancer-classification
       ├─ rf_n50_d3    │ accuracy=0.9035 │ f1=0.9024 │ 2026-03-22
       ├─ rf_n100_d5   │ accuracy=0.9561 │ f1=0.9558 │ 2026-03-22  ← 최고
       └─ rf_n200_d None│ accuracy=0.9386 │ f1=0.9381 │ 2026-03-22

[Parallel Coordinates 뷰]
  n_estimators ── max_depth ── accuracy ── f1_score
  (파라미터와 메트릭 간 상관관계를 시각적으로 파악)

[Model Registry 탭]
  BreastCancerClassifier
    Version 1: Staging  (검증 중)
    Version 2: Production (현재 서비스)
    Version 3: None     (실험 단계)
```

---

## 실전 팁: 소규모 팀에서 MLOps 시작하기

### 단계별 도입 로드맵

**1단계: 실험 추적부터 시작 (Day 1~2)**

`mlflow ui` 명령 한 줄로 로컬 MLflow 서버를 실행하고, 기존 학습 스크립트에 `mlflow.log_param`, `mlflow.log_metric` 10줄만 추가합니다. 얻는 것: 모든 실험 기록, 파라미터-성능 비교, 최적 모델 추적.

**2단계: 모델 버전 관리 (Week 1)**

`dvc init && dvc remote add -d s3remote s3://my-bucket/dvc`로 DVC를 초기화합니다. 데이터와 모델 파일을 DVC로 관리하면 데이터-코드-모델 삼위일체 버전 관리가 가능합니다.

**3단계: 기본 CI/CD (Week 2~3)**

GitHub Actions로 PR 시 자동 학습·평가 워크플로를 추가합니다. 성능 기준(예: accuracy >= 0.90)을 통과해야만 main 브랜치 머지를 허용하면 모델 품질 게이트가 생깁니다.

**4단계: 배포 및 모니터링 (Month 1)**

FastAPI + Docker로 모델 서빙 컨테이너를 구성하고, Prometheus + Grafana로 예측 지연, 처리량, 드리프트 메트릭 대시보드를 구축합니다.

### 필수 도구 선택 가이드

| 목적 | 소규모 팀 추천 | 대규모 팀 추천 |
|------|--------------|---------------|
| 실험 추적 | MLflow (셀프 호스팅) | Weights & Biases |
| 데이터 버전 관리 | DVC | LakeFS / Delta Lake |
| 파이프라인 오케스트레이션 | GitHub Actions | Kubeflow / Airflow |
| 피처 스토어 | 커스텀 PostgreSQL | Feast / Tecton |
| 모델 서빙 | FastAPI + Docker | BentoML / Triton |
| 모니터링 | Evidently + Grafana | WhyLogs / Arize AI |

### 자동화 우선순위 원칙

1. **먼저 수동으로 해보기**: 자동화하기 전에 프로세스를 충분히 이해합니다.
2. **병목부터 자동화**: 가장 반복적이고 오류가 많은 단계를 먼저 자동화합니다.
3. **테스트 없는 자동화는 없다**: 모든 파이프라인 단계에 검증 단계를 추가합니다.
4. **점진적 도입**: 한 번에 전체 MLOps 스택을 구축하려 하지 않습니다.

### 재학습 트리거 설계

언제 모델을 재학습할지 결정하는 기준이 필요합니다.

| 트리거 유형 | 설명 | 예시 |
|------------|------|------|
| 시간 기반 | 일정 주기마다 재학습 | 매주 일요일 자정 |
| 데이터 기반 | 새 데이터가 N건 쌓이면 | 10만 건 누적 시 |
| 성능 기반 | 모니터링 지표가 임계값 이하 | AUC < 0.85이면 |
| 드리프트 기반 | 드리프트 탐지 시 | PSI > 0.2이면 |

---

## 마무리

MLOps는 도구의 집합이 아니라 **문화와 관행**입니다. 완벽한 MLOps 시스템을 한 번에 구축하려 하기보다, 오늘 당장 MLflow 실험 추적 한 가지부터 시작해 보세요. 작은 자동화 하나가 팀의 생산성과 모델 신뢰성을 눈에 띄게 향상시키는 경험을 하게 될 것입니다.

핵심 요약:
- **실험 추적**: MLflow로 파라미터·메트릭·아티팩트를 체계적으로 관리
- **버전 관리**: DVC로 데이터-코드-모델의 일관된 버전 추적
- **CI/CD**: GitHub Actions로 모델 품질 게이트 자동화
- **배포 전략**: Canary/Shadow 배포로 안전하게 신규 모델 검증
- **모니터링**: PSI·KS 검정으로 드리프트를 조기 감지하고 자동 재학습