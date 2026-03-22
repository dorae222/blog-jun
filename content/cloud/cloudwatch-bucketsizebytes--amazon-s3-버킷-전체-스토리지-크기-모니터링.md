---
title: CloudWatch BucketSizeBytes — Amazon S3 버킷 전체 스토리지 크기 모니터링
slug: "cloudwatch-bucketsizebytes--amazon-s3-버킷-전체-스토리지-크기-모니터링"
category: cloud
tags: ["amazon-s3", "aws", "aws-cli", "bucket-size", "cloudwatch", "cost-optimization", "monitoring", "s3-metrics", "storage"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:04.893633+00:00"
---

---
Category: Cloud
Subcategory: 11.AWS
Quality grade: A


---
---
aliases:
  - CloudWatch BucketSizeBytes
---
`Amazon CloudWatch`의 **`BucketSizeBytes`**는 **Amazon S3 버킷의 총 스토리지 크기를 바이트 단위로 나타내는 메트릭**입니다.  
이 메트릭은 S3 버킷의 **모든 객체 크기의 총합**을 **CloudWatch에 주기적으로 수집하여 표시**합니다.

---

## 📦 `BucketSizeBytes`란?

|항목|설명|
|---|---|
|이름|`BucketSizeBytes`|
|서비스|Amazon CloudWatch (대상: S3)|
|의미|S3 버킷 내 객체들의 **전체 크기 (bytes 단위)**|
|사용 목적|스토리지 사용량 모니터링, 비용 예측, 알림 설정 등|
|업데이트 빈도|**하루 1회** (통상 **UTC 기준 자정**에 측정됨)|

---

## 🧭 주요 차원 (Dimensions)

|차원 이름|설명|
|---|---|
|**BucketName**|메트릭이 속한 S3 버킷 이름|
|**StorageType**|다음 중 하나로 세분화됨:– `StandardStorage`– `StandardIAStorage`– `GlacierStorage`– `DeepArchiveStorage` 등|
|**Region**|버킷이 존재하는 AWS 리전|

> 예: `BucketSizeBytes` with `StorageType=StandardStorage`, `BucketName=my-bucket`, `Region=us-east-1`

---

## 📊 사용 예

CloudWatch 콘솔 또는 AWS CLI/SDK에서 다음과 같이 `BucketSizeBytes`를 확인할 수 있습니다:

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/S3 \
  --metric-name BucketSizeBytes \
  --dimensions Name=BucketName,Value=my-bucket Name=StorageType,Value=StandardStorage \
  --start-time 2025-07-01T00:00:00Z \
  --end-time 2025-07-02T00:00:00Z \
  --period 86400 \
  --statistics Average
```

---

## 🔔 알림 설정 활용 예시

- S3 버킷 크기가 **1TB 이상**일 경우 알림 전송
    
- 특정 스토리지 유형(`GlacierStorage`)에 크기 급증 감지
    

---

## ⚠️ 주의사항

|항목|설명|
|---|---|
|**실시간 아님**|`BucketSizeBytes`는 **1일 1회** 수집 → **실시간 크기 확인에는 적합하지 않음**|
|**무료 아님**|S3의 **Storage Metrics는 기본적으로 유료 CloudWatch 메트릭** (요금 발생 가능)|

---

## ✅ 요약

|항목|설명|
|---|---|
|메트릭 이름|`BucketSizeBytes`|
|대상 서비스|Amazon S3 (CloudWatch에서 조회)|
|의미|S3 버킷 내 모든 객체의 전체 크기 (바이트 단위)|
|측정 주기|하루 1회 (비실시간)|
|차원|`BucketName`, `StorageType`, `Region`|
|활용|비용 예측, 스토리지 증가 감지, 알림 설정 등|
