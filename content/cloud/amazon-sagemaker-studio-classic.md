---
title: Amazon SageMaker Studio Classic
slug: "amazon-sagemaker-studio-classic"
category: cloud
tags: ["aws", "cloud", "iam", "jupyterlab", "machine-learning", "mlops", "sagemaker", "sagemaker-studio-classic", "vpc"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.892602+00:00"
---

## 🧩 Quick Overview

| 항목              | 설명 |
|-------------------|------|
| **이름**           | Amazon SageMaker Studio Classic |
| **유형**           | **기존 UI 기반의 SageMaker 통합 개발 환경 (IDE)** |
| **출시 연도**      | 2019년 |
| **대상 사용자**     | 데이터 과학자, ML 엔지니어, 분석가

> 🧪 **목적**: 브라우저 기반으로 **머신러닝 워크플로우 전체를 코드 중심으로 개발 및 관리**할 수 있는 종합 IDE 환경

---

## 🧬 주요 기능

| 기능 영역         | 설명 |
|-------------------|------|
| **JupyterLab 기반** | Studio Classic은 JupyterLab 인터페이스 위에 SageMaker 기능을 확장한 형태 |
| **통합 작업 공간** | 훈련, 추론, 파이프라인, 디버깅, 실험 추적까지 하나의 IDE에서 수행 가능 |
| **SageMaker 통합** | Processing Job, Training Job, Model Registry, Pipelines, Debugger 등 완전 통합 |
| **커널/이미지 선택** | TensorFlow, PyTorch, Hugging Face 등 다양한 커널 및 컨테이너 지원 |
| **실험 추적**       | SageMaker Experiments 기반 실험 버전 관리 및 비교 지원

---

## ✅ 장점

- 올인원 머신러닝 개발 환경(코드 중심)
- SageMaker 리소스와 직접 연결되어 로컬 리소스가 불필요함
- 여러 노트북 인스턴스를 동시에 실행 가능
- IAM 및 VPC 기반의 보안 제어 지원

---

## ⚠️ 한계 및 주의점

| 항목 | 설명 |
|------|------|
| **신규 Studio UI와 병행 운영 중** | 현재는 **Studio Classic (기존)**과 **Studio (차세대)**로 분리되어 병행 운영 중 |
| **JupyterLab 위주 환경** | GUI 중심 사용자는 접근성이 낮을 수 있음 |
| **정책 구성 필요** | 초기 설정 시 IAM Role, Domain, User Profile 등의 정책 구성이 필요함

---

## 🧾 요약

| 항목 | 설명 |
|------|------|
| **정의** | SageMaker가 제공하는 Jupyter 기반의 **기존형 통합 ML 개발 환경** |
| **주요 특징** | 코드 중심 개발, SageMaker 리소스 통합, 다양한 커널 지원 |
| **차이점** | Studio Classic은 **기존 JupyterLab 중심**이고, Studio(NextGen)는 **GUI 기반으로 기능을 확장 중** |
