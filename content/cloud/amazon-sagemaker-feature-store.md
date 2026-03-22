---
title: Amazon SageMaker Feature Store
slug: "amazon-sagemaker-feature-store"
category: cloud
tags: ["amazon-sagemaker", "aws", "feature-engineering", "feature-store", "machine-learning", "mlops", "offline-store", "online-store", "python-sdk", "sagemaker-studio"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.829140+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---

---
aliases:
  - SageMaker Feature Store
---

## 🧩 Quick Overview

| 항목              | 설명 |
|-------------------|------|
| **서비스명**       | Amazon SageMaker Feature Store |
| **기능**           | 머신러닝 모델의 학습 및 추론에 사용되는 **피처(Feature)를 저장·관리·공유**하는 전용 저장소 |
| **구성 요소**      | Feature Group, Record, Offline Store, Online Store |
| **통합성**         | SageMaker Studio, Training Jobs, Batch Transform, Realtime Inference 등과 연동 |

> 🧠 **목적**: ML 파이프라인에서 **재사용 가능하고 일관된 피처를 중앙에서 관리**하여 학습과 추론 간의 **데이터 불일치 문제를 방지**하는 것

---

## 🧬 핵심 구성 요소

| 구성 요소        | 설명 |
|------------------|------|
| **Feature Group** | 관련 피처들을 논리적으로 묶은 단위(테이블 개념) |
| **Record**        | 각 Feature Group에 저장되는 하나의 행(row) |
| **Event Time**    | 시간 축 기준 데이터 정렬에 사용하는 필드(필수) |
| **Online Store**  | 실시간 추론용 피처 저장소(빠른 조회를 지원하며 보존 기간이 짧음) |
| **Offline Store** | 학습 및 배치 예측용 저장소(S3 기반, 장기간 보존) |

---

## 🧪 사용 예시 (Python SDK)

```python
from sagemaker.feature_store.feature_group import FeatureGroup

feature_group = FeatureGroup(name="customer_features", sagemaker_session=sagemaker_session)

feature_group.create(
    feature_definitions=[
        FeatureDefinition(feature_name="customer_id", feature_type="String"),
        FeatureDefinition(feature_name="age", feature_type="Integral"),
        FeatureDefinition(feature_name="churn", feature_type="Fractional"),
    ],
    record_identifier_name="customer_id",
    event_time_feature_name="event_time",
    role=role,
    enable_online_store=True
)
```