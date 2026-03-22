---
title: AWS Glue Job Bookmark
slug: "aws-glue-job-bookmark"
category: cloud
tags: ["aws", "aws-glue", "etl", "glue", "incremental-processing", "job-bookmark", "pyspark", "s3"]
status: published
post_type: til
quality_score: 9.0
created_at: "2026-03-02T01:08:03.931492+00:00"
---

**AWS Glue Job Bookmark**는
Glue ETL 작업에서 **이미 처리한 데이터를 기억해 다음 실행 시 새 데이터만 처리하도록 하는 증분 처리 기능**입니다.

---

## 한 줄 정의

> **AWS Glue Job Bookmark는 이전 실행 상태를 저장하여 이후 실행에서 중복 처리 없이 증분 데이터만 처리하게 해주는 메커니즘이다.**

---

## 왜 Job Bookmark가 필요한가?

- S3에 데이터가 **계속 누적**되는 파이프라인

- 매번 전체 데이터를 처리하면:
  - 비용 증가
  - 처리 시간 증가
  - 중복 데이터 위험

👉 **Job Bookmark로 “한 번 처리한 데이터는 다시 처리하지 않음”**

---

## 어떻게 동작하나?

### 내부 동작 개념

- Glue가 각 실행 시:
  - 처리한 **S3 객체/파티션/파일 메타데이터**
  - (경로, 파일명, 타임스탬프 등)
- 이를 **Bookmark 상태로 저장**
- 다음 실행 시:
  - Bookmark 이후에 추가된 데이터만 읽음

---

## 지원 대상 (중요)

|데이터 소스|Bookmark 지원|
|---|---|
|Amazon S3|✅|
|JDBC 소스|✅ (PK/Watermark 기반)|
|DynamoDB|제한적|
|스트리밍|❌|

---

## 사용 예시 (PySpark)

```python
glueContext.create_dynamic_frame.from_options(
    connection_type="s3",
    connection_options={
        "paths": ["s3://my-bucket/data/"],
        "recurse": True
    },
    format="json",
    transformation_ctx="datasource"
)
```

- Job 설정에서 **Job bookmark = Enable** 만 하면 자동 적용

---

## 중요한 설정 옵션

### Job bookmark 상태

- **Enable**: 증분 처리
- **Disable**: 항상 전체 처리
- **Pause**: 상태 유지, 갱신 안 함

---

## 자주 발생하는 문제

### ❌ Bookmark 켰는데 재처리됨

주요 원인:

- S3 권한 부족 (`s3:GetObjectAcl`)
- 파일 overwrite (같은 경로/이름)
- 파티션 구조 미사용
- Glue 버전 이슈

---

## Job Bookmark vs 수동 증분 처리

|항목|Job Bookmark|수동 처리|
|---|---|---|
|구현 난이도|매우 낮음|높음|
|운영 부담|낮음|높음|
|유연성|중간|높음|
|Glue 표준|✅|❌|

---

## 시험 대비 핵심 포인트

- “증분 처리” → **Job Bookmark**
- “Glue 중복 처리 방지” → **Job Bookmark**
- “이미 처리한 파일 추적” → **Job Bookmark**
