---
title: Amazon DataZone 개요 및 핵심 기능
slug: "amazon-datazone-개요-및-핵심-기능"
category: cloud
tags: ["amazon-datazone", "aws", "data-catalog", "data-governance", "data-marketplace", "data-mesh", "glue", "lake-formation", "s3"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:04.988874+00:00"
---

**NOTE:**

- **조직 내 데이터 자산을 발견·이해·공유·거버넌스**하기 위한 **데이터 관리 서비스**
- **Data Catalog + Data Governance + Data Marketplace** 개념을 통합
- 데이터 생산자(Producer)와 소비자(Consumer)를 명확히 분리
- **셀프서비스(Self-service) 데이터 접근** 지원
- AWS 분석 서비스(S3, Redshift, Glue, Athena 등)와 연동
- 중앙 통제 + 분산 소유(Data Mesh) 모델 지원

**Amazon DataZone**은
**조직 전체의 데이터를 ‘찾고, 이해하고, 안전하게 사용’할 수 있도록 돕는 데이터 거버넌스 및 데이터 공유 플랫폼**이다.

---

## 🌐 Amazon DataZone이란?

**Amazon DataZone**은
조직 내에 흩어져 있는 데이터 자산을 **카탈로그화**하고,
**정책 기반으로 접근을 제어**하며,
사용자가 **필요한 데이터를 스스로 찾아 활용**할 수 있게 해주는 서비스다.

핵심 목표는 단 하나👇

> **“데이터는 많이 있는데, 아무도 못 쓰는 문제 해결”**

---

## 🏗️ 전체 구조 개념

```text
[Data Producer]
 (S3 / Redshift / Glue)
        │
        ▼
[Amazon DataZone]
 ├─ Business Catalog
 ├─ Data Governance
 ├─ Approval Workflow
 └─ Data Marketplace
        │
        ▼
[Data Consumer]
 (Analyst / Scientist)
```

---

## 🚀 Amazon DataZone의 핵심 기능

### 1️⃣ 데이터 카탈로그 (Business-friendly)

|기능|설명|
|---|---|
|데이터 자산 등록|S3, Redshift 등 자동 수집|
|비즈니스 메타데이터|기술 용어 → 비즈니스 용어|
|검색|키워드 기반 데이터 탐색|
|데이터 설명|Owner, 목적, 품질 정보|

📌 기술 중심 ❌ → **비즈니스 중심 카탈로그** ✅

---

### 2️⃣ 데이터 거버넌스 & 접근 제어

|기능|설명|
|---|---|
|정책 기반 접근|IAM + DataZone 정책|
|승인 워크플로우|데이터 접근 요청/승인|
|감사(Audit)|누가 어떤 데이터 사용했는지 추적|
|도메인 기반 관리|팀/조직 단위 데이터 소유|

📌 시험 키워드

> _“중앙 통제 + 팀별 소유”_

---

### 3️⃣ 데이터 마켓플레이스 (중요)

> **내부 데이터 공유 포털**

|기능|설명|
|---|---|
|데이터 게시|Producer가 데이터 공개|
|데이터 구독|Consumer가 요청|
|승인 절차|Owner 승인 후 사용|
|재사용 촉진|중복 데이터 생성 방지|

📌 시험 포인트

> _“사내 데이터 마켓” → Amazon DataZone_

---

### 4️⃣ Data Mesh 지원

|개념|DataZone 역할|
|---|---|
|Domain|조직/팀 단위 데이터 소유|
|Product|데이터 = 제품|
|Governance|중앙 정책 유지|
|Self-service|사용자 자율 활용|

👉 **Data Mesh 아키텍처의 AWS 구현체**

---

## 📦 주요 개념 정리

|개념|설명|
|---|---|
|**Domain**|데이터 소유 조직 단위|
|**Project**|데이터 작업 단위|
|**Environment**|실제 데이터가 존재하는 리소스|
|**Data Asset**|S3 테이블, Redshift 테이블 등|
|**Subscription**|데이터 사용 요청|
|**Approval**|접근 승인 프로세스|

---

## 🧠 DataZone vs Glue Data Catalog

|항목|DataZone|Glue Data Catalog|
|---|---|---|
|목적|**거버넌스 + 공유**|메타데이터 저장|
|사용자|비즈니스 사용자 중심|기술 사용자 중심|
|승인 워크플로우|O|X|
|마켓플레이스|O|X|
|Data Mesh|O|X|

👉 **Glue = 기술 메타데이터**  
👉 **DataZone = 조직 차원 데이터 운영**

---

## 🆚 DataZone vs Lake Formation

|항목|DataZone|Lake Formation|
|---|---|---|
|역할|데이터 발견·공유·거버넌스|권한 제어 중심|
|UI 중심|O|제한적|
|비즈니스 친화성|높음|낮음|
|통합 관계|Lake Formation 권한 사용|DataZone에 통합됨|

📌 **DataZone은 Lake Formation 위에서 동작**

---

## 🧪 시험에 자주 나오는 문제 유형

### ❓ 문제 1

> 여러 팀이 S3, Redshift에 데이터를 생성하지만
> 데이터가 어디에 있는지 모르고,
> 접근 권한 요청이 복잡하다.

✅ 정답

- **Amazon DataZone**
    

---

### ❓ 문제 2

> 데이터 소유권은 팀별로 유지하면서
> 조직 차원의 거버넌스를 적용하고 싶다.

✅ 정답

- **Amazon DataZone (Data Mesh)**
    

---

### ❌ 오답 유도

- Glue Catalog (권한/승인 부족)

- Athena (쿼리 도구)

- Redshift (저장소)
    

---

## ⚠️ 주의 사항 (시험 포인트)

- DataZone은 **데이터를 저장하지 않음**
- DataZone은 **쿼리 엔진 아님**
- 실제 권한 제어는 **IAM / Lake Formation**
- DataZone은 **조정·관리 레이어**

---

## ✅ 사용 사례

- 🏢 대기업 데이터 거버넌스
- 📊 데이터 민주화(Data Democratization)
- 🧠 Data Mesh 아키텍처 구현
- 🔐 규제 환경(금융/공공) 데이터 관리
- 📦 내부 데이터 마켓플레이스 구축

---

## ✅ 요약 (암기용)

|항목|핵심|
|---|---|
|이름|**Amazon DataZone**|
|목적|데이터 발견·공유·거버넌스|
|핵심 기능|Catalog, Approval, Marketplace|
|아키텍처|Data Mesh|
|저장/쿼리|❌|
|연계|Glue, Lake Formation, IAM|

---

### 📌 한 줄 요약 (시험용)

> **Amazon DataZone = 조직 전체 데이터 거버넌스 & 데이터 마켓플레이스**