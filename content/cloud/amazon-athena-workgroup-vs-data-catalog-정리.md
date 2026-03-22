---
title: "Amazon Athena: Workgroup vs Data Catalog 정리"
slug: "amazon-athena-workgroup-vs-data-catalog-정리"
category: cloud
tags: ["amazon-athena", "analytics", "aws", "data-catalog", "data-governance", "glue", "s3", "serverless", "workgroup"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:04.760517+00:00"
---

Category: Cloud  
Subcategory: 11.AWS  
Quality grade: A

---

## 1️⃣ Amazon Athena란?

> **Amazon Athena는 S3에 저장된 데이터를 SQL로 직접 분석하는 서버리스 쿼리 서비스**입니다.

- 인프라 관리 불필요
- 사용한 쿼리 스캔량만큼 과금
- AWS Glue Data Catalog와 긴밀히 연동

---

## 2️⃣ Athena의 두 핵심 관리 축

Athena는 **두 가지 서로 다른 관리 단위**를 가집니다:

|구분|역할|
|---|---|
|**Workgroup**|_쿼리 실행을 어떻게 관리할지_
|**Catalog**|_쿼리 대상 데이터가 무엇인지_

👉 **“실행 관리 vs 메타데이터 관리”**

---

## 3️⃣ Athena Workgroup (쿼리 실행 관리)

### 정의

> **Workgroup은 Athena 쿼리 실행의 비용, 설정, 접근 제어를 관리하는 단위**

### 관리 대상

- 쿼리 실행 권한
- 결과 저장 위치
- 암호화
- 비용 한도
- 감사 로그

### 주요 기능 요약

|기능|설명|
|---|---|
|비용 제한|그룹별 쿼리 비용 제한|
|설정 강제|결과 위치, 암호화 강제|
|접근 제어|IAM으로 실행 권한 분리|
|감사|그룹별 쿼리 이력|

### 언제 쓰나?

- 팀별 비용 통제
- 실험/운영 쿼리 분리
- 보안 설정 강제

---

## 4️⃣ Amazon Athena Data Catalog (메타데이터 관리)

### 정의

> **Catalog는 Athena가 쿼리할 데이터의 스키마와 위치를 정의하는 메타데이터 저장소**

### 기본 Catalog

- `AwsDataCatalog`  
    → **AWS Glue Data Catalog 기반**

### Catalog가 관리하는 것

- 데이터베이스
- 테이블
- 컬럼
- 파티션
- 데이터 위치(S3)

### 예시

```sql
SELECT * FROM sales_db.orders;
```

|요소|Catalog 역할|
|---|---|
|sales_db|데이터베이스|
|orders|테이블|
|S3 위치|s3://bucket/path/|

---

## 5️⃣ Workgroup vs Catalog 핵심 차이

|구분|Workgroup|Catalog|
|---|---|---|
|목적|쿼리 실행 관리|데이터 구조 정의|
|관리 대상|비용·보안·설정|스키마·테이블|
|IAM 제어|쿼리 실행 권한|메타데이터 접근|
|S3 결과|✔️ 관리|❌|
|데이터 위치|❌|✔️|
|시험 키워드|**비용/거버넌스**|**스키마/메타데이터**|

---

## 6️⃣ 함께 쓰이는 구조 (중요)

```text
사용자
  └─ Athena Workgroup (실행 규칙)
        └─ Athena Query
              └─ Data Catalog (테이블 정의)
                    └─ S3 데이터
```

- **Workgroup 없이는 쿼리 실행 불가**
- **Catalog 없이는 쿼리 대상 정의 불가**
- 서로 **완전히 다른 역할**

---

## 7️⃣ 시험에서 자주 나오는 패턴

### 문제 → 답

- “Athena 비용 제한” → **Workgroup**
- “쿼리 결과 위치 강제” → **Workgroup**
- “테이블 스키마 관리” → **Catalog**
- “Glue 크롤러” → **Catalog**
- “팀별 Athena 접근 분리” → **Workgroup**

---

## 8️⃣ 한 문장 요약 (암기용)

> **Workgroup은 ‘어떻게 쿼리할지’,  
> Catalog는 ‘무엇을 쿼리할지’를 관리한다.**

---

## 9️⃣ 실무 베스트 프랙티스

- 팀/환경별 Workgroup 분리 (prod / dev / adhoc)
- Catalog는 Glue Data Catalog 단일 표준 사용
- Workgroup에서 S3 결과 암호화 강제

---

## 최종 요약

|항목|핵심|
|---|---|
|Athena|서버리스 SQL 엔진|
|Workgroup|실행·비용·보안 관리|
|Catalog|스키마·테이블 관리|
|관계|상호보완적|

---

원하시면

- **Athena + Glue + Lake Formation 관계도**
- **시험 문제 10문제 패턴 요약**
- **실무 IAM 정책 예제**

까지 이어서 정리해 드릴게요.