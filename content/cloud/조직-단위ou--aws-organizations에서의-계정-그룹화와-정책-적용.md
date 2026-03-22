---
title: 조직 단위(OU) — AWS Organizations에서의 계정 그룹화와 정책 적용
slug: "조직-단위ou--aws-organizations에서의-계정-그룹화와-정책-적용"
category: cloud
tags: ["account-management", "aws", "aws-organizations", "cloud-governance", "multi-account", "organizational-units", "ou", "scp", "security"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:07.216597+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---

---
aliases:
  - OU
  - 조직 단위
---
**조직 단위(OU, Organizational Unit)**는 **AWS Organizations**에서 여러 AWS 계정을 **논리적으로 그룹화**하는 기능입니다. OU를 사용하면 **정책(SCP)을 그룹 단위로 적용하고**, **계정 관리와 보안을 중앙에서 일괄적으로 제어**할 수 있습니다.

---

## 🏢 조직 단위(OU, Organizational Unit)란?

> **OU(조직 단위)**는 AWS Organizations에서 여러 계정을 **계층적으로 구성하기 위한 논리적 컨테이너**입니다. OU를 사용하면 비슷한 역할, 부서, 보안 정책을 공유하는 계정들을 한데 묶어, **공통된 정책을 일괄 적용**할 수 있습니다.

---

## 🧱 OU 구조 예시

```
루트 (Root)
│
├── 보안-OU
│   ├── 보안 계정
│   └── 감사 계정
│
├── 개발-OU
│   ├── dev-1 계정
│   └── dev-2 계정
│
└── 운영-OU
    ├── prod-1 계정
    └── prod-2 계정
```

- **루트(Root)**: OU와 계정들의 최상위 컨테이너 (필수)

- **OU**: 루트 하위 또는 다른 OU 안에 또 다른 OU를 포함할 수 있음 (최대 5단계 계층 가능)

- **계정**: OU에 포함되는 AWS 계정

---

## 🎯 왜 OU를 사용하는가?

|목적|설명|
|---|---|
|**정책 일괄 적용(SCP)**|OU 전체 계정에 한 번에 정책 적용 가능|
|**조직 관리 단순화**|팀/부서/환경별로 계정 정리|
|**보안 및 거버넌스 강화**|역할에 따라 서비스 사용 제한 가능|
|**비용 추적 및 예산 설정**|OU 단위로 비용 정리 가능|

---

## 🔐 OU + SCP 활용 예시

> 예: `운영-OU`에는 보안 강화를 위해 **IAM 사용자 생성 금지 SCP**를 적용
> → `prod-1`, `prod-2` 계정 모두 해당 정책 적용됨
> → OU에 속한 모든 계정에 **정책이 자동 상속**

---

## ✅ 요약

|항목|내용|
|---|---|
|명칭|**OU (Organizational Unit)**|
|역할|AWS 계정을 **논리적 그룹화**하여 **정책, 관리, 보안 통제**|
|핵심 장점|정책 일괄 적용, 계층적 관리, 보안 일관성|
|사용 예시|부서별, 환경별(Dev/Prod), 목적별 계정 구성|