---
title: AWS Glue Studio 개요 및 핵심 포인트
slug: "aws-glue-studio-개요-및-핵심-포인트"
category: cloud
tags: ["aws", "aws-glue", "data-lake", "data-pipeline", "etl", "glue-studio", "pyspark", "redshift", "serverless"]
status: published
post_type: tutorial
quality_score: 9.0
created_at: "2026-03-02T01:08:03.961072+00:00"
---

> **NOTE:**
> 
> - **AWS Glue의 시각적(Visual) ETL 개발 환경**
>     
> - **드래그 앤 드롭 방식**으로 ETL 파이프라인 설계
>     
> - **Apache Spark 기반 서버리스 ETL**
>     
> - 코드 없이(No/Low-code) 또는 **코드 병행 개발 가능**
>     
> - Amazon S3, Redshift, RDS, DynamoDB 등과 연동
>     
> - 자동으로 **PySpark 코드 생성**
>     

**AWS Glue Studio**는
**AWS Glue ETL 작업을 GUI 기반으로 설계·개발·실행할 수 있는 통합 개발 환경(IDE)**입니다.

---

## 🧠 AWS Glue Studio란?

> **AWS Glue Studio**는
> 데이터 엔지니어가 **복잡한 Spark 코드를 직접 작성하지 않고도**
> **시각적으로 ETL(Extract, Transform, Load) 파이프라인을 구축**하도록 도와주는 도구입니다.

- Glue = **엔진**
    
- Glue Studio = **개발 UI**
    

👉 **“Glue를 사용하기 쉽게 만든 화면”**

---

## 🏗️ 전체 구조 개념

```text
[Source]
 (S3 / RDS / Redshift)
        │
        ▼
[AWS Glue Studio]
 (Visual ETL Design)
        │
        ▼
[Glue Spark Job]
 (Serverless)
        │
        ▼
[Target]
 (S3 / Redshift / DW)
```

---

## 🚀 주요 기능

### 1️⃣ 시각적 ETL 파이프라인 설계 ⭐

|기능|설명|
|---|---|
|Drag & Drop|소스, 변환, 타겟 연결|
|DAG 구조|ETL 흐름 시각화|
|실시간 검증|스키마/컬럼 미리보기|

📌 시험 키워드

> _“GUI 기반 ETL”_

---

### 2️⃣ Transform 제공 (코드 없이 가능)

|변환 유형|예시|
|---|---|
|필터|조건부 행 제거|
|매핑|컬럼 이름/타입 변경|
|조인|다중 데이터 소스 결합|
|집계|Group By|
|파생 컬럼|계산 컬럼 생성|

---

### 3️⃣ 자동 코드 생성 (중요)

- 시각적 설계 → **PySpark 코드 자동 생성**
    
- 사용자는 필요 시 **코드 직접 수정 가능**
    

📌 시험 포인트

> _“Glue Studio는 Spark 코드를 생성한다”_

---

### 4️⃣ 개발자 친화 기능

|기능|설명|
|---|---|
|Job Run 모니터링|실행 상태 확인|
|Debug|데이터 샘플 테스트|
|버전 관리|Job 설정 유지|
|북마크|증분 처리 지원|

---

## 📦 Glue Studio에서 사용하는 핵심 개념

|개념|설명|
|---|---|
|**Job**|실행 가능한 ETL 단위|
|**Node**|Source / Transform / Target|
|**DynamicFrame**|Glue 전용 데이터 구조|
|**Spark Session**|분산 처리 엔진|

---

## 🧠 Glue Studio vs Glue Console vs Glue DataBrew

| 항목    | Glue Studio | Glue Console | Glue DataBrew |
| ----- | ----------- | ------------ | ------------------------------------ |
| 목적    | ETL 개발      | 리소스 관리       | 데이터 정제                               |
| 방식    | 시각적 + 코드    | 설정 중심        | 완전 노코드                               |
| Spark | O           | O            | X                                    |
| 대상    | 엔지니어        | 관리자          | 분석가                                  |

👉 **Studio = 개발**, **DataBrew = 데이터 클렌징**

---

## 🆚 Glue Studio vs Apache Sqoop (시험 대비)

| 항목    | Glue Studio | Sqoop        |
| ----- | ----------- | ------------ |
| 처리 방식 | Spark ETL   | MapReduce 배치 |
| 플랫폼   | 서버리스        | Hadoop 클러스터  |
| 실시간   | ❌           | ❌            |
| 현대적   | ✅           | ❌ (레거시)      |

---

## 🧪 시험에 자주 나오는 문제 유형

### ❓ 문제 1

> Spark 코드를 직접 작성하지 않고
> AWS에서 ETL 파이프라인을 시각적으로 만들고 싶다.

✅ 정답

- **AWS Glue Studio**
    
---

### ❓ 문제 2

> S3의 데이터를 변환하여 Redshift로 적재하려 한다.
> 서버 관리 없이 구현하고 싶다.

✅ 정답

- **AWS Glue Studio**
    
---

### ❌ 오답 유도

- Athena (쿼리 도구)
    
- EMR (클러스터 관리 필요)
    
- DataBrew (대규모 ETL 부적합)
    

---

## ⚠️ 제한 사항 (시험 포인트)

- Glue Studio ≠ 실시간 스트리밍
    
- Spark 기반 → **Cold Start 존재**
    
- 대화형 쿼리 ❌
    
- Glue 비용 = **DPU 사용량 기반**
    
---

## ✅ 사용 사례

- 🔄 S3 → Redshift ETL
    
- 📊 Data Lake 정제 파이프라인
    
- 🧠 DW 적재 전 데이터 가공
    
- 🔐 규제 데이터 마스킹
    
- 🧪 배치 기반 데이터 변환
    
---

## ✅ 요약 (암기용)

|항목|핵심|
|---|---|
|이름|**AWS Glue Studio**|
|역할|시각적 ETL 개발 환경|
|엔진|Apache Spark|
|방식|Drag & Drop + PySpark|
|서버 관리|❌|
|대상|배치 ETL|

---

### 📌 한 줄 요약 (시험용)

> **AWS Glue Studio = GUI 기반 서버리스 Spark ETL 개발 도구**