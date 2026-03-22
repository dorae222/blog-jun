---
title: AWS Control Tower 개요 및 구성
slug: "aws-control-tower-개요-및-구성"
category: cloud
tags: ["account-factory", "aws-config", "aws-control-tower", "aws-organizations", "cloudtrail", "guardrails", "landing-zone", "multi-account-management", "service-control-policy"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:03.656126+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---

- 계정 생성 및 관리의 자동화를 제공하며, 보안 및 규정 준수를 위한 가드레일을 설정한다.
- 계정 생성 시 표준화된 보안 및 운영 가드레일을 자동으로 적용한다.
- OU 계층 구조의 변경 사항을 식별하는 기능은 제공하지 않는다.
- <mark style="background: #FFF3A3A6;">사전 제어</mark>는 특정 리소스의 배포를 방지할 수 있는 기능을 제공한다.
- <mark style="background: #FFF3A3A6;">탐지 제어</mark>는 이미 배포된 리소스를 모니터링하고 감지하는 데 유용하며 사후 감지에 초점이 있다.
- 인라인 정책의 세부적인 내용까지 제어하는 데는 한계가 있다.
- 공용 IP 주소의 사용을 제어하는 기능이 제한적이다.


**AWS Control Tower**는 여러 AWS 계정과 조직(Organizations)을 **중앙에서 손쉽게 생성, 관리, 거버넌스 적용**할 수 있게 해주는 **완전관리형 서비스**이다.  
특히 **대규모 조직, 엔터프라이즈 환경, 규제 산업** 등에서 **보안, 정책, 계정 구조를 자동화하고 표준화**하기 위해 사용된다.

---

## 🎯 핵심 개념 요약

| 항목                                                         | 설명                                                       |
| ---------------------------------------------------------- | -------------------------------------------------------- |
| **계정 생성 자동화**                                              | 새로운 AWS 계정을 안전하고 표준화된 방식으로 생성할 수 있다.                         |
| **Landing Zone 구성**                                        | 거버넌스·보안·네트워크 표준이 적용된 **기초 AWS 환경**을 자동으로 구축한다.                 |
| **통합 거버넌스**                                                | **SCP(서비스 제어 정책), CloudTrail, AWS Config** 등을 중앙에서 자동 적용한다. |
| **다중 계정 관리**                                               | AWS Organizations를 기반으로 여러 계정에 **정책·로그·보안**을 공통 적용한다.        |
| **Account Factory** | **표준화된 계정 템플릿**을 통해 새 계정 생성 및 구성을 자동화한다.                     |

---

## 🏗️ 구성 요소 설명

|구성 요소|설명|
|---|---|
|**Landing Zone**|Control Tower가 자동 구성하는 **보안·네트워크 표준이 설정된 기본 환경**|
|**AWS Organizations**|다중 계정을 하나의 조직 단위로 구성해 중앙에서 관리한다|
|**Account Factory**|사용자가 **새로운 계정을 생성**할 수 있도록 하는 템플릿 기반 포털이다|
|**Guardrails**|사전 구성된 **정책 및 규정 준수 규칙** (예: S3 퍼블릭 차단, 리전 제한 등)|
|**Audit 계정**|중앙 감사를 위한 전용 계정. AWS CloudTrail, Config 등이 설정된다|
|**Log Archive 계정**|모든 계정의 로그를 수집하는 전용 계정 (보관 및 감사를 위해 사용)|

---

## 📋 예시 시나리오

> 대기업 IT 부서가 개발, 테스트, 운영 환경용으로 여러 AWS 계정을 관리한다고 가정:

- Control Tower를 통해 **Landing Zone 생성**
- 각 부서별로 **Account Factory**로 계정 생성
- 모든 계정에 **CloudTrail, Config, SCP 등 정책 자동 적용**
- 개발 계정은 특정 리전만 사용 가능하게 제한 (Guardrails)

---

## 🔐 Guardrails (보안 정책)

Control Tower는 기본적으로 **"경고형(Detective)"**과 **"강제형(Preventive)"** 두 종류의 Guardrail을 제공한다.

| 유형                                                           | 예시                                             |
| ------------------------------------------------------------ | ---------------------------------------------- |
| **강제형 (Preventive)**
→ SCP 사용 | 특정 리전 사용 제한, S3 퍼블릭 차단 등                       |
| **경고형 (Detective)**
→ AWS Config 사용                   | IAM 정책 변경 감지, 비암호화 S3 버킷 감지 등 (AWS Config와 연동) |

---

## ✅ 주요 장점

|항목|설명|
|---|---|
|**빠른 계정 온보딩**|수작업 없이 계정 생성부터 보안 정책 적용까지 자동화한다|
|**보안 및 규정 준수**|Guardrails를 통한 정책 강제 적용이 가능하다|
|**중앙 감사/모니터링**|모든 계정의 CloudTrail, Config 로그를 중앙 계정에서 관리할 수 있다|
|**확장성**|수십~수백 개 계정도 관리 가능 (대기업/공공기관 등에 적합)|
|**비용 최적화 지원**|리소스 태그 관리, 리전 제한 등으로 통제가 가능하다|

---

## 🆚 AWS Control Tower vs AWS Organizations vs SCP

|항목|Control Tower|Organizations|SCP (Service Control Policy)|
|---|---|---|---|
|목적|**계정 생성 + 거버넌스 자동화**|계정 구조 관리|조직 수준 권한 제어|
|자동화 수준|✅ 높음 (Landing Zone 구성 포함)|❌ 없음|❌ 없음|
|UI/콘솔|✅ 제공|❌ 수동 구성|❌ 수동 구성|
|보안 정책|✅ Guardrails 포함|❌ 직접 구성 필요|✅ 강력한 권한 제어|

---

## 📌 요약

|항목|설명|
|---|---|
|서비스명|**AWS Control Tower**|
|역할|AWS 계정 구조를 표준화하고, **보안과 거버넌스를 자동화**한다|
|대상|**다계정 환경, 대기업, 규제 산업, 기관** 등|
|장점|빠른 시작, 자동 정책 구성, 통합 보안 감시|
|핵심 기능|Landing Zone, Guardrails, Account Factory, 중앙 로깅|
