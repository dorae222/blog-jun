---
title: AWS Compute Optimizer 빠른 개요
slug: "aws-compute-optimizer-빠른-개요"
category: cloud
tags: ["auto-scaling", "aws", "cloudwatch", "compute-optimizer", "cost-optimization", "ebs", "ec2", "fargate", "lambda"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:03.619754+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---
---
aliases:
  - Compute Optimizer
---
## 🧩 Quick Overview

| 항목              | 설명 |
|-------------------|------|
| **서비스명**       | AWS Compute Optimizer |
| **기능**           | EC2, Lambda, EBS, Fargate 등의 **컴퓨팅 리소스 최적화 추천** 제공 |
| **분석 대상**      | 사용량 메트릭, 성능 히스토리, 리소스 설정 |
| **출력 결과**      | 인스턴스/디스크/함수 유형 변경 추천 (Under/Over-provisioned 등)

> 🎯 **목적**: 과도하거나 부족한 리소스 설정을 자동 분석하여 **비용 절감 + 성능 유지**를 위한 인스턴스 유형, 크기, 설정 개선안을 제시

---

## 🔍 주요 기능

- EC2 인스턴스: 인스턴스 타입/크기/세대 전환 추천
- EBS 볼륨: IOPS 및 처리량 기준으로 유형 최적화 제안
- Lambda 함수: 메모리 및 실행 시간 기준으로 리소스 할당 조정 추천
- Auto Scaling 그룹: 규모, 용량 조정 제안
- Fargate 서비스: vCPU/메모리 조정 제안

---

## ✅ 장점

- 비용 절감 가능성 제시 (과다 프로비저닝 탐지)
- 성능 저하 우려 시 과소 설정도 탐지
- 운영 부담이 적음 (자동 분석, 클릭 한 번으로 권장안 확인)
- CloudWatch 통합 → 과거 사용량 기반의 정확한 분석

---

## 🧾 요약

| 항목 | 설명 |
|------|------|
| **정의** | AWS 리소스의 실제 사용량을 분석하여 최적화된 인프라 구성을 추천하는 서비스 |
| **지원 리소스** | EC2, EBS, Lambda, Fargate, Auto Scaling |
| **주요 효과** | 비용 절감, 성능 유지, 자원 낭비 방지 |
| **분석 기반** | CloudWatch Metrics (최소 14일 이상의 사용 데이터 필요) |