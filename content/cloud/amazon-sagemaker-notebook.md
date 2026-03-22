---
title: Amazon SageMaker Notebook
slug: "amazon-sagemaker-notebook"
category: cloud
tags: ["amazon-sagemaker", "aws", "deep-learning", "jupyter", "machine-learning", "mlops", "notebook-instance", "sagemaker", "sagemaker-studio"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:05.920225+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A


---
---
aliases:
  - Amazon SageMaker Notebook
  - SageMaker Notebook
---
## 🧩 Quick Overview

| 항목              | 설명 |
|-------------------|------|
| **이름**           | Amazon SageMaker Notebook (노트북 인스턴스 / Studio 노트북) |
| **기능**           | 브라우저 기반의 **Jupyter Notebook 환경에서 ML 개발, 실험, 시각화** 수행 |
| **유형**           | 노트북 인스턴스 / Studio 노트북 (Classic 및 New Studio 포함)

> 📘 **목적**: 머신러닝 모델의 전처리, 학습, 평가, 디버깅, 배포를 **코드 기반으로 개발할 수 있도록 지원하는 AWS의 노트북 환경**

---

## 🧬 유형별 구분

| 유형 | 설명 |
|------|------|
| **Notebook Instance** | EC2 기반의 독립 실행형 노트북 환경 (수동 인프라 관리 필요) |
| **Studio Notebook** | SageMaker Studio 내 통합된 노트북 (자동 확장, 빠른 시작, 공유 가능) |

---

## 🛠️ 주요 기능

- **JupyterLab 환경** 제공 (Studio 기반은 개선된 UI 제공)
- 다양한 **커널/프레임워크 (PyTorch, TensorFlow, Hugging Face)** 지원
- SageMaker SDK로 **학습/추론/튜닝/파이프라인 실행 코드 작성**
- Studio 노트북은 **자동 저장, 리소스 일시 정지, 협업 공유** 지원

---

## ✅ 장점

| 항목 | 설명 |
|------|------|
| **브라우저 기반** | 설치 없이 즉시 사용 가능 |
| **SageMaker 완전 연동** | 모델 훈련, 디버깅, 추론까지 연결 가능 |
| **유연한 커널 선택** | 다양한 버전과 프레임워크 지원 |
| **협업 기능 (Studio)** | 노트북 공유, 실행 세션 분리 가능 |

---

## ⚠️ 주의사항

- **Notebook Instance는 인프라 직접 관리 필요** (시작/중지, 스토리지 등)
- Studio 노트북은 **IAM, VPC 구성 필요**
- 리소스 선택 시 비용 고려 필요 (GPU 인스턴스 등)

---

## 🧾 요약

| 항목 | 설명 |
|------|------|
| **정의** | SageMaker에서 제공하는 **Jupyter 기반 ML 개발 환경** |
| **형태** | Notebook Instance (Legacy), Studio Notebook (Modern) |
| **주요 용도** | 데이터 전처리, 모델 훈련, 실험, 추론 코드 개발 |
| **장점** | AWS 통합, 다양한 커널, 협업 기능 (Studio) |
