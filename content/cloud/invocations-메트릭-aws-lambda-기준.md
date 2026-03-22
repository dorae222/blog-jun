---
title: Invocations 메트릭 (AWS Lambda 기준)
slug: "invocations-메트릭-aws-lambda-기준"
category: cloud
tags: ["api-gateway", "aws", "aws-lambda", "cloudwatch", "metrics", "observability", "serverless"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:07.035416+00:00"
---

## 🧩 Quick Overview

| 항목              | 설명 |
|-------------------|------|
| **메트릭 이름**     | `Invocations` |
| **서비스 연동**     | AWS Lambda, Step Functions, API Gateway 등 |
| **기능**           | 리소스 또는 함수가 **호출된 횟수(Count)**를 기록 |
| **측정 단위**      | Count (1초~1분 단위 가능)

> 🔁 **의미**: 지정한 시간 동안 **Lambda 함수가 호출된 횟수**를 나타내는 **기본적인 사용량 지표**

---

## 🔍 Invocations 메트릭 상세 (Lambda 기준)

| 항목 | 설명 |
|------|------|
| **정의** | 함수가 실행된 총 횟수 (성공 + 실패 포함) |
| **포함 항목** | 요청에 의해 호출된 모든 실행 (재시도 포함) |
| **미포함 항목** | 동시성 제한으로 거부된 요청 (→ `Throttles`로 측정됨) |
| **관련 지표** | `Errors`, `Throttles`, `Duration`, `ConcurrentExecutions` |

---

## ✅ 활용 시나리오

- Lambda 사용량 및 트래픽 분석
- 이상 호출 탐지 (갑작스런 증가/감소)
- 비용 추정 (Invocation 수에 따라 과금)
- Auto Scaling 정책 설계 시 기준 지표로 활용

---

## 🧾 요약

| 항목 | 설명 |
|------|------|
| **메트릭명** | `Invocations` |
| **기록 대상** | 함수 호출 횟수 (정상 + 실패 포함) |
| **단위** | Count |
| **적용 서비스** | Lambda, API Gateway, Step Functions 등 |
| **비교 메트릭** | `Errors`, `Throttles`, `Duration`, `SuccessRate` |