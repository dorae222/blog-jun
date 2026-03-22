---
title: "SSE-KMS"
slug: "sse-kms"
category: cloud
tags: ["aws", "cloud-security", "encryption", "key-management", "kms", "s3", "server-side-encryption", "sse-kms"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:07.795510+00:00"
---

**SSE-KMS**는 **Server-Side Encryption with AWS Key Management Service**의 약자로,  
Amazon S3와 같은 AWS 서비스에서 **AWS KMS(Key Management Service)를 사용해 데이터를 암호화하는 방식**입니다.

---

## 🔐 SSE-KMS란?

> **SSE-KMS**는 AWS가 제공하는 **서버 측 암호화(Server-Side Encryption)** 방식 중 하나로,  
> **AWS KMS 키를 사용해 S3 객체 등의 데이터를 암호화**하며, 암호화 키에 대한 **접근 제어와 감사(logging)** 기능을 함께 제공하는 보안 기능입니다.

---

## 📦 SSE 종류 비교 (요약)

|암호화 방식|설명|
|---|---|
|**SSE-S3**|AWS에서 관리하는 키로 암호화 (자동 키 관리)|
|**SSE-KMS**|**KMS 키를 명시적으로 사용**하여 암호화 + 세부 권한 제어|
|**SSE-C**|고객이 직접 제공한 키로 암호화 (Client 제공 키)|

→ 이 중 **SSE-KMS는 가장 보안 통제가 강력하고 유연함**

---

## 🔧 SSE-KMS 작동 방식

1. 사용자가 객체를 업로드할 때 S3가 AWS KMS를 호출하여 **데이터 키(Data Key)**를 생성합니다.

2. 이 데이터 키로 S3 객체를 암호화하고, 데이터 키는 **AWS KMS 키(CMK 또는 AWS managed key)**로 다시 암호화되어 저장됩니다.

3. KMS는 이러한 **키 요청 및 사용 내역을 CloudTrail에 로깅**하여 감사가 가능하도록 합니다.

---

## 🔐 SSE-KMS의 주요 장점

|항목|설명|
|---|---|
|**KMS 키 관리 통합**|CMK (Customer Managed Key) 또는 AWS Managed Key 사용 가능|
|**접근 제어**|KMS 키에 대한 IAM 정책 및 키 정책으로 **세밀한 권한 설정** 가능|
|**로깅**|CloudTrail로 키 사용 내역 기록 가능 (누가 언제 사용했는지 감사)|
|**자동 암호화**|S3 Bucket Policy로 자동 암호화 강제 가능|
|**S3 버킷, RDS, EBS, DynamoDB 등과 통합**|다양한 서비스에서 공통 사용 가능|

---

## 📌 예시: S3에 SSE-KMS로 업로드

```bash
aws s3 cp myfile.txt s3://my-bucket/ \
  --sse aws:kms \
  --sse-kms-key-id arn:aws:kms:ap-northeast-2:123456789012:key/abcd-efgh-ijkl
```

- `--sse aws:kms`: SSE-KMS 방식으로 암호화 지정
    
- `--sse-kms-key-id`: 사용할 KMS 키 ARN 지정
    
---

## ⚠️ 주의사항

|주의점|설명|
|---|---|
|**KMS 요청 한도**|기본 초당 1000 요청(Region당), 초과 시 스로틀 가능|
|**추가 요금**|KMS 키 사용량에 따라 **소액의 추가 비용** 발생|
|**권한 부족 시 오류**|`AccessDenied` 또는 `KMSNotFoundException` 발생 가능|

---

## ✅ 요약

|항목|설명|
|---|---|
|정식 명칭|**Server-Side Encryption with AWS KMS (SSE-KMS)**|
|암호화 위치|**AWS 서버 측** (S3, EBS 등에서 저장 전 암호화)|
|특징|**고급 키 관리, 감사 로깅, 접근 제어**|
|대표 사용처|S3 보안 강화, RDS 암호화, KMS 기반 권한 분리 필요 환경|