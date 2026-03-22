---
title: "STV(System Table Views)란?"
slug: "stvsystem-table-views란"
category: cloud
tags: ["amazon-redshift", "aws", "cloud", "database", "monitoring", "redshift", "sql", "stl", "stv", "system-views"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:07.943221+00:00"
---

## STV란?

**STV(System Table Views)**는
Amazon Redshift 클러스터의 **현재(실시간) 상태를 보여주는 시스템 뷰(View)**입니다.

> ✔️ 실시간 상태 확인  
> ✔️ 현재 실행 중인 쿼리·리소스 상태  
> ✔️ 읽기 전용  
> ✔️ 휘발성 정보 (시간이 지나면 사라짐)

---

## 한 줄 정의

> **STV는 Redshift 클러스터의 ‘지금 이 순간’ 상태를 보여주는 실시간 시스템 뷰다.**

---

## STL vs STV 핵심 차이

|구분|STL|STV|
|---|---|---|
|의미|System Table Logs|System Table Views|
|성격|과거 로그|실시간 상태|
|저장|일정 기간 유지|휘발성|
|목적|분석·감사|모니터링|
|예|실행 기록, 경고|현재 쿼리, 노드 상태|

---

## STV에서 주로 보는 정보

### 1️⃣ 현재 실행 중인 쿼리

```sql
SELECT * FROM stv_recents;
```

- 현재 또는 최근 실행된 쿼리 목록
- 각 쿼리의 실행 시간
- 쿼리를 실행한 사용자 정보

---

### 2️⃣ 리소스 사용 상태

- CPU
- 메모리
- 디스크
- 슬롯

예:

```sql
SELECT * FROM stv_blocklist;
```

---

### 3️⃣ 락(Lock) 상태

```sql
SELECT * FROM stv_locks;
```

---

## STV의 특징 정리

- 실시간 문제 진단에 적합
- 현재 발생 중인 병목 파악 가능
- 장기 이력 분석에는 부적합 (휘발성)
- 클러스터 운영 모니터링에 유용

---

## 언제 STV를 쓰나?

- 쿼리가 즉시 멈추거나 응답하지 않을 때
- 리소스 병목(예: 메모리·디스크·CPU) 확인이 필요할 때
- 락으로 인한 대기 상태를 조사할 때
- 운영 중 장애 대응 시 실시간 상태 조회가 필요할 때

---

## 핵심 포인트

- **STV = 실시간 상태**  
- "현재 실행 중인 쿼리" 확인 → STV 사용  
- "과거 로그" 확인 → STL 사용