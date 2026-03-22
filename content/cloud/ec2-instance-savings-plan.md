---
title: EC2 Instance Savings Plan
slug: "ec2-instance-savings-plan"
category: cloud
tags: ["aws", "aws-billing", "cloud-costs", "cloud-finance", "cost-optimization", "ec2", "instance-savings-plan", "savings-plans"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:06.691286+00:00"
---

**EC2 Instance Savings Plan**은 Amazon EC2 인스턴스를 일정 기간 지속적으로 사용하기로 약정하면 **온디맨드 요금 대비 최대 72%까지 절감**할 수 있는 **비용 절감 옵션**입니다.

이는 AWS의 할인 모델인 **Savings Plans**의 한 종류로, 특정 인스턴스 패밀리와 리전에 대해 약정 사용량을 설정하는 방식입니다.

---

## 💡 EC2 Instance Savings Plan이란?

> **EC2 Instance Savings Plan**은
> 특정 리전에서 특정 **인스턴스 패밀리(CPU/RAM 타입)**에 대해,
> **1년 또는 3년 약정**을 기반으로 EC2 인스턴스 요금을 **대폭 절감**할 수 있는 AWS 요금제입니다.

---

## 🎯 주요 특징

|항목|설명|
|---|---|
|**대상 서비스**|Amazon EC2 인스턴스 전용|
|**적용 범위**|특정 **인스턴스 패밀리**, 특정 **리전**|
|**할인 방식**|약정된 시간당 사용량(USD 기준) 이상을 초과하면 온디맨드 요금 부과|
|**유형**|**1년 또는 3년 약정**, **전액/부분/무선결제 옵션 선택 가능**|
|**유연성**|인스턴스 크기, OS, 테넌시 변경 가능 (같은 패밀리 내에서)|

---

## 🔁 EC2 Instance Savings Plan vs Compute Savings Plan

|항목|EC2 Instance Savings Plan|Compute Savings Plan|
|---|---|---|
|적용 범위|특정 리전 + 인스턴스 패밀리|EC2, Fargate, Lambda 전반|
|유연성|제한적 (패밀리 고정)|매우 유연|
|절감율|**더 높음 (최대 72%)**|다소 낮음 (최대 66%)|
|주요 목적|특정 워크로드에 최적화된 절약|다양한 컴퓨팅 활용에 유리|

---

## 🧩 예시

> 서울 리전에서 `m5` 인스턴스를 3년 동안 계속 사용할 예정이라면?

- `EC2 Instance Savings Plan`으로 `Asia Pacific (Seoul)` 리전의 `m5` 패밀리를 선택
- `m5.large`, `m5.xlarge` 등 크기 변경 가능
- Windows/Linux 모두 허용
- 비용 최대 72% 절감 가능

---

## ✅ 장점

|장점|설명|
|---|---|
|💰 비용 절감|최대 **72% 할인** 가능|
|🔄 유연성|인스턴스 크기, OS, AZ 변경 가능|
|📉 예측 가능한 요금|월 사용량 기반으로 예측 및 계획 가능|
|⚙️ 자동 적용|약정 범위 내에서 자동 할인 적용됨|

---

## ⚠️ 유의사항

|항목|설명|
|---|---|
|고정된 인스턴스 패밀리|예: `m5`로 약정했으면 `c5`에는 적용되지 않음|
|리전 종속|특정 리전에만 적용됨|
|약정 위반 시|초과분은 **온디맨드 요금**으로 부과됨|

---

## 📌 요약

|항목|내용|
|---|---|
|이름|**EC2 Instance Savings Plan**|
|목적|EC2 인스턴스 장기 사용 시 **비용 절감**|
|적용 범위|**특정 인스턴스 패밀리 + 특정 리전**|
|유연성|인스턴스 크기/OS/테넌시 변경 가능 (단, 같은 패밀리 내에서)|
|할인율|최대 **72% 절감**|
|약정 기간|1년 또는 3년 (결제 옵션 선택 가능)|