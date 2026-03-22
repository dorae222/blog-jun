---
title: "Apache Flink의 내장 `RANDOM_CUT_FOREST (RCF)` 함수"
slug: "apache-flink의-내장-random_cut_forest-rcf-함수"
category: cloud
tags: ["anomaly-detection", "apache-flink", "aws", "iot", "random-cut-forest", "sql", "streaming", "table-api"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:07.317407+00:00"
---

**Apache Flink의 내장 `RANDOM_CUT_FOREST (RCF)` 함수**는 **스트리밍 데이터에서 이상치(Anomaly)를 감지**하는 기능입니다. 이 함수는 **Amazon에서 개발한 Random Cut Forest 알고리즘**을 기반으로 하며, **Flink의 Table API 및 SQL에서 사용할 수 있는 함수**로 제공됩니다.

즉, **실시간으로 들어오는 데이터 흐름에서 자동으로 이상 징후를 탐지할 수 있도록 설계된 내장 함수**입니다.

---

## 🧩 RANDOM_CUT_FOREST란?

|항목|설명|
|---|---|
|**알고리즘 종류**|이상치 탐지 (Anomaly Detection)|
|**기술 원리**|고차원 공간에서 랜덤으로 데이터를 분할(cut)하여 이상치를 판단|
|**기반 라이브러리**|Amazon RCF 알고리즘 (AWS에서 오픈소스로 제공)|
|**Flink 내 위치**|Table API 및 SQL 함수로 포함 (`RANDOM_CUT_FOREST(...)`)|

---

## 🧠 어떤 문제를 해결하나?

- 로그 스트림에서 **비정상 이벤트 감지**

- IoT 센서 데이터에서 **이상값 탐지**

- 금융 거래의 **사기 탐지**

- 웹 트래픽의 **비정상 트렌드 분석**

---

## 🧪 사용 예시 (Flink SQL)

```sql
SELECT
  sensor_id,
  event_time,
  reading,
  RANDOM_CUT_FOREST(reading, 100, 256, 0.1) AS anomaly_score
FROM
  sensor_readings;
```

### 설명:

- `reading`: 감지 대상 값 (ex. 온도, 전류, 속도 등)

- `100`: 샘플 개수 (슬라이딩 윈도우 길이)

- `256`: 트리 개수 (모델 복잡도)

- `0.1`: 임계값 (이상치로 판단할 민감도)

> 💡 `anomaly_score`가 1.0에 가까울수록 이상치 가능성이 높습니다.

---

## ⚙️ 주요 파라미터 설명

|파라미터|설명|
|---|---|
|**target column**|이상치 분석 대상 열 (숫자형)|
|**sample_size**|슬라이딩 윈도우 크기, 일반적으로 100~500|
|**num_trees**|RCF 트리 개수, 일반적으로 50~500|
|**anomaly_threshold**|이상치 민감도 (0.0~1.0)|

---

## ✅ 장점

- **스트리밍에 적합**: 실시간 이상치 탐지 가능

- **비지도 학습 기반**: 라벨링된 데이터 없이 동작

- **경량 모델**: 빠른 처리 가능 (CPU 비용 낮음)

- **SQL에서 바로 사용 가능**: 비개발자도 사용 가능

---

## ⚠️ 제한 사항

- 입력은 **숫자형 벡터 또는 단일 수치 컬럼**이어야 함

- 다차원 이상 탐지를 위해서는 **벡터 입력 구성** 필요

- 윈도우 크기나 민감도를 잘못 설정하면 **과도한 오탐 또는 누락** 발생 가능

---

## 📌 사용 사례 요약

|사용 분야|설명|
|---|---|
|**IoT 센서 감시**|기계 상태 감지, 예지 정비|
|**보안 로그 분석**|이상 로그인/접속 패턴 탐지|
|**사용자 행동 분석**|클릭/결제 패턴 이상 감지|
|**금융 트랜잭션 모니터링**|비정상 결제/송금 이벤트 탐지|

---

## 🧾 요약

|항목|내용|
|---|---|
|**함수명**|`RANDOM_CUT_FOREST(...)`|
|**제공 위치**|Apache Flink Table API/SQL|
|**기능**|실시간 이상치 탐지|
|**장점**|비지도 학습, 실시간 처리, SQL 호환|
|**기반 알고리즘**|Amazon Random Cut Forest (RCF)|