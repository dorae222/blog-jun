---
title: Shadow Endpoint (섀도우 엔드포인트)
slug: "shadow-endpoint-섀도우-엔드포인트"
category: cloud
tags: ["a/b-testing", "amazon-sagemaker", "cloudwatch", "inference-recommender", "mlops", "model-validation", "s3", "shadow-endpoint"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:08.281182+00:00"
---

## 🧩 Quick Overview

| 항목              | 설명 |
|-------------------|------|
| **이름**           | Shadow Endpoint (섀도우 엔드포인트) |
| **관련 서비스**     | Amazon SageMaker |
| **기능**           | 실제 사용자 요청을 **복제하여 별도의 테스트용 엔드포인트**로 전달 → **결과는 사용자에게 미반영** |

> 🌗 **Shadow Endpoint**는 **운영 중인 모델과 동일한 입력을 새 모델에도 적용**해 예측 결과를 분석하되, 사용자 응답에는 영향을 주지 않는 안전한 실험 방식입니다.

---

## 🧬 개념 비교

| 구성 요소         | 설명 |
|-------------------|------|
| **Primary Endpoint** | 실제 사용자 요청을 처리하고 응답을 반환하는 운영 엔드포인트 |
| **Shadow Endpoint**  | 요청을 복사 받아 별도로 예측만 수행 (응답 없음) |
| **응답 처리**        | Shadow 결과는 **CloudWatch, S3 등으로 기록만 함** |

---

## ✅ 사용 목적

- **신규 모델 성능 테스트**: 운영 중인 모델과 비교 분석
- **리스크 없는 실험**: 사용자 경험에 영향 없이 실시간 트래픽 테스트
- **모델 배포 전 검증 단계**: A/B 테스트 전 안전성 확인
- **모델 튜닝 또는 인프라 최적화 실험**

---

## 🛠️ 작동 방식 (SageMaker 예시)

1. 엔드포인트 구성 시 ShadowProductionVariants 지정
2. 트래픽은 **실제 응답용(Primary) + Shadow용으로 복제**
3. Shadow 결과는 저장, 로깅, 비교만 수행
4. Inference Recommender 또는 사용자 정의 로직으로 분석

---

## ⚠️ 고려 사항

| 항목 | 설명 |
|------|------|
| **실제 사용자 응답에는 영향 없음** | 오직 테스트 목적 |
| **Shadow도 리소스를 사용함** | 추론 비용 및 메모리 고려 필요 |
| **로그 수집 필수** | 결과 분석을 위한 CloudWatch/S3 구성 필요 |

---

## 🧾 요약

| 항목 | 설명 |
|------|------|
| **정의** | 운영 요청을 복사하여 예측만 수행하는 테스트용 SageMaker 엔드포인트 |
| **응답 처리** | 사용자에겐 전달 안 됨, 내부 기록용 |
| **주요 활용** | 모델 비교 실험, 배포 전 검증, 무중단 품질 테스트 |