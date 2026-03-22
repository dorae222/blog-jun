---
title: Amazon Redshift SUPER
slug: "amazon-redshift-super"
category: cloud
tags: ["amazon-redshift", "aws", "data-warehouse", "json", "partiql", "redshift", "schema-evolution", "semistructured-data", "super"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:04.278855+00:00"
---

**Amazon Redshift SUPER**는
**반정형(semi-structured) 데이터(JSON 등)를 네이티브로 저장·쿼리**하기 위해 Redshift에 도입된 **유연한 데이터 타입**입니다.

---

## 한 줄 정의

> **Amazon Redshift SUPER는 JSON 같은 반정형 데이터를 그대로 저장하고, SQL로 탐색·분석할 수 있게 해주는 데이터 타입이다.**

---

## 왜 SUPER가 필요한가?

기존 Redshift는 **정형 스키마**가 필수라서:

- JSON 구조가 자주 바뀌면 스키마 관리가 어려움
    
- 일부 필드만 필요한 경우도 처리 복잡
    
👉 **SUPER는 스키마를 미리 고정하지 않고** 데이터를 담아두고, 필요할 때 꺼내 씁니다.

---

## 핵심 특징

### 1️⃣ 반정형 데이터 네이티브 저장

- JSON, 배열, 중첩 객체를 그대로 저장
    
- 스키마를 사전 정의할 필요가 없음
    

```sql
CREATE TABLE events (
  event_id BIGINT,
  payload SUPER
);
```

---

### 2️⃣ PartiQL로 쿼리

Redshift는 **PartiQL(SQL 확장)**을 사용해 SUPER를 탐색합니다.

```sql
SELECT payload.user.id
FROM events
WHERE payload.event_type = 'purchase';
```

- 점 표기법(`.`)
    
- 배열 접근
    
- 중첩 필드 조건 검색 가능
    
---

### 3️⃣ 중첩 구조 지원

```json
{
  "user": { "id": 123, "region": "KR" },
  "items": [
    { "sku": "A1", "price": 10 },
    { "sku": "B2", "price": 20 }
  ]
}
```

```sql
SELECT item.sku, item.price
FROM events,
     events.payload.items AS item;
```

---

### 4️⃣ 스키마 진화에 강함

- JSON 필드 추가/삭제에 테이블 변경 불필요
    
- 이벤트 로그, IoT, API 응답 데이터에 적합
    
---

## SUPER vs VARCHAR(JSON 문자열)

|항목|SUPER|VARCHAR(JSON)|
|---|---|---|
|쿼리 편의성|매우 높음|낮음|
|중첩 접근|✅|❌|
|PartiQL|✅|❌|
|성능 최적화|우수|제한적|

---

## SUPER vs 정형 컬럼

- 자주 조회되는 필드 → **정형 컬럼**
    
- 구조가 자주 바뀌는 필드 → **SUPER**  
    👉 혼합 설계가 베스트 프랙티스
    
---

## 데이터 로드 예시 (COPY)

```sql
COPY events
FROM 's3://bucket/events/'
IAM_ROLE 'arn:aws:iam::123:role/redshift'
FORMAT AS JSON 'auto';
```

JSON이 자동으로 SUPER 컬럼에 매핑됩니다.

---

## 언제 SUPER를 써야 하나?

- 이벤트/로그/IoT 데이터
    
- API 응답 데이터
    
- 스키마가 자주 바뀌는 데이터
    
- 빠른 적재 + 유연한 분석 필요
    
---

## 시험 대비 핵심 포인트

- “Redshift에서 JSON 저장/쿼리” → **SUPER**
    
- “반정형 데이터” → **SUPER**
    
- “PartiQL” → **SUPER**
    
- “스키마 진화” → **SUPER**
    
---

## 한 문장 암기

> **Redshift SUPER는 반정형 데이터를 스키마 없이 저장하고 SQL로 탐색하는 데이터 타입이다.**