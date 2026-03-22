---
title: EC2 인스턴스
slug: "ec2-인스턴스"
category: cloud
tags: ["ami", "aws", "ec2", "elastic-ip", "eni", "networking", "placement-group", "security-groups", "vpc"]
status: published
post_type: til
quality_score: 7.0
created_at: "2026-03-02T01:08:05.082480+00:00"
---

### EC2 인스턴스

### EC2 네트워킹 & 네트워크 인터페이스
- 인스턴스를 시작할 때 VPC에서 서브넷을 선택 가능
- 인스턴스 시작 시 네트워크 통신을 위해 기본 네트워크 인터페이스가 생성됨
- 인스턴스는 서브넷의 IP 주소 대역에서 프라이빗 IP 주소를 기본 네트워크 인터페이스에 할당
- 퍼블릭 IP 주소가 필요한 경우 네트워크 인터페이스에 할당
- ENI

### EC2 Instance Store

### Security Group

### Elastic IP

### Amazon Machine Image

### Placement Group

### EC2 Life Cycle