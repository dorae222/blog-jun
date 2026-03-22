---
title: Original Access ID (원본 액세스 ID)
slug: "original-access-id-원본-액세스-id"
category: cloud
tags: ["access-tracking", "assumerole", "audit", "aws", "cloudtrail", "iam", "s3", "security", "sts"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:07.228091+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A


---
---
aliases:
  - 원본 액세스 ID
  - OAI
---
**Original Access ID**는 AWS 공식 서비스 용어로서 **정식 정의된 단일 기능 이름은 아닙니다**. 그러나 통상적으로 다음 두 가지 문맥에서 쓰이는 용어입니다:

---

## 1️⃣ **AWS CloudTrail 로그에서의 "Original Access ID"**

AWS CloudTrail은 API 호출을 기록하는 감사 로그 서비스이며, 로그 내의 **"originalAccessId"** 또는 유사 항목은 다음을 의미할 수 있습니다:

> **역할을 전환(Assume Role)한 경우, 원래 요청을 시작한 사용자(Principal)의 ID**를 가리킵니다.

### 예시:

- 어떤 IAM 역할을 `AssumeRole`로 사용해 액세스한 경우,
    로그에는 실제 API 호출을 수행한 **역할**의 ARN과
    그 역할을 **처음 호출한 사용자 또는 서비스 계정의 ID (Original Access ID)**가 함께 기록됩니다.

|필드|의미|
|---|---|
|**userIdentity.arn**|API 요청 시 사용된 현재 역할 ARN|
|**userIdentity.sessionContext.sessionIssuer.arn**|원래의 IAM 역할 ARN|
|**originalAccessId (또는 sourceIdentity)**|**역할을 최초로 호출한 사용자의 고유 식별자**|

➡️ 이 정보를 통해 "누가 실제로 무슨 일을 했는가?"를 추적할 수 있습니다.

---

## 2️⃣ **S3 / IAM 관련 감사 또는 권한 위임 추적 시**

"Original Access ID"라는 용어가 **S3 ACL 변경**이나 **IAM 권한 위임** 맥락에서 등장하면, 다음을 의미할 수 있습니다:

> 요청이 **중간 서비스(예: Lambda, STS, ECS Task Role 등)**를 통해 오더라도,
> **최초의 주체(사용자 또는 서비스)의 ID**를 추적할 수 있도록 제공되는 **감사 정보 필드**입니다.

---

## ✅ 요약

|항목|설명|
|---|---|
|용어|**Original Access ID**|
|공식 용어 여부|❌ AWS의 공식 서비스 명칭은 아님 (CloudTrail 내에서는 해당 의미로 사용됨)|
|의미 1|**AssumeRole 요청의 원래 주체 ID (CloudTrail 로그)**|
|의미 2|**IAM 역할 위임 시 실제 시작한 사용자나 서비스의 식별자**|
|사용 맥락|CloudTrail, IAM 역할 추적, 보안 감사, 권한 위임 해석 등|

---

## 📚 관련 AWS 문서

- [AWS CloudTrail `userIdentity` 구조](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-event-reference-user-identity.html)

- [AssumeRole과 `sourceIdentity`](https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRole.html)