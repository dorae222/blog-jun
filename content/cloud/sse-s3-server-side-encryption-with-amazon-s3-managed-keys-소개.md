---
title: "SSE-S3 (Server-Side Encryption with Amazon S3-Managed Keys) 소개"
slug: "sse-s3-server-side-encryption-with-amazon-s3-managed-keys-소개"
category: cloud
tags: ["aes-256", "amazon-s3", "aws", "encryption", "s3-encryption", "server-side-encryption", "sse-kms", "sse-s3"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:07.806833+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A


---

---
aliases:
  - SSE-S3
---
**SSE-S3**는 **Server-Side Encryption with Amazon S3-Managed Keys**의 약자로,
Amazon S3에 객체를 저장할 때 **자동으로 암호화**해 주는 가장 간단한 **서버 측 암호화 방식**입니다.

---

## 🔐 SSE-S3란?

> **SSE-S3 (Server-Side Encryption - S3)**는 Amazon S3가 자체적으로 관리하는 키를 사용해
> S3 객체를 저장할 때 **자동으로 암호화하고 복호화하는 기능**입니다.

고객은 별도로 키를 관리할 필요가 없으며, S3가 **AES-256 알고리즘으로 데이터를 암호화**합니다.

---

## 🔧 작동 방식

1. 사용자가 객체를 S3에 업로드
    
2. S3가 **자동으로 AES-256으로 암호화**
    
3. 저장 후 요청 시 자동으로 복호화하여 제공
    

✔️ 암호화와 복호화 과정은 **완전히 투명하게 처리되며**, 애플리케이션에서 별도 작업이 필요 없습니다.

---

## ✅ SSE-S3의 특징

|항목|내용|
|---|---|
|**암호화 주체**|S3 자체 (AWS에서 완전 관리)|
|**키 관리**|사용자가 키를 직접 관리할 필요 없음|
|**암호화 알고리즘**|AES-256|
|**설정 방법**|버킷 수준 또는 객체 업로드 시 설정 가능|
|**추가 비용**|없음 (SSE-KMS와 달리 KMS 요금 없음)|

---

## 🆚 SSE-S3 vs SSE-KMS vs SSE-C

|항목|SSE-S3|SSE-KMS|SSE-C|
|---|---|---|---|
|**키 관리 주체**|S3 자체|AWS KMS|고객|
|**접근 제어 세밀성**|낮음|높음 (IAM+KMS 정책)|사용자가 직접 제어|
|**CloudTrail 로깅**|❌ 불가|✅ 가능|❌ 불가|
|**복잡도**|가장 간단함|중간|가장 복잡함|
|**추가 비용**|❌ 없음|✅ KMS 사용 비용|❌ 없음|

---

## 📝 설정 방법 예 (CLI)

```bash
aws s3 cp file.txt s3://my-bucket/ --sse AES256
```

또는 버킷 기본 암호화 설정에서 **"AES-256 (SSE-S3)"**를 선택할 수 있습니다.

---

## ✅ 요약

|항목|내용|
|---|---|
|명칭|**SSE-S3 (Server-Side Encryption with S3-managed keys)**|
|암호화 주체|**Amazon S3 자체에서 키 관리**|
|알고리즘|**AES-256**|
|장점|설정 간단, 자동 암호화, 비용 없음|
|사용 목적|민감한 데이터 보호, 규정 준수(예: GDPR, HIPAA 등)|