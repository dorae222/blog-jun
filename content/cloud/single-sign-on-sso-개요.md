---
title: "Single Sign-On (SSO) 개요"
slug: "single-sign-on-sso-개요"
category: cloud
tags: ["aws", "iam-identity-center", "identity-provider", "mfa", "oauth", "openid-connect", "saml", "single-sign-on", "sso"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:04.428254+00:00"
---

---
aliases:
  - Single Sign-On
  - SSO
---
**Single Sign-On (SSO)**이란, **사용자가 한 번의 로그인으로 여러 시스템이나 애플리케이션에 접근할 수 있도록 해주는 인증 방식**입니다.

---

## 🧩 SSO의 정의

> **SSO (Single Sign-On)**은 한 번의 로그인으로 사용자가  
> **여러 독립적인 시스템에 인증 절차를 다시 거치지 않고 계속 접근**할 수 있게 해주는 **통합 인증 시스템**입니다.

---

## 🔐 SSO의 핵심 기능

|기능|설명|
|---|---|
|✅ **단일 로그인**|사용자 인증은 **한 번만** 수행되며, 이후에는 추가 로그인 없이 다른 서비스에 접근할 수 있습니다.|
|✅ **중앙 인증**|인증은 **중앙의 IdP(Identity Provider)**에서 관리됩니다.|
|✅ **자동 인증 연동**|SAML, OIDC, OAuth 등을 통해 시스템 간 로그인 세션을 공유합니다.|
|✅ **보안 강화**|중앙에서 인증 정책과 MFA 등을 적용하여 보안을 강화할 수 있습니다.|
|✅ **사용자 경험 향상**|서비스 간에 반복적인 로그인 없이 원활하게 이동할 수 있습니다.|

---

## 🏢 SSO 활용 예시

|상황|설명|
|---|---|
|🧑‍💻 **기업 내부 시스템**|이메일, 사내 인트라넷, ERP, 클라우드 등 여러 서비스에 매번 로그인하지 않고 접근할 수 있습니다.|
|☁️ **클라우드 서비스 연동**|AWS, Microsoft 365, Salesforce 등 다양한 클라우드 서비스를 하나의 로그인으로 이용할 수 있습니다.|
|🔐 **MFA와 연계**|초기 로그인 시 MFA를 적용하고, 이후 서비스 이동 시에는 별도 인증을 요구하지 않을 수 있습니다.|

---

## 🔗 기술 구성 요소

|구성 요소|설명|
|---|---|
|**IdP (Identity Provider)**|사용자 인증을 처리하는 시스템 (ex: AWS IAM Identity Center, Okta, Azure AD)|
|**SP (Service Provider)**|인증된 사용자에게 서비스를 제공하는 시스템 (ex: AWS, Salesforce 등)|
|**프로토콜**|SAML 2.0, OAuth 2.0, OpenID Connect 등|

---

## 🎯 AWS에서의 SSO

- 이전 서비스: **AWS Single Sign-On (현재는 IAM Identity Center로 통합)**

- 역할: 기업의 **AD, Azure AD, Okta** 같은 외부 IdP와 연동해 AWS 계정 접근을 관리합니다.

- 기능:
    - 하나의 로그인으로 **여러 AWS 계정 및 콘솔에 접근**할 수 있습니다.
    - **SAML 기반 연동**으로 외부 애플리케이션에 로그인 가능하게 합니다.
    - 사용자 그룹 및 권한을 일괄로 제어할 수 있습니다.

---

## 🆚 일반 로그인 vs SSO

|항목|일반 로그인|SSO|
|---|---|---|
|로그인 횟수|서비스마다 별도 로그인 필요|한 번의 로그인으로 여러 서비스 접근|
|사용자 경험|로그인 반복으로 불편|단일 인증으로 원활한 전환|
|보안|각 서비스별로 별도 보안 정책 필요|중앙 관리로 통일된 보안 정책 적용 가능|
|유지보수|서비스별로 개별 관리 필요|중앙에서 통합 관리 가능|

---

## ✅ 요약

|항목|설명|
|---|---|
|이름|**SSO (Single Sign-On)**|
|의미|한 번 로그인으로 여러 서비스에 접근할 수 있도록 해주는 인증 방식|
|구성|**IdP + SP**, SAML/OIDC 기반|
|장점|사용자 편의성 향상, 보안 정책 통합, 운영 효율성 증대|
|AWS 활용|**IAM Identity Center (구 AWS SSO)**를 통해 구현 가능|
