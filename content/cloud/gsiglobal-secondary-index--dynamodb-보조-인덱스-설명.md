---
title: GSI(Global Secondary Index) — DynamoDB 보조 인덱스 설명
slug: "gsiglobal-secondary-index--dynamodb-보조-인덱스-설명"
category: cloud
tags: ["aws", "cloud", "database-indexing", "dynamodb", "global-secondary-index", "gsi", "lsi", "secondary-index"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:06.878906+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---

---
aliases:
  - GSI
  - 글로벌 보조 인덱스
---
감사합니다! 문맥을 제공해 주셔서 아래에서 GSI를 보다 명확하게 설명드릴 수 있었습니다.

---

## 🔍 여기서 GSI란?

여기서 말하는 **GSI(Global Secondary Index)**는
**Amazon DynamoDB**의 기능 중 하나로,
**기본 키(primary key) 외의 다른 속성(attribute)**을 기준으로 **효율적인 쿼리 실행을 가능하게 해 주는 보조 인덱스**입니다.

즉, GSI는 **데이터 검색 성능을 향상**시키기 위한 **DynamoDB 내부 인덱스 기능**입니다.
이때 **“Global”**이라는 단어는 **리전 간의 글로벌(전역) 복제**를 의미하는 것이 아니라,
**테이블의 파티션 키와 다른 키를 기반으로 인덱스를 만들 수 있다**는 의미에서의 **글로벌**입니다.

---

## 📌 Global Secondary Index (GSI)란?

|항목|설명|
|---|---|
|정식 이름|**Global Secondary Index**|
|대상 서비스|**Amazon DynamoDB**|
|역할|**기본 키 이외의 속성에 대해 쿼리를 가능하게 해주는 보조 인덱스**|
|핵심 특징|파티션 키와 정렬 키를 **기존 테이블 키와 다르게 설정 가능**|
|Global 의미|리전 간이 아니라, **모든 항목에서 사용할 수 있는 인덱스**라는 의미|

---

## 🆚 GSI vs LSI (Local Secondary Index)

|항목|GSI|LSI|
|---|---|---|
|파티션 키|**다를 수 있음**|동일해야 함|
|정렬 키|변경 가능|변경 가능|
|쓰기 시점 정의|테이블 생성 후에도 추가 가능|테이블 생성 시에만 설정 가능|
|용도|범용 쿼리 최적화|동일 파티션 키 내 정렬 쿼리 최적화|

---

## ✅ GSI 요약

|항목|설명|
|---|---|
|이름|Global Secondary Index|
|위치|DynamoDB 테이블 인덱싱|
|주요 목적|비기본 키 속성 기반으로 효율적 쿼리 지원|
|글로벌 의미|"전체 항목 대상 인덱싱 가능"의 의미 (리전과 무관)|
|주의|**리전 간 고가용성**이나 복제를 위한 기능은 아님 (그 역할은 **DynamoDB 글로벌 테이블**이 수행함)|

---

## 🔄 오해 방지

- ❌ **GSI ≠ 글로벌 데이터 복제**
    
- ✅ GSI는 **DynamoDB 테이블 내에서 쿼리 성능 향상을 위한 인덱스**입니다.
