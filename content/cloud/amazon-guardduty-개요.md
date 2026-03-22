---
title: Amazon GuardDuty 개요
slug: "amazon-guardduty-개요"
category: cloud
tags: ["amazon-guardduty", "aws", "aws-cloudtrail", "aws-organizations", "cloud-security", "dns-logs", "security-automation", "threat-detection", "vpc-flow-logs"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.205413+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---

## 🧩 Quick Overview

| 항목              | 설명 |
|-------------------|------|
| **서비스명**       | Amazon GuardDuty |
| **유형**           | **AWS 계정·워크로드·데이터 보호를 위한 위협 탐지 서비스** |
| **주요 목적**       | **AWS 환경에서 악의적 활동·이상 행위·잠재적 보안 위협을 실시간 탐지**하여  
                       **경고(Alert) 제공**

> 🛡 **Amazon GuardDuty**는 AWS 로그 및 위협 인텔리전스를 활용해  
> **비정상 행동과 잠재적 침해 시도를 자동으로 탐지**하는 **관리형 보안 모니터링 서비스**입니다.

---

## 🔧 주요 특징

| 항목 | 설명 |
|------|------|
| **지속적 모니터링** | 24/7 실시간 위협 탐지 (서버리스) |
| **로그 분석 기반** | CloudTrail, VPC Flow Logs, DNS Logs 등 자동 수집·분석 |
| **위협 인텔리전스 연계** | AWS, 서드파티 블랙리스트, ML 모델 기반 탐지 |
| **자동화 연동** | Security Hub, EventBridge, Lambda를 통해 대응 자동화 가능 |
| **멀티 계정 지원** | AWS Organizations와 연계해 중앙 보안 관리 가능 |

---

## 📦 분석 대상 로그

1. **VPC Flow Logs** – 네트워크 트래픽 분석  
2. **AWS CloudTrail Logs** – API 호출 패턴 및 이상 행위 탐지  
3. **DNS Query Logs** – 의심스러운 도메인 접속 탐지  
4. **EKS Audit Logs** – Kubernetes 환경 보안 이벤트 (선택)  
5. **S3 Data Events** – S3 데이터 접근 이상 징후 (선택)

---

## 🧪 활용 예시

- **비정상 API 호출 탐지**
  - 예: 루트 계정에서 의심스러운 지역에서의 로그인
- **악성 IP/도메인 접근 차단**
  - Threat List 기반으로 감염된 인스턴스 탐지
- **데이터 유출 가능성 모니터링**
  - S3에서 예기치 않은 다운로드 트래픽 감지
- **EKS/Kubernetes 보안 강화**
  - Public 액세스 포트 스캔, 권한 상승 시도 탐지

---

## ✅ 장점

- **완전관리형** → 에이전트 설치 불필요
- **지속적 모니터링** → 24/7 자동 위협 탐지
- **보안 자동화 용이** → Security Hub·EventBridge와 통합
- **멀티 계정 중앙화** → 조직 단위 보안 관리 가능

---

## ⚠️ 유의사항

| 항목 | 설명 |
|------|------|
| **사후 탐지 중심** | 탐지는 가능하지만 차단은 별도 서비스 필요 (예: NACL, WAF, Security Hub 연계) |
| **비용 발생** | 분석되는 로그 및 이벤트 수에 따라 과금 |
| **False Positive 가능성** | ML 기반 탐지 시 일부 정상 동작도 경고로 발생 가능 |

---

## 🧾 요약

| 항목       | 설명 |
|------------|------|
| **정의**     | AWS 환경의 **악의적 활동·이상 행위·잠재적 보안 위협**을 실시간 탐지하는 관리형 보안 서비스 |
| **주요 기능** | CloudTrail·VPC Flow·DNS Logs 분석, 위협 인텔리전스 활용, 경고 생성 |
| **활용 예** | 침해 징후 탐지, 데이터 유출 방지, 네트워크 이상 행위 모니터링 |
