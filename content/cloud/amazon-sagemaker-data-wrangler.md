---
title: Amazon SageMaker Data Wrangler
slug: "amazon-sagemaker-data-wrangler"
category: cloud
tags: ["amazon-sagemaker", "aws", "data-preprocessing", "data-visualization", "data-wrangler", "etl", "feature-engineering", "pandas", "pyspark", "sagemaker-studio"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.797635+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A


---
---
aliases:
  - SageMaker Data Wrangler
---
## 🧩 Quick Overview

| 항목         | 설명                                                                                   |
| ---------- | ------------------------------------------------------------------------------------ |
| **서비스명**   | Amazon SageMaker Data Wrangler                                                       |
| **기능**     | 데이터 탐색, 정제(Cleansing), 변환(Transformation), 풍부화(Enrichment) 등 **ML 전처리 전체를 시각적으로 수행** |
| **대상 사용자** | 데이터 과학자, 분석가                                                                         |
| **통합 환경**  | SageMaker Studio 내 통합                                                                |
| **출력**     | SageMaker Processing Job, Pipeline Step, Python Script 등으로 내보내기 가능                   |

> 🔄 **목적**: ML 모델 학습 전 데이터를 **정제, 가공, 피처 엔지니어링, 풍부화**하여  
> **코드 없이 GUI에서 반복 가능한 워크플로우**로 구성

---

## 🔧 주요 기능

### 1️⃣ 데이터 연결 (Data Connectivity)
- Amazon S3, Amazon Athena, Amazon Redshift, Snowflake 등 외부 데이터 소스에 직접 연결
- 데이터셋 탐색 및 샘플링 지원

### 2️⃣ 데이터 정제 (Cleansing)
- Null/결측치 처리
- 중복 제거
- 이상치 감지 및 필터링
- 형식 표준화(문자열 트림, 타입 변환 등)

### 3️⃣ 데이터 변환 (Transformation)
- 40+ 내장 변환 제공(스케일링, 원-핫 인코딩, 수치 변환 등)
- 파티션, 병합, 집계와 같은 복합 변환 지원
- PySpark/Pandas 코드로 사용자 정의 변환을 확장 가능

### 4️⃣ 데이터 풍부화 (Enrichment)
- 외부 소스 조인(Join) 및 파생 피처 생성
- 타임스탬프 분해(연/월/일), 지리 정보 생성
- 통계 기반 집계 및 그룹별 파생 변수 추가

### 5️⃣ 시각화 & 통계 분석
- 데이터 분포, 상관관계, 이상치 시각화
- 기본 통계(평균, 표준편차, NULL 비율) 제공

### 6️⃣ 파이프라인 및 코드 내보내기
- SageMaker Pipeline Step 또는 Processing Job으로 변환
- Python 스크립트 자동 생성 → 재현 가능성 확보

---

## ✅ 장점

- **코드 최소화**: GUI 기반으로 데이터 정제·변환·풍부화를 수행 가능
- **반복 가능한 워크플로우**: 데이터 처리 단계의 시각화 및 추적이 용이
- **SageMaker 완전 통합**: 학습/추론 파이프라인과 손쉽게 연결 가능
- **자동화·확장성**: Python script나 Processing Job으로 전환해 대규모 데이터 처리 지원

---

## 🧾 요약

| 항목       | 설명 |
|------------|------|
| **정의**     | ML 데이터 전처리를 위한 SageMaker Studio 기반의 시각적 워크플로우 도구 |
| **주요 기능** | 데이터 연결, Cleansing, Transformation, Enrichment, 시각화, 파이프라인/코드 출력 |
| **장점**     | 코드 최소화, 반복 가능, Studio·Pipeline 통합 |
| **출력 방식** | Processing Job, Pipeline Step, Python Script |
