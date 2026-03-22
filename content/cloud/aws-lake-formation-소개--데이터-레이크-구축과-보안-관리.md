---
title: AWS Lake Formation 소개 — 데이터 레이크 구축과 보안 관리
slug: "aws-lake-formation-소개--데이터-레이크-구축과-보안-관리"
category: cloud
tags: ["access-control", "athena", "aws", "aws-glue", "data-governance", "data-lake", "lake-formation", "redshift-spectrum", "s3"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:04.125115+00:00"
---

**AWS Lake Formation**은 AWS에서 **데이터 레이크(Data Lake)**를 **쉽고, 빠르고, 안전하게 구축하고 관리**할 수 있도록 도와주는 **완전관리형 서비스**입니다.

---

## 🌊 AWS Lake Formation이란?

> **AWS Lake Formation**은 S3에 저장된 정형 및 비정형 데이터를 수집, 정리, 보안 제어, 카탈로그화하여,  
> **데이터 레이크를 구축하고 제어하는 작업을 단순화**해주는 서비스입니다.

---

## 🔍 주요 목적

- S3 기반의 **데이터 레이크(Data Lake)** 구축을 더 쉽게 하기 위해
- 다양한 데이터 소스를 통합하고 **중앙에서 접근 권한을 통제**하기 위해
- **데이터 분석 서비스들과 연동되도록 메타데이터를 카탈로그화**하기 위해

---

## 🧱 주요 기능 및 구성 요소

| 구성 요소                           | 설명                                                     |
| ------------------------------- | ------------------------------------------------------ |
| **Data Catalog 통합**             | Glue Catalog를 사용하여 스키마와 메타데이터 관리 |
| **Fine-grained access control** | 사용자/그룹 별로 **테이블, 열, 행 수준 접근 제어** 가능                    |
| **Permissions Manager**         | IAM 외에도 데이터 접근 권한을 별도로 관리                              |
| **Crawler & Blueprint**         | 데이터 자동 등록 및 ETL 파이프라인 생성 지원                            |
| **Lake Formation Console**      | 분석가, 데이터 엔지니어가 데이터 카탈로그에 쉽게 접근하고 관리할 수 있는 인터페이스 제공     |

---

## 🔐 데이터 보안 및 거버넌스

Lake Formation은 단순한 IAM이 아닌 **데이터 레벨의 보안 제어**를 제공합니다:

|보안 수준|예시|
|---|---|
|테이블 수준|`sales_data` 테이블 접근 허용/차단|
|열 수준|`customer_ssn` 열만 마스킹 또는 차단|
|행 수준|`region = 'KR'`인 행만 볼 수 있도록 제한|

---

## 🧪 사용 시나리오 예시

- S3에 다양한 부서의 로그, 판매 데이터, 센서 데이터를 저장하고 있음
- 마케팅팀은 `marketing_data` 테이블만 조회 가능해야 함
- 회계팀은 `financial_data`에서 `ssn` 열은 보지 못하도록 제한해야 함
- 이러한 **보안 정책을 중앙에서 통제**하려면 Lake Formation 사용이 적합

---

## 🛠️ 통합 가능한 서비스

Lake Formation은 다음과 같은 AWS 서비스와 통합됩니다:

|서비스|연동 방식|
|---|---|
|**Amazon Athena**|쿼리 실행 시 Lake Formation 권한 체크|
|**Amazon Redshift Spectrum**|외부 테이블 접근 시 권한 통제|
|**Amazon EMR**|Spark 또는 Hive 작업 실행 시 보안 적용|
|**AWS Glue**|ETL 작업 및 데이터 카탈로그 공유|

---

## ✅ 요약

> **AWS Lake Formation**은 S3 기반 데이터 레이크에 대해 **중앙 집중식 보안 관리**, **세분화된 권한 제어**, **자동화된 메타데이터 등록** 등을 제공하여  
> **보안이 강화된 데이터 분석 환경**을 빠르고 쉽게 구축할 수 있도록 해주는 서비스입니다.