---
title: Common Vulnerabilities and Exposures (CVE)
slug: "common-vulnerabilities-and-exposures-cve"
category: cloud
tags: ["cna", "cve", "cvss", "log4j", "mitre", "nvd", "security", "vulnerabilities", "vulnerability-management"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:06.404382+00:00"
---

**Common Vulnerabilities and Exposures (CVE)**는 소프트웨어의 **공통된 보안 취약점과 노출(CVE, 취약점 ID)**을 표준화된 방식으로 식별하고 공유하기 위한 **국제 표준 식별자 체계**입니다.

즉, 전 세계 보안 연구자나 개발자가 발견한 취약점에 대해 **고유한 ID를 부여하고 공통 데이터베이스에 등록**하여 보안 패치, 리스크 분석, 자동화 도구에 활용할 수 있도록 돕는 시스템입니다.

---

## 🔐 CVE란?

> **CVE (Common Vulnerabilities and Exposures)**는
> **공식적으로 식별된 소프트웨어 보안 취약점에 부여되는 고유 식별 번호(ID)**이며,
> 이를 통해 **보안 관련 커뮤니케이션의 일관성과 자동화된 보안 도구 연동**을 가능하게 합니다.

---

## 📌 예시

```text
CVE-2024-12345
```

- `CVE`: 고유 접두어
    
- `2024`: 해당 취약점이 등록된 연도
    
- `12345`: 고유 식별 번호 (일련번호)
    

> 예: `CVE-2021-44228`은 유명한 Log4j 취약점입니다 (Log4Shell).

---

## 🧩 주요 특징

|항목|설명|
|---|---|
|📇 **고유 ID 부여**|전 세계 보안 취약점을 통일된 방식으로 식별 가능|
|📚 **공개 데이터베이스**|누구나 CVE 목록을 조회 가능|
|🔄 **보안 도구 통합**|취약점 스캐너, IDS/IPS, SIEM 도구와 연동|
|🛡️ **보안 패치 관리**|벤더는 CVE ID를 기준으로 패치 노트를 발행|

---

## 🧱 CVE 시스템 구성

|요소|설명|
|---|---|
|**CVE ID**|고유한 취약점 식별자|
|**CVE Description**|어떤 문제인지에 대한 간략한 설명|
|**References**|관련 벤더 페이지, 패치 정보 등|
|**CNA (CVE Numbering Authorities)**|CVE ID를 발급하는 기관 (예: Microsoft, Google, Red Hat 등)|

---

## 🔍 CVE vs CVSS

|용어|설명|
|---|---|
|**CVE**|_어떤 취약점이 있는가?_ → 식별자 제공|
|**CVSS**|_얼마나 위험한가?_ → 취약점의 심각도 점수화 (0.0 ~ 10.0)|

> CVE는 존재 자체에 대한 표준 ID이고,
> **CVSS (Common Vulnerability Scoring System)**는 위험도의 수치화를 위한 기준입니다.

---

## ✅ 요약

|항목|설명|
|---|---|
|이름|**Common Vulnerabilities and Exposures (CVE)**|
|목적|**전 세계 보안 취약점에 표준 ID 부여 및 공개 공유**|
|발행 기관|MITRE Corporation (미국 DHS 지원)|
|사용처|보안 분석, 침투 테스트, 패치 관리, 컴플라이언스 대응 등|
|대표 예|`CVE-2021-44228` (Log4Shell), `CVE-2017-0144` (WannaCry)|

---

## 📚 참고 사이트

- [🔗 공식 CVE 사이트 (cve.org)](https://www.cve.org/)
    
- [🔍 NVD (National Vulnerability Database)](https://nvd.nist.gov/)
