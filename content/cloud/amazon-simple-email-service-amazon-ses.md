---
title: Amazon Simple Email Service (Amazon SES)
slug: "amazon-simple-email-service-amazon-ses"
category: cloud
tags: ["amazon-ses", "aws", "cloud", "deliverability", "dkim", "email", "smtp", "spf", "transactional-email"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.970685+00:00"
---

**Amazon Simple Email Service (Amazon SES)**는  
**대량 이메일 전송 및 수신을 위한 클라우드 기반 이메일 서비스**입니다.  
주로 **마케팅 이메일, 트랜잭션 이메일(예: 비밀번호 재설정), 알림 이메일**을 안전하고 확장 가능하게 전송할 수 있도록 지원합니다.

---

## ✉️ Amazon SES란?

> **Amazon SES (Simple Email Service)**는  
> **신뢰성 있는 이메일 전송을 위한 고확장성·보안성·비용 효율적인 서비스**입니다.  
> SMTP 또는 API를 통해 이메일을 전송하며, **수신 및 피드백 루프(반송, 수신 거부 등) 처리도 가능**합니다.

---

## 📦 주요 기능

|기능|설명|
|---|---|
|📤 **이메일 전송**|SMTP 또는 AWS SDK/API를 통해 이메일을 전송|
|📩 **이메일 수신**|특정 도메인/주소로 수신된 메일을 S3, Lambda, SNS로 전달 가능|
|📊 **피드백 추적**|반송(Bounce), 수신 거부(Complaint), 전달 성공 추적|
|🔐 **보안**|DKIM, SPF, DMARC 인증 지원|
|🧠 **IP 평판 관리**|전용 IP 주소 또는 공유 IP 풀 사용 가능|
|📈 **통계 분석**|전송 성공률, 클릭률, 오픈율 등 지표 제공 (CloudWatch 연동)|
|🏷 **템플릿 기능**|변수 기반의 HTML 템플릿 이메일 지원|

---

## 🔧 전송 방식

|방식|설명|
|---|---|
|**SMTP 인터페이스**|기존 이메일 클라이언트 또는 애플리케이션과 통합 가능|
|**SES API (AWS SDK)**|Lambda, 앱 백엔드 등에서 직접 호출|
|**Amazon SNS 연동**|반송/불만 알림을 이벤트 기반으로 처리 가능|

---

## 🔐 도메인 인증 및 발신자 검증

|검증 대상|설명|
|---|---|
|**Email 주소 검증**|수신자에게 인증 링크를 보내 직접 승인|
|**도메인 검증**|DNS에 TXT/CNAME 레코드를 추가해 소유권 확인 (SPF/DKIM 포함)|

> 도메인 인증은 **전송 신뢰도 향상** 및 **스팸 방지**에 필수적입니다.

---

## 💰 요금

|항목|가격 (2025년 기준, 미국 리전)|
|---|---|
|**EC2에서 전송**|매월 62,000건까지 무료|
|**그 외**|$0.10 / 1,000건 전송|
|**첨부 파일 데이터 요금**|$0.12 / GB|
|**수신 이메일**|$0.10 / 1,000건 (옵션)|

---

## ✅ 요약

|항목|설명|
|---|---|
|이름|**Amazon Simple Email Service (Amazon SES)**|
|용도|**대량 이메일 전송 및 수신**|
|활용 사례|마케팅 메일, 알림 메일, 트랜잭션 메일 등|
|전송 방식|SMTP / SES API / AWS SDK|
|연동 가능|Lambda, S3, SNS, EventBridge 등|
|보안 기능|SPF, DKIM, DMARC, IAM 제어|
|분석 기능|반송, 수신 거부, 클릭률 추적 등 (CloudWatch)|

---

## 🛠️ 활용 예시

- 가입 확인 이메일 자동 전송 (Lambda + SES)

- 매일 뉴스레터 발송 (API 호출 + 템플릿)

- 수신 이메일을 S3에 저장 → SNS로 알림
