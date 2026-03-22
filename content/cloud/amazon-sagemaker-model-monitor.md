---
title: Amazon SageMaker Model Monitor
slug: "amazon-sagemaker-model-monitor"
category: cloud
tags: ["aws", "cloudwatch", "data-drift", "mlops", "model-monitoring", "model-quality", "s3", "sagemaker"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.874942+00:00"
---

## 🧩 Quick Overview

| 항목              | 설명 |
|-------------------|------|
| **이름**           | Amazon SageMaker Model Monitor |
| **기능**           | **실시간 또는 주기적으로 배포된 모델의 품질, 데이터 드리프트, 이상치 등을 자동 감시** |
| **감시 대상**      | 입력 데이터, 예측 결과, 지표(metric), 스킴(Schema) 등 |
| **활용 형태**      | 추론 엔드포인트에 연결하여 **자동 모니터링 + 알림 + 로깅 수행** |

> 📡 **목적**: 머신러닝 모델이 **운영 환경에서도 일관되게 동작하고 있는지**를 추적 → **모델 품질 저하나 데이터 이상 발생 시 자동 탐지 및 경고**

---

## 🔍 지원하는 모니터링 유형

| 모니터링 종류 | 설명 |
|---------------|------|
| **데이터 품질 (Data Quality)** | 입력 특성의 분포 변화 감지 (예: 누락 값 증가, 범위 변화 등) |
| **모델 품질 (Model Quality)** | 실제 레이블이 제공되는 경우, 예측 정확도 추적 |
| **스킴 변경 (Schema Drift)** | 피처 수, 데이터 타입 등의 스키마 변경 여부 감지 |
| **이상치 감지 (Bias & Outlier)** | 편향 또는 비정상값 분포 감지 |

---

## 🛠️ 구성 요소

| 요소 | 설명 |
|------|------|
| **Baseline** | 기준 데이터의 통계 및 스킴 (S3에 저장됨) |
| **Monitoring Schedule** | 일정 주기로 실행되는 모니터링 작업 |
| **Constraints & Statistics** | 기준에 대한 제약 조건(JSON), 통계 요약 |
| **Reports** | 분석 결과 (CloudWatch 또는 S3에 저장) |
| **Alerts** | CloudWatch Alarms, SNS 연동 가능 |

---

## ✅ 장점

- **자동화된 모니터링**: 스케줄 기반 또는 지속적 실행 가능
- **모델 품질 문제 조기 감지**
- **SageMaker 엔드포인트와 쉽게 연동**
- **CloudWatch/S3 로그 및 지표 저장**
- **SageMaker Pipelines과 통합 가능**

---

## 🧪 예시: 모니터링 스케줄 설정

```python
from sagemaker.model_monitor import DefaultModelMonitor

monitor = DefaultModelMonitor(role=sagemaker_role)
monitor.create_monitoring_schedule(
    endpoint_input=endpoint_name,
    output_s3_uri="s3://my-bucket/monitor-output/",
    schedule_cron_expression="cron(0 * ? * * *)",  # 매 시간 실행
    baseline_dataset="s3://my-bucket/baseline.csv",
)
````

---

## ⚠️ 유의사항

|항목|설명|
|---|---|
|**실제 라벨 필요 여부**|`Model Quality` 모니터링은 **실제 라벨** 필요|
|**추론 결과 저장 설정 필수**|엔드포인트에서 `Capture` 활성화 필요|
|**비용 발생**|모니터링 실행 시 Processing Job 단위로 과금|

---

## 🧾 요약

|항목|설명|
|---|---|
|**정의**|SageMaker에서 **배포된 모델의 성능과 데이터 품질을 자동 추적**하는 기능|
|**주요 기능**|데이터 품질, 모델 품질, 스키마 변경, 이상 감지|
|**필수 구성 요소**|Baseline, Monitoring Schedule, Capture 설정|
|**활용 목적**|모델 신뢰성 유지, 이상 조기 감지, 모니터링 자동화|
