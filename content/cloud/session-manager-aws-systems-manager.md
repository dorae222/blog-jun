---
title: Session Manager (AWS Systems Manager)
slug: "session-manager-aws-systems-manager"
category: cloud
tags: ["aws", "aws-systems-manager", "ec2", "hybrid-cloud", "iam", "port-forwarding", "remote-access", "session-manager"]
status: published
post_type: til
quality_score: 8.0
created_at: "2026-03-02T01:08:04.398585+00:00"
---

AWS Systems Manager Agent

> **NOTE:**
> - **IAM 정책으로 관리형 노드에 대한 중앙 집중식 액세스 제어**
> - **인바운드 포트를 열 필요가 없으며 Bastion Host 또는 SSH 키를 관리할 필요가 없음**
> - **콘솔과 CLI에서 클릭 한 번으로 관리형 노드에 액세스 가능**
> - **[하이브리드 및 멀티클라우드](https://docs.aws.amazon.com/ko_kr/systems-manager/latest/userguide/operating-systems-and-machine-types.html#supported-machine-types) 환경의 Amazon EC2 인스턴스와 비 EC2 관리형 노드 모두에 연결 가능**
> - **포트 전달 지원**
> - **Windows, Linux 및 macOS에 대한 크로스 플랫폼 지원**
> - **세션 활동 로그 기록**