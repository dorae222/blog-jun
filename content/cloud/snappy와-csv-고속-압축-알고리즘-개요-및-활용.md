---
title: "Snappy와 CSV: 고속 압축 알고리즘 개요 및 활용"
slug: "snappy와-csv-고속-압축-알고리즘-개요-및-활용"
category: cloud
tags: ["avro", "aws-athena", "big-data", "compression", "csv", "hadoop", "parquet", "pyarrow", "snappy", "spark"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:07.892471+00:00"
---

**Snappy**는 Google에서 개발한 **고속 데이터 압축 알고리즘**입니다. 주로 대용량 데이터를 다루는 빅데이터 및 분석 시스템에서 사용되며, **압축 속도와 해제 속도**가 매우 빠른 것이 특징입니다. 특히 CSV, Parquet, Avro 등의 포맷과 함께 사용되어 **저장 효율성**과 **입출력 성능 개선**을 동시에 제공합니다.

---

## 📦 Snappy란?

|항목|설명|
|---|---|
|**개발 주체**|Google|
|**목적**|**고속 압축과 해제** (압축률보다 속도 우선)|
|**라이선스**|BSD 오픈소스|
|**언어 지원**|C++, Java, Python 등 다양한 언어 바인딩|
|**특징**|매우 빠른 압축/해제 속도, 낮은 CPU 사용|

---

## 🚀 특징

### 1. **빠른 압축 속도**

- 압축 속도가 초당 수백 MB 이상 가능.

- 느린 디스크나 네트워크보다 빠른 경우가 많아 I/O 성능을 개선.


### 2. **빠른 해제 속도**

- 데이터 압축 해제 시간이 짧아 분석/처리에 유리.

- 실시간 분석 및 스트리밍 워크로드에 적합.


### 3. **낮은 압축률**

- Gzip이나 Bzip2보다 압축률은 낮지만 속도는 훨씬 빠름.

- **속도 vs. 압축률 트레이드오프**를 감안한 설계.

---

## 🧾 Snappy로 압축된 CSV란?

CSV 파일을 일반 텍스트로 저장할 경우 용량이 크기 때문에, **Snappy 알고리즘을 적용해 압축**하여 저장하면 디스크 공간을 절약할 수 있고, **압축 해제 속도가 빠르기 때문에 읽는 성능에도 유리**합니다.

- 보통 **Hadoop, Spark, Hive, Presto, AWS Athena** 같은 빅데이터 도구에서 사용됩니다.

- 직접 `.csv.snappy` 형태로 저장되기보다는, 보통은 **Parquet, Avro 등의 파일 포맷 내부에서 Snappy로 압축된 컬럼이나 블록**으로 사용되는 경우가 많습니다.

> 💡 CSV 자체는 구조화된 압축 포맷을 정의하지 않기 때문에, 일반적으로 **Snappy 압축 스트림으로 감싼 CSV 파일** 또는 **파일 전체를 Snappy로 압축한 바이너리 형태**가 사용됩니다.

---

## 🛠️ 다루는 방법

### Python에서 처리 예시

```python
import snappy

with open("file.csv.snappy", "rb") as f:
    compressed_data = f.read()
    decompressed_data = snappy.uncompress(compressed_data)

# 문자열로 디코딩
csv_text = decompressed_data.decode("utf-8")
```

또는 PyArrow를 사용해 Parquet 파일을 Snappy로 압축하거나 읽을 수 있습니다:

```python
import pyarrow.parquet as pq

table = pq.read_table('file.parquet')
df = table.to_pandas()
```

---

## ✅ 요약

|항목|내용|
|---|---|
|**Snappy**|Google이 만든 고속 압축 알고리즘|
|**장점**|매우 빠른 압축 및 해제 속도|
|**단점**|압축률은 Gzip보다 낮음|
|**CSV와의 관계**|대용량 CSV 데이터를 빠르게 압축/해제하기 위해 사용됨|
|**주 사용처**|빅데이터 처리 환경 (Spark, Hadoop, Athena 등)|