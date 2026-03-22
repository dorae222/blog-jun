---
title: Amazon SageMaker Clarify
slug: "amazon-sagemaker-clarify"
category: cloud
tags: ["ai-ethics", "aws", "bias-detection", "machine-learning", "model-explainability", "model-fairness", "model-monitoring", "sagemaker", "shap"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.786898+00:00"
---

## 🧩 Quick Overview

| 항목              | 설명 |
|-------------------|------|
| **이름**           | Amazon SageMaker Clarify |
| **기능 유형**       | 머신러닝 모델의 **공정성(Fairness), 편향(Bias), 설명가능성(Explainability)** 분석 도구 |
| **통합 위치**       | Amazon SageMaker (학습 전후 분석 + 배포 후 추적) |

---

## 🎯 목적

- **모델이 왜 그런 예측을 내렸는지** 설명하고
- **데이터와 모델에 내재된 편향을 사전에 진단하거나 사후 분석**하여
- **공정하고 투명한 머신러닝 파이프라인 구축**을 지원

---

## 🧠 주요 기능

| 기능 | 설명 |
|------|------|
| **데이터 편향 탐지 (Pre-training Bias Detection)** | 학습 데이터 내 불균형 또는 불공정 구조 탐지 |
| **모델 편향 탐지 (Post-training Bias Detection)** | 모델 출력이 특정 그룹에 편향되는지 분석 |
| **SHAP 기반 설명 (Feature Attribution)** | 모델 예측에 기여한 주요 피처 확인 |
| **실시간 설명 추적 (Inference Explainability)** | 배포된 모델의 예측 결과에 대한 실시간 설명 생성 |
| **Bias metric 시각화** | Demographic parity, equal opportunity 등 수십 가지 편향 지표 제공 |

---

## 📊 예시 분석 결과

- 모델이 여성 지원자에게 더 낮은 점수를 부여함
- `income` 피처가 예측에 가장 큰 영향을 줌
- train set에서 특정 지역 출신 비율이 과도하게 높음

---

## ✅ 장점

| 항목 | 설명 |
|------|------|
| **사전/사후 편향 분석** | 학습 전 데이터와 학습 후 예측 결과를 모두 진단 가능 |
| **내장 시각화** | SageMaker Studio에서 편향 및 피처 기여도를 그래프로 확인 가능 |
| **SHAP 지원** | Tree 기반 모델뿐 아니라 다양한 모델에 대한 설명 제공 |
| **자동화 연계** | SageMaker Pipelines, Model Monitor 등과 통합하여 자동화 가능한 워크플로우 구성 가능 |

---

## ⚠️ 유의사항

| 항목 | 설명 |
|------|------|
| **모델/데이터 준비 필요** | feature 타입, label 정의, 민감 그룹 지정 등 사전 설정이 필요 |
| **추론 속도 영향** | 실시간 설명은 추론 지연을 초래할 수 있음 |
| **완벽한 공정성 보장은 아님** | 분석 도구로서 도움을 주지만 정책적 판단과 보완 조치는 별도 필요 |

---

## 🧾 요약

| 항목       | 설명 |
|------------|------|
| **정의**     | SageMaker에서 제공하는 **모델 편향 및 설명가능성 분석 도구** |
| **주요 기능** | 편향 진단, SHAP 기반 설명, 실시간 예측 설명 |
| **적용 대상** | 민감 피처가 있는 모델(예: 성별, 인종 등), 모델 디버깅, 감사 추적 |
| **통합성**   | SageMaker Studio, Pipelines, Endpoint, Model Monitor 등과 통합 |
