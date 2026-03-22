---
title: AWS Secrets Manager
slug: "aws-secrets-manager"
category: cloud
tags: ["aws", "aws-secrets-manager", "iam", "kms", "rds", "rotation", "secrets-management", "security"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:04.351797+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A


---
---
aliases:
  - Secrets Manager
---

> **NOTE:**
> - 보안 정보(자격 증명)를 중앙에서 저장·검색·접근 제어·교체·감사·모니터링하는 서비스입니다.
> - 보안 정보에는 데이터베이스 자격 증명, 온프레미스 리소스 자격 증명, SaaS 애플리케이션 자격 증명, 타사 API 키, SSH 키 등이 포함될 수 있습니다.
> - 보안 정보를 저장하는 방식
>   - 사용자가 소유한 AWS KMS 키로 시크릿을 암호화하여 저장합니다.
>   - 사용자는 AWS IAM 정책으로 시크릿에 대한 접근을 제어합니다.
>   - 사용자가 시크릿을 조회하면 Secrets Manager가 해당 시크릿을 복호화해 TLS로 안전하게 전송합니다.
> - 시크릿의 자동 교체 및 관리 기능
>   - Amazon RDS, Redshift, DocumentDB와 기본 통합되어 이러한 DB 자격 증명을 자동으로 교체할 수 있습니다.
>   - Lambda 함수를 활용해 30일, 60일 등 교체 주기를 지정해 자격 증명을 자동으로 교체하도록 구성할 수 있습니다.
> - Secrets Manager에 저장된 비밀은 KMS 키로 암호화되어 내부적으로 S3에 저장됩니다.


|서비스|관리 대상|주요 목적|예시|
|---|---|---|---|
|**ACM**|SSL/TLS 인증서|HTTPS 통신 암호화 (전송 계층 보호)|CloudFront에 인증서 적용|
|**Secrets Manager**|비밀번호, API Key, 토큰|비밀 값 보관·조회·자동 교체 (저장된 민감 데이터 보호)|DB 비밀번호 관리|
|**KMS**|암호화 키|암호화/복호화 키 관리 (데이터 보호)|S3/EBS 암호화, Secrets 암호화|

---
**AWS Secrets Manager**는 애플리케이션, 서비스, 사용자 등이 사용하는 **비밀 정보(Secrets)**—예: **데이터베이스 자격 증명, API 키, OAuth 토큰**—을 **안전하게 저장·관리·검색·자동 교체**할 수 있도록 제공하는 **<mark style="background: #FFF3A3A6;">완전관리형</mark> 시크릿 관리 서비스**입니다.

---

## 🔐 주요 기능

|기능|설명|
|---|---|
|**비밀 정보 저장**|데이터베이스 사용자명/비밀번호, API 키, 토큰 등 저장|
|**암호화 저장 (KMS)**|기본적으로 AWS Key Management Service(KMS)로 암호화|
|**자동 교체 (Rotation)**|비밀번호나 API 키를 주기적으로 자동 교체 가능 (예: RDS 통합)|
|**IAM 기반 접근 제어**|누가 어떤 시크릿에 접근 가능한지 IAM 정책으로 제어|
|**버전 관리**|시크릿 변경 시 버전 추적 및 롤백 가능|
|**CloudTrail 로깅**|모든 시크릿 접근 및 변경 내역 감사 가능|

---

## 🛠️ 사용 예시

1. **RDS 비밀번호 저장 및 자동 교체**
    
    - 비밀번호를 Secrets Manager에 저장하고,
        
    - Lambda를 이용해 **주기적인 자동 교체 및 애플리케이션 연결값 갱신**을 구현할 수 있습니다.
        
2. **시크릿 생성 (예: CLI 사용)**
    
    ```bash
    aws secretsmanager create-secret \
      --name prod/db_password \
      --secret-string '{"username":"admin","password":"mypassword"}'
    ```
    
3. **시크릿 검색**
    
    ```bash
    aws secretsmanager get-secret-value --secret-id prod/db_password
    ```
    
---

## 🔁 Secrets Manager vs Parameter Store

|항목|**Secrets Manager**|**Parameter Store (SecureString)**|
|---|---|---|
|**주 용도**|민감한 비밀 정보 관리|일반 설정값 및 간단한 시크릿|
|**자동 교체**|✅ 가능 (지원 서비스에 한함)|❌ 직접 구성 필요|
|**버전 관리**|✅ 있음|✅ 있음|
|**가격**|유료 (교체 기능 포함)|기본 무료 / 고급 기능 유료|
|**통합**|Lambda, RDS, CloudFormation 등과 자동 통합|ECS, Lambda 등에서 수동 통합|

---

## 📦 지원되는 시크릿 유형

- 데이터베이스 자격 증명 (MySQL, PostgreSQL, Aurora 등)
- API Key, OAuth Token
- 인증서, SSH 키
- 기타 사용자 정의 비밀 값

---

## ✅ 사용 사례

|사례|설명|
|---|---|
|**DB 인증정보 저장**|MySQL/RDS 자격 증명을 안전하게 저장하고 자동 교체|
|**ECS / Lambda 구성**|시크릿을 안전하게 컨테이너나 함수에 주입|
|**CI/CD 파이프라인 보안**|GitHub Token, Docker Hub Key 등 저장|
|**서비스 간 인증**|마이크로서비스 간 API 인증 토큰 관리|

---

## 📌 요약

|항목|내용|
|---|---|
|서비스 이름|**AWS Secrets Manager**|
|목적|**비밀 값(Secrets)의 안전한 저장, 관리, 자동 교체**|
|암호화|AWS KMS 기반|
|주요 장점|자동 로테이션, IAM 제어, 감사 추적|
|대표 사례|DB 비밀번호, API 키, 토큰 저장 및 자동 교체|
|비용|유료 서비스 (사용량 기반 청구)|
- BatchGetSecretValue API
