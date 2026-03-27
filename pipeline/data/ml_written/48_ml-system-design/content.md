## 개요

많은 ML 프로젝트가 실험실에서는 훌륭한 성능을 보이지만, 프로덕션 환경에 배포되면 예상치 못한 문제에 직면합니다. 학술 논문에서는 정적인 데이터셋 위에서 모델 정확도만 측정하면 되지만, 실제 서비스에서는 **지속적으로 변화하는 데이터**, **지연 시간(Latency) 요구사항**, **시스템 장애 복구**, **모델 성능 저하 감지** 등 수많은 엔지니어링 과제가 존재합니다.

구글의 논문 "Hidden Technical Debt in Machine Learning Systems"(2015)에 따르면, ML 시스템에서 실제 ML 코드가 차지하는 비중은 전체의 5%에 불과하고, 나머지 95%는 인프라와 주변 코드로 구성됩니다. 즉, **시스템 설계가 모델 알고리즘만큼 중요합니다**.

이 글에서는 프로덕션 ML 시스템을 설계할 때 반드시 알아야 할 핵심 패턴들을 수학적 배경부터 실제 코드 구현까지 체계적으로 살펴봅니다.

---

## 수학적 배경: 데이터 드리프트 감지

### KL Divergence (쿨백-라이블러 발산)

프로덕션 환경에서 가장 중요한 문제 중 하나는 **데이터 드리프트(Data Drift)**입니다. 학습 데이터의 분포와 실제 서비스에 유입되는 데이터의 분포가 달라지는 현상입니다.

두 확률 분포 $P$(학습 분포)와 $Q$(현재 서빙 분포) 사이의 차이를 KL Divergence로 측정합니다.

$$D_{KL}(P \| Q) = \sum_{x} P(x) \log \frac{P(x)}{Q(x)}$$

$D_{KL}(P \| Q) = 0$이면 두 분포가 동일하고, 값이 클수록 분포 차이가 큽니다. 단, KL Divergence는 비대칭($D_{KL}(P \| Q) \neq D_{KL}(Q \| P)$)이므로 실전에서는 Jensen-Shannon Divergence를 사용하기도 합니다.

$$D_{JS}(P \| Q) = \frac{1}{2} D_{KL}(P \| M) + \frac{1}{2} D_{KL}(Q \| M), \quad M = \frac{P + Q}{2}$$

### PSI (Population Stability Index)

PSI는 금융권에서 시작된 지표로, 변수의 분포 변화를 정량화하는 데 널리 사용됩니다.

$$PSI = \sum_{i=1}^{n} \left( (Q_i - P_i) \times \ln \frac{Q_i}{P_i} \right)$$

여기서 $P_i$는 학습 데이터의 버킷 $i$ 비율, $Q_i$는 현재 데이터의 버킷 $i$ 비율입니다.

| PSI 값 | 해석 |
|--------|------|
| $< 0.1$ | 분포 변화 없음 (안정) |
| $0.1 \sim 0.25$ | 약간의 변화 (주의 필요) |
| $> 0.25$ | 심각한 분포 변화 (재학습 필요) |

### 서빙 지연 분석

온라인 서빙 시스템의 Latency는 다음과 같이 분해할 수 있습니다.

$$L_{total} = L_{network} + L_{preprocessing} + L_{inference} + L_{postprocessing}$$

P99 지연(99번째 백분위수)을 SLO(Service Level Objective)로 설정하는 것이 일반적이며, $L_{inference}$를 줄이기 위해 모델 양자화(Quantization), 프루닝(Pruning), TensorRT/ONNX 변환 등을 활용합니다.

---

![ML 시스템 아키텍처: 프로덕션 ML 시스템의 전체 구성 요소와 데이터 흐름](figures/ml_system_architecture.png)
*ML 시스템 아키텍처: 데이터 수집, 피처 스토어, 모델 서빙, 모니터링까지 프로덕션 ML 시스템의 핵심 구성 요소를 보여준다.*

