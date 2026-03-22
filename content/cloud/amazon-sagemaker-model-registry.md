---
title: Amazon SageMaker Model Registry
slug: "amazon-sagemaker-model-registry"
category: cloud
tags: ["aws", "ci-cd", "machine-learning", "mlops", "model-management", "model-registry", "sagemaker", "sagemaker-pipelines"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:07.691165+00:00"
---

---
aliases:
  - Amazon SageMaker Model Registry
  - SageMaker Model Registry
---
## 🧩 Quick Overview

| 항목              | 설명 |
|-------------------|------|
| **이름**           | Amazon SageMaker Model Registry |
| **기능 유형**       | **모델 버전 관리 및 승인 흐름을 제공하는 중앙 저장소** |
| **목적**           | 훈련된 모델을 저장하고, 버전 관리하며, **승인된 모델만 배포하도록 제어**하는 기능

> 📦 **Model Registry**는 SageMaker Pipeline, Studio, AutoML 등에서 생성한 모델을
> 체계적으로 관리하고, 배포 흐름에서 승인/검증 절차를 거칠 수 있도록 하는 **ML MLOps 핵심 구성요소**입니다.

---

## 🧠 주요 기능

| 기능 | 설명 |
|------|------|
| **모델 등록(Register)** | 훈련된 모델을 Model Group에 버전 단위로 저장 |
| **모델 승인 상태 관리** | `Approved`, `Pending`, `Rejected` 상태로 나눠 운영 제어 |
| **버전 관리** | 각 모델 버전별 메타데이터, 아티팩트, 설명 등을 자동 관리 |
| **SageMaker Pipeline 연동** | 학습 완료 후 자동으로 모델을 등록하고 승인을 요청 |
| **모델 배포 통합** | 승인된 모델만 실시간 Endpoint 또는 Batch Transform으로 배포 가능

---

## 📁 구성 요소

| 요소 | 설명 |
|------|------|
| **Model Group** | 모델의 논리적 이름 (예: fraud-detector) |
| **Model Version** | 각 훈련마다 등록된 새로운 버전 (예: v1, v2, ...) |
| **Approval Status** | 각 버전별 승인 상태 (`Pending`, `Approved`, `Rejected`) |
| **Model Package** | 실제 등록된 모델 아티팩트 (.tar.gz), 환경 정보 등 포함

---

## 🔁 활용 흐름 예시

```plaintext
[모델 학습 완료]
     ↓
[Model Registry에 버전 등록]
     ↓
[승인 프로세스: Pending → Approved]
     ↓
[배포 또는 CI/CD 연계 배포]
````

---

## ✅ 장점

|항목|설명|
|---|---|
|**통제된 배포**|미승인 모델은 배포 차단 → 품질 유지|
|**모델 버전 추적**|성능 개선 모델 간 비교, 롤백 가능|
|**CI/CD 연동**|SageMaker Pipelines, CodePipeline 등과 통합 가능|
|**설명력 확보**|모델 설명 정보, 평가 결과 등 메타데이터 자동 기록|

---

## ⚠️ 유의사항

|항목|설명|
|---|---|
|**승인 상태는 수동 설정 가능**|Auto-approval도 가능하나 보안상 수동 승인을 권장|
|**등록된 모델은 S3에 저장됨**|아티팩트 스토리지는 S3 경로 기반|
|**파이프라인 연동 시 권한 필요**|Pipeline이 등록 및 승인 작업을 수행하려면 IAM 역할 필요|

---

## 🧾 요약

|항목|설명|
|---|---|
|**정의**|SageMaker 내에서 훈련된 모델을 **버전 단위로 등록·관리·승인·배포**하는 중앙 저장소|
|**주요 기능**|모델 버전 등록, 승인 상태 설정, 배포 통제, CI/CD 연계|
|**활용 대상**|ML 운영 자동화, MLOps 파이프라인, 품질 보증된 모델 배포|
