---
title: AWS Systems Manager Parameter Store
slug: "aws-systems-manager-parameter-store"
category: cloud
tags: ["aws", "cloudtrail", "ec2", "iam", "kms", "lambda", "parameter-store", "secrets-management", "ssm"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:04.509959+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A


---
---
aliases:
  - Parameter Store
  - SSM Parameter Store
---
**AWS Systems Manager Parameter Store**는 애플리케이션 설정값, 구성 데이터, 비밀번호, API 키, 데이터베이스 연결 문자열과 같은 **구성 파라미터를 안전하게 저장하고 관리하는 서비스**입니다. AWS Systems Manager의 기능 중 하나로서 **보안, 버전 관리, 접근 제어, 감사 추적** 기능을 제공합니다.

---

## 🔐 주요 기능

| 기능                            | 설명                                    |
| ----------------------------- | ------------------------------------- |
| **계층적 파라미터 저장**               | `/app/env/db/password` 형태로 디렉터리처럼 구조화 |
| **보안 파라미터 저장 (SecureString)** | KMS 키로 암호화된 값을 저장 가능               |
| ==**버전 관리**==                 | 파라미터 값 변경 시 버전이 자동으로 증가하고 기록됩니다             |
| **태그 지원**                     | 파라미터에 태그를 붙여 분류 및 필터링할 수 있습니다              |
| ==**IAM 기반 접근 제어**==          | 사용자 및 역할별로 읽기/쓰기 권한을 제어할 수 있습니다             |
| ==**CloudTrail 로깅**==         | 변경 기록 및 액세스 기록을 감사할 수 있습니다                  |
| **표준 vs 고급 파라미터**             | 고급 파라미터는 더 많은 수, 더 큰 크기, 추가 정책 기능을 지원(유료)    |

---

## 🏗️ 파라미터 유형

|유형|설명|
|---|---|
|**String**|일반 텍스트 값 (예: `app_mode = production`)|
|**StringList**|쉼표로 구분된 문자열 리스트 (예: `host1,host2,host3`)|
|**SecureString**|암호화된 비밀값 (예: 비밀번호, API 키 등) – KMS로 보호|

---

## 🔧 사용 예시

1. **DB 비밀번호 저장**
    
    ```bash
    aws ssm put-parameter \
      --name "/myapp/db/password" \
      --value "mypassword123" \
      --type "SecureString" \
      --key-id "alias/aws/ssm"
    ```
    
2. **Lambda, EC2, ECS에서 사용**
    
    - AWS SDK 또는 `aws ssm get-parameter` 명령으로 파라미터를 읽습니다。
    
    - 파라미터에 접근하려면 사용자 또는 인스턴스에 적절한 IAM 권한이 필요합니다。
        

---

## ✅ 활용 시나리오

|사용 사례|설명|
|---|---|
|🔑 **시크릿 관리**|비밀번호, API 키 등을 암호화해서 저장합니다 (대안: AWS Secrets Manager)|
|⚙️ **환경 구성값 관리**|스테이지별 설정(`dev`, `prod`, `test`)을 통합적으로 관리할 수 있습니다|
|📋 **애플리케이션 설정 버전 관리**|파라미터 변경 이력을 추적할 수 있습니다|
|🔐 **IAM 권한 기반 제어**|어떤 애플리케이션이나 역할이 어떤 값에 접근 가능한지 제어할 수 있습니다|

---

## 🆚 Parameter Store vs Secrets Manager

|항목|Parameter Store|Secrets Manager|
|---|---|---|
|주 사용 목적|구성값 저장|비밀 정보 저장 (주로 인증 관련)|
|자동 교체 기능|❌ 없음|✅ 있음 (예: RDS 비밀번호 자동 교체)|
|가격|기본 기능은 무료 (고급 기능은 유료)|유료|
|통합 서비스|SSM, EC2, Lambda 등|RDS, Lambda, IAM 등|

---

## 📌 요약

|항목|내용|
|---|---|
|서비스명|AWS Systems Manager Parameter Store|
|기능|파라미터(설정값, 시크릿)를 안전하게 저장하고 접근을 제어함|
|장점|KMS 암호화, 계층적 관리, IAM 권한 제어, 버전 관리 기능|
|활용|애플리케이션 설정, 비밀번호 보관, 자동화된 구성 관리|
|보안 옵션|`SecureString` 유형 사용 시 KMS 기반 암호화를 적용할 수 있음|