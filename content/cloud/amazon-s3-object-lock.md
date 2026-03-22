---
title: Amazon S3 Object Lock
slug: "amazon-s3-object-lock"
category: cloud
tags: ["amazon-s3", "aws", "cloud-security", "compliance", "data-protection", "legal-hold", "ransomware", "retention", "s3-object-lock"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:07.538390+00:00"
---

**Amazon S3 Object Lock**은 S3 버킷에 저장된 **객체(Object)에 대해 삭제나 덮어쓰기를 방지할 수 있는 기능**으로, **데이터 무결성 보장**, **규정 준수**, **랜섬웨어 방어** 등 다양한 보안 목적에 활용됩니다.

---

## 🔐 Amazon S3 Object Lock이란?

> **S3 Object Lock**은 객체를 **WORM(Write Once, Read Many)** 방식으로 저장하여,
> 한 번 저장된 데이터를 **일정 기간 동안 수정하거나 삭제하지 못하도록 잠그는 기능**입니다.

---

## 🎯 사용 목적

|용도|설명|
|---|---|
|**법적/규제 준수**|금융, 의료, 공공기관 등에서 법적으로 요구되는 데이터 보존 기간 준수|
|**랜섬웨어 방지**|악성 코드나 내부 사용자에 의한 의도치 않은 삭제 방지|
|**백업 보호**|백업된 데이터를 지정 기간 동안 변경 불가 상태로 유지|

---

## 🧱 주요 구성 요소

|구성 요소|설명|
|---|---|
|**Retention Mode**|객체 잠금 모드 (`Governance` 또는 `Compliance`)|
|**Retention Period**|객체를 잠금 상태로 유지할 기간 (예: 30일, 1년 등)|
|**Legal Hold**|특정 개체에 대해 수동으로 무기한 잠금 설정|

---

### 🔐 잠금 모드 유형

|모드|설명|
|---|---|
|**Governance**|관리자 권한이 있으면 **잠금 해제 가능** (감사 로그 기록됨)|
|**Compliance**|**절대 해제 불가**, 기간이 끝나기 전에는 **삭제나 덮어쓰기 불가**|

---

## 🏗️ S3 Object Lock 활성화 절차

1. S3 버킷 생성 시 **Object Lock 활성화** 옵션 선택  
    → 기존 버킷에는 설정 불가, 반드시 **생성 시점에만 가능**
    
2. 각 객체 업로드 시 Retention 설정 지정
    
3. 필요하면 **Legal Hold** 추가
	- 객체 버전을 덮어쓰거나 삭제할 수 없도록 하는 기능
	- 객체를 수정해야 하는 사용자의 IAM 정책에 `s3 PutobjectLegalHold` 권한을 추가하면 해당 사용자는 객체를 수정, 삭제 가능

---

## ✅ 예시 시나리오

> 회사가 백업 데이터를 Amazon S3에 저장하고 있으며, 최소 90일 동안 **삭제되거나 덮어쓰기되지 않도록** 보호해야 함  
> → 이 경우, S3 Object Lock에서 `Governance` 모드로 90일 retention 설정

---

## 📌 요약

|항목|설명|
|---|---|
|정식 이름|**Amazon S3 Object Lock**|
|기능|객체에 대한 삭제/수정 제한 (WORM 저장)|
|사용 목적|규제 준수, 백업 보호, 보안 강화|
|잠금 모드|Governance / Compliance|
|필수 조건|**버킷 생성 시점에 활성화 필요**|