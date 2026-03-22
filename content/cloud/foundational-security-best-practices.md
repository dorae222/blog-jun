---
title: Foundational Security Best Practices
slug: "foundational-security-best-practices"
category: cloud
tags: ["aws", "compliance", "ec2", "foundational-security-best-practices", "iam", "rds", "s3", "security", "security-hub"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:06.819206+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---

---
aliases:
  - FSBP
---
**Foundational Security Best Practices**는 AWS에서 제공하는 **보안 기준 가이드라인(Security Benchmark)**으로, 핵심 AWS 서비스에 대한 필수 보안을 자동으로 점검할 수 있도록 설계된 규칙 집합입니다. 이는 AWS Security Hub 기능 중 하나로 제공되며, AWS 환경의 보안 상태를 지속적으로 평가하고 잠재적 위험을 식별하는 데 도움을 줍니다.

---

## 🔐 Foundational Security Best Practices란?

> AWS Security Hub에서 제공하는 **보안 표준(Security Standard)** 중 하나로, AWS에서 권장하는 핵심 보안 설정 및 구성 규칙을 서비스별로 자동으로 검사하여 보안 미비점을 식별하고 권장 조치를 안내합니다.

---

## 📦 주요 특징

|항목|설명|
|---|---|
|✅ **자동화된 보안 점검**|AWS 리소스의 상태를 지속적으로 모니터링합니다.|
|🛠 **서비스별 권장 구성 확인**|S3, IAM, EC2, RDS 등 주요 서비스에 대한 권장 설정을 점검합니다.|
|📚 **AWS 권장 보안 기준 반영**|AWS 보안 백서 및 업계 권장사항을 기반으로 합니다.|
|🔄 **지속적 컴플라이언스 확인**|매일 상태를 평가하고 결과를 업데이트합니다.|
|🎯 **Security Hub에서 연동**|점검 결과를 Findings(보안 경고) 형태로 제공합니다.|
|📎 **CIS Benchmarks와 병행 사용 가능**|다른 컴플라이언스 프레임워크와 함께 운영할 수 있습니다.|

---

## 🧩 예시 점검 항목

|서비스|점검 항목 예시|
|---|---|
|**IAM**|루트 계정에 MFA 활성화 여부, 오래된 액세스 키 제거 여부 등을 점검합니다.|
|**S3**|퍼블릭 액세스 차단 설정, 객체 암호화 사용 여부 등을 확인합니다.|
|**RDS**|자동 백업 설정 여부, 저장 암호화 여부 등을 점검합니다.|
|**EC2**|보안 그룹의 포트 제한 적용 여부, EBS 암호화 여부 등을 확인합니다.|
|**CloudTrail**|로그가 S3에 저장되는지, 로그 무결성 검증 설정 여부를 점검합니다.|
|**Secrets Manager**|시크릿이 KMS로 암호화되어 있는지 등을 확인합니다.|

---

## 🛡️ 작동 방식

1. **Security Hub 활성화**
2. **"Foundational Security Best Practices v1.0.0" 표준 선택**
3. **평가 대상 서비스 자동 감지**
4. **점검 결과(Finding) 생성**
5. **각 미비 항목에 대해 Remediation 가이드 제공**

---

## 🧾 예시 Finding 메시지

```text
[Severity: HIGH]
IAM.6 – IAM 사용자가 루트 권한을 가지고 있으며 MFA가 활성화되지 않았습니다.
Remediation: IAM 사용자에 MFA를 활성화하십시오.
```

---

## ✅ 요약

|항목|내용|
|---|---|
|이름|**Foundational Security Best Practices**|
|위치|AWS Security Hub|
|역할|핵심 AWS 서비스에 대한 보안 구성 점검을 자동화함|
|제공 방식|자동화된 보안 평가 및 Findings(알림) 제공|
|대상 서비스|IAM, S3, EC2, RDS, CloudTrail 등 주요 서비스|
|작동 주기|매일 평가 및 상태 업데이트|

---

## 🔗 관련 서비스

- **AWS Security Hub** – 보안 표준 실행 및 Findings 통합
- **AWS Config** – 리소스 상태 기록 및 평가
- **AWS Organizations + SCP** – 조직 단위 정책 제어와 병행 가능
