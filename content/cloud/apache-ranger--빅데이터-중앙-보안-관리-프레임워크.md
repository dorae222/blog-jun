---
title: Apache Ranger — 빅데이터 중앙 보안 관리 프레임워크
slug: "apache-ranger--빅데이터-중앙-보안-관리-프레임워크"
category: cloud
tags: ["access-management", "apache-ranger", "audit-logging", "big-data", "data-security", "fine-grained-access-control", "hadoop", "lake-formation"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:06.153374+00:00"
---

**Apache Ranger**는 **빅데이터 환경에서 중앙 집중식 보안 관리(권한·감사)**를 제공하는 **오픈소스 데이터 보안 프레임워크**입니다. 주로 Hadoop 및 데이터 레이크 생태계에서 **세밀한 접근 제어와 감사 로깅**을 담당합니다.

---

## 핵심 개념 한 줄 요약

> **Apache Ranger = 여러 데이터 서비스(Hive, HDFS 등)에 대한 권한 정책을 한 곳에서 정의·관리·감사하는 보안 컨트롤 타워**

---

## Apache Ranger의 주요 기능

### 1) 중앙 집중식 권한 관리

- 다양한 데이터 서비스의 접근 정책을 **하나의 UI/정책 저장소**에서 관리
- 사용자·그룹·역할 기반 권한(RBAC) 지원
- 예: “analytics 그룹은 Hive의 sales 테이블 읽기만 허용”

### 2) 세밀한 접근 제어 (Fine-grained Access Control)

- **테이블 / 컬럼 / 행 수준** 권한 제어
- 조건부 정책(시간, IP, 사용자 속성 등)
- 마스킹/익명화(컬럼 마스킹) 정책 지원

### 3) 데이터 감사(Auditing)

- 누가 언제 어떤 데이터에 접근했는지 **상세 감사 로그** 수집
- 규제/컴플라이언스 대응(GDPR, HIPAA 등)

### 4) 플러그인 기반 아키텍처

- 각 데이터 서비스에 **Ranger Plugin**을 설치해 정책을 적용
- 서비스 예:
    - HDFS
    - Hive
    - HBase
    - Kafka
    - Impala
    - Presto/Trino
    - Spark SQL
    - NiFi 등

---

## 구성 요소

- **Ranger Admin**
    - 정책 관리 UI 및 REST API 제공
    - 정책 저장 및 배포의 중앙 허브
- **Ranger Plugin**
    - 각 데이터 서비스에 설치
    - 실제 접근 요청 시 정책을 평가·차단/허용
- **Ranger UserSync**
    - LDAP/AD에서 사용자·그룹 동기화
- **Ranger Audit**
    - 접근 로그를 HDFS, Solr, Elasticsearch 등으로 저장

---

## Apache Ranger vs AWS 서비스 비교

|Apache Ranger|AWS 대응 서비스|
|---|---|
|중앙 권한 관리|**AWS Lake Formation**|
|테이블/컬럼/행 제어|Lake Formation, Redshift RLS/CLS|
|감사 로그|CloudTrail, Lake Formation audit|
|Hadoop 중심|AWS 관리형 데이터 서비스|

👉 **AWS 환경에서는 Ranger 대신 Lake Formation을 사용하는 경우가 많음**

---

## 언제 Apache Ranger를 사용하는가?

- 온프레미스 또는 EMR 기반 Hadoop 환경
- Hive/HDFS/Kafka 등 **다양한 빅데이터 서비스에 일관된 보안 정책**이 필요할 때
- 규제 환경에서 **정교한 감사·마스킹** 요구가 있을 때

---

## 한 줄 결론

> **Apache Ranger는 빅데이터 환경에서 “누가 어떤 데이터에 접근할 수 있는지”를 중앙에서 통제하고 감사하는 표준 보안 프레임워크다.**