## 핵심 패턴

### 1. 배치(Batch) vs 온라인(Online) 서빙

**배치 서빙**은 대량의 데이터를 미리 처리해 결과를 저장소에 적재하는 방식입니다.

- 장점: 처리량(Throughput) 극대화, 인프라 비용 절감, 구현 단순
- 단점: 실시간성 없음, 결과가 오래될 수 있음
- 적합한 케이스: 추천 시스템 사전 계산, 리포트 생성, 야간 배치 스코어링

**온라인(실시간) 서빙**은 요청이 들어올 때마다 즉시 예측을 반환합니다.

- 장점: 실시간 개인화, 최신 데이터 반영
- 단점: 지연 시간 요구사항 엄격, 인프라 비용 높음
- 적합한 케이스: 사기 탐지, 실시간 가격 최적화, 챗봇

### 2. Feature Store 패턴

Feature Store는 ML 피처를 중앙 집중식으로 저장, 공유, 재사용하는 시스템입니다. 학습과 서빙 간 **피처 일관성(Training-Serving Skew)**을 방지하는 핵심 인프라입니다.

```
[데이터 소스] → [Feature Pipeline] → [오프라인 저장소 (S3/BigQuery)] ← [학습]
                                  → [온라인 저장소 (Redis/DynamoDB)] ← [실시간 서빙]
```

### 3. 모델 레지스트리

모델 레지스트리는 학습된 모델의 버전, 메타데이터, 실험 결과를 관리하는 중앙 저장소입니다. MLflow, Weights & Biases, Vertex AI Model Registry 등이 대표적입니다.

### 4. Shadow Mode (그림자 배포)

새 모델을 프로덕션 트래픽의 일부에 적용하되, 실제 결과는 기존 모델의 것을 반환하고 새 모델의 예측은 로깅만 하는 방식입니다. A/B 테스트 전에 신규 모델의 안정성을 검증할 때 유용합니다.

---

## Python 구현

### FastAPI + scikit-learn 모델 서빙

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import numpy as np
import time
import logging
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import PlainTextResponse

# 메트릭 정의
REQUEST_COUNT = Counter('ml_requests_total', '총 예측 요청 수', ['status'])
LATENCY = Histogram('ml_inference_latency_seconds', '추론 지연 시간')

app = FastAPI(title="ML Serving API")

# 모델 로드 (애플리케이션 시작 시 1회)
model = joblib.load("model.pkl")
scaler = joblib.load("scaler.pkl")

class PredictRequest(BaseModel):
    features: list[float]

class PredictResponse(BaseModel):
    prediction: float
    probability: float
    model_version: str
    latency_ms: float

