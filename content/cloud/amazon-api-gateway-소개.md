---
title: Amazon API Gateway 소개
slug: "amazon-api-gateway-소개"
category: cloud
tags: ["amazon-api-gateway", "api-gateway", "api-security", "aws", "http-api", "lambda", "rate-limiting", "serverless", "websocket"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:04.716643+00:00"
---

**API Key 및 Usage Plan**을 사용해 API 요청을 제어할 수 있습니다. 정품 사용자에게만 API 키를 발급하고, 각 키에 대해 요청 제한(쿼터, 초당 제한 등)을 설정하면 **봇넷의 과도한 요청을 제한**하거나 차단할 수 있습니다. 이는 인증되지 않은 사용자 요청에 대한 첫 번째 방어선이 됩니다.

---

## 📌 **Amazon API Gateway란?**

**Amazon API Gateway**는
👉 **클라우드에서 API(애플리케이션 프로그래밍 인터페이스)를 만들고, 배포하고, 관리할 수 있게 해주는 완전 관리형 서비스**입니다.

쉽게 말해,

> 💡 **“외부 클라이언트(앱, 웹사이트 등)와 백엔드 서비스(Lambda, EC2, DynamoDB 등)를 연결해주는 게이트웨이”**  
> 👉 요청을 받아서, 필요한 검증/변환을 거쳐 백엔드로 전달하고, 응답을 클라이언트로 돌려주는 역할을 합니다.

---

## ✨ **주요 기능**

✅ **API 생성 및 관리**

- REST API, WebSocket API, HTTP API를 간단하게 만들고 관리할 수 있습니다.
    

✅ **보안 강화**

- IAM, Lambda Authorizer, Cognito 등과 연동해 인증·인가(Authorization)가 가능합니다.
    
- WAF(Web Application Firewall)와 연계해 공격을 방어할 수 있습니다.
    
- 요청·응답을 암호화(HTTPS)로 처리합니다.
    

✅ **트래픽 제어**

- 요청 속도를 제한(Rate Limiting)할 수 있습니다.
    
- 스로틀링(Throttle) 및 버스트 제한으로 과도한 트래픽을 방지합니다.
    

✅ **변환과 라우팅**

- 요청과 응답을 **필터링하거나 포맷 변환**할 수 있습니다 (예: JSON → 다른 구조).
    
- 여러 백엔드(Lambda, 다른 API, EC2 등)로 라우팅할 수 있습니다.
    

✅ **모니터링 및 로깅**

- CloudWatch와 연계해 사용량 모니터링과 에러 추적이 가능합니다.
    

---

## 🛠️ **API Gateway가 연결하는 백엔드 예시**

- **AWS Lambda**  
    👉 서버리스 아키텍처 구현이 가능합니다. (API 요청 → Lambda 실행)
    
- **EC2 인스턴스**  
    👉 직접 관리하는 서버로 요청을 전달합니다.
    
- **AWS 서비스** (DynamoDB, S3 등)  
    👉 데이터 CRUD를 API로 제공합니다.
    
- **외부 엔드포인트**  
    👉 다른 API나 시스템으로 프록시 역할을 합니다.
    
---

## 💡 **주요 사용 사례**

✔ **서버리스 백엔드 구현**

- 프론트엔드 앱에서 오는 요청을 Lambda로 전달해 서버 없이 서비스 운영이 가능합니다.
    
✔ **API 관리와 배포 간소화**

- 대규모 사용자에게 API를 안정적으로 제공할 수 있습니다.
    
✔ **보안이 중요한 API**

- 인증/인가 및 요청 제한을 손쉽게 적용할 수 있습니다.
    
✔ **멀티 리전, 글로벌 API**

- CloudFront와 함께 글로벌 배포가 가능합니다.
    
---

## 📦 **API 종류 (API Gateway에서 지원)**

|종류|특징|예시|
|---|---|---|
|**REST API**|전통적 RESTful API, 세밀한 기능과 통합|모바일 앱 백엔드|
|**HTTP API**|가벼운 REST API, 저지연, 저비용|단순 Lambda 호출|
|**WebSocket API**|실시간 양방향 통신 지원|채팅 앱, 실시간 알림|

---

## 🎯 **비유로 이해하기**

🚦 **API Gateway = 고속도로 톨게이트**

- 차(클라이언트 요청)가 지나갈 때:
    
    - 요금(인증) 확인,
        
    - 속도제한(Throttle),
        
    - 길 안내(백엔드 라우팅),
        
    - 기록(로깅)  
        등을 처리한 뒤 **백엔드로 안전하게 전달**합니다.
        
---

## ✅ **한눈에 정리**

|항목|설명|
|---|---|
|역할|API를 생성, 배포, 관리하는 완전 관리형 서비스|
|연결 대상|Lambda, EC2, DynamoDB, S3 등|
|보안|인증/인가, 트래픽 제어, WAF 연계|
|장점|서버리스 아키텍처 구현, 확장성, 모니터링|
