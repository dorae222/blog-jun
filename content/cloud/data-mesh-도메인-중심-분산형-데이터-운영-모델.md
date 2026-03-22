---
title: "Data Mesh: 도메인 중심 분산형 데이터 운영 모델"
slug: "data-mesh-도메인-중심-분산형-데이터-운영-모델"
category: cloud
tags: ["apache-iceberg", "athena", "aws", "data-architecture", "data-governance", "data-mesh", "data-product", "glue", "lake-formation"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:06.512650+00:00"
---

**Data Mesh**는
데이터를 중앙 팀이 독점 관리하는 방식에서 벗어나, **각 도메인(업무 조직)이 데이터의 소유자이자 제품 제공자**가 되는 **분산형 데이터 아키텍처·운영 패러다임**입니다.

---

## 한 줄 정의

> **Data Mesh는 데이터를 ‘플랫폼’이 아니라 ‘제품’으로 보고,
> 도메인별로 소유·책임·자율성을 분산하는 데이터 운영 모델이다.**

---

## 왜 Data Mesh가 등장했나?

전통적인 중앙 집중형 데이터 레이크/웨어하우스는:

- 병목(중앙 팀 과부하)
- 도메인 이해 부족
- 변화에 느린 파이프라인

👉 **조직이 커질수록 확장성이 떨어짐**

Data Mesh는 **조직 구조(도메인)**와 **데이터 소유권**을 정렬해 이러한 문제를 해결합니다.

---

## Data Mesh의 4대 핵심 원칙

### 1️⃣ 도메인 중심 소유 (Domain-oriented ownership)

- 각 도메인 팀이 **자신의 데이터를 직접 소유·관리**합니다.
- 예: 주문, 결제, 배송, 마케팅 도메인

---

### 2️⃣ 데이터 제품화 (Data as a Product)

- 데이터를 내부 고객을 위한 **제품**으로 다룹니다.
- 명확한:
  - 스키마
  - Service Level Agreement
  - 품질
  - 문서
  - 접근 정책

---

### 3️⃣ 셀프서비스 데이터 플랫폼

- 중앙 플랫폼 팀은:
  - 공통 인프라 제공
  - 파이프라인 템플릿
  - 보안/카탈로그/모니터링
- 도메인 팀은 **빠르게 데이터 제품을 생성**할 수 있습니다.

---

### 4️⃣ 연합 거버넌스 (Federated Governance)

- 완전 자유 ❌
- 완전 중앙 ❌
- **공통 규칙과 도메인 자율성의 균형**을 지향합니다.

---

## 전통적 아키텍처 vs Data Mesh

|항목|중앙집중형|Data Mesh|
|---|---|---|
|데이터 소유|중앙 팀|도메인 팀|
|확장성|낮음|높음|
|변경 속도|느림|빠름|
|책임|불명확|명확|
|거버넌스|중앙|연합|

---

## Data Mesh 아키텍처 개념도 (텍스트)

```text
[Order Domain]      [Payment Domain]     [Marketing Domain]
   Data Product        Data Product          Data Product
        \                  |                     /
         \                 |                    /
          ------ Shared Self-Service Platform ------
                 (Storage, Catalog, Security)
```

---

## AWS에서의 Data Mesh 구현 예

### 🧩 공통 플랫폼

- Amazon S3 (데이터 저장)
- AWS Glue Data Catalog (메타데이터)
- AWS Lake Formation (거버넌스)
- Amazon Athena / Redshift (분석)
- IAM / KMS (보안)

### 🧩 도메인 팀

- 각자 Glue/EMR/Fluent 파이프라인
- 각자 S3 prefix / Iceberg 테이블
- 데이터 품질·문서 책임

---

## Data Mesh에 잘 맞는 기술

- **Apache Iceberg** (테이블 제품화)
- **Athena Workgroup** (도메인별 비용 관리)
- **Lake Formation** (연합 거버넌스)
- **Event-driven ingestion**

---

## 언제 Data Mesh가 적합한가?

- 조직이 크고 도메인이 명확할 때
- 데이터 팀 병목이 심할 때
- 여러 팀이 서로 다른 데이터 요구를 가질 때
- 데이터 사용자가 많을 때

❌ 소규모 조직이나 단일 분석팀에는 과도할 수 있습니다.

---

## 시험 대비 핵심 키워드

- “도메인 소유”
- “데이터를 제품으로”
- “셀프서비스 플랫폼”
- “연합 거버넌스”