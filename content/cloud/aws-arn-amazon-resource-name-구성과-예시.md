---
title: AWS ARN (Amazon Resource Name) 구성과 예시
slug: "aws-arn-amazon-resource-name-구성과-예시"
category: cloud
tags: ["arn", "aws", "cloudwatch", "cross-account", "dynamodb", "iam", "lambda", "s3", "security"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.721815+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---
---
aliases:
  - ARNs
---

### 📌 구성 요소 설명:

| 요소          | 설명 |
|---------------|------|
| `arn`         | 고정 접두사 (`arn`) |
| `partition`   | AWS 파티션 (예: `aws`, `aws-cn`, `aws-us-gov`) |
| `service`     | AWS 서비스명 (예: `s3`, `ec2`, `lambda`) |
| `region`      | 리전 (예: `us-east-1`, `ap-northeast-2`) |
| `account-id`  | AWS 계정 ID (12자리 숫자) |
| `resource`    | 리소스 식별자 (종류별로 구조 상이함) |

---

## 🧪 예시

| 리소스 유형 | ARN 예시 |
|-------------|----------|
| S3 버킷 | `arn:aws:s3:::my-bucket-name` |
| Lambda 함수 | `arn:aws:lambda:us-west-2:123456789012:function:my-function` |
| IAM 사용자 | `arn:aws:iam::123456789012:user/my-user` |
| DynamoDB 테이블 | `arn:aws:dynamodb:ap-northeast-2:123456789012:table/my-table` |

---

## ✅ 사용 사례

- **IAM 정책에서 리소스 권한 제어**
- **S3 이벤트 트리거 대상 Lambda 함수 지정**
- **CloudWatch, SNS, Step Functions 등에서 대상 지정**
- **Cross-account 리소스 참조**

---

## 🧾 요약

| 항목 | 설명 |
|------|------|
| **정의** | AWS 리소스를 전역적으로 식별하기 위한 표준 문자열 |
| **형식** | `arn:partition:service:region:account-id:resource` |
| **활용처** | 권한 설정, 서비스 연동, 리소스 참조 |
| **중요성** | 보안과 접근 제어의 핵심 구성 요소 |
