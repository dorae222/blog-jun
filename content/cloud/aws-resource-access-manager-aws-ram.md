---
title: AWS Resource Access Manager (AWS RAM)
slug: "aws-resource-access-manager-aws-ram"
category: cloud
tags: ["aws", "aws-organizations", "aws-ram", "cloud-architecture", "multi-account", "resource-sharing", "transit-gateway", "vpc"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:04.288318+00:00"
---

**AWS Resource Access Manager (AWS RAM)**는 **AWS 계정 간 또는 AWS 조직 내에서 리소스를 안전하게 공유할 수 있도록 돕는 서비스**입니다. 특히 멀티 계정 아키텍처에서 **리소스 중복을 줄이면서 보안을 유지한 채 공유**할 수 있게 해줍니다.

---

## 📦 AWS Resource Access Manager (RAM)란?

> **AWS RAM**은
> **VPC, 서브넷, Transit Gateway, License, Route 53 Resolver 등 다양한 AWS 리소스를
> 다른 AWS 계정 또는 조직 단위(OU)와 안전하게 공유할 수 있도록 하는 서비스**입니다.

즉, 조직 내 여러 계정이 **공통 인프라 자원(VPC 등)을 재사용**하거나
**<mark style="background: #FFF3A3A6;">중앙</mark> 네트워크 계정에서 구성한 리소스를 다른 계정에 제공**할 수 있습니다.

---

## 🧩 공유 가능한 주요 리소스 예시

|리소스 종류|공유 가능 여부|
|---|---|
|**VPC 서브넷**|✅|
|**Transit Gateway**|✅|
|**Route 53 Resolver 규칙**|✅|
|**License Manager**|✅|
|**AWS Backup Vault**|✅|
|**Compute Optimizer 권장 사항**|✅|

> ❗ EC2 인스턴스, S3 버킷 같은 **리소스 수준 권한 관리가 아닌 것**은 공유 대상이 아닙니다.

---

## 🛠️ 어떻게 작동하나요?

1. **공유하려는 리소스**를 선택
    
2. **공유 대상(AWS 계정, OU, 전체 조직)** 지정
    
3. **리소스 공유(Share)** 생성 → 수신 계정에서 **수락(Accept)** 필요 (조직 내 자동 수락도 가능)
    
4. 수신 계정은 **해당 리소스를 자체 계정 내 리소스처럼 사용할 수 있음**
    

---

## 🏗️ 실무 아키텍처 예시

### 예: 중앙 네트워크 계정에서 Transit Gateway 공유

```
[Account A (중앙 네트워크 계정)]
         │
  ┌───── AWS RAM ─────┐
  ▼                  ▼
Account B        Account C
(VPC 연결)       (VPC 연결)
```

- Account A는 **Transit Gateway를 생성 및 공유**
    
- Account B, C는 **자신들의 VPC를 공유된 TGW에 연결**
    

---

## 🔐 보안과 제어

|항목|설명|
|---|---|
|**IAM 정책 통제**|RAM 리소스를 공유/수락할 수 있는 권한을 IAM으로 제어할 수 있음|
|**조직 기반 공유**|AWS Organizations를 활용하면 **자동 승인** 설정 가능|
|**세분화된 공유 제어**|특정 리소스 타입만 공유하거나 읽기 전용 등 제어 가능|

---

## ✅ 장점

|항목|설명|
|---|---|
|**중복 제거**|동일한 리소스를 각 계정이 따로 생성할 필요 없음|
|**비용 효율**|리소스 재사용으로 관리비용 절감|
|**보안 유지**|IAM과 RAM으로 최소 권한 원칙을 유지 가능|
|**조직 내 확장성**|수십~수백 계정이 있는 조직에서도 공유 관리를 중앙에서 수행 가능|

---

## ✅ 요약

|항목|설명|
|---|---|
|이름|**AWS Resource Access Manager (AWS RAM)**|
|목적|AWS 리소스를 **다른 계정 또는 조직과 안전하게 공유**|
|공유 대상|AWS 계정, 조직, OU|
|공유 가능한 리소스|VPC, Transit Gateway, Route 53 Resolver 등|
|장점|자원 재사용, 계정 간 분리 + 중앙 제어, 비용 절감, 보안 유지|