---
title: AWS Database 서비스 정리
slug: "aws-database-서비스-정리"
category: cloud
tags: ["aurora", "aws", "database-migration", "documentdb", "dynamodb", "elasticache", "rds", "redshift"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:06.526549+00:00"
---

![](/media/posts/imported/aws/Pasted%20image%2020250611142221.png)

![](/media/posts/imported/aws/Pasted%20image%2020250611130709.png)

- Amazon Aurora
- Amazon DynamoDB
- Amazon ElastiCache
- Amazon Keyspaces
- Amazon Memory DB for Redis
- Amazon Neptune
- Amazon Relational Database Service
- Amazon RDS for Db2
- Amazon RDS on VMware
- Amazon Quantum Ledger Database (Amazon QLDB)
- Amazon Timestream
-  Amazon DocumentDB
- Amazon Lightsail

# AWS Database 정리

## 1. Amazon RDS (Relational Database Service)

### 개요
- 관리형 관계형 데이터베이스 서비스
- MySQL, PostgreSQL, MariaDB, Oracle, SQL Server, Aurora 지원
- 자동 백업, 모니터링, 패치 적용, 멀티 AZ 지원

### 주요 기능
- **Multi-AZ 배포**: 고가용성 확보를 위한 장애 조치 기능
- **Read Replica**: 읽기 부하 분산 및 복제 기반 확장성 제공
- **자동 스냅샷 및 수동 백업**
- **VPC 내부에서의 격리 가능**
- **성능 향상을 위한 옵션 그룹/파라미터 그룹 사용**

### 비용
- EC2 인스턴스처럼 인스턴스 크기 및 저장 용량 기준 과금
- IOPS에 따른 추가 요금 가능

---

## 2. Aurora

### 개요
- AWS가 자체 개발한 고성능 RDS 호환 엔진
- MySQL 및 PostgreSQL 호환
- RDS보다 최대 5배(MySQL), 3배(PostgreSQL) 빠름

### 특징
- 6개 복제본을 3개 AZ에 자동 배치 (고가용성 보장)
- 자동 장애 감지 및 장애 조치 (failover)
- Auto Scaling 지원
- Global Database로 다중 리전에 복제 가능

---

## 3. DynamoDB

### 개요
- 완전관리형 NoSQL 키-값 및 문서형 데이터베이스
- 밀리초 단위의 응답 속도
- 무제한 확장성

### 특징
- **서버리스**로 인프라 관리 불필요
- **DAX (DynamoDB Accelerator)**: 인메모리 캐시로 지연시간 단축
- **Global Tables**: 다중 리전 복제 가능
- **자동 스케일링** 및 **온디맨드 모드 지원**

### 사용 사례
- IoT, 실시간 분석, 게임 세션 데이터, 사용자 세션 정보

---

## 4. ElastiCache

### 개요
- 인메모리 데이터 저장소
- Redis, Memcached 지원
- 데이터 캐싱 및 빠른 조회 용도

### 특징
- 마이크로초 단위의 응답
- 멀티 AZ 지원 (Redis 기준)
- 클러스터 모드 사용 가능
- 자동 장애 감지 및 복구

### 사용 사례
- 캐시 레이어, 리더보드, 세션 관리, Pub/Sub 메시징

---

## 5. Redshift

### 개요
- 완전관리형 데이터 웨어하우스 서비스
- PostgreSQL 기반, 대규모 분석 쿼리 최적화

### 특징
- 대량 데이터에 대해 병렬 쿼리 처리 (MPP)
- Spectrum 기능으로 S3 데이터까지 직접 쿼리 가능
- 자동 백업, 보안 그룹 통합, VPC 격리 가능
- 데이터 압축, 컬럼 저장 방식

### 사용 사례
- BI 분석, 보고서 생성, 데이터 레이크 통합

---

## 6. Database Migration Service (AWS DMS)

### 개요
- 온프레미스 또는 클라우드 간 데이터베이스 마이그레이션 서비스
- 동종 또는 이종 DB 간 마이그레이션 지원

### 특징
- **데이터 복제 중에도 DB 운영 가능**
- **복제 유형**: 전체 복제, 변경 데이터 캡처(CDC)
- **소스와 타겟 지원**: RDS, DynamoDB, S3 등 포함

---

## 7. 기타 DB 관련 서비스

| 서비스 | 설명 |
|--------|------|
| **DocumentDB** | MongoDB 호환 문서형 DB |
| **Neptune** | 그래프 데이터베이스 (SPARQL, Gremlin 지원) |
| **Timestream** | 시계열 데이터 저장 최적화 DB (IoT, 모니터링용) |
| **Qldb (Quantum Ledger DB)** | 변경 불가능한 트랜잭션 로그 저장 DB |
| **Keyspaces** | Apache Cassandra 호환 완전관리형 DB |


| 항목    | RDS            | Aurora                          | ElastiCache                |
| ----- | -------------- | ------------------------------- | -------------------------- |
| 유형    | 관계형 DB         | 고성능 RDB (MySQL, PG 호환)          | 인메모리 캐시 (Redis, Memcached) |
| 확장성   | 수동 조정 또는 읽기 복제 | 자동 확장 (스토리지, Aurora Serverless) | 수평 확장 (노드 기반)              |
| 고가용성  | Multi-AZ       | 6-way replication in 3 AZ       | Redis: Multi-AZ 지원         |
| 성능    | 엔진에 따라 다름      | RDS보다 3~5배 빠름                   | 밀리초 응답 시간                  |
| 사용 사례 | 전통적 웹/앱 백엔드    | 대규모 트랜잭션/글로벌 서비스                | 세션/쿼리/랭킹 캐싱                |