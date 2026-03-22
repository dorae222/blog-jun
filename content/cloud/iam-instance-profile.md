---
title: IAM Instance Profile
slug: "iam-instance-profile"
category: cloud
tags: ["aws", "dynamodb", "ec2", "iam", "iam-role", "instance-profile", "s3", "security", "temporary-credentials"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:08.312179+00:00"
---

AWS의 **IAM Instance Profile**이라는 **IAM 개념**을 설명합니다.

## 🛠 **IAM Instance Profile이란?**

- **정의**:  
    EC2 인스턴스가 IAM 역할을 사용할 수 있도록 하는 **중간 매개체** 역할을 하는 IAM 리소스입니다.
    
- **왜 필요할까?**  
    EC2 인스턴스는 직접 IAM 역할을 붙일 수 없기 때문에, IAM 역할을 **Instance Profile**에 담아놓고, 그 **Instance Profile을 EC2에 연결**하는 방식으로 역할을 할당합니다.
    
---

## 🔑 **구성 이해하기**

|개념|설명|
|---|---|
|**IAM Role**|EC2 인스턴스가 갖게 될 권한을 정의한 역할|
|**Instance Profile**|EC2가 실제로 그 역할을 사용할 수 있도록 하는 컨테이너 (IAM에서 생성)|
|**EC2 콘솔(UI)**|인스턴스를 생성하거나 수정할 때 Instance Profile을 선택하는 화면|

---

## ✨ **흔한 오해**

- ❌ “프로필 = EC2 콘솔의 설정 페이지”
    
- ✅ “프로필 = IAM Instance Profile(역할을 연결하는 컨테이너)”
    
즉, 실제로는 IAM에서 Instance Profile을 만들어두고, EC2 인스턴스를 생성하거나 편집할 때 그 프로필을 연결하는 것입니다.

---

## 📖 **실제 동작 흐름**

1. IAM에서 **역할(Role)** 생성 (예: S3FullAccessRole)
    
2. IAM에서 **인스턴스 프로필(Instance Profile)** 생성 후, 해당 역할을 할당
    
3. EC2 인스턴스를 생성하거나 기존 인스턴스를 수정할 때  
    **IAM 역할(Instance Profile)** 항목에서 선택하여 연결
    
👉 이렇게 하면, EC2 인스턴스 내부에서 실행되는 애플리케이션이 **임시 보안 자격 증명**을 통해 S3, DynamoDB 등 지정된 리소스에 접근할 수 있게 됩니다.

---

## ✅ **정리**

문장에서 말하는 ‘프로필’은 EC2 콘솔의 설정 페이지가 아니라 **IAM Instance Profile**을 의미합니다. EC2 콘솔은 단순히 그 프로필을 선택하는 UI를 제공할 뿐이며, 실제 프로필 리소스는 IAM에서 생성·관리됩니다.

추가로 Instance Profile 생성 절차나 화면 캡처 예시가 필요하시면 말씀해 주세요! ✨🖥️