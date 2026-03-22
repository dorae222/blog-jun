---
title: AWS DMS (Database Migration Service)
slug: "aws-dms-database-migration-service"
category: cloud
tags: ["aurora", "aws", "aws-dms", "cdc", "cloud-migration", "database-migration", "high-availability", "rds", "schema-conversion"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:03.707926+00:00"
---

**AWS DMS**는 **AWS Database Migration Service**의 약자로, **데이터베이스를 AWS로 마이그레이션하거나 AWS 내에서 다른 데이터베이스로 이전할 수 있게 해주는 완전관리형 서비스**입니다.

---

## 🌐 AWS DMS (Database Migration Service)란?

> **AWS DMS**는 온프레미스, 다른 클라우드, 또는 AWS 내에서 실행 중인 데이터베이스 간에 **데이터를 실시간으로 복제하거나 이전(migration)** 할 수 있도록 도와주는 **관리형 데이터베이스 마이그레이션 서비스**입니다.

---

## 🎯 주요 기능

|기능|설명|
|---|---|
|**데이터베이스 마이그레이션**|온프레미스 → AWS, AWS → AWS, AWS → 온프레미스 가능|
|**동종 및 이기종 간 마이그레이션**|예: MySQL → MySQL (동종), Oracle → Aurora (이기종)|
|**실시간 복제 지원**|변경 데이터 캡처(CDC)를 통해 지속적 동기화 가능|
|**자동 장애 복구**|오류 발생 시 재시도 및 자동 복구 처리|
|**고가용성 구성 지원**|멀티 AZ 배포로 안정성 향상 가능|
|**보안 지원**|SSL 암호화, VPC 내 실행, IAM 연동 가능|

---

## 🏗️ 동작 방식 (핵심 구성요소)

|구성요소|역할|
|---|---|
|**소스 데이터베이스**|마이그레이션 대상의 기존 DB (온프레미스, RDS, EC2 등)|
|**타겟 데이터베이스**|마이그레이션 후 저장할 DB (RDS, Aurora, Redshift 등)|
|**복제 인스턴스 (Replication Instance)**|데이터 이동을 담당하는 DMS 서버 역할|
|**엔드포인트(Endpoints)**|DMS가 소스/타겟 DB에 접근할 수 있게 해주는 연결 설정|

---

## 🧪 어떤 상황에서 사용하나요?

- Oracle → Amazon Aurora로 전환
- MySQL → Amazon RDS for PostgreSQL
- 온프레미스 DB → AWS RDS 또는 DynamoDB
- 멀티리전 또는 백업 목적의 실시간 데이터 복제
- 클라우드 간 마이그레이션 (예: Azure → AWS)

---

## ✅ 장점

|항목|장점|
|---|---|
|**무중단 마이그레이션**|실시간 CDC(Change Data Capture) 기능 지원|
|**관리형 서비스**|인프라 설정과 유지보수 불필요|
|**광범위한 지원**|Oracle, SQL Server, PostgreSQL, MySQL, MariaDB, MongoDB 등 다수 지원|
|**비용 효율적**|사용한 만큼만 비용 발생 (시간 단위 과금)|

---

## 📌 예시 시나리오

> 한 회사가 온프레미스 Oracle DB를 Amazon Aurora PostgreSQL로 이전하려고 한다.  
> AWS DMS를 사용하면 전체 데이터를 마이그레이션한 후, 실시간 변경 사항도 복제하여 **다운타임 없이 전환** 가능하다.

---

## 📚 관련 서비스

- **AWS SCT (Schema Conversion Tool)**  
    → 스키마 구조가 다른 경우 (예: Oracle → PostgreSQL), 이를 자동으로 변환

---

## ✨ 요약

> **AWS DMS**는 다양한 데이터베이스 간의 **마이그레이션 또는 실시간 복제**를 지원하는 **관리형 서비스**로,  
> 무중단 이전, 다양한 DB 지원, 자동화된 장애 복구 등 **효율적이고 안전한 데이터 이전을 가능하게** 합니다.