@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    start = time.time()
    try:
        X = np.array(request.features).reshape(1, -1)
        X_scaled = scaler.transform(X)
        pred = model.predict(X_scaled)[0]
        prob = model.predict_proba(X_scaled)[0].max()
        latency_ms = (time.time() - start) * 1000
        REQUEST_COUNT.labels(status='success').inc()
        LATENCY.observe(time.time() - start)
        return PredictResponse(
            prediction=float(pred),
            probability=float(prob),
            model_version="v1.2.0",
            latency_ms=latency_ms
        )
    except Exception as e:
        REQUEST_COUNT.labels(status='error').inc()
        logging.error(f"예측 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    # Prometheus 메트릭 엔드포인트
    return generate_latest()

@app.get("/health")
def health():
    return {"status": "ok"}
```

### Feature Store 패턴 구현

```python
import redis
import json
import hashlib
from datetime import datetime, timedelta
from typing import Any

class FeatureStore:
    """경량 온라인 Feature Store (Redis 기반)"""

    def __init__(self, host: str = "localhost", port: int = 6379):
        self.client = redis.Redis(host=host, port=port, decode_responses=True)

    def _make_key(self, entity_type: str, entity_id: str, feature_group: str) -> str:
        return f"fs:{entity_type}:{entity_id}:{feature_group}"

    def set_features(
        self,
        entity_type: str,
        entity_id: str,
        feature_group: str,
        features: dict[str, Any],
        ttl_hours: int = 24
    ) -> None:
        """피처를 온라인 저장소에 저장"""
        key = self._make_key(entity_type, entity_id, feature_group)
        payload = {
            "features": features,
            "created_at": datetime.utcnow().isoformat()
        }
        self.client.setex(key, timedelta(hours=ttl_hours), json.dumps(payload))

    def get_features(
        self,
        entity_type: str,
        entity_id: str,
        feature_group: str
    ) -> dict[str, Any] | None:
        """온라인 저장소에서 피처 조회"""
        key = self._make_key(entity_type, entity_id, feature_group)
        raw = self.client.get(key)
        if raw is None:
            return None
        return json.loads(raw)["features"]

# 사용 예시
fs = FeatureStore()

# 피처 저장 (배치 파이프라인에서 주기적으로 갱신)
fs.set_features(
    entity_type="user",
    entity_id="user_123",
    feature_group="behavior",
    features={
        "avg_session_duration": 342.5,
        "purchase_count_7d": 3,
        "last_active_days_ago": 1
    },
    ttl_hours=6
)

# 서빙 시점에서 피처 조회
features = fs.get_features("user", "user_123", "behavior")
print(features)  # {'avg_session_duration': 342.5, ...}
```

<!-- Execution error: ModuleNotFoundError: No module named 'redis' -->

### PSI 계산 유틸리티

```python
import numpy as np

def calculate_psi(expected: np.ndarray, actual: np.ndarray, buckets: int = 10) -> float:
    """
    Population Stability Index 계산
    expected: 학습(기준) 데이터
    actual: 현재 서빙 데이터
    """
    # 학습 데이터 기준으로 버킷 경계 설정
    breakpoints = np.percentile(expected, np.linspace(0, 100, buckets + 1))
    breakpoints[0] = -np.inf
    breakpoints[-1] = np.inf

    expected_counts = np.histogram(expected, bins=breakpoints)[0]
    actual_counts = np.histogram(actual, bins=breakpoints)[0]

    # 0 나눗셈 방지: 최소값 1e-4 보정
    expected_pct = expected_counts / len(expected) + 1e-4
    actual_pct = actual_counts / len(actual) + 1e-4

    psi = np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct))
    return psi

# 사용 예시
train_scores = np.random.normal(0.6, 0.15, 10000)
current_scores = np.random.normal(0.4, 0.20, 5000)  # 드리프트 발생 시뮬레이션

psi_value = calculate_psi(train_scores, current_scores)
print(f"PSI: {psi_value:.4f}")
if psi_value > 0.25:
    print("경고: 심각한 분포 변화 감지 ( 모델 재학습 필요")
elif psi_value > 0.1:
    print("주의: 약간의 분포 변화 감지 ) 모니터링 강화 필요")
else:
    print("정상: 분포 안정")
