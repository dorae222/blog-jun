---
title: AWS Glue Crawler 개요
slug: "aws-glue-crawler-개요"
category: cloud
tags: ["athena", "aws", "aws-glue", "crawler", "data-catalog", "etl", "redshift", "s3"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:03.855926+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---

## 🧩 Quick Overview

| 항목        | 설명                                                                          |
| --------- | --------------------------------------------------------------------------- |
| **서비스명**  | AWS Glue Crawler                                                            |
| **기능**    | 데이터 소스를 자동 스캔하여 메타데이터(스키마)를 수집하고 Data Catalog에 등록 |
| **지원 소스** | Amazon S3, RDS, Redshift, DynamoDB, JDBC 등                                  |
| **출력 대상** | AWS Glue Data Catalog (데이터베이스 및 테이블)                                        |

> 🔍 **목적**: 다양한 저장소의 데이터를 자동으로 스캔해 스키마를 추론하고, 분석 및 ETL 작업에 필요한 데이터 카탈로그를 자동으로 생성하는 데 사용

---

## 🔧 주요 기능

- 다양한 파일 포맷 인식 (CSV, JSON, Parquet, Avro 등)
- 다중 파티션 자동 인식 (예: `year=2024/month=07/`)
- 증분 인식 및 기존 테이블 업데이트 가능
- 주기적 스케줄링(정기 크롤링 지원)

---

## ✅ 장점

- 수동으로 스키마를 정의하지 않아도 자동으로 데이터 카탈로그를 구축할 수 있음
- 다양한 데이터 소스를 통합해 일관된 스키마 관리 가능
- Athena, Redshift Spectrum, Glue ETL 등 AWS 분석 서비스와 즉시 연동 가능
- 변경된 데이터에 대해 반복 크롤링을 통해 손쉽게 반영 가능

---

## 🧾 요약

| 항목 | 설명 |
|------|------|
| **정의** | S3 등 데이터 소스를 자동으로 스캔해 스키마를 추출하고 Glue Data Catalog에 등록하는 도구 |
| **출력** | 데이터베이스와 테이블(스키마) |
| **활용처** | Athena 쿼리, Glue ETL 작업, Redshift Spectrum 등 |
| **주요 특징** | 자동 스키마 추론, 증분 업데이트, 포맷 자동 인식 |