---
title: Comprehend ImportModel API — 계정 간 커스텀 모델 복사(Import)
slug: "comprehend-importmodel-api--계정-간-커스텀-모델-복사import"
category: cloud
tags: ["amazon-comprehend", "aws", "comprehend", "exportmodel", "iam", "importmodel", "kms", "model-migration", "s3"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:04.954326+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A


---
---
aliases:
  - Comprehend ImportModel API
  - Comprehend ImportModel
---
## 🧩 Quick Overview

| 항목                | 설명 |
|---------------------|------|
| **API 이름**         | `ImportModel` |
| **소속 서비스**      | Amazon Comprehend |
| **기능**             | 다른 AWS 계정 또는 외부에서 학습된 **커스텀 모델을 현재 계정으로 복사(import)**  
| **용도**             | 계정 간 모델 공유, 재사용, 마이그레이션

> 📦 `ImportModel` API는 Amazon Comprehend의 **커스텀 엔티티 인식(Custom NER)** 또는 **문서 분류 모델(Custom Classifier)**을  
> **다른 AWS 계정에서 복사하여 사용할 수 있도록 하는 API 작업**입니다.

---

## 🔧 작동 방식

1. **계정 A**: `ExportModel` API를 호출해 모델을 Amazon S3에 내보냄
2. **공유 설정**: S3 객체 + KMS 키 + Comprehend 모델 리소스를 계정 B와 공유
3. **계정 B**: `ImportModel` API를 호출해 해당 모델을 자신의 Comprehend 환경에 가져옴

---

## 🧠 주요 파라미터

| 파라미터             | 설명 |
|----------------------|------|
| `SourceModelArn`     | 복사하려는 모델의 ARN (계정 A의 모델) |
| `ModelName`          | 가져온 후 사용할 새 모델 이름 |
| `DataAccessRoleArn`  | S3 및 KMS 키에 접근할 수 있는 IAM 역할 |
| `ModelKmsKeyId`      | 암호화된 모델에 접근하기 위한 KMS 키 (선택)

---

## ✅ 활용 예

```json
POST /import-model
{
  "SourceModelArn": "arn:aws:comprehend:us-east-1:111111111111:document-classifier/my-model",
  "ModelName": "imported-classifier",
  "DataAccessRoleArn": "arn:aws:iam::222222222222:role/comprehend-import-role"
}
````

---

## ✅ 장점

|항목|설명|
|---|---|
|🔁 **모델 재사용**|이미 학습한 모델을 다른 계정/리전에서 활용 가능|
|🔐 **보안 기반 공유**|IAM, KMS, S3 권한을 통해 안전하게 복사|
|🌍 **멀티 계정/조직 환경 지원**|조직 단위 ML 거버넌스에 유용|

---

## ⚠️ 유의사항

|항목|설명|
|---|---|
|**ExportModel 선행 필요**|먼저 내보내야 import 가능|
|**S3 권한 필수**|계정 B에서 S3에 접근 가능해야 함|
|**KMS 공유 필요**|암호화된 모델이라면 KMS 키도 공유해야 함|
|**Import 시간 소요**|몇 분 단위의 모델 복사 및 배포 시간 존재|

---

## 🧾 요약

|항목|설명|
|---|---|
|**정의**|Comprehend에서 다른 계정의 커스텀 모델을 가져오는 API|
|**전제 조건**|Export된 모델 + 권한 있는 S3/KMS|
|**활용 목적**|계정 간 모델 공유, 거버넌스, 멀티 리전 운영|