```

```output
PSI: 1.1341
경고: 심각한 분포 변화 감지 ( 모델 재학습 필요
```

---

![시스템 모니터링 대시보드: 모델 성능, 데이터 드리프트, 시스템 메트릭을 실시간으로 추적하는 대시보드](figures/system_monitoring_dashboard.png)
*시스템 모니터링 대시보드: 모델 정확도, 지연 시간, 데이터 드리프트 지표를 실시간으로 모니터링하여 성능 저하를 조기에 감지한다.*

## 시각화

### ML 시스템 아키텍처 다이어그램

```python
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

fig, ax = plt.subplots(figsize=(14, 8))
ax.set_xlim(0, 14)
ax.set_ylim(0, 8)
ax.axis('off')
ax.set_facecolor('#f8f9fa')
fig.patch.set_facecolor('#f8f9fa')

# 컴포넌트 정의: (x, y, width, height, label, color)
components = [
    (0.5, 5.5, 2, 1, "데이터 소스\n(DB/Kafka/S3)", '#AED6F1'),
    (3.5, 6, 2, 1, "Feature\nPipeline", '#A9DFBF'),
    (6.5, 6.5, 2.5, 1, "Feature Store\n(Redis/BigQuery)", '#F9E79F'),
    (3.5, 4.5, 2, 1, "모델 학습\n(Training)", '#A9DFBF'),
    (6.5, 4.5, 2.5, 1, "모델 레지스트리\n(MLflow)", '#F9E79F'),
    (10, 5.5, 2.5, 1.5, "서빙 서버\n(FastAPI)", '#F1948A'),
    (0.5, 2.5, 2, 1, "모니터링\n(Prometheus)", '#D7BDE2'),
    (3.5, 2.5, 2, 1, "알림\n(PagerDuty)", '#D7BDE2'),
    (6.5, 2.5, 2.5, 1, "드리프트 감지\n(PSI/KL-Div)", '#D7BDE2'),
]

for (x, y, w, h, label, color) in components:
    rect = mpatches.FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.1",
        linewidth=1.5, edgecolor='#555', facecolor=color
    )
    ax.add_patch(rect)
    ax.text(x + w/2, y + h/2, label, ha='center', va='center',
            fontsize=8.5, fontweight='bold', color='#222')

# 화살표 연결
arrow_props = dict(arrowstyle='->', color='#444', lw=1.5)
connections = [
    (2.5, 6.0, 3.5, 6.5),    # 데이터소스 -> 피처파이프라인
    (5.5, 6.5, 6.5, 7.0),    # 피처파이프라인 -> Feature Store
    (5.5, 5.0, 6.5, 5.0),    # 학습 -> 모델레지스트리
    (9.0, 7.0, 10.0, 6.3),   # Feature Store -> 서빙
    (9.0, 5.0, 10.0, 5.8),   # 모델레지스트리 -> 서빙
    (10.0, 3.0, 6.5, 3.0),   # 서빙 -> 드리프트감지 (모니터링)
    (6.5, 3.0, 5.5, 3.0),    # 드리프트 -> 알림
    (3.5, 3.0, 2.5, 3.0),    # 알림 -> 모니터링
]
for (x1, y1, x2, y2) in connections:
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=arrow_props)

ax.set_title('프로덕션 ML 시스템 아키텍처', fontsize=14, fontweight='bold', pad=15, color='#222')
plt.tight_layout()
plt.savefig('ml_system_architecture.png', dpi=150, bbox_inches='tight')
plt.show()
```

![Ml-System-Design Fig 1](/media/figures/outputs/ml-system-design/ml-system-design_fig_1.png)

### 드리프트 모니터링 대시보드

```python
import matplotlib.pyplot as plt
import numpy as np

np.random.seed(42)
days = np.arange(1, 31)
# PSI 값: 초반 안정 → 중반 상승 → 경보
psi_values = np.concatenate([
    np.random.uniform(0.02, 0.08, 10),   # 안정 구간
    np.random.uniform(0.10, 0.20, 10),   # 주의 구간
    np.random.uniform(0.22, 0.35, 10)    # 경보 구간
])

fig, axes = plt.subplots(2, 1, figsize=(12, 7), facecolor='#f8f9fa')

# PSI 트렌드
ax1 = axes[0]
ax1.plot(days, psi_values, 'o-', color='#2980B9', lw=2, ms=5, label='PSI')
ax1.axhline(0.1, color='#F39C12', ls='--', lw=1.5, label='주의 임계값 (0.1)')
ax1.axhline(0.25, color='#E74C3C', ls='--', lw=1.5, label='경보 임계값 (0.25)')
ax1.fill_between(days, 0, 0.1, alpha=0.08, color='#27AE60')
ax1.fill_between(days, 0.1, 0.25, alpha=0.08, color='#F39C12')
ax1.fill_between(days, 0.25, 0.4, alpha=0.08, color='#E74C3C')
ax1.set_ylabel('PSI 값', fontsize=10)
ax1.set_title('30일 PSI 드리프트 모니터링', fontsize=12, fontweight='bold')
ax1.legend(fontsize=9)
ax1.set_facecolor('#ffffff')
ax1.grid(alpha=0.3)

# 모델 정확도 트렌드
acc_values = 0.92 - psi_values * 0.8 + np.random.normal(0, 0.01, 30)
ax2 = axes[1]
ax2.plot(days, acc_values, 's-', color='#8E44AD', lw=2, ms=5, label='모델 정확도')
ax2.axhline(0.85, color='#E74C3C', ls='--', lw=1.5, label='최소 허용 정확도 (0.85)')
ax2.set_xlabel('날짜 (일)', fontsize=10)
ax2.set_ylabel('정확도', fontsize=10)
ax2.set_title('모델 정확도 추이', fontsize=12, fontweight='bold')
ax2.legend(fontsize=9)
ax2.set_facecolor('#ffffff')
ax2.grid(alpha=0.3)

plt.tight_layout()
plt.savefig('drift_monitoring_dashboard.png', dpi=150, bbox_inches='tight')
plt.show()
```

![Ml-System-Design Fig 2](/media/figures/outputs/ml-system-design/ml-system-design_fig_2.png)

---

## 실전 팁

### 서빙 전략 선택 기준

| 기준 | 배치 서빙 | 온라인 서빙 |
|------|-----------|-------------|
| 지연 허용 | 분~시간 단위 허용 | 100ms 이하 필요 |
| 데이터 신선도 | 낮아도 무방 | 최신 데이터 필수 |
| 인프라 비용 | 낮음 | 높음 |
| 구현 복잡도 | 낮음 | 높음 |
| 예시 | 주간 리포트, 추천 사전 계산 | 사기 탐지, 실시간 검색 |

### 모니터링 필수 지표

1. **모델 메트릭**: 정확도, F1, AUC ) 실제 레이블이 있을 때
2. **데이터 메트릭**: PSI, 피처별 평균/분산, 결측값 비율
3. **인프라 메트릭**: P50/P95/P99 지연, 초당 요청 수(RPS), 에러율
4. **비즈니스 메트릭**: CTR, 전환율, 최종 목적과 연결

### 장애 패턴과 복구

- **Training-Serving Skew**: 학습과 서빙의 피처 계산 방식 불일치 → Feature Store로 해결
- **모델 스톨(Stale Model)**: 재학습 파이프라인 중단 → 모델 나이(Model Age) 모니터링
- **Cold Start**: 신규 사용자/아이템의 피처 부재 → Fallback 규칙 기반 모델 준비
- **메모리 누수**: 온라인 서빙 서버 장기 운영 시 → 주기적 재시작 + 메모리 메트릭 알림

### 비용 최적화

- **배치 크기 조절**: 온라인 서빙에서도 마이크로 배치(Micro-batching)로 GPU 활용률 향상
- **모델 경량화**: ONNX 변환, INT8 양자화로 추론 비용 30~50% 절감 가능
- **Auto-scaling**: 트래픽 패턴 기반 인스턴스 수 자동 조정 (HPA/KEDA)
- **캐싱**: 동일 입력에 대한 예측 결과를 Redis에 캐싱 (TTL 설정 필수)

---

## 마무리

프로덕션 ML 시스템 설계는 단순히 좋은 모델을 만드는 것에서 끝나지 않습니다. **데이터 파이프라인의 안정성**, **모델 버전 관리**, **실시간 드리프트 감지**, **장애 복구 전략**이 모두 갖춰져야 비로소 신뢰할 수 있는 ML 서비스가 완성됩니다.

처음부터 모든 패턴을 도입할 필요는 없습니다. 서비스 규모와 팀 역량에 맞춰 **배치 서빙 → Feature Store 도입 → 온라인 서빙 → 드리프트 모니터링** 순서로 점진적으로 발전시켜 나가는 것이 현실적입니다.