---
title: Assume Role (IAM 역할 임시 위임)
slug: "assume-role-iam-역할-임시-위임"
category: cloud
tags: ["assume-role", "aws", "cross-account", "ec2", "iam", "lambda", "least-privilege", "security", "temporary-credentials"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:06.963930+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A


---
---
aliases:
  - Assume Role
---
**정의**

- **IAM 역할(ROLE)을 임시로 받아서 그 역할에 부여된 권한을 사용하는 것**을 말합니다.

- AWS 계정 안에서 **다른 역할을 위임받아** 작업하거나, **다른 계정 간 접근**을 허용할 때 사용합니다.

---

## 🛠 **동작 원리**

1. **역할(ROLE)** 은 IAM 사용자나 서비스가 직접 로그인하는 계정과 별개로, 권한 정책이 붙어 있고, **누가 맡을 수 있는지(신뢰 정책)** 가 정의돼 있습니다.

2. 사용자가 `AssumeRole` API 또는 콘솔 전환을 통해 역할을 맡으면, AWS는 **임시 보안 자격 증명(Temporary Security Credentials)** 을 발급합니다.  
   → 이 자격 증명으로만 그 역할에 허용된 작업을 수행할 수 있습니다.

---

## ✨ **주요 특징**

|항목|내용|
|---|---|
|**보안**|장기 액세스 키 대신, 짧은 만료시간의 임시 자격 증명을 사용|
|**최소 권한 원칙**|필요한 작업 범위의 Role 권한만 임시로 부여 가능|
|**교차 계정 접근**|다른 AWS 계정 리소스에 접근할 때 자주 사용|
|**서비스 통합**|EC2, Lambda 등 리소스에 역할을 부여해 자동 Assume Role 가능|

---

## 🔑 **구성 요소**

1. **신뢰 정책(Trust Policy)**
    
    - 어떤 주체(Principal)가 이 역할을 맡을 수 있는지 정의합니다.
        
2. **권한 정책(Permission Policy)**
    
    - 역할을 맡은 주체가 어떤 AWS 작업을 수행할 수 있는지 정의합니다.
        
---

## 📖 **예시 시나리오**

✅ **교차 계정 접근**

- 계정 A에 있는 S3 버킷에 계정 B 사용자가 접근해야 할 때, 계정 A에서 신뢰 정책을 구성한 Role을 만들고, 계정 B 사용자가 AssumeRole을 호출하여 접근합니다.
    

✅ **운영/배포 엔지니어 시나리오**

- 일반 사용자 계정은 최소 권한만 주고, 특정 배포 작업이 필요할 때만 CloudFormation 전용 Role로 **Assume Role**하여 배포합니다.
    
---

## ✅ **시험 대비 포인트**

- **AssumeRole을 사용하면?**
    
    - ➡️ 임시 자격 증명을 발급받아 최소 권한으로 작업이 가능합니다.
        
- **Root 사용자로 직접 접근?**
    
    - ❌ 잘못된 방식입니다. AssumeRole 사용 권장.
        
- **교차 계정 접근 시?**
    
    - IAM 역할 + AssumeRole을 조합해서 사용합니다.
        
---

## 💡 **정리**

> **IAM Assume Role = 다른 역할을 일시적으로 맡아, 그 역할의 권한으로 작업하기 위해 사용하는 메커니즘.**
> 
> ✅ 최소 권한 원칙 준수  
> ✅ 임시 보안 자격 증명 사용  
> ✅ 교차 계정 및 서비스 권한 위임에 필수적