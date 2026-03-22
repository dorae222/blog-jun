---
title: Apache Oozie
slug: "apache-oozie"
category: cloud
tags: ["apache-oozie", "batch-processing", "etl", "hadoop", "hive", "mapreduce", "oozie-coordinator", "workflow-scheduler"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:06.131563+00:00"
---

> **NOTE:**
> 
> - **Hadoop 생태계용 워크플로 스케줄러**
>     
> - **배치 기반 작업(MapReduce, Hive, Pig, Sqoop 등)**을 순서대로 실행
>     
> - **시간 기반(Time)·데이터 기반(Data) 트리거** 지원
>     
> - XML 기반 워크플로 정의
>     
> - 현재는 **레거시(Deprecated 성격)** 도구로 분류됨
>     

**Apache Oozie**는
**Hadoop 클러스터에서 실행되는 여러 배치 작업을 의존성에 따라 자동으로 실행·관리하는 워크플로 관리 도구**다.

---

## 🧠 Apache Oozie란?

> **Apache Oozie**는
> Hadoop 생태계(MapReduce, Hive, Pig, Sqoop 등)에서
> **여러 작업(Job)을 하나의 흐름(Workflow)으로 묶어 실행**하기 위한
> **전용 스케줄링 및 오케스트레이션 엔진**이다.

- “Hadoop판 Airflow”
- 복잡한 배치 파이프라인을 자동화하는 목적

---

## 🏗️ 동작 구조

```text
[Time / Data Trigger]
        │
        ▼
[Oozie Coordinator]
        │
        ▼
[Oozie Workflow]
 ├─ MapReduce
 ├─ Hive
 ├─ Sqoop
 └─ Pig
        │
        ▼
[HDFS / S3]
```

---

## 🚀 주요 구성 요소 (시험 단골)

### 1️⃣ Workflow

- 작업 흐름을 정의
- 지원 노드: **Action / Decision / Fork / Join / Kill / End**

```xml
<workflow-app name="etl">
  <action name="hive-job">
    <hive xmlns="uri:oozie:hive-action:0.5">
      ...
    </hive>
  </action>
</workflow-app>
```

---

### 2️⃣ Coordinator ⭐

|기능|설명|
|---|---|
|시간 트리거|매일/매시간 실행|
|데이터 트리거|특정 파일 도착 시 실행|

📌 시험 키워드

> _“데이터 도착 시 자동 실행”_

---

### 3️⃣ Bundle

- 여러 Coordinator를 하나로 묶음
- 대규모 파이프라인 관리에 사용

---

## 🧩 지원 작업 유형

|작업|예시|
|---|---|
|MapReduce|대용량 배치|
|Hive|SQL 배치|
|Pig|스크립트|
|Sqoop|RDBMS ↔ Hadoop|
|Shell|커스텀 스크립트|

---

## 🆚 Apache Oozie vs 현대 도구

### vs Apache Airflow

|항목|Oozie|Airflow|
|---|---|---|
|환경|Hadoop 전용|범용|
|정의 방식|XML|Python|
|사용성|낮음|높음|
|현재 위치|레거시|표준|

---

### vs AWS Step Functions

|항목|Oozie|Step Functions|
|---|---|---|
|관리|클러스터 필요|서버리스|
|통합|Hadoop|AWS 서비스|
|현대성|낮음|높음|

---

## ⚠️ 한계 및 주의점 (시험 포인트)

- XML 기반 → 가독성 낮음
- Hadoop에 강결합
- 실시간 처리 지원 불가
- 현대적 클라우드 환경에는 부적합

📌 시험 표현

> _“레거시 Hadoop 배치 스케줄러”_

---

## 🧪 시험에 자주 나오는 질문

### ❓ 문제

> Hadoop 환경에서
> Hive → Sqoop → MapReduce 작업을
> **순서·시간·데이터 의존성**에 따라 자동 실행하려 한다.

✅ 정답

- **Apache Oozie**

---

## ❌ 오답 유도

- Kafka (스트리밍)
- Spark Streaming (실시간)
- Kinesis (AWS 스트리밍)

---

## ✅ 요약 (암기용)

|항목|핵심|
|---|---|
|이름|**Apache Oozie**|
|목적|Hadoop 배치 워크플로 관리|
|방식|XML 기반|
|트리거|시간 / 데이터|
|현재|레거시|

---

### 📌 한 줄 요약 (시험용)

> **Oozie = Hadoop 배치 작업을 순서대로 실행하는 워크플로 스케줄러**
