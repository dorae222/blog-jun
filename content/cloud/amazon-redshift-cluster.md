---
title: Amazon Redshift Cluster
slug: "amazon-redshift-cluster"
category: cloud
tags: ["amazon-redshift", "aws", "cloud", "data-warehouse", "dc2", "olap", "performance-tuning", "ra3", "security"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.582021+00:00"
---

**Amazon Redshift Cluster**는 대규모 분석(OLAP) 워크로드를 처리하기 위해 설계된 **완전관리형 데이터 웨어하우스 인프라 집합**입니다.

---

## 한 줄 정의

> **Amazon Redshift Cluster는 하나 이상의 노드가 결합된 분산 데이터 웨어하우스로, 페타바이트 규모 데이터를 빠르게 분석하기 위한 컴퓨팅 환경입니다.**

---

## Redshift Cluster의 구성

### 1️⃣ 리더 노드 (Leader Node)

- 클라이언트(SQL) 요청 수신
- 쿼리 파싱 및 최적화
- 작업을 컴퓨팅 노드에 분배
- 결과 집계 후 반환

---

### 2️⃣ 컴퓨팅 노드 (Compute Nodes)

- 실제 데이터 저장 및 처리
- 병렬 쿼리 실행
- 노드 간 고속 통신

---

### 3️⃣ 노드 타입

- **RA3** (권장)
  - 컴퓨팅과 스토리지 분리
  - Amazon Redshift Managed Storage 사용
- **DC2** (레거시)
  - 컴퓨팅과 스토리지 결합

---

## 클러스터 크기

- 최소 1 노드부터 수십 노드까지 확장 가능
- 노드 수 증설로 성능 확장
- RA3는 스토리지 자동 확장

---

## 데이터 저장 방식

- 컬럼 기반 저장(Columnar Storage)
- 압축(Encoding)
- 분산 저장(Distribution Style)

---

## 성능 최적화 요소

|요소|설명|
|---|---|
|Distribution Key|노드 간 데이터 분산|
|Sort Key|디스크 스캔 최소화|
|Materialized View|사전 계산 결과|
|Result Cache|동일 쿼리 캐시|

---

## 보안

- IAM 인증
- VPC 내부 배치
- KMS 암호화(저장/전송 중)
- RBAC, RLS, CLS, 데이터 마스킹

---

## 클러스터 vs Serverless

|항목|Cluster|Redshift Serverless|
|---|---|---|
|인프라 관리|필요|불필요|
|비용|상시 노드 비용|사용량 기반|
|예측 가능성|높음|가변|
|튜닝|가능|제한적|

---

## 언제 Cluster를 쓰나?

- 지속적인 분석 쿼리
- 고정된 성능 요구
- 세밀한 성능 튜닝 필요
- 기존 Redshift 운영 중

---

## 요약

- Redshift Cluster = **분산 OLAP 엔진**
- Leader + Compute 노드 구조
- 대규모 데이터 분석에 최적화
- RA3 노드가 표준