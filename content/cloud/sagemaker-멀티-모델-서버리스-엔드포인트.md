---
title: SageMaker 멀티 모델 서버리스 엔드포인트
slug: "sagemaker-멀티-모델-서버리스-엔드포인트"
category: cloud
tags: ["aws", "cost-optimization", "inference", "ml-deployment", "mme", "multi-model", "s3", "sagemaker", "serverless"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:08.247582+00:00"
---

---
Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---
---
aliases:
  - Sagemaker 멀티 모델 서버리스 엔드포인트
  - SageMaker Multi-Model Serverless Endpoint
  - Multi-Model Serverless Endpoint
---
## 🧩 Quick Overview

| 항목               | 설명 |
|--------------------|------|
| **기능명**          | SageMaker Multi-Model Serverless Endpoint (MME + Serverless) |
| **핵심 개념**       | 여러 개의 머신러닝 모델을 **서버리스 환경에서 단일 엔드포인트로 서비스** |
| **모델 관리 방식**   | 모델은 S3에 저장 → 호출 시 동적 로딩 (Lazy Load) |
| **비용 구조**       | 호출 수 + 처리 시간 + 메모리 사용량 기반 과금

> 🔀 **목적**: 수십~수백 개의 모델을 **효율적·유연하게 배포**하면서, **서버 관리 없이 비용을 절감**할 수 있는 추론 인프라 제공

---

## ⚙️ 구성 특징

| 요소 | 설명 |
|------|------|
| **멀티 모델** | 여러 모델을 한 엔드포인트에서 공유 (S3로부터 호출 시 로드) |
| **서버리스** | 항상 켜져 있지 않으며, **요청 시 실행됨** (콜드 스타트 가능성 있음) |
| **모델 라우팅** | 요청마다 `TargetModel` 지정 가능 (HTTP Header or SDK) |
| **최대 동시 모델** | 수백 개 모델까지 확장 가능 (메모리 한도 내) |
| **적용 대상** | 라이트한 모델 다수 또는 사용자별 커스터마이즈 모델 제공 등 |

---

## ✅ 장점

- **비용 효율성 극대화**
  - 유휴 시간에 대한 과금 없음 + 다수 모델 공유로 리소스 절약
- **모델 관리 간소화**
  - 모델을 별도 등록할 필요 없이 S3 경로만 지정하여 호출 가능
- **배포 속도 향상**
  - 수백 개 모델도 단일 엔드포인트로 커버하여 배포가 간편
- **서버 관리 불필요**
  - 오토스케일링 및 추론 인프라를 AWS가 자동으로 관리

---

## 🧪 예시 (Invoke 시 모델 지정)

```python
response = sagemaker_runtime.invoke_endpoint(
    EndpointName="my-serverless-mme-endpoint",
    ContentType="application/json",
    TargetModel="modelA.tar.gz",  # S3 key 기준
    Body=json.dumps({"input": [1, 2, 3]})
)
```
