---
title: AWS SDK (Software Development Kit)
slug: "aws-sdk-software-development-kit"
category: cloud
tags: ["aws", "aws-sdk", "boto3", "cloud", "ec2", "lambda", "python", "s3", "sdk"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:04.314368+00:00"
---

---
aliases:
  - Software Development Kit
  - AWS Software Development Kit
---
## 🧩 Quick Overview

| 항목        | 설명                                                                   |
| --------- | -------------------------------------------------------------------- |
| **이름**    | AWS SDK (Software Development Kit)                                   |
| **기능**    | 프로그래밍 언어에서 AWS 서비스에 직접 접근하고 제어할 수 있는 라이브러리 모음                        |
| **지원 언어** | Python (`boto3`), JavaScript/TypeScript, Java, Go, C++, .NET, Ruby 등 |
| **주요 대상** | 개발자, 자동화 시스템, 서버리스 애플리케이션                                            |

> 🧩 **목적**: AWS 리소스를 코드에서 **직접 생성/제어/관리**하기 위한 API 클라이언트 도구

---

## 🧬 주요 특징

| 항목 | 설명 |
|------|------|
| **직접 제어** | 코드로 S3 버킷 생성, EC2 인스턴스 시작, Lambda 실행 등 가능 |
| **API 추상화** | 복잡한 REST API 호출을 간단한 함수 호출로 변환 |
| **인증 통합** | IAM 자격 증명(AWS credentials) 자동 관리 |
| **비동기 및 고급 기능 지원** | 일부 SDK는 Promise, async/await 등 현대적 언어 특성 반영 |

---

## ✅ 사용 예시

### 📘 Python (boto3)

```python
import boto3

s3 = boto3.client('s3')
s3.upload_file('local.txt', 'my-bucket', 'uploaded.txt')
```