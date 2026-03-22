---
title: "TLD(Top-Level Domain)"
slug: "tldtop-level-domain"
category: cloud
tags: ["aws", "cctld", "certificate-manager", "dns", "domain", "fqdn", "gtld", "route53", "tld"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:07.976512+00:00"
---

**TLD(Top-Level Domain)**는 도메인 이름 구조에서 **가장 최상위에 위치한 마지막 부분**입니다.

---

## 한 줄 정의

> **TLD는 도메인 네임 시스템(DNS)에서 가장 상위 계층에 해당하는 도메인이다.**

---

## TLD의 위치 (구조)

예:

```text
www.example.com
```

|구성 요소|설명|
|---|---|
|`www`|서브도메인|
|`example`|2단계 도메인|
|**`com`**|**TLD**|

---

## TLD의 주요 역할

- 도메인 이름 공간의 **최상위 분류**
- 도메인 관리 주체 식별
- 국가·조직·목적 구분

---

## TLD의 종류

### 1️⃣ 일반 최상위 도메인 (gTLD)

- 목적/분야 기반

예:

- `.com` (상업)
- `.org` (비영리)
- `.net`
- `.info`
- `.cloud`, `.aws` 등

---

### 2️⃣ 국가 코드 최상위 도메인 (ccTLD)

- 국가/지역 기반 (ISO 3166)

예:

- `.kr` (대한민국)
- `.jp`
- `.us`
- `.uk`

---

### 3️⃣ 인프라 TLD

- 특수 목적

예:

- `.arpa` (DNS 인프라)

---

## TLD vs 도메인 vs FQDN

|구분|예|
|---|---|
|TLD|`com`|
|도메인|`example.com`|
|FQDN|`api.dev.example.com`|

---

## AWS와 TLD

- Route 53에서 도메인 등록 시 TLD 선택
- TLS 인증서(Certificate Manager)는 FQDN을 기준으로 발급
- ALB, API Gateway 등도 FQDN 기반 접근