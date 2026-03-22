---
title: DynamoDB Accelerator (DAX)
slug: "dynamodb-accelerator-dax"
category: cloud
tags: ["aws", "caching", "dax", "distributed-systems", "dynamodb", "in-memory-cache", "latency", "performance"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:06.588461+00:00"
---

---
Category: Cloud
Subcategory: 11.AWS
Quality grade: A


---
---
aliases:
  - DAX
---
- **DynamoDB Accelerator**, 줄여서 **DAX(DynamoDB Accelerator)** 는 **Amazon DynamoDB의 읽기 성능을 대폭 향상시키기 위한 인메모리 캐시 서비스**입니다.
- DynamoDB의 캐싱 솔루션

---

## ⚡ DynamoDB Accelerator(DAX)란?

> **Amazon DAX**는 DynamoDB에 통합되는 **완전관리형 인메모리 캐시 서비스**로,  
> **읽기 요청(latency)** 을 **마이크로초(μs) 수준**으로 줄여주는 고성능 캐시 계층입니다.

---

## 🚀 왜 DAX를 사용할까?

|일반 DynamoDB|DAX 사용 시|
|---|---|
|평균 **몇 밀리초(ms)** 수준의 읽기 지연|**마이크로초 수준**의 빠른 응답|
|높은 TPS 처리에 부담|인메모리 캐시로 부담 감소|
|데이터 읽을 때마다 DB 접근|자주 읽는 데이터는 캐시에 유지|

---

## 🧱 핵심 특징

|항목|설명|
|---|---|
|**완전관리형**|노드 설치, 유지보수 없이 AWS가 운영|
|**인메모리 캐시**|Redis처럼 RAM 기반으로 동작 (읽기 성능 향상)|
|**API 호환성**|기존 DynamoDB API와 동일하게 동작 → 코드 변경 최소화|
|**클러스터 기반**|최소 1~10개 노드로 구성 가능|
|**읽기 전용 캐시**|DAX는 **쓰기 요청을 DynamoDB로 전달**, 읽기 결과만 캐시에 유지|

---

## 🛠️ 어떻게 동작하나요?

1. 애플리케이션이 DAX 클러스터 엔드포인트를 통해 요청을 보냄
    
2. DAX에서 해당 키에 대한 캐시가 있는지 확인
    
    - ✅ 캐시에 있으면 → **바로 반환 (초고속)**
        
    - ❌ 없으면 → DynamoDB에 요청 후 응답을 캐시에 저장
        
3. 쓰기/업데이트는 항상 **DynamoDB에 직접 반영**되고, DAX 캐시는 무효화됨
    

---

## 🧪 사용 사례

|사용 시나리오|설명|
|---|---|
|**읽기 비율이 높은 게임 상태 저장**|로그인 시 유저 상태, 랭킹 등을 빠르게 반환|
|**추천 콘텐츠 캐싱**|사용자별 개인화 콘텐츠 캐시|
|**자주 조회되는 설정 데이터**|나라 코드, 환율 정보, 상품 정보 등|

---

## 🔒 주의할 점

- **쓰기 지연은 줄이지 않음** → 오직 **읽기 성능 최적화 용도**
    
- **결과 일관성(Eventually Consistent)** 기반
    
- **데이터 정합성이 중요한 경우**에는 TTL 설정 또는 캐시 무효화 전략 필요
    

---

## ✅ 요약

|항목|내용|
|---|---|
|정식 이름|**Amazon DynamoDB Accelerator (DAX)**|
|역할|**DynamoDB 읽기 요청을 빠르게 처리하는 인메모리 캐시**|
|지연 시간|**μs(마이크로초) 수준**|
|코드 변경|거의 없음 (API 호환)|
|주요 특징|완전관리형, 읽기 성능 향상, 멀티 노드 클러스터 구성|
