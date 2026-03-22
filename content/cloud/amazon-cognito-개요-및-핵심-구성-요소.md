---
title: Amazon Cognito 개요 및 핵심 구성 요소
slug: "amazon-cognito-개요-및-핵심-구성-요소"
category: cloud
tags: ["amazon-cognito", "authentication", "authorization", "aws", "cognito", "identity-management", "mfa", "oauth2", "openid-connect"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:04.940144+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---

---
aliases:
  - Cognito
---
**Amazon Cognito**는 사용자 인증(Authentication), 권한 부여(Authorization), 사용자 관리(User Management)를 손쉽게 구현할 수 있도록 도와주는 **AWS의 사용자 인증 서비스**입니다. 모바일 앱, 웹 애플리케이션, 서버리스 앱 등에서 **사용자 로그인/로그아웃/등록/토큰 발급** 등의 기능을 빠르게 구축할 수 있게 해줍니다.

---

## 🔐 Amazon Cognito의 핵심 구성 요소

|구성 요소|설명|
|---|---|
|**User Pools**|사용자 디렉터리. 사용자 등록, 로그인, MFA, 비밀번호 리셋 등 관리 가능|
|**Identity Pools** (Federated Identities)|인증된 사용자에게 AWS 리소스 접근 권한(임시 자격 증명)을 부여|
|**Cognito Sync** _(사용 중단됨)_|클라이언트 간 사용자 데이터 동기화 기능 (현재는 AWS AppSync 등으로 대체됨)|

---

## 🧱 1. Cognito User Pools

> 사용자 인증과 관리를 위한 자체 인증 시스템 (사용자 이름, 이메일, 비밀번호 등)

- 회원가입, 로그인, 이메일 인증, 비밀번호 변경 등 제공
- MFA(다단계 인증), 이메일/전화번호 검증 가능
- OAuth2, OpenID Connect 지원
- **SNS, Google, Facebook, Apple 로그인과 통합 가능**

✅ **사용처**: 인증 기반 앱 → 사용자가 로그인하는 앱/웹사이트

---

## 🔁 2. Cognito Identity Pools (Federated Identity)

> 사용자에게 **AWS 서비스에 접근 가능한 임시 자격 증명 (IAM Role)**을 부여

- Cognito User Pool, Google, Facebook, Apple 등에서 인증된 사용자를 연결
- 인증된 사용자에게 S3, DynamoDB, API Gateway 등의 접근 권한 부여 가능
- **IAM 역할(Roles)을 기반으로 세분화된 권한 부여 가능**

✅ **사용처**: 인증된 사용자에게 **S3 업로드, API 호출, Lambda 접근 권한** 부여 등

---

## ☁️ 통합 가능한 외부 ID 공급자 (Federation)

Cognito는 다음과 같은 **외부 ID 제공자**와 연동할 수 있습니다:

|유형|예시|
|---|---|
|소셜 로그인|Google, Facebook, Apple, Amazon|
|엔터프라이즈 로그인|SAML 2.0 (Azure AD, Okta 등)|
|개발자 자체 인증 시스템|사용자 지정 ID 공급자 (Custom Identity Provider)|

---

## 🛡️ 보안 기능

|기능|설명|
|---|---|
|MFA|SMS 또는 TOTP 기반 다단계 인증|
|비밀번호 정책|최소 길이, 문자 구성 규칙 등 설정 가능|
|사용자 속성 검증|이메일, 전화번호 인증 지원|
|토큰 기반 인증|JWT(Token)을 통한 세션 관리 (Access/ID/Refresh Token)|

---

## 🧪 사용 예시 시나리오

1. 사용자가 웹사이트에 회원가입
2. 이메일을 통해 인증
3. 로그인 후 JWT 토큰을 발급받음
4. 이 토큰을 Authorization 헤더에 실어 API Gateway 호출
5. Cognito Identity Pool을 통해 IAM 권한이 부여되고 S3 업로드 허용됨

---

## ✅ Amazon Cognito 요약

| 항목    | 내용                                       |
| ----- | ---------------------------------------- |
| 서비스명  | **Amazon Cognito**                       |
| 역할    | ==사용자 인증 및 AWS 리소스 접근 제어==               |
| 구성    | User Pools (인증) + Identity Pools (권한 부여) |
| 주요 기능 | 소셜 로그인 연동, MFA, 토큰 발급, AWS 서비스 권한 연결     |
| 사용 사례 | 로그인 기능, 보안 API 호출, 권한 기반 S3 접근 등         |

---

## 🔗 관련 서비스와의 비교

|서비스|차이점|
|---|---|
|AWS IAM|AWS 내부 사용자/서비스 인증 및 권한|
|AWS SSO|조직의 ID 관리 및 통합 로그인 (기업 중심)|
|AWS Secrets Manager|비밀번호 저장 용도 (인증 시스템은 아님)|