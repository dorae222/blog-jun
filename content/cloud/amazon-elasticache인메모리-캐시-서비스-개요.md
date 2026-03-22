---
title: Amazon ElastiCache(인메모리 캐시 서비스) 개요
slug: "amazon-elasticache인메모리-캐시-서비스-개요"
category: cloud
tags: ["aws", "caching", "cloudwatch", "database-performance", "elasticache", "high-availability", "in-memory-cache", "memcached", "redis"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.104504+00:00"
---

> **NOTE:**
> - 인메모리 데이터 스토어
> - 1밀리 초 미만의 빠른 응답시간을 제공
> - 빠른 응답이 필요한 애플리케이션에 사용
> - 기존의 DB와 연결하여 DB응답성능을 개선하기 위해 사용 (사용하는 DB 데이터를 캐시)
> - ElastiCache를 사용하기 위해서는 애플리케이션의 코드변경이 필요
> - 세션 스토어, 게임 리더보드, 스트리밍 및 분석과 같이 내구성이 필요하지 않는 기본 데이터 스토어로 사용
> - 오픈소스 인메모리 데이터베이스 솔루션인 Redis또는 Memcached 두가지 유형을 지원 
> - Memcached는 멀티쓰레드 지원, Redis는 싱글쓰레드만 지원
> - 일반적으로 Redis가 더 많은 기능을 지원 (스냅샷 백업, 복제기능, 고가용성 제공 등)

### ✅ 개요
- Redis 및 Memcached 기반의 **인메모리 캐시 서비스**
- 밀리초 단위의 지연으로 **초고속 응답**을 제공

### ✅ 지원 엔진
- **Amazon Memory DB for Redis**
  - 단일 스레드
  - 퍼시스턴스, 복제, 클러스터링, pub/sub 기능
  - 자동 장애 조치 및 보안 기능 강화(암호화, IAM 인증 등)
- **Memcached**
  - 멀티스레드 기반
  - 단순한 캐싱 구조
  - 수평 확장에 적합

### ✅ 주요 기능
- **캐시 클러스터 구성**
- **자동 장애 조치 및 복구 (Redis)**
- **노드 모니터링 및 경보**
- **보안 기능**: TLS, IAM, VPC 내 배치
- **CloudWatch 연동 모니터링**

### ✅ 사용 사례
- 세션 저장소
- 데이터베이스 쿼리 결과 캐싱
- 실시간 순위 시스템
- Pub/Sub 메커니즘 기반 메시지 처리