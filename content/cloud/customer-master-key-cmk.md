---
title: Customer Master Key (CMK)
slug: "customer-master-key-cmk"
category: cloud
tags: ["aws", "aws-kms", "cloudtrail", "cmk", "encryption", "key-management", "security", "sse-kms"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:06.483768+00:00"
---

**Customer Master Key (CMK)**는 AWS Key Management Service(AWS KMS)에서 사용하는 **고객이 생성하거나 관리하는 암호화 키의 논리적 표현**입니다. 이 키는 **데이터 암호화·복호화의 핵심 역할**을 하며, **보안, 권한, 로깅**을 포함한 다양한 관리 기능을 제공합니다.

---

## 🔐 CMK란?

> **CMK (Customer Master Key)**는
> AWS KMS에서 **데이터를 암호화하거나 다른 암호화 키(Data Key)를 생성하는 데 사용되는 주요 키(Master Key)**입니다. 고객이 직접 생성하거나 AWS가 관리할 수 있으며, **정책 기반 접근 제어**, **감사 로깅(CloudTrail)**, **자동 회전** 등의 기능을 제공합니다.

---

## 🔧 CMK의 구성

|구성 요소|설명|
|---|---|
|**Key ID**|고유한 키 식별자|
|**Key ARN**|AWS 리소스 이름 형식의 전체 경로|
|**Alias**|사람이 읽을 수 있는 이름 (예: `alias/myKey`)|
|**Description**|키 설명|
|**Key Policy**|이 키에 대한 권한 정책|
|**Key Material**|실제 암호화 키(내부 저장 또는 Bring Your Own Key 방식 가능)|

---

## 📚 CMK 유형

|유형|설명|
|---|---|
|**AWS 관리형 CMK**|AWS 서비스가 자동으로 생성·관리 (예: S3, EBS 등)|
|**고객 관리형 CMK**|사용자가 직접 생성하고 세부 제어(정책, 회전 등)가 가능|
|**외부 키(BYOK)**|외부에서 생성한 키를 업로드하여 사용|

---

## 🔐 주요 기능

|기능|설명|
|---|---|
|✅ **정책 기반 접근 제어**|IAM 또는 Key Policy로 세부 권한 제어 가능|
|🔁 **자동 키 회전 (1년 주기)**|고객 관리형 CMK에 대해 적용 가능|
|🔒 **암호화 키의 생성 및 관리**|Data Key 생성, Envelope Encryption 등에 사용|
|🪵 **CloudTrail 로깅**|키 사용 이력을 추적 가능|
|🔗 **다양한 AWS 서비스와 통합**|S3, RDS, EBS, Lambda, Secrets Manager 등과 통합|

---

## 🔒 사용 예시

- S3 객체를 **SSE-KMS(S3 서버측 KMS 암호화)**로 보호
- EBS 볼륨을 CMK로 암호화
- Lambda 환경 변수 암호화
- DynamoDB 테이블 암호화
- Secrets Manager에서 비밀번호 보호

---

## ✅ 요약

|항목|내용|
|---|---|
|이름|**Customer Master Key (CMK)**|
|위치|**AWS Key Management Service (KMS)**|
|역할|데이터 키 생성 및 직접 암호화/복호화 수행|
|관리 주체|AWS 또는 고객|
|핵심 기능|접근 제어, 자동 회전, 로깅, 서비스 통합|
|사용 예시|S3, EBS, RDS, Lambda, Secrets Manager 등|
