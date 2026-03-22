---
title: "Fine-Grained Controls (정밀 제어)"
slug: "fine-grained-controls-정밀-제어"
category: cloud
tags: ["api-gateway", "aws", "aws-waf", "fine-grained-access-control", "iam", "least-privilege", "network-firewall", "s3", "security"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:06.810941+00:00"
---

AWS 또는 일반적인 보안 시스템에서 **매우 정밀하고 구체적인 조건에 따라 접근, 필터링, 동작 등을 제어할 수 있는 기능**을 말합니다.

쉽게 말해,

> **“누가, 언제, 어떤 조건에서, 어떤 리소스에, 어떤 방식으로 접근할 수 있는지”를
> 매우 구체적으로 설정할 수 있는 기능**입니다.

---

## 🔍 Fine-Grained Controls의 핵심 개념

|항목|설명|
|---|---|
|🎯 **정밀 제어 범위**|IP 주소, 포트, 프로토콜, 요청 경로, 헤더, 도메인, 사용자 그룹 등|
|🔐 **보안 강화**|불필요한 접근을 차단하여 **최소 권한 원칙(Least Privilege)** 구현|
|⚙️ **정책 설정 유연성**|하나의 정책 내에서 **예외 조건**이나 **필터링 규칙**을 상세하게 정의 가능|
|🧩 **적용 대상**|IAM, S3, AWS Network Firewall, AWS WAF, API Gateway 등 다양한 서비스|

---

## 📦 예: AWS Network Firewall에서의 Fine-Grained Controls

아래는 트래픽을 정밀하게 제어하는 정책 예시들입니다:

|제어 항목|예시|
|---|---|
|**IP & Port 제어**|`203.0.113.0/24`에서 오는 `TCP:443`만 허용|
|**Protocol 제어**|SMB(445), FTP(21) 프로토콜 **차단**|
|**도메인 기반 허용**|`*.mycorp.com`에만 아웃바운드 허용|
|**정규 표현식 필터링**|URI 또는 헤더에 `^/admin.*` 요청은 **Drop**|
|**행위 기반 필터링**|비정상적인 패킷 수, 트래픽 양 이상 시 **Alert 또는 Drop**|

---

## 🛡️ Fine-Grained Controls 사용의 이점

|장점|설명|
|---|---|
|✅ **보안 강화**|불필요한 접근을 제한하고 공격 경로를 최소화|
|✅ **규제 및 감사 대응**|특정 조건만 허용해 **정책 기반 보안 준수** 가능|
|✅ **유연한 운영 정책**|다양한 조건을 조합해 **정책을 세분화**할 수 있음|
|✅ **통합 로깅 및 분석**|어떤 조건에서 차단/허용됐는지 정확히 기록하여 분석 가능|

---

## ✅ 요약

|항목|설명|
|---|---|
|정의|**트래픽, 권한, 요청 등을 매우 상세한 조건으로 제어하는 보안 및 정책 기능**|
|관련 서비스|AWS Network Firewall, IAM, S3 정책, API Gateway, AWS WAF 등|
|활용 목적|**보안 강화**, **세부 제어 정책 설정**, **모니터링/로깅 향상**|

- AWS Network Firewall
- IAM