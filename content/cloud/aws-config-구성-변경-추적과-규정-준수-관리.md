---
title: "AWS Config: 구성 변경 추적과 규정 준수 관리"
slug: "aws-config-구성-변경-추적과-규정-준수-관리"
category: cloud
tags: ["aws", "aws-config", "cloud", "cloud-security", "cloudtrail", "compliance", "lambda", "sns"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:03.629099+00:00"
---

**AWS Config**는 AWS 리소스의 **구성 변경 이력 추적**, **상태 평가**, **규정 준수 검사**를 제공하는 **완전관리형 감사 및 컴플라이언스 서비스**입니다. 쉽게 말해, **"누가 언제 어떤 리소스를 만들었고 바꿨는지"**, 그리고 **"지금 리소스들이 보안 정책을 잘 지키고 있는지"**를 **자동으로 기록하고 분석**해 줍니다.

---

## 🧩 핵심 기능 요약

|기능|설명|
|---|---|
|✅ **구성 변경 이력 추적**|EC2, S3, IAM, VPC 등 리소스가 생성/수정/삭제될 때 상태를 기록|
|✅ **구성 스냅샷 저장**|주기적으로 전체 리소스 상태를 저장해 시점 간 비교 가능|
|✅ **규정 준수 검사 (Compliance)**|사전 정의된 또는 사용자 지정된 규칙을 통해 리소스 상태 평가|
|✅ **CloudTrail 통합**|변경 작업의 **주체(사용자, 서비스, API 호출 등)** 확인 가능|
|✅ **SNS 알림, Lambda 연동**|변경 사항에 따라 자동 알림 또는 자동화 처리 가능|

---

## 🛠️ 사용 예시

1. S3 버킷이 **퍼블릭으로 설정되었는지 감지**

2. EC2 인스턴스가 **허용되지 않은 타입(m5.large 외)으로 생성됐는지 검사**

3. VPC 보안 그룹이 **특정 포트를 열어두었는지 확인**

4. **IAM 정책 변경 내역 추적** (누가 언제 어떤 권한을 부여했는가?)

---

## 🔍 리소스 변경 추적 예시

```text
[Before]
EC2 Instance: t2.micro
Security Group: Allow only port 22

[After]
EC2 Instance: t2.large
Security Group: Allow port 22, 80

변경 시각: 2025-07-01 11:15
변경자: Alice (via AWS Console)
```

이런 상세 내역을 Config가 **자동으로 기록**해 줍니다.

---

## 📋 규칙 기반 평가 (Config Rules)

Config는 **사전 정의된 규칙 (Managed Rules)** 또는 **사용자 정의 규칙 (Custom Lambda)**을 통해
리소스의 **규정 준수 상태를 평가**할 수 있습니다.

|규칙 이름|설명|
|---|---|
|`s3-bucket-public-read-prohibited`|S3 버킷이 공개적으로 읽히지 않도록 제한|
|`ec2-instance-type-check`|특정 타입의 EC2 인스턴스만 허용|
|`encrypted-volumes`|EBS 볼륨이 암호화되었는지 확인|

✅ 평가 결과는 `COMPLIANT` / `NON_COMPLIANT`로 나뉘며,
AWS Config 대시보드에서 시각적으로 확인할 수 있습니다.

---

## 🧠 왜 중요한가?

|항목|이유|
|---|---|
|📜 **감사 추적(Auditing)**|규제 기관이나 보안 감사 대응을 위해 리소스 변경 내역을 기록해야 함|
|🔐 **보안 위반 탐지**|보안 정책에 맞지 않는 리소스를 자동으로 탐지 가능|
|🛡️ **자동 복구 가능**|Config와 Lambda를 연동하면 위반 시 자동 수정도 가능|
|⚖️ **컴플라이언스 준수**|PCI-DSS, HIPAA, SOC 등 규정 요구사항 대응에 유리|

---

## 🧬 AWS Config vs CloudTrail 차이

|항목|AWS Config|AWS CloudTrail|
|---|---|---|
|추적 대상|리소스 상태 및 변경 이력|API 호출 및 사용자 활동|
|추적 예시|S3 퍼블릭 설정 여부, IAM 권한 변경|누가 콘솔에서 S3를 만들었는가|
|데이터 유형|리소스 Snapshot 및 비교|이벤트 로그 중심|
|목적|**보안 정책 준수, 상태 평가**|**사용자 활동 기록** 중심|

→ 둘은 보완 관계이며 **동시에 사용하는 것이 가장 효과적**입니다.

---

## ✅ 요약

|항목|설명|
|---|---|
|서비스 이름|**AWS Config**|
|핵심 기능|리소스 구성 변경 추적, 규정 준수 상태 평가|
|대표 기능|스냅샷 기록, 규칙 기반 평가, 감사 추적|
|주요 사용 사례|S3 퍼블릭 감지, 리전 제한, 암호화 여부 평가|
|통합 서비스|AWS CloudTrail, SNS, Lambda, AWS Organizations 등|
|요금|활성 리소스 수, 규칙 수, 평가 횟수 기준 과금|