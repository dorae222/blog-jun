---
title: Airflow DAG 개요
slug: "airflow-dag-개요"
category: cloud
tags: ["airflow", "dag", "data-pipelines", "etl", "ml-pipelines", "orchestration", "scheduling", "task-scheduling", "workflow"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:04.702149+00:00"
---

## 한 줄 정의

> **Airflow DAG는 작업(Task)들의 실행 순서와 의존성을 정의한 ‘순환 없는 방향 그래프’ 기반 워크플로이다.**

---

## DAG라는 이름의 의미

|단어|의미|
|---|---|
|**Directed**|실행 흐름에 방향이 있음|
|**Acyclic**|순환(무한 루프) 없음|
|**Graph**|노드(Task)와 엣지(의존성)로 구성|

👉 즉,
**“한 번 시작하면 정해진 방향으로만 진행하며, 다시 되돌아오지 않는 작업 흐름”**

---

## DAG의 구성 요소

### 1️⃣ DAG 객체

워크플로 전체를 감싸는 컨테이너

```python
from airflow import DAG
```

---

### 2️⃣ Task

실제 실행 단위

- BashOperator
    
- PythonOperator
    
- KubernetesPodOperator
    
- GlueJobOperator 등
    

```python
task_a = BashOperator(
    task_id="task_a",
    bash_command="echo hello"
)
```

---

### 3️⃣ Dependency (의존성)

Task 간 실행 순서 정의

```python
task_a >> task_b >> task_c
```

---

## DAG의 기본 예시

```python
with DAG(
    dag_id="example_dag",
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False
) as dag:

    extract = PythonOperator(...)
    transform = PythonOperator(...)
    load = PythonOperator(...)

    extract >> transform >> load
```

---

## DAG의 중요한 특징

### ✅ 순환 불가 (Acyclic)

아래는 ❌ 불가능:

```text
A → B → C → A
```

이유:

- 무한 실행 방지
    
- 실행 순서 명확화
    

---

### ✅ 선언적(Declarative)

- “어떻게” 실행 ❌
    
- “무엇을, 어떤 순서로” 실행 ⭕
    

Airflow는 **오케스트레이션 도구**, 처리 엔진이 아님

---

### ✅ 스케줄링 가능

- cron 표현식
    
- @daily, @hourly
    
- Event 기반 트리거
    

---

### ✅ 재시도·실패 관리

- retry
    
- retry_delay
    
- SLA miss 감지
    

---

## DAG Run vs Task Instance (중요)

|개념|의미|
|---|---|
|DAG|워크플로 정의|
|DAG Run|특정 시점의 실행|
|Task Instance|DAG Run 안의 개별 Task 실행|

---

## DAG가 적합한 상황

- ETL 파이프라인
    
- ML 학습 파이프라인
    
- 데이터 품질 검사
    
- 멀티 단계 배치 작업
    

---

## 핵심 포인트

- DAG = 워크플로 정의
    
- 순환 ❌
    
- Task 간 의존성
    
- Airflow는 실행 ❌, **오케스트레이션 ⭕**