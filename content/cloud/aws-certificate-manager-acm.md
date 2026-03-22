---
title: AWS Certificate Manager (ACM)
slug: "aws-certificate-manager-acm"
category: cloud
tags: ["acm", "api-gateway", "aws", "aws-private-ca", "certificate-management", "cloudfront", "elastic-load-balancing", "ssl", "tls"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:03.429559+00:00"
---

**AWS Certificate Manager (ACM)**는  
**SSL/TLS 인증서를 손쉽게 프로비저닝, 관리 및 배포할 수 있도록 지원하는 AWS의 관리형 서비스**입니다.  
즉, 웹사이트나 애플리케이션의 **HTTPS 보안 연결(암호화)**을 위해 필요한 인증서를 **무료로 생성하거나 업로드하고 자동으로 갱신**해주는 서비스입니다.

---

## 🔐 AWS Certificate Manager란?

> **AWS Certificate Manager (ACM)**는  
> **도메인에 대한 공개 키 기반 인증서(SSL/TLS)를 발급 및 관리**하고,  
> 이를 **ALB, CloudFront, API Gateway, Elastic Beanstalk 등과 연동**해 HTTPS 보안 통신을 활성화하는 서비스입니다.

---

## 🧩 주요 기능

|기능|설명|
|---|---|
|📥 **무료 퍼블릭 인증서 발급**|ACM을 통해 *.example.com 등의 인증서를 무료로 발급|
|🔄 **자동 갱신**|ACM 인증서는 유효 기간 만료 전에 자동으로 갱신|
|🔐 **비공개 인증서 관리**|AWS Private CA와 통합해 사내 전용 인증서도 관리 가능|
|🧾 **인증서 가져오기**|외부에서 발급받은 인증서(.crt, .key 등)를 수동으로 업로드|
|🔗 **서비스 통합**|ELB, CloudFront, API Gateway, App Runner 등과 쉽게 연결|
|🔍 **도메인 검증 방식 지원**|DNS 또는 이메일 기반 검증 방식 선택 가능|

---

## 🌐 ACM이 지원하는 대상 서비스

|연동 서비스|설명|
|---|---|
|**Elastic Load Balancing (ALB/NLB)**|HTTPS 리스너에 인증서 적용|
|**Amazon CloudFront**|SSL 인증서로 콘텐츠 암호화|
|**Amazon API Gateway**|API 엔드포인트의 HTTPS 보안 활성화|
|**AWS Elastic Beanstalk**|환경 구성 시 HTTPS 설정|
|**App Runner / Lightsail**|도메인에 맞는 인증서 적용 가능|

---

## 🔎 인증서 유형

|인증서 유형|설명|
|---|---|
|**퍼블릭 인증서**|ACM에서 무료로 발급 (인터넷 대상)|
|**프라이빗 인증서**|AWS Private CA를 통해 발급 (사내망 등 내부용)|
|**업로드한 인증서**|타 인증기관에서 발급받은 기존 인증서|

---

## 🧪 도메인 인증 방식

|방식|설명|
|---|---|
|**DNS 검증**|Route 53 등 DNS에 CNAME 레코드 등록|
|**이메일 검증**|도메인 WHOIS 이메일 주소로 인증 메일 수신|

---

## 🛡️ 보안 이점

- **HTTPS 암호화로 중간자 공격 방지**

- **브라우저 신뢰 체인에 등록된 루트 CA 사용**

- **자동 갱신으로 운영 리스크 최소화**

---

## ✅ 요약

|항목|설명|
|---|---|
|이름|**AWS Certificate Manager (ACM)**|
|목적|**도메인 기반 SSL/TLS 인증서의 발급, 관리, 배포**|
|가격|**퍼블릭 인증서 무료**, 프라이빗 인증서는 유료 (Private CA 필요)|
|자동 갱신|✅ 지원|
|주요 연동|ELB, CloudFront, API Gateway, Beanstalk, App Runner 등|
|인증 방법|DNS 검증, 이메일 검증|
|관리 대상|ACM에서 발급하거나 외부 인증서 업로드 가능|