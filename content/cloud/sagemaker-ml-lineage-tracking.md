---
title: SageMaker ML Lineage Tracking
slug: "sagemaker-ml-lineage-tracking"
category: cloud
tags: ["aws", "boto3", "machine-learning", "ml-lineage", "model-tracking", "reproducibility", "sagemaker", "sagemaker-studio"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.858853+00:00"
---

## 🧩 Quick Overview

| 항목              | 설명 |
|-------------------|------|
| **이름**           | SageMaker ML Lineage Tracking |
| **기능**           | 머신러닝 모델 개발의 전체 이력(데이터, 코드, 파라미터, 모델)을 **추적 및 시각화** |
| **연동 대상**      | Processing Job, Training Job, Model, Endpoint, Dataset 등 |
| **시각화 지원**    | SageMaker Studio UI 및 SDK 기반 |

> 🧬 **목적**: 모델 생성 과정을 구성하는 요소들 간의 관계(계보, lineage)를 추적하여 재현성, 감사, 디버깅을 향상시키는 것입니다.

---

## 🔍 주요 추적 대상(Artifacts)

| 항목            | 설명 |
|------------------|------|
| **Dataset Artifact** | 학습에 사용된 원본 또는 전처리된 데이터 |
| **Model Artifact**   | 훈련 결과로 생성된 모델 파일(e.g., `model.tar.gz`) |
| **Code Artifact**    | 학습 또는 처리에 사용된 스크립트 |
| **Training Job**     | 모델을 생성한 훈련 작업 |
| **Processing Job**   | 데이터 전처리, 검증 등 처리 작업 |

---

## 🔁 주요 관계(Association)

- **ProcessingJob → Dataset + Output Dataset**
- **TrainingJob → Input Dataset + Model Artifact**
- **Model → Model Artifact**
- **Endpoint → Model**

---

## ✅ 장점

| 항목 | 설명 |
|------|------|
| **재현성 보장** | 어떤 데이터와 어떤 코드로 모델이 만들어졌는지 명확히 추적할 수 있습니다. |
| **모델 비교** | 실험 간 차이를 추적해 성능 비교 및 원인 분석을 지원합니다. |
| **보안 및 규정 준수** | 모델 생성 경로를 기록해 감사 로그로 활용할 수 있습니다. |
| **자동 기록** | SageMaker Pipeline, Studio, SDK로 생성된 작업은 자동으로 추적됩니다. |

---

## 🧪 예시: Python SDK (boto3 / sagemaker.lineage)

```python
from sagemaker.lineage import context, artifact, association

training_context = context.Context.load(name="my-training-job")
model_artifact = artifact.ModelArtifact.load(source_uri="s3://.../model.tar.gz")

# 관계 연결
association.Association(
    source=model_artifact,
    destination=training_context,
    association_type="Produced"
).save()
````

---

## 🧾 요약

|항목|설명|
|---|---|
|**정의**|SageMaker에서 ML 워크플로우 전반의 요소(데이터, 코드, 모델) 간의 관계를 추적하는 기능|
|**기반 요소**|Artifact, Context, Action, Association|
|**활용**|재현성 확보, 실험 분석, 규정 감사|
|**연동**|SageMaker Studio, SDK, Pipelines와 자동 연계|
