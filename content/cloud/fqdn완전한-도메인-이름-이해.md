---
title: FQDN(완전한 도메인 이름) 이해
slug: "fqdn완전한-도메인-이름-이해"
category: cloud
tags: ["alb", "aws", "dns", "domain-name", "fqdn", "networking", "rds", "ssl", "tls"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:06.828566+00:00"
---

## 한 줄 정의

> **FQDN은 호스트 이름부터 최상위 도메인까지 모두 포함한 ‘완전한 도메인 이름’이다.**

---

## FQDN의 구성 요소

예시:

```text
db01.prod.example.com
```

|구성|설명|
|---|---|
|`db01`|호스트 이름|
|`prod`|서브도메인|
|`example`|도메인|
|`com`|최상위 도메인(TLD)|

👉 이 전체 문자열이 **FQDN**

---

## FQDN vs 일반 도메인

|구분|예|
|---|---|
|FQDN|`api.dev.company.co.kr`|
|부분 도메인|`api.dev`|
|도메인|`company.co.kr`|

---

## 왜 FQDN이 중요한가?

### 1️⃣ 네트워크 연결

- 서버, DB, API 엔드포인트를 식별할 때 사용됩니다.
- IP가 변경되어도 이름(FQDN)으로 접근할 수 있어 관리가 용이합니다.

---

### 2️⃣ 보안 (TLS/SSL)

- 인증서는 일반적으로 **FQDN 기준**으로 발급됩니다.
- 인증서의 CN 또는 SAN 필드에 FQDN이 포함되어야 올바르게 인증됩니다.

---

### 3️⃣ AWS 서비스 설정

- Glue, RDS, Redshift, ALB 등 여러 AWS 서비스에서 연결 설정 시 **FQDN을 요구**하는 경우가 많습니다.

예:

```text
mydb.cluster-xyz.us-east-1.rds.amazonaws.com
```

---

## FQDN과 DNS

- FQDN을 DNS에 조회하면 해당 호스트의 IP 주소를 얻습니다.
- 도메인 네임은 계층적(hierarchical)으로 해석됩니다.

---

## 핵심 포인트

- “전체 도메인 이름” → FQDN
- “호스트 + 도메인 + TLD” → FQDN
- “SSL 인증서 기준 이름” → FQDN
