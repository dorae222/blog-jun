---
title: AWS CodeCommit
slug: "aws-codecommit"
category: cloud
tags: ["aws", "cicd", "codecommit", "devops", "git", "iam", "infrastructure-as-code", "security"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:03.577094+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---

## 한 줄 정의

> **AWS CodeCommit은 소스 코드를 안전하게 저장·관리·버전 관리할 수 있는 AWS의 관리형 Git 리포지토리 서비스이다.**

---

## 무엇을 해결해 주나?

- Git 서버 직접 운영 불필요 ❌
- 패치, 백업, 확장 관리 불필요 ❌
- IAM 기반 접근 제어 가능 ⭕
- AWS 서비스와 네이티브 통합 가능 ⭕

---

## 핵심 특징

### 1️⃣ Git 완전 호환

- 표준 Git 명령어 사용

```bash
git clone
git push
git pull
```

- GitHub/GitLab과 동일한 워크플로

---

### 2️⃣ 완전관리형(Managed)

- 서버 관리 불필요
- 자동 확장
- 고가용성

---

### 3️⃣ 강력한 보안

- IAM 기반 인증/권한
- VPC 엔드포인트 지원
- 저장·전송 중 암호화

---

### 4️⃣ AWS DevOps 통합

- CodeBuild
- CodePipeline
- CodeDeploy
- Lambda, ECS, EKS

---

## 인증 방식

|방식|설명|
|---|---|
|HTTPS + IAM|일반적|
|SSH + IAM|SSH 키 기반|
|Git 자격 증명|IAM 사용자 매핑|

---

## 사용 예시

- 애플리케이션 소스 코드
- ETL 스크립트 (Glue, Spark)
- IaC (CloudFormation, Terraform)
- ML 파이프라인 코드

---

## CodeCommit vs GitHub

|항목|CodeCommit|GitHub|
|---|---|---|
|퍼블릭 리포지토리|❌|✅|
|프라이빗 리포지토리|✅|✅|
|IAM 통합|**강력**|제한|
|AWS 통합|**네이티브**|외부|

---

## 언제 CodeCommit을 쓰나?

- 코드가 AWS 내부에만 있어야 할 때
- IAM으로 접근 제어가 필요할 때
- AWS 네이티브 CI/CD를 구성할 때

---

## 핵심 포인트

- “AWS 관리형 Git” → CodeCommit
- “프라이빗 리포지토리” → CodeCommit
- “IAM 기반 접근 제어” → CodeCommit
