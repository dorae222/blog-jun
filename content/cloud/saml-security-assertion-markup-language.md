---
title: SAML (Security Assertion Markup Language)
slug: "saml-security-assertion-markup-language"
category: cloud
tags: ["authentication", "aws", "federation", "iam", "identity-provider", "saml", "security", "sso", "xml"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:07.770408+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---

---
aliases:
  - SAML
---
**Security Assertion Markup Language (SAML)**은
웹 기반 인증 및 권한 부여를 위한 **XML 기반 오픈 표준 프로토콜**로,
**사용자 인증 정보를 안전하게 전달하는 데 사용됩니다**. 특히 **싱글 사인온(SSO, Single Sign-On)** 환경에서 널리 활용됩니다.

---

## 🔐 SAML이란?

> **SAML (Security Assertion Markup Language)**은
> 사용자 인증(Authentication)과 권한(Authorization) 정보를 **XML 메시지로 교환**하여
> **웹 서비스 간에 사용자 신원을 안전하게 공유**할 수 있도록 설계된 **표준 프로토콜**입니다.

---

## 🏗️ 기본 구성 요소

|구성 요소|설명|
|---|---|
|**Identity Provider (IdP)**|사용자의 신원을 인증하는 서비스 (예: Okta, Google Workspace, ADFS 등)|
|**Service Provider (SP)**|사용자가 실제로 접근하려는 서비스 (예: AWS, Salesforce, Box 등)|
|**Assertion**|사용자에 대한 인증 정보와 속성(Attributes)을 담은 XML 문서|
|**SAML Protocol**|Assertion을 주고받는 방식 (HTTP Redirect, POST, Artifact 등)|

---

## 🔁 동작 흐름 예시

1. 사용자가 서비스(예: AWS 콘솔)에 접근을 시도합니다.
2. SP는 사용자를 IdP로 리디렉션합니다.
3. IdP는 사용자를 인증합니다(예: 사내 로그인).
4. IdP는 서명된 SAML Assertion을 생성해 브라우저로 전달합니다.
5. 사용자는 해당 Assertion을 SP로 전송합니다.
6. SP는 Assertion을 검증하고 사용자에게 접근 권한을 부여합니다.

---

## 📦 AWS에서의 활용 예

|항목|설명|
|---|---|
|**IAM SAML 연동**|기업의 IdP와 AWS IAM을 연동하여 **SSO 구성 가능**|
|**AWS SSO / IAM Identity Center**|SAML IdP를 통해 사용자 인증 수행|
|**Federated Access**|사용자는 AWS 자격 증명이 없이도 기업 계정으로 로그인 가능|

예시:
회사가 **Google Workspace 또는 Azure AD**를 IdP로 사용해
AWS 콘솔에 로그인하는 구조

---

## ✅ 장점

- ✅ **SSO 지원** – 여러 서비스에 한 번의 로그인으로 접근 가능합니다.
- ✅ **보안 강화** – 비밀번호 저장이 불필요하며, 암호화된 Assertion을 사용합니다.
- ✅ **표준 기반** – 다양한 플랫폼과 서비스 간 상호 운용성이 있습니다.
- ✅ **중앙화된 사용자 관리** – 사용자 관리와 인증을 IdP에서 통제할 수 있습니다.

---

## 📄 Assertion 예시 (XML 일부)

```xml
<saml:Assertion xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion">
  <saml:Subject>
    <saml:NameID>user@example.com</saml:NameID>
  </saml:Subject>
  <saml:AttributeStatement>
    <saml:Attribute Name="Role">
      <saml:AttributeValue>arn:aws:iam::123456789012:role/SAMLRole</saml:AttributeValue>
    </saml:Attribute>
  </saml:AttributeStatement>
</saml:Assertion>
```

---

## ✅ 요약

|항목|내용|
|---|---|
|정식 명칭|**Security Assertion Markup Language (SAML)**|
|목적|**SSO 및 사용자 인증 정보 전달**|
|포맷|XML|
|사용 주체|IdP (인증자), SP (서비스 제공자), 사용자|
|AWS 내 활용|IAM SAML 연동, AWS Identity Center, Federated Access|
|특징|중앙화된 인증, 보안성, 표준화|

---

필요하다면 **SAML을 통한 AWS IAM 역할 연동 설정 방법**,
또는 **SAML vs OIDC 비교표**도 정리해드릴 수 있습니다.
