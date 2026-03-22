---
title: Apache Sqoop 개요 — RDBMS와 Hadoop 간 배치 데이터 전송 도구
slug: "apache-sqoop-개요--rdbms와-hadoop-간-배치-데이터-전송-도구"
category: cloud
tags: ["apache-sqoop", "batch-processing", "data-migration", "etl", "hadoop", "hbase", "hdfs", "hive", "mapreduce", "rdbms"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:06.163465+00:00"
---

> **NOTE:**
> 
> - **RDBMS ↔ Hadoop 간 대용량 데이터 전송 도구**
>     
> - 주 용도: **관계형 데이터베이스 → HDFS/Hive/HBase**
>     
> - **MapReduce 기반 병렬 처리**로 고속 전송
>     
> - **배치(Batch) 처리 전용** (실시간 X)
>     
> - CLI 기반 도구
>     
> - 현재는 **레거시(Deprecated) 성격**이 강함
>     

**Apache Sqoop**은
**관계형 데이터베이스(RDBMS)와 Hadoop 생태계 간의 대용량 데이터를 효율적으로 이동시키기 위한 배치 데이터 전송 도구**입니다.

---

## 🐘 Apache Sqoop이란?

> **Apache Sqoop**은
> **MySQL, Oracle, PostgreSQL, SQL Server** 같은
> **RDBMS의 테이블 데이터를 Hadoop(HDFS/Hive/HBase)으로 가져오거나(export)**
> 그 반대 방향으로 내보내기 위한 도구입니다.

- 이름 의미: **SQL + Hadoop**

- 핵심 목적: **ETL 중 “Extract & Load”**

---

## 🏗️ 동작 방식

```text
[RDBMS]
 (MySQL / Oracle)
        │
        ▼
[Apache Sqoop]
 (MapReduce Jobs)
        │
        ▼
[HDFS / Hive / HBase]
```

- Sqoop은 내부적으로 **MapReduce Job을 생성**합니다.
- 여러 Mapper가 **병렬로 데이터를 분할해 전송**합니다.
- 대용량 데이터 처리에 매우 효율적입니다.

---

## 🚀 주요 특징

|기능|설명|
|---|---|
|**대용량 전송**|TB급 데이터 처리|
|**병렬 처리**|MapReduce 기반|
|**양방향 이동**|Import / Export|
|**Schema 자동 매핑**|RDB → Hive/HDFS|
|**증분 적재**|Incremental Import 지원|
|**보안 연동**|Kerberos 지원|

---

## 📦 핵심 명령어

### 🔽 Import (RDBMS → Hadoop)

```bash
sqoop import \
--connect jdbc:mysql://db/mydb \
--username user \
--password pass \
--table orders \
--target-dir /data/orders
```

---

### 🔼 Export (Hadoop → RDBMS)

```bash
sqoop export \
--connect jdbc:mysql://db/mydb \
--table orders \
--export-dir /data/orders
```

---

## 🧠 Incremental Import (시험 단골)

|방식|설명|
|---|---|
|**append**|새 레코드만 추가|
|**lastmodified**|수정된 데이터 기준|

📌 시험 키워드

> _“RDBMS에서 변경된 데이터만 Hadoop으로”_ → **Sqoop Incremental Import**

---

## 🧩 Sqoop Import 대상

|대상|설명|
|---|---|
|**HDFS**|원본 저장|
|**Hive**|분석용 테이블|
|**HBase**|NoSQL 저장|

---

## 🆚 Sqoop vs 다른 도구

### vs Apache Flume

|항목|Sqoop|Flume|
|---|---|---|
|데이터 유형|구조화 데이터|로그/이벤트|
|처리 방식|배치|스트리밍|
|출처|RDBMS|App/Log|
|사용 사례|DB 덤프|로그 수집|

---

### vs AWS Glue

|항목|Sqoop|Glue|
|---|---|---|
|플랫폼|Hadoop 기반|서버리스|
|실시간|❌|❌|
|관리 부담|있음|거의 없음|
|현대적 대안|❌|✅|

---

## ⚠️ 한계 및 주의점

- ❌ **실시간 처리 불가**
- ❌ **MapReduce 의존**
- ❌ **운영 및 설정 복잡**
- ❌ **현재는 유지보수 모드**

📌 실무/시험 관점

> *“레거시 Hadoop 환경”*에서 주로 언급됩니다.

---

## 🧪 시험에서 나오는 전형적인 질문

### ❓ 문제

> RDBMS의 대규모 테이블을
> Hadoop(HDFS/Hive)으로 **배치 방식**으로 가져와야 한다.
> 가장 적합한 도구는?

✅ 정답

- **Apache Sqoop**

---

### ❌ 오답 유도

- Flume (로그 스트리밍용)
- Kafka (실시간 메시지)
- Kinesis (AWS 스트리밍)
- Glue (서버리스 ETL)

---

## ✅ 요약 (암기용)

|항목|핵심|
|---|---|
|이름|**Apache Sqoop**|
|목적|RDBMS ↔ Hadoop 데이터 이동|
|방식|배치, MapReduce|
|대상|구조화 데이터|
|강점|대용량 병렬 전송|
|한계|레거시, 실시간 불가|
