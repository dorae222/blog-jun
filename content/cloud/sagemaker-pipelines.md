---
title: SageMaker Pipelines
slug: "sagemaker-pipelines"
category: cloud
tags: ["automation", "aws", "ci-cd", "machine-learning", "mlops", "pipeline", "python", "sagemaker", "sagemaker-pipelines"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.883771+00:00"
---

## 🧩 Quick Overview

|항목|설명|
|---|---|
|**기능**|머신러닝 워크플로우(ML workflow) 자동화|
|**구성 단위**|`Pipeline`, `Step`, `StepArguments`, `Condition`, `Callback` 등|
|**주요 Step 유형**|Processing, Training, Tuning, Model, Transform, Register, Condition 등|
|**통합**|SageMaker SDK, Studio, EventBridge, CloudWatch 등과 연동|
|**형식**|Python 기반 정의 (`sagemaker.workflow` 모듈)|

> ✅ **목적**: 모델 학습과 배포에 필요한 **모든 단계를 정의하고 자동화**하여 **재현 가능한 ML 파이프라인 구축**을 가능하게 함

---

## 🛠️ SageMaker Pipelines란?

**Amazon SageMaker Pipelines**는 AWS에서 제공하는 **머신러닝(ML) 워크플로우 자동화 플랫폼**입니다. 데이터 준비, 모델 학습, 평가, 모델 등록 및 배포에 이르는 **전체 MLOps 흐름을 코드로 정의하고 실행**할 수 있도록 지원합니다.

SageMaker Pipelines는 SageMaker SDK(Python)를 통해 파이프라인을 선언적으로 작성하며, 각 단계를 독립적으로 추적하고 관리할 수 있게 설계되어 있습니다.

---

## 🔧 구성 요소

|구성 요소|설명|
|---|---|
|**Pipeline**|전체 워크플로우를 정의하는 객체|
|**Step**|파이프라인 내의 개별 단계(ex. TrainingStep, ProcessingStep 등)|
|**Step Arguments**|각 단계에 전달되는 실행 입력(함수/컨테이너/모델 등)|
|**ConditionStep**|조건 분기(예: 성능 기준을 만족할 때만 모델 등록)|
|**CallbackStep**|외부 이벤트 또는 사용자 승인이 필요한 경우 사용|

---

## 🧬 주요 Step 유형 예시

|Step 이름|용도|
|---|---|
|`ProcessingStep`|데이터 전처리, Feature Engineering|
|`TrainingStep`|모델 학습|
|`TuningStep`|하이퍼파라미터 튜닝|
|`ModelStep`|모델 생성|
|`TransformStep`|배치 추론|
|`RegisterModel`|모델 레지스트리에 등록|
|`ConditionStep`|조건에 따른 분기 처리|
|`CallbackStep`|외부 입력 대기 또는 승인 흐름 연결|

---

## ✅ 주요 장점

- **엔드투엔드 자동화**: 전체 학습/배포 과정을 수동 개입 없이 자동화할 수 있음
- **재현 가능성 확보**: 동일한 파이프라인을 반복 사용하여 실험의 일관성 보장
- **리소스 추적**: 모든 아티팩트(S3, 모델, 출력 등)를 자동으로 기록
- **조건 분기 및 유연한 설계**: 모델 품질 기준이나 승인 여부 등으로 흐름 제어 가능
- **SageMaker Studio와 연동**: 시각화된 UI에서 파이프라인 구성과 실행 상태를 확인 가능

---

## 🧪 사용 예시 (Python SDK)

```python
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import ProcessingStep, TrainingStep

# 전처리 스텝
step_process = ProcessingStep(...)

# 학습 스텝
step_train = TrainingStep(...)

# 파이프라인 정의
pipeline = Pipeline(
    name="MyPipeline",
    steps=[step_process, step_train],
)
pipeline.upsert(role_arn="arn:aws:iam::123456789012:role/SageMakerExecutionRole")
pipeline.start()
```

---

## 🧠 활용 사례

|사용 예|설명|
|---|---|
|**ML 모델 주기적 재학습 자동화**|주기적으로 새 데이터로 모델을 재학습하고 배포|
|**AutoML 워크플로우 구성**|전처리 → HPO → 검증 → 등록 → 배포까지 자동화된 흐름 구성|
|**CI/CD 기반 MLOps**|CodePipeline 등과 결합해 지속적 통합/배포 파이프라인 구축|
|**실험 추적 및 결과 재현**|동일 파라미터로 실험을 반복하여 결과를 재현 가능|

---

## 🧾 요약

|항목|내용|
|---|---|
|**정의**|SageMaker에서 제공하는 코드 기반 ML 워크플로우 자동화 프레임워크|
|**장점**|재현성, 자동화, 시각화, 통합성|
|**대상 사용자**|데이터 사이언티스트, MLOps 엔지니어|
|**필수 조건**|SageMaker SDK, IAM Role, S3 등 사전 구성 필요|
