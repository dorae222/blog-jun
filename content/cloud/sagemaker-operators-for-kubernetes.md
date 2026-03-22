---
title: SageMaker Operators for Kubernetes
slug: "sagemaker-operators-for-kubernetes"
category: cloud
tags: ["aws", "crd", "inference", "k8s", "kubernetes", "mlops", "operators", "sagemaker", "training"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:07.668051+00:00"
---

## 🧩 Quick Overview

| 항목             | 설명 |
|------------------|------|
| **이름**          | SageMaker Operators for Kubernetes |
| **기능**          | Kubernetes 환경에서 Amazon SageMaker의 ML 작업(학습, 추론 등)을 직접 실행하도록 해주는 **K8s 연동 도구** |
| **핵심 역할**     | SageMaker의 기능을 **Kubernetes CRD(Custom Resource Definitions)** 형태로 사용 |

> 🎛️ **목적**: 쿠버네티스 사용자가 익숙한 K8s 환경에서 **SageMaker 리소스를 선언적(Declarative)으로 관리·실행**할 수 있도록 지원합니다.

---

## 🧬 지원하는 SageMaker 작업 유형

| CRD 리소스 타입       | 설명 |
|------------------------|------|
| `TrainingJob`          | SageMaker에서 훈련 작업을 실행합니다. |
| `HyperParameterTuningJob` | 하이퍼파라미터 튜닝 작업을 실행합니다. |
| `Model`                | 모델 아티팩트 정의 및 SageMaker 모델 리소스를 생성합니다. |
| `EndpointConfig`       | 엔드포인트 구성을 정의합니다. |
| `Endpoint`             | 추론용 엔드포인트를 배포합니다. |
| `BatchTransformJob`    | 배치 추론 작업을 실행합니다. |

---

## ✅ 장점

- **Kubernetes 친화적**: kubectl을 통해 SageMaker 리소스를 관리할 수 있습니다.
- **SageMaker의 인프라 자동화 혜택 유지**: 스케일링, 로깅, 보안 등 SageMaker가 제공하는 관리형 기능을 그대로 활용할 수 있습니다.
- **CI/CD 연동 유리**: GitOps, Helm 등과 통합해 MLOps 파이프라인을 구현하기 쉽습니다.
- **모델/추론 분리 가능**: 모델 학습은 SageMaker에서, 애플리케이션은 Kubernetes에서 독립적으로 운영할 수 있습니다.

---

## ⚠️ 고려사항

| 항목 | 설명 |
|------|------|
| **SageMaker 외부 실행은 불가** | CRD로 K8s 리소스를 정의하더라도 실제 작업 실행은 SageMaker에서 이뤄집니다. |
| **리소스 통제 필요** | IAM 역할과 네트워크/VPC 권한 등 적절한 권한·보안 설정이 필요합니다. |
| **추론 호스팅은 SageMaker 기준** | 엔드포인트는 Kubernetes가 아닌 SageMaker 인프라에 생성되어 호스팅됩니다. |

---

## 🧾 요약

| 항목 | 설명 |
|------|------|
| **정의** | Kubernetes에서 SageMaker 작업을 선언적으로 실행할 수 있게 해주는 오픈소스 연동 도구입니다. |
| **형태** | Kubernetes Operator와 CRD 조합으로 동작합니다. |
| **사용자 대상** | K8s 기반 MLOps 사용자 및 플랫폼 엔지니어를 주요 대상으로 합니다. |
| **주요 효과** | Kubernetes 기반 워크플로우와 SageMaker의 강력한 학습/추론 인프라를 통합할 수 있습니다. |