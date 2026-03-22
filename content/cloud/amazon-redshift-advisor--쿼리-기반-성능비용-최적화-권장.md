---
title: Amazon Redshift Advisor — 쿼리 기반 성능·비용 최적화 권장
slug: "amazon-redshift-advisor--쿼리-기반-성능비용-최적화-권장"
category: cloud
tags: ["amazon-redshift", "aws", "materialized-view", "performance-optimization", "query-optimization", "redshift", "vacuum-analyze", "wlm"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.569907+00:00"
---

> **NOTE:**
> 
> - **Amazon Redshift 성능·비용 최적화를 위한 자동 권장 서비스**
>     
> - 쿼리 패턴과 클러스터 사용 현황을 **지속적으로 분석**
>     
> - **테이블 설계(SORT / DIST), Materialized View, WLM, Vacuum/Analyze** 등에 대한 권장 제공
>     
> - **권장 사항은 자동 적용 ❌ (사용자 검토 후 적용)**
>     
> - Amazon Redshift 콘솔에서 확인 가능
>     

**Amazon Redshift Advisor**는  
**Redshift 클러스터의 쿼리 성능과 리소스 사용을 분석해 최적화 권장 사항을 제시하는 지능형 어드바이저**다.

---

## 🧠 Amazon Redshift Advisor란?

> **Amazon Redshift Advisor**는  
> **실제 워크로드(쿼리 이력, 테이블 사용 패턴)**를 기반으로  
> **성능 개선 및 비용 절감을 위한 구체적인 권장 사항을 자동으로 제안**하는 기능이다.

- “이론적인 베스트 프랙티스” ❌
    
- **“내 클러스터의 실제 사용 데이터 기반”** ✅
    

---

## 🏗️ 동작 개념

```text
[Redshift Cluster]
 (Query Logs / Metrics)
        │
        ▼
[Redshift Advisor]
 (Workload Analysis)
        │
        ▼
[Recommendations]
 (SORT / DIST / MV / WLM 등)
```

- 과거 쿼리 기록과 시스템 메트릭을 분석
    
- 반복 실행되는 패턴을 중심으로 권장을 생성
    

---

## 🚀 주요 권장 항목 (시험 단골)

### 1️⃣ 테이블 설계 최적화

|항목|설명|
|---|---|
|**DIST KEY 추천**|조인 성능 개선|
|**SORT KEY 추천**|범위 조회, 정렬 성능 개선|
|**테이블 재정렬**|쿼리 스캔 효율 향상|

📌 시험 키워드

> _“조인이 느리다” → DIST KEY_  
> _“범위 쿼리가 느리다” → SORT KEY_

---

### 2️⃣ Materialized View 추천 ⭐

|항목|설명|
|---|---|
|대상|반복 실행되는 집계 쿼리|
|효과|쿼리 시간 대폭 감소|
|방식|사전 계산 결과 재사용|

📌 시험 포인트

> _“동일한 집계 쿼리가 반복 실행된다”_ → **Materialized View**

---

### 3️⃣ Vacuum / Analyze 권장

|항목|설명|
|---|---|
|**VACUUM**|삭제/업데이트 후 정렬 복구|
|**ANALYZE**|쿼리 옵티마이저 통계 갱신|

📌 시험 표현

> _“쿼리 플랜이 비효율적이다”_ → ANALYZE

---

### 4️⃣ WLM (Workload Management) 권장

|항목|설명|
|---|---|
|큐 분리|ETL vs BI|
|동시성 조정|쿼리 대기 시간 감소|
|메모리 할당|쿼리 실패 방지|

---

### 5️⃣ 비용 및 리소스 최적화

|항목|설명|
|---|---|
|노드 타입|과/저 스펙 감지|
|스토리지|사용률 분석|
|Spectrum|외부 테이블 활용 제안|

---

## 🆚 Redshift Advisor vs 다른 도구

|항목|Redshift Advisor|Performance Insights|
|---|---|---|
|목적|**개선 권장**|**문제 원인 분석**|
|자동 제안|O|X|
|설계 변경|제안|분석만|

---

## ⚠️ 중요한 제한 사항 (시험 포인트)

- ❌ **자동 적용 아님**
    
- ❌ 실시간 반영 ❌ (분석 주기 기반)
    
- ❌ SQL 튜닝 자체를 대신해주지 않음
    
- ✅ **사용자 판단 필수**
    

📌 시험 표현

> _“Advisor가 자동으로 테이블을 변경한다”_ ❌

---

## 🧪 시험에 자주 나오는 질문 유형

### ❓ 문제 1

> Redshift에서 반복되는 집계 쿼리의 성능을  
> 가장 쉽게 개선하는 방법은?

✅ 정답

- **Redshift Advisor의 Materialized View 권장 활용**
    

---

### ❓ 문제 2

> 조인 성능이 저하되고 있다.  
> 별도의 분석 없이 빠르게 개선 방향을 알고 싶다.

✅ 정답

- **Amazon Redshift Advisor**
    

---

### ❌ 오답 유도

- 수동 쿼리 튜닝만 수행
    
- 클러스터 재생성
    
- 무작위 DIST KEY 변경
    

---

## ✅ 요약 (암기용)

|항목|핵심|
|---|---|
|이름|**Amazon Redshift Advisor**|
|목적|성능·비용 최적화 권장|
|기반|실제 워크로드 분석|
|주요 대상|SORT / DIST / MV / WLM|
|자동 적용|❌|
|위치|Redshift 콘솔|

---

### 📌 한 줄 요약 (시험용)

> **Redshift Advisor = 실제 쿼리 기반 최적화 ‘권장’ 서비스**