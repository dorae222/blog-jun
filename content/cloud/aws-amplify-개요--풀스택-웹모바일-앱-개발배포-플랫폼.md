---
title: AWS Amplify 개요 — 풀스택 웹·모바일 앱 개발·배포 플랫폼
slug: "aws-amplify-개요--풀스택-웹모바일-앱-개발배포-플랫폼"
category: cloud
tags: ["amplify", "app-development", "appsync", "aws", "aws-amplify", "ci-cd", "cognito", "dynamodb", "hosting", "serverless"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:03.254459+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---

| 항목        | 설명                                                                        |
| --------- | ------------------------------------------------------------------------- |
| **서비스명**  | AWS Amplify                                                               |
| **유형**    | **풀스택 웹·모바일 애플리케이션 개발·배포 플랫폼**                                            |
| **주요 목적** | **프론트엔드·백엔드 개발, 호스팅, 인증·스토리지·API 통합**을 간소화하여 애플리케이션을 빠르게 출시할 수 있도록 지원 |

> ⚡ **AWS Amplify**는 개발자가 **풀스택 클라우드 애플리케이션을 빠르게 빌드·배포**하도록
> **호스팅, 인증, GraphQL·REST API, 스토리지, 푸시 알림** 등 기능을 통합 제공하는 서비스입니다.

---

## 🔧 주요 특징

| 항목 | 설명 |
|------|------|
| **프론트엔드 호스팅** | React, Vue, Angular, Next.js 등 정적/SSR 웹앱의 자동 배포 지원 |
| **백엔드 구축** | GraphQL(AppSync), REST API, DynamoDB, Lambda 연계로 서버리스 백엔드 구성 가능 |
| **인증/보안 통합** | Amazon Cognito 기반의 사용자 인증·인가 기능 제공 |
| **스토리지 지원** | S3 기반 파일 스토리지와 CloudFront CDN 연계 지원 |
| **DevOps 자동화** | GitHub, GitLab, Bitbucket, CodeCommit 등과 연동한 CI/CD 자동화 |
| **실시간 데이터** | GraphQL Subscriptions 및 Pub/Sub 기반의 실시간 애플리케이션 지원 |

---

## 🧪 활용 시나리오

- **웹/모바일 앱 빠른 출시**
  - 스타트업의 MVP, 사내 포털, 이벤트 페이지 등 빠른 배포가 필요한 경우
- **서버리스 백엔드 구축**
  - Lambda + DynamoDB + AppSync 조합으로 서버리스 아키텍처 구성
- **멀티 플랫폼 앱**
  - React Native, Flutter 앱에서 인증·스토리지·푸시 알림 등을 통합 관리
- **CI/CD 기반 정적 웹 호스팅**
  - Git 브랜치 푸시만으로 자동으로 배포되는 정적 사이트 운영

---

## ✅ 장점

- **풀매니지드** → 서버 관리 없이 웹·모바일 앱을 배포 가능
- **개발 속도 향상** → 인증, 스토리지, API를 몇 줄의 코드로 쉽게 통합
- **CI/CD 통합 용이** → Git 푸시로 배포가 자동화되어 개발 흐름 단순화
- **실시간·오프라인 앱 지원** → GraphQL Subscriptions 및 캐싱 등으로 실시간 및 오프라인 기능 지원
- **AWS 서비스 연계** → Cognito, S3, Lambda, DynamoDB, AppSync 등과 직접 통합되어 생태계 활용 가능

---

## ⚠️ 유의사항

| 항목 | 설명 |
|------|------|
| **커스텀 아키텍처 한계** | 매우 복잡한 엔터프라이즈 수준 아키텍처는 CDK/CloudFormation 같은 인프라 도구가 더 적합할 수 있음 |
| **벤더 종속성** | Amplify SDK 및 CLI 중심 설계로 인해 AWS 환경에 종속되는 특성이 있음 |
| **백엔드 확장 고려 필요** | 대규모 트래픽이나 고도의 맞춤형 백엔드는 추가 설계 및 최적화가 필요함 |

---

## 🧾 요약

| 항목       | 설명 |
|------------|------|
| **정의**     | 풀스택 웹·모바일 앱을 **빠르게 개발·배포**할 수 있도록 돕는 AWS 플랫폼 |
| **주요 기능** | 호스팅, 인증, 스토리지, GraphQL/REST API, CI/CD 통합 |
| **활용 예** | 스타트업 MVP, 서버리스 앱, 정적 웹 호스팅, 실시간 앱 개발 |