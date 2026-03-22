---
title: Hyperband (하이퍼밴드) — 내가 정리한 메모
slug: "hyperband-하이퍼밴드"
category: cloud
tags: ["하이퍼밴드", "하이퍼파라미터", "HPO", "hyperband", "ml"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:08.452171+00:00"
---

## Quick Overview

| 항목              | 설명 |
|-------------------|------|
| **이름**           | Hyperband (하이퍼밴드) |
| **종류**           | 하이퍼파라미터 최적화 알고리즘 |
| **기반 개념**      | Successive Halving + 자원(예산) 기반 반복 |
| **용도**           | 하이퍼파라미터 조합을 **효율적으로 탐색**하여 최적값에 빠르게 수렴시키기 |

> **목적**: **많은 후보 조합을 소량의 자원으로 빠르게 평가**하고, 유망한 후보만 정밀하게 학습시켜 → **하이퍼파라미터 탐색 비용을 최소화**

---

## Hyperband 작동 방식

1. 전체 자원(시간, epoch, 샘플 수 등)을 예산으로 설정
2. 많은 하이퍼파라미터 조합을 소량 자원으로 학습 (1단계)
3. 성능 상위 일부만 선택하여 자원 추가 할당 (2단계)
4. 이 과정을 **반복적으로 줄여가며** 최적값으로 수렴시킴

- 처음엔 단순히 "많이 돌려서 좋은 것을 고르는" 방식인 줄 알았는데, 예산을 나눠서 단계적으로 버리는 방식이라 자원 효율이 훨씬 좋았습니다.

> **핵심 아이디어**: **"좋은 조합만 점점 더 학습시키자"**

---

## 장점

- **랜덤 탐색 대비 훨씬 효율적**
  - 내가 실험해보니 동일 자원 내에서 더 빨리 괜찮은 조합을 찾았습니다.
- **자원 낭비 최소화**: 성능이 낮은 후보는 조기에 제거
  - 초반에 성능이 안 나오면 바로 중단되니 비용 절감 효과가 큽니다.
- **병렬 실행 가능**
  - 대규모 클러스터에서 여러 Job을 동시에 돌려 가속화하기 좋았습니다.
- 탐색 조기 중단(early stopping) 지원
  - 실제로 몇몇 실험에서 epoch 3~5 내에 후보를 걸러낼 수 있었습니다.

---

## 한계

| 항목 | 설명 |
|------|------|
| **모델 초기 성능 신뢰 필요** | 초반 평가가 부정확하면 잠재적으로 좋은 조합이 일찍 제거될 수 있음 |
| **리소스 예산 설정 필요** | 총 훈련 시간이나 epoch 기준을 명확히 정의해야 함 |
| **베이지안 방식보다 덜 정밀** | 확률 기반 최적화가 아니므로 정밀 탐색 보다는 빠른 탐색에 더 적합 |

- 이 부분에서 막혔는데, 특히 초기 성능 지표가 noisy한 모델(예: 학습 불안정한 네트워크)은 Hyperband와 잘 맞지 않았습니다.

---

## 적용 예시 (SageMaker에서 사용)

```python
from sagemaker.tuner import HyperbandStrategyConfig

tuner = HyperparameterTuner(
    estimator=my_estimator,
    objective_metric_name="validation:accuracy",
    hyperparameter_ranges={
        "learning_rate": ContinuousParameter(0.001, 0.2),
        "batch_size": IntegerParameter(32, 256)
    },
    max_jobs=20,
    max_parallel_jobs=5,
    hyperband_strategy_config=HyperbandStrategyConfig()
)
```

- 내 경우 SageMaker에서 간단히 설정해 두고 돌려보니, max_jobs와 max_parallel_jobs 조합만 잘 맞추면 실험 관리가 훨씬 편했습니다.

(원본 노션/옵시디언 — 이 내용 기준으로 빠짐없이 반영)
