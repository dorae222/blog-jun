---
title: Amazon Augmented AI (Amazon A2I)
slug: "amazon-augmented-ai-amazon-a2i"
category: cloud
tags: ["amazon-a2i", "amazon-mechanical-turk", "aws", "data-validation", "hitl", "human-in-the-loop", "machine-learning", "mlops", "rekognition", "textract"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:04.784115+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---
---
aliases:
  - A2I
  - Amazon A2I
---
## 🧩 Quick Overview

| 항목              | 설명 |
|-------------------|------|
| **서비스명**       | Amazon Augmented AI (Amazon A2I) |
| **유형**           | **휴먼 인 더 루프(Human-in-the-Loop, HITL) ML 서비스** |
| **주요 목적**       | 머신러닝 모델 예측 결과를 **사람이 검증·보정할 수 있도록** 워크플로우 제공

> 👨‍💻 **Amazon A2I**는 자동화된 AI 예측 결과에 대해 필요할 때 사람의 검증을 결합하여
> **정확도와 신뢰성**을 높이는 서비스입니다.

---

## 🔧 동작 방식

1. **모델 예측 수행**
   - Amazon Textract, Rekognition, Custom ML 모델 등으로 예측을 수행합니다.
2. **휴먼 리뷰 조건 충족 시 트리거**
   - Confidence Score가 낮거나 사전에 정의된 조건을 만족하면 A2I가 활성화됩니다.
3. **휴먼 검증(Human Loop)**
   - 검증자는 A2I의 UI에서 예측 결과를 확인하고 필요 시 수정합니다.
4. **최종 결과 반환**
   - 검증된 데이터는 애플리케이션이나 데이터 스토리지에 저장됩니다.

---

## 📦 주요 구성 요소

| 요소 | 설명 |
|------|------|
| **Flow Definition** | Human Loop 워크플로우(트리거 조건, 태스크 UI, 작업자 그룹 등)를 정의합니다. |
| **Human Task UI**   | 브라우저 기반의 검증 화면(커스텀 HTML로 UI 정의 가능) |
| **Workforce**       | 내부 직원, Amazon Mechanical Turk, 서드파티 검증 인력 등에서 작업자를 선택할 수 있습니다. |
| **Human Loop**      | 특정 예측 결과를 사람이 검증하는 단위 프로세스입니다. |

---

## ✅ 활용 사례

| 사례 | 설명 |
|------|------|
| **문서 처리** | Amazon Textract로 추출한 문서 필드의 정확도를 사람이 검증합니다. |
| **이미지 라벨링** | Rekognition의 출력 결과를 사람이 확인하여 라벨 품질을 보장합니다. |
| **모델 예측 검수** | 커스텀 모델에서 Confidence가 낮은 결과만 선별해 검토합니다. |
| **규제/감사 대응** | 민감 데이터나 법적 검증이 필요한 예측에 대해 HITL을 적용합니다. |

---

## 🧪 예시 아키텍처

```plaintext
S3 (원본 데이터)
      ↓
Textract / Custom ML
      ↓
Confidence Score 확인
      ↓ (조건 충족 시)
Amazon A2I Human Loop
      ↓
검증 결과 S3 저장
```
