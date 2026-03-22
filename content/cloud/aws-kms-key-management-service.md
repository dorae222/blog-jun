---
title: AWS KMS (Key Management Service)
slug: "aws-kms-key-management-service"
category: cloud
tags: ["aws", "aws-kms", "cloud-security", "ebs", "encryption", "key-management", "kms", "rds", "s3"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:04.105943+00:00"
---

> **NOTE:**
> - 암호화 키를 생성 및 관리하는 서비스
> - 키(Key)는 데이터를 암호화하고 복호화하는 역할을 수행함
> - AWS에서 암호화 관련 서비스 대부분은 KMS와 연동됨
> - EBS, S3, RDS 등의 AWS 서비스 데이터 암호화에 KMS 사용
> - 키 자동 교체 기능을 지원함
> - 감사 목적으로 AWS CloudTrail과 통합되어 모든 키 사용에 대한 로그 제공
> - 3가지 유형의 키 제공
>   - 고객 관리형 키(Customer managed keys)
>     - 사용자가 생성·소유·관리하는 AWS 계정 내의 KMS 키
>     - 키 정책, IAM 정책 및 권한 부여, 암호화 구성 요소 등에 대한 제어 권한을 사용자가 가짐
>   - AWS 관리형 키(AWS managed keys)
>     - AWS 서비스가 고객 계정에서 고객을 대신해 생성·관리·사용하는 KMS 키
>     - 키 정책이나 키 삭제 등의 제어 권한이 없거나 제한됨
>   - AWS 소유 키(AWS owned keys)
>     - AWS 서비스가 여러 AWS 계정에서 사용하기 위해 소유·관리하는 KMS 키 모음

- CSE-KMS