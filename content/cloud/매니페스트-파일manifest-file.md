---
title: 매니페스트 파일(Manifest File)
slug: "매니페스트-파일manifest-file"
category: cloud
tags: ["athena", "aws", "csv", "data-management", "datasync", "glue", "json", "manifest", "s3"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:08.238414+00:00"
---

**매니페스트 파일(Manifest File)**은 처리하거나 전송할 객체(파일)의 목록과 메타데이터를 담고 있는 파일입니다.

---

### 📌 **상세 설명**

- 매니페스트 파일은 일반적으로 **CSV, JSON** 등의 형식으로 작성되며, 어떤 객체들을 다룰 것인지에 대한 정보를 포함합니다.

- 예를 들어 Amazon S3에서 특정 파일들만 복사하거나 DataSync 같은 작업에서 일부 파일만 처리하고 싶을 때, 대상 객체들의 키(Key)나 경로를 하나의 목록 파일로 만들어 두는 것이 매니페스트 파일입니다.

---

### ✨ **포함되는 정보 예시**

|Key(파일 경로)|크기(Byte)|수정 시간|…|
|---|---|---|---|
|folder1/data1.csv|12345|2024-06-01T10:00:00Z|…|
|folder1/data2.csv|56789|2024-06-01T11:00:00Z|…|

또는 단순히 S3 객체 키 목록만 나열한 텍스트 파일일 수도 있습니다:

```
s3://mybucket/data/file1.csv
s3://mybucket/data/file2.csv
s3://mybucket/data/file3.csv
```

---

### ✅ **이 매니페스트 파일을 사용하는 이유**

- 어떤 파일을 작업 대상으로 할지 **명확히 지정**할 수 있습니다.

- 불필요한 전체 스캔을 피하고, **필요한 데이터만 선택적으로 전송/처리**할 수 있습니다.

- S3, DataSync, Glue, Athena 등 AWS 서비스에서도 **매니페스트 파일을 통한 대상 지정**을 지원합니다.

---

💡 **정리하자면:**
👉 **매니페스트 파일 = S3에 업로드하거나 처리할 객체 목록을 정의한 파일**입니다. 보통 CSV·JSON 형태로 작성하며, 대상 파일들의 키나 메타데이터를 포함합니다.