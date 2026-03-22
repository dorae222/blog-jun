---
title: Shadow Variant (섀도우 변형) — Amazon SageMaker Endpoint
slug: "shadow-variant-섀도우-변형--amazon-sagemaker-endpoint"
category: cloud
tags: ["a/b-testing", "amazon-sagemaker", "aws", "inference", "model-deployment", "model-monitoring", "sagemaker", "shadow-variant"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:08.271861+00:00"
---

## 🧩 Quick Overview

| 항목              | 설명 |
|-------------------|------|
| **개념 이름**       | Shadow Variant (섀도우 변형) |
| **관련 서비스**     | Amazon SageMaker Endpoint |
| **기능**           | 실제 프로덕션 트래픽을 **복제**하여 지정한 모델 변형(variant)으로 보내는 **테스트 전용 배포 대상** |

> 🌗 **Shadow Variant**는 **사용자 요청을 복사해서 처리하지만, 결과는 반환하지 않고 기록만 수행**하는 모델 변형입니다.  
> → **실제 운영 중인 모델과 비교 분석용으로 사용**

---

## 🧬 구성 원리

| 구성 항목        | 설명 |
|------------------|------|
| **Primary Variant** | 사용자 요청에 응답하는 운영 모델 |
| **Shadow Variant** | 동일 요청을 복제 받아 예측을 수행하지만 응답은 무시함 |
| **트래픽 전달 비율** | 요청의 100%를 Shadow에도 복사 가능 (`VariantWeight=0`) |
| **Metrics 비교** | 예측값, 지연 시간, 오류율 등을 모니터링 도구로 분석 |

---

## ✅ 사용 목적

- 신규 모델의 **품질, 속도, 안정성**을 실제 운영 조건에서 비교
- **무중단 검증**: 실 사용자에 영향 없이 테스트 가능
- **성능 튜닝 실험** (Inference Recommender 등과 병행)
- **A/B 테스트 준비 단계**로 활용

---

## 🛠️ SageMaker JSON 예시

```json
"ProductionVariants": [
  {
    "VariantName": "prod-variant",
    "ModelName": "prod-model",
    "InitialVariantWeight": 1.0
  },
  {
    "VariantName": "shadow-variant",
    "ModelName": "candidate-model",
    "InitialVariantWeight": 0.0,
    "ShadowProductionVariants": true
  }
]
```
