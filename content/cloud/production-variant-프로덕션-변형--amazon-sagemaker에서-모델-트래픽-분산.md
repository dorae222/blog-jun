---
title: Production Variant (프로덕션 변형) — Amazon SageMaker에서 모델 트래픽 분산
slug: "production-variant-프로덕션-변형--amazon-sagemaker에서-모델-트래픽-분산"
category: cloud
tags: ["a-b-testing", "amazon-sagemaker", "canary-deployment", "cloudwatch", "model-deployment", "production-variant", "real-time-inference", "shadow-testing"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:08.436704+00:00"
---

## 🧩 Quick Overview

| 항목              | 설명 |
|-------------------|------|
| **이름**           | Production Variant (프로덕션 변형) |
| **소속 서비스**     | Amazon SageMaker |
| **기능 유형**       | 실시간 엔드포인트에 **여러 모델을 병렬로 배포**하여 **트래픽을 분산 처리**하는 구성 단위

> 🎯 **프로덕션 변형(Production Variant)**은  
> 하나의 SageMaker 엔드포인트에 **둘 이상의 모델을 동시에 배치**하고  
> 각 모델에 대해 **트래픽 비율, 인스턴스 수, 리소스 할당** 등을 설정할 수 있게 해주는 메커니즘입니다.

---

## 🧠 구성 요소

| 항목 | 설명 |
|------|------|
| `ModelName`           | 해당 변형에 연결할 모델 이름 |
| `VariantName`         | 식별용 이름 (예: `baseline`, `v2-shadow`, `canary`) |
| `InitialVariantWeight`| 전체 트래픽 중 해당 모델에 할당할 비율 (0.0 ~ 1.0) |
| `InstanceType`        | 추론 실행용 인스턴스 타입 |
| `InitialInstanceCount`| 인스턴스 개수 |

---

## 🔁 작동 방식

```json
"ProductionVariants": [
  {
    "VariantName": "baseline",
    "ModelName": "fraud-detector-v1",
    "InitialVariantWeight": 0.9
  },
  {
    "VariantName": "candidate",
    "ModelName": "fraud-detector-v2",
    "InitialVariantWeight": 0.1
  }
]
````

- 위 설정은 90% 트래픽을 기존 모델(v1), 10%는 새 모델(v2)로 전달합니다.
- 실시간 추론 시 두 모델이 트래픽 비율에 따라 동시에 요청을 처리합니다.
- CloudWatch에서 각 Variant별 호출 수 및 지연 시간(latency)을 모니터링할 수 있습니다.

---

## ✅ 활용 사례

|시나리오|설명|
|---|---|
|**A/B 테스트**|두 모델의 실시간 성능을 비교할 때 사용 (예: v1 vs v2)|
|**점진적 롤아웃**|새 모델을 소량의 트래픽으로 먼저 테스트한 뒤 점진적으로 비중을 늘림|
|**카나리아 배포**|작은 비율로 새 모델을 실험적으로 배포하여 안정성 확인|
|**Shadow Testing**|변형 가중치를 0으로 설정해 트래픽은 전달하지 않고 로그만 수집 가능|

---

## ⚠️ 유의사항

|항목|설명|
|---|---|
|**추론 결과는 단일 응답**|실제 사용자에게는 여러 모델의 출력 중 하나만 단일 응답으로 전달됩니다.|
|**트래픽은 확률 기반 분배**|설정한 비율이 정확히 매 호출마다 일치하지 않을 수 있으며, 확률적으로 분산됩니다.|
|**비용은 변형 수에 따라 증가**|배포하는 모델 수와 인스턴스 수에 따라 요금이 증가합니다.|

---

## 🧾 요약

|항목|설명|
|---|---|
|**정의**|SageMaker 실시간 엔드포인트에 **여러 모델을 병렬 배치**하고, **트래픽 비율을 조절**하는 단위|
|**활용 목적**|A/B 테스트, 점진적 배포, Shadow 테스트 등|
|**구성 요소**|모델 이름, 가중치, 인스턴스 타입, Variant 이름 등|
|**모니터링**|CloudWatch로 Variant별 호출 수, latency, error를 확인|
