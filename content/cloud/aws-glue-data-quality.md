---
title: AWS Glue Data Quality
slug: "aws-glue-data-quality"
category: cloud
tags: ["aws", "aws-glue", "cloudwatch", "data-governance", "data-pipeline", "data-quality", "data-validation", "etl"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:03.879171+00:00"
---

## 🧩 Quick Overview

| 항목              | 설명 |
|-------------------|------|
| **이름**           | AWS Glue Data Quality |
| **소속 서비스**     | AWS Glue (ETL/데이터 처리 플랫폼) |
| **기능 유형**       | 데이터 품질 검증 및 관리 도구  |
| **목적**           | 데이터 파이프라인에서 **데이터의 정확성, 완전성, 일관성** 등을 자동으로 검증 |

---

## 🧠 주요 기능

| 기능                     | 설명 |
|--------------------------|------|
| **자동 규칙 생성 (Auto rules)** | 데이터 샘플을 기반으로 품질 검증 규칙을 자동으로 생성 |
| **사용자 정의 규칙**        | SQL-like DSL을 이용해 수동으로 규칙을 작성 가능 |
| **데이터 품질 스캔 (DQ scan)** | 테이블에 대해 품질 규칙을 실행하고 통과/실패 여부를 기록 |
| **통계 수집**              | NULL 비율, 고유값 개수, 분포 등 기본 프로파일링 정보를 수집 |
| **CloudWatch 연동**        | 품질 실패 시 알림과 모니터링을 CloudWatch로 연동 가능 |
| **ETL 파이프라인 통합**     | Glue Job이나 Workflow 내에 품질 검사를 삽입하여 자동화 가능 |

---

## ✅ 예시 품질 규칙

| 규칙 종류      | 예시 |
|----------------|------|
| Null 체크      | `column IS NOT NULL` |
| 고유성         | `column IS UNIQUE` |
| 범위 제약      | `column BETWEEN 100 AND 500` |
| 값 포함 여부    | `column IN (‘A’, ‘B’, ‘C’)` |
| 값 길이 제한    | `length(column) < 20` |

---

## 🛠️ 사용 예시

```sql
RULE "no_nulls" AS column_a IS NOT NULL;
RULE "valid_age" AS column_b BETWEEN 0 AND 120;
````

```bash
aws glue start-data-quality-ruleset-evaluation-run \
  --data-quality-ruleset MyRuleSet \
  --table-name my_table \
  --database-name my_db
```

---

## ⚙️ 통합 활용

- **Glue Crawler와 연계**: 테이블 생성 후 자동으로 품질 검사를 실행할 수 있음
- **ETL Job 전후 품질 점검**: 데이터 처리 전후에 무결성과 품질을 확인하여 이상을 탐지
- **CI/CD 파이프라인 검증**: ETL 배포 전 자동으로 품질 기준 만족 여부를 검증하여 안정적 배포 지원

---

## 🧾 요약

|항목|설명|
|---|---|
|**정의**|AWS Glue 기반의 **데이터 품질 검증 및 규칙 기반 점검 도구**|
|**주요 기능**|자동/수동 품질 규칙 생성, 품질 스캔 실행, 결과 시각화와 통계 수집|
|**장점**|코드 없이 품질 관리를 가능하게 하고, Glue 워크플로우와 연동되어 자동화된 검증을 지원|
|**활용 대상**|ETL 처리 전/후 데이터 검증, DWH 적재 전 품질 확인, 신뢰도 높은 데이터 파이프라인 운영|
