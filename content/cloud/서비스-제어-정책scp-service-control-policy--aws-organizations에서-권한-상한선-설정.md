---
title: "서비스 제어 정책(SCP, Service Control Policy) — AWS Organizations에서 권한 상한선 설정"
slug: "서비스-제어-정책scp-service-control-policy--aws-organizations에서-권한-상한선-설정"
category: cloud
tags: ["aws", "aws-organizations", "cloud-security", "cloudwatch", "ec2", "governance", "iam", "s3", "scp"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:07.837421+00:00"
---

**서비스 제어 정책(SCP, Service Control Policy)**는 **AWS Organizations에서 계정 또는 조직 단위(OU)에 적용되는 권한 상한선 정책**입니다. 즉, 해당 계정이 **어떤 AWS 서비스와 작업을 사용할 수 있는지 중앙에서 제어하는 정책 도구**입니다.

---

## 🔐 서비스 제어 정책(SCP)란?

> **SCP는 AWS Organizations의 계정 또는 OU에 적용되어, 해당 계정의 IAM 사용자나 역할이 가질 수 있는 _최대 권한(허용 범위)_을 정의하는 정책입니다.**

> ⚠️ **IAM 정책이 허용하더라도, SCP가 차단하면 해당 작업을 수행할 수 없습니다.**

> ⚠️ SCP 자체로는 권한을 부여하지 않습니다 — 예를 들어 CloudWatch 데이터 접근 권한과 같은 실제 권한은 IAM 정책으로 부여되어야 하며, SCP는 그 권한을 제한하는 역할만 합니다.

---

## 📌 핵심 특징

|항목|설명|
|---|---|
|**정책 유형**|IAM과 유사한 JSON 기반 정책|
|**적용 대상**|OU(조직 단위), 개별 계정|
|**권한 상한선 제어**|**해당 계정에서 절대 사용 불가능한 서비스/작업을 지정 가능**|
|**루트 계정 포함**|루트 사용자에게도 적용 가능 (강력한 통제력)|
|**IAM과 병행 작동**|실제 권한 = IAM 정책과 SCP의 허용 범위의 교집합|

---

## 🧠 IAM vs SCP 비교

|항목|IAM 정책|SCP|
|---|---|---|
|역할|**실제 권한 부여**|**최대 허용 범위 제한**|
|위치|IAM 사용자, 그룹, 역할에 연결|AWS Organizations의 계정 또는 OU에 연결|
|차단 방식|권한이 부여되지 않으면 사용 불가|SCP에서 허용되지 않으면 **절대 사용 불가**|
|예시|EC2 인스턴스 시작 권한 부여|모든 EC2 인스턴스 삭제 차단|

---

## 🛠️ 예시 정책

### ✅ 예: 모든 EC2 인스턴스 종료 금지

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Deny",
      "Action": "ec2:TerminateInstances",
      "Resource": "*"
    }
  ]
}
```

### ✅ 예: S3 및 CloudWatch만 허용 (모든 다른 작업은 차단)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:*",
        "cloudwatch:*"
      ],
      "Resource": "*"
    }
  ]
}
```

> 이 정책을 OU에 연결하면, 해당 OU 내 계정은 S3와 CloudWatch 외에는 **아무것도 사용할 수 없습니다.**

---

## 🚨 SCP 적용 시 주의사항

- SCP는 **IAM 권한을 직접 부여하지는 않지만**, **IAM에서 허용된 작업조차도 SCP에 의해 제한될 수 있습니다.**
- SCP는 Allow와 Deny를 모두 사용할 수 있으나, Deny는 강력한 차단을 의미하므로 신중히 사용해야 합니다.
- SCP를 잘못 설정하면 **계정 전체가 기능을 상실할 수도 있으므로** 반드시 테스트 환경에서 검증하세요.

---

## ✅ 요약

|항목|내용|
|---|---|
|정식 명칭|**Service Control Policy (SCP)**|
|적용 대상|AWS Organizations의 계정 또는 OU|
|역할|**IAM 권한의 상한선 정의 (허용 범위 제한)**|
|주 용도|보안 강화, 거버넌스, 규정 준수, 리소스 제한|
|IAM과 관계|IAM 정책과 SCP의 교집합만 실제로 사용 가능|
