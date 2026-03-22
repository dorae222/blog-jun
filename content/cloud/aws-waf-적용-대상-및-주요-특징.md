---
title: AWS WAF 적용 대상 및 주요 특징
slug: "aws-waf-적용-대상-및-주요-특징"
category: cloud
tags: ["api-gateway", "application-load-balancer", "appsync", "aws", "aws-waf", "cloudfront", "cognito", "layer7", "web-acl"]
status: published
post_type: til
quality_score: 7.0
created_at: "2026-03-02T01:08:04.601829+00:00"
---

| Application Load Balancer |
| ----------------------------- |
| Amazon API Gateway        |
| Amazon CloudFront         |
| AWS AppSync GraphQL API   |
| Amazon Cognito User Pool  |

- 주로 웹 애플리케이션의 인바운드 트래픽을 필터링한다.
  - Layer 7은 HTTP 계층이다.
- 아웃바운드 트래픽 필터링에는 적합하지 않다.
- Web ACL은 CloudFront를 제외하고는 Regional이다.