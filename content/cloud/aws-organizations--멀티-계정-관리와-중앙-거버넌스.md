---
title: AWS Organizations — 멀티 계정 관리와 중앙 거버넌스
slug: "aws-organizations--멀티-계정-관리와-중앙-거버넌스"
category: cloud
tags: ["aws", "aws-organizations", "billing", "cloud-governance", "cloud-security", "cost-optimization", "multi-account", "scp", "service-control-policy"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:04.206517+00:00"
---

- 기본적인 계정 관리만 제공
 
**AWS Organizations**는 여러 AWS 계정을 **중앙에서 생성·관리하고, 정책·비용·액세스를 통합적으로 제어할 수 있게 해주는 서비스**입니다.

---

## 🏢 AWS Organizations란?

> **AWS Organizations**는 여러 AWS 계정을 하나의 조직 단위로 묶어
> **계정 생성, 관리, 정책 적용, 결제 통합** 등을 중앙에서 관리할 수 있게 해주는
> **완전관리형 계정 관리 서비스**입니다.

---

## 🎯 왜 사용하는가?

| 목적                 | 설명                                       |
| ------------------ | ---------------------------------------- |
| **계정 분리 및 격리**     | 개발·운영·보안 등 팀별로 별도 계정 사용(보안성 향상)       |
| **중앙 통제**          | 관리 계정에서 조직 전체에 정책을 적용해 통제 가능           |
| **서비스 제어 정책(SCP)** | IAM보다 상위 개념으로 계정의 사용 권한을 제한 가능             |
| **비용 통합(Billing)** | 모든 계정 비용을 하나로 청구(Consolidated Billing) |
| **보안 및 거버넌스 강화**   | 보안 계정·감사 계정 등 별도 관리가 용이                  |

---

## 🧱 주요 구성 요소

| 구성 요소                                          | 설명                            |
| ---------------------------------------------- | ----------------------------- |
| **관리 계정 (Management Account)**                 | 조직 전체를 관리하는 루트 계정             |
| **구성 계정 (Member Account)**                     | 조직에 포함된 개별 AWS 계정           |
| **조직 단위 (Organizational Unit, OU)** | 계정들을 그룹으로 묶는 논리적 단위           |
| **SCP (Service Control Policy)**           | OU나 계정 단위로 **최대 권한을 제한**하는 정책 |

---

## 🔐 Service Control Policies(SCP)

- IAM 정책과 유사하게 보이지만, **계정 전체에 적용되는 상위 수준의 제한 정책**입니다.
- 예: 모든 계정에서 `ec2:TerminateInstances` 금지
    
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Deny",
      "Action": "ec2:TerminateInstances",
      "Resource": "*"
    }
  ]
}
```

> ✅ **IAM 권한 + SCP 허용**이 모두 있어야 실제 작업이 가능합니다.

---

## 💳 결제 통합(Consolidated Billing)

- 모든 계정의 사용량을 **하나의 청구서로 통합**합니다.
- **리전별 할인, EC2 예약 인스턴스 공유 혜택**을 받을 수 있습니다.
- 비용 추적은 계정별로 계속 가능합니다.

---

## 🧪 사용 시나리오

| 상황 | 설명 |
|---|---|
| 여러 팀이 각각 AWS 리소스를 운영함 | 각 팀에 독립 계정을 부여하고 SCP로 권한을 제한 |
| 회계팀이 모든 비용을 통합 관리하고 싶음 | Billing 계정을 관리 계정으로 설정 |
| 보안팀은 모든 계정에 감사 로깅을 강제하고 싶음 | CloudTrail 필수 활성화 정책 적용 |

---

## ✅ 요약

| 항목 | 내용 |
|---|---|
| 이름 | **AWS Organizations** |
| 기능 | **멀티 계정 관리, SCP 정책 적용, 결제 통합** |
| 핵심 장점 | 보안성 강화, 비용 최적화, 중앙 통제 |
| 주로 사용처 | 엔터프라이즈 환경, 거버넌스 강화 조직 |