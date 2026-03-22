---
title: EC2에서 SSM 기능을 사용하기 위한 IAM 정책 권한 요약
slug: "ec2에서-ssm-기능을-사용하기-위한-iam-정책-권한-요약"
category: cloud
tags: ["amazon-ec2", "aws", "aws-ssm", "iam", "iam-policies", "session-manager", "ssm-agent", "systems-manager"]
status: published
post_type: til
quality_score: 7.0
created_at: "2026-03-02T01:08:05.745070+00:00"
---

이 <mark style="background: #FFF3A3A6;">IAM 정책</mark>은 다음 권한을 포함합니다:

- Systems Manager Agent(SSM Agent)가 EC2 인스턴스에서 실행되어 AWS Systems Manager와 통신할 수 있도록 허용합니다.

- 세션 매니저(Session Manager), 명령 실행(Run Command), 패치 매니저(Patch Manager) 등 다양한 SSM 기능의 사용을 허용합니다.

> 즉, 이 정책이 연결되지 않으면 EC2 인스턴스는 Systems Manager 기능(예: Session Manager)으로 **접속하거나 관리될 수 없습니다.**