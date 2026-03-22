---
title: Compute Savings Plan
slug: "compute-savings-plan"
category: cloud
tags: ["aws", "aws-billing", "aws-fargate", "aws-lambda", "cloud-costs", "compute-savings-plan", "cost-optimization", "ec2", "savings-plans"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:06.419208+00:00"
---

**Compute Savings Plan**은 AWS에서 EC2, AWS Fargate, AWS Lambda와 같은 **컴퓨팅 서비스의 장기 사용을 약정함으로써**
**온디맨드 요금 대비 최대 66%까지 비용을 절감할 수 있는 유연한 요금제**입니다.

---

## 💡 Compute Savings Plan이란?

> **Compute Savings Plan**은 AWS에서 일정 시간당 컴퓨팅 사용량(USD 기준)을
> **1년 또는 3년 기간 동안 약정**함으로써,
> 다양한 컴퓨팅 서비스에 자동으로 할인을 적용하는 **유연하고 강력한 비용 절감 옵션**입니다.

---

## ✅ 적용 대상

|서비스|설명|
|---|---|
|**Amazon EC2**|인스턴스 타입, 리전, OS, 테넌시, 크기에 상관없이 할인 적용|
|**AWS Fargate**|ECS 또는 EKS 기반의 서버리스 컨테이너 워크로드|
|**AWS Lambda**|서버리스 함수 실행 비용에 할인 적용 가능|

---

## 🎯 Compute Savings Plan의 장점

|장점|설명|
|---|---|
|✅ **가장 유연함**|인스턴스 패밀리, 리전, OS, 테넌시 관계 없이 사용 가능|
|✅ **서비스 간 할인 공유**|EC2와 Fargate, Lambda를 함께 사용할 때에도 자동 적용|
|✅ **자동 적용**|약정한 금액 이하 사용 시 자동으로 할인 적용, 초과분은 온디맨드 요금 부과|
|✅ **최대 66% 절감**|Compute Savings Plan 기준으로 온디맨드 대비 할인 제공|

---

## 🔁 EC2 Instance Savings Plan과의 비교

|항목|Compute Savings Plan|EC2 Instance Savings Plan|
|---|---|---|
|**적용 서비스**|EC2, Fargate, Lambda|EC2 전용|
|**인스턴스 패밀리**|모두 지원 (c5→m5 가능)|제한적 (고정 패밀리)|
|**리전**|모두 지원 (us-west → ap-northeast 변경 가능)|고정 리전|
|**할인율**|**최대 66%**|**최대 72%**|
|**유연성**|**가장 높음**|상대적으로 제한적|
|**적합 대상**|다양한 워크로드 운영자|특정 EC2 워크로드에 고정된 사용자|

---

## 🧮 요금 적용 방식

- 약정 기준: “**USD/hour 기준**”의 컴퓨트 사용량을 설정

- 예: 1시간에 $10의 사용량을 1년 약정
    - 시간당 $10 이하의 사용은 자동으로 할인 적용
    - 초과 사용분은 온디맨드 요금 부과

---

## 🧩 활용 예시

> **하이브리드 워크로드 환경**

- EC2 + Fargate + Lambda를 병행 운영 중인 기업
- 리전 변경, 인스턴스 변경, 서비스 변경 가능성이 높은 경우
- Compute Savings Plan을 선택하면 다양한 변경 상황에서도 유연하게 할인 적용 가능

---

## ⚠️ 유의사항

|항목|설명|
|---|---|
|약정금액은 시간당 USD 기준으로 고정됨||
|약정한 시간당 금액을 사용하지 못해도 환불 없음||
|초과 사용은 온디맨드 요금으로 자동 전환됨||

---

## 📌 요약

|항목|내용|
|---|---|
|이름|**Compute Savings Plan**|
|약정 대상|**시간당 USD 단위의 컴퓨트 사용량**|
|적용 서비스|EC2, Fargate, Lambda|
|유연성|인스턴스 타입, 크기, 리전, OS 등 **모두 유연하게 적용**|
|할인율|**최대 66% 할인**|
|약정 기간|1년 또는 3년 (선불, 부분 선불, 무선결제 선택 가능)|