---
title: gzip 개요 및 사용법
slug: "gzip-개요-및-사용법"
category: cloud
tags: ["big-data", "compression", "decompression", "deflate", "gzip", "http", "linux", "logs", "tar"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:08.097687+00:00"
---

**gzip**은 파일이나 데이터 스트림을 **압축(Compress)** 하기 위한 **압축 형식 및 소프트웨어 도구**입니다. 주로 **텍스트 기반 데이터**(예: 로그 파일, CSV, JSON 등)를 압축할 때 널리 사용되며, **빠른 처리 속도와 높은 압축률**로 시스템 전반에서 흔하게 사용됩니다.

---

## 🧩 gzip의 기본 개념

|항목|설명|
|---|---|
|**정식 명칭**|GNU zip|
|**개발자**|Jean-loup Gailly, Mark Adler (GNU 프로젝트)|
|**파일 확장자**|`.gz`|
|**압축 알고리즘**|DEFLATE (LZ77 + 허프만 인코딩)|
|**용도**|텍스트, 로그, 데이터 파일 등의 압축/해제|

---

## ⚙️ gzip의 특징

### ✅ 장점

- **높은 압축률**: 특히 텍스트 데이터에서 우수합니다.
- **빠른 압축 및 해제 속도**
- **리눅스/유닉스 기본 내장**: `gzip`, `gunzip`, `zcat` 등의 명령어를 제공합니다.
- **스트리밍 압축 지원**: 대용량 파일에도 적합합니다.

### ⚠️ 단점

- **단일 파일만 압축**: gzip 자체로는 **디렉터리 전체를 압축할 수 없습니다.**
- 디렉터리 압축은 보통 `tar`과 함께 사용합니다 (`tar.gz` 또는 `.tgz`).

---

## 📁 예시

### 리눅스 명령어 사용 예:

```bash
# 파일 압축
gzip example.txt   # 결과: example.txt.gz

# 압축 해제
gunzip example.txt.gz

# 압축된 내용 보기 (해제 없이)
zcat example.txt.gz
```

---

## 📦 gzip과 tar의 조합

- gzip은 디렉터리 단위 압축 기능이 없어, 보통 `tar` 명령어와 조합해 사용합니다.
- 이때 생성되는 확장자는 `.tar.gz` 또는 `.tgz`입니다.

```bash
# 디렉터리 전체 압축
tar -czvf archive.tar.gz my_folder/

# 압축 해제
tar -xzvf archive.tar.gz
```

---

## 📊 gzip vs 다른 압축 포맷

|포맷|압축률|속도|특징|
|---|---|---|---|
|**gzip**|높음|빠름|표준 텍스트 압축|
|**bzip2**|더 높음|느림|정밀 압축에 유리|
|**xz**|매우 높음|매우 느림|최고 압축률|
|**snappy/zstd**|낮음~보통|매우 빠름|스트리밍/빅데이터용|

---

## 💡 gzip 사용 사례

- 웹 서버: HTTP 응답 압축 (ex. `Content-Encoding: gzip`)
- 로그 저장: 시스템 로그, 서비스 로그 압축 보관
- 데이터 처리: CSV, JSON 등 텍스트 데이터 압축 저장
- 빅데이터 분석: Hadoop, Spark 등에서도 지원

---

## 🧾 요약

|항목|설명|
|---|---|
|**gzip이란**|DEFLATE 기반 파일 압축 도구 및 포맷|
|**확장자**|`.gz`|
|**압축 대상**|주로 텍스트 기반 데이터|
|**장점**|속도 빠르고 압축률 좋음|
|**제한**|단일 파일만 직접 압축 가능 (디렉터리는 tar와 조합 필요)|