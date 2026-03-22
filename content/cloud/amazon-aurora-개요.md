---
title: Amazon Aurora 개요
slug: "amazon-aurora-개요"
category: cloud
tags: ["amazon-aurora", "aurora-serverless", "aws", "global-database", "mysql", "postgresql", "rds", "replication", "scalability"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:04.821185+00:00"
---

### ✅ 개요
- RDS와 호환되는 고성능 DB 서비스 (MySQL, PostgreSQL 호환)
- **AWS가 직접 설계한 엔진**

### ✅ 구조 및 특징
- **스토리지 레벨 복제**: 6개의 복제본을 3개 AZ에 자동 배치
- **자동 장애 감지 및 복구**
- **스토리지 자동 확장**: 최대 128TB
- **백트랙 기능**: 수 초 단위로 이전 시점으로 복원 가능한 Backtrack
- **서버리스 옵션**: Aurora Serverless V2로 무중단으로 확장/축소 가능

### ✅ Aurora Global Database
- **다중 리전 복제본 생성 가능**
- 글로벌 애플리케이션에 적합

### ✅ 성능
- MySQL 대비 **최대 5배**, PostgreSQL 대비 **최대 3배** 성능
- **기본 리더 엔드포인트 및 커스텀 리더 엔드포인트** 제공

### ✅ 사용 사례
- 대규모 고성능 트랜잭션 서비스
- 글로벌 서비스를 위한 멀티리전 구성
- 이벤트 기반 확장(서버리스) 환경