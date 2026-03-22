---
title: AWS CodePipeline
slug: "aws-codepipeline"
category: cloud
tags: ["aws", "aws-codepipeline", "ci-cd", "codebuild", "codecommit", "codedeploy", "deployment", "devops", "github"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:03.599143+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---
---
aliases:
  - CodePipeline
---
## 🧩 Quick Overview

| 항목              | 설명 |
|-------------------|------|
| **서비스명**       | AWS CodePipeline |
| **유형**           | **CI/CD(Continuous Integration / Continuous Delivery) 파이프라인 서비스** |
| **목적**           | 애플리케이션 및 인프라 코드를 **자동으로 빌드, 테스트, 배포**하여  
                     **소프트웨어 출시 속도와 안정성**을 높이는 서비스

> ⚙️ **CodePipeline**은 **코드 커밋 → 빌드 → 테스트 → 배포** 단계를 자동화하여  
> 반복 가능한 CI/CD 워크플로우를 손쉽게 구성하도록 지원합니다.

---

## 🔧 동작 방식

1. **소스 감지(Source Stage)**  
   - CodeCommit, GitHub, Bitbucket 등에서 코드 변경 감지
2. **빌드(Build Stage)**  
   - AWS CodeBuild, Jenkins 등으로 애플리케이션 빌드
3. **테스트(Test Stage)**  
   - 단위/통합 테스트 실행, 정적 분석 수행 가능
4. **배포(Deploy Stage)**  
   - CodeDeploy, CloudFormation, ECS, Lambda 등으로 자동 배포
5. **승인(Manual Approval, Optional)**  
   - 운영 환경 배포 전 수동 검증 단계를 추가 가능

---

## 🧪 예시 아키텍처

```plaintext
CodeCommit → CodePipeline → CodeBuild → CodeDeploy → EC2/ECS/Lambda
````

---

## ✅ 장점

- **풀매니지드**: 서버 관리 없이 CI/CD 실행
    
- **자동화**: 코드 변경 시 즉시 빌드/테스트/배포 진행
    
- **유연성**: AWS 및 서드파티(예: GitHub, Jenkins) 통합 가능
    
- **신뢰성 향상**: 표준화된 파이프라인으로 인적 실수 감소
    
- **배포 전략 지원**: Blue/Green, Canary, Rolling 등 다양한 배포 방식 적용
    

---

## ⚠️ 유의사항

- **파이프라인 복잡도**: 대규모 프로젝트는 단계 관리 및 IAM 권한 설계 필요
    
- **실행 제한**: 각 단계 동시 실행 수 제한 존재
    
- **외부 서비스 연동 시 권한 관리 중요**: GitHub, Jenkins 등 연계 시 OIDC/IAM 역할 필수
    

---

## 🧾 요약

|항목|설명|
|---|---|
|**정의**|AWS에서 제공하는 **풀매니지드 CI/CD 파이프라인 서비스**|
|**기능**|코드 변경 감지, 빌드, 테스트, 배포 자동화|
|**장점**|무서버 운영, 유연한 통합, 배포 속도 향상|
|**활용 사례**|웹/모바일 앱 배포, 서버리스·컨테이너 워크로드 CI/CD|