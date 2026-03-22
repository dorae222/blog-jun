---
title: "AWS 보안 그룹(Security Group, SG) 개요"
slug: "aws-보안-그룹security-group-sg-개요"
category: cloud
tags: ["aws", "cloud", "ec2", "firewall", "network-security", "security-group", "stateful", "vpc"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:07.779944+00:00"
---

- EC2 인스턴스에 대한 인바운드 및 아웃바운드 트래픽을 제어하는 가상 방화벽 역할
	- 인바운드 트래픽: 외부에서 EC2 인스턴스로 들어오는 트래픽
	- 아웃바운드 트래픽: EC2 인스턴스에서 외부로 나가는 트래픽
- 제어 규칙
	- 트래픽 유형 (예: SSH, HTTP 등)
	- 프로토콜 (TCP, UDP 등)
	- 포트 (예: SSH 22, HTTP 80, HTTPS 443, MySQL 3306, FTP 21 등)
	- 대상 (개별 IP 주소, IP 주소 대역, 다른 보안 그룹)
- EC2 인스턴스의 ENI와 연결됨
- 보안 그룹은 ==허용 규칙만 지정가능==하고 거부 규칙은 지정할 수 없음
- 보안 그룹은 연결 상태를 추적하는 상태저장 방화벽(Stateful Firewall)
	- 허용된 인바운드 트래픽에 대한 응답으로 외부로 나가는 흐름은 아웃바운드 규칙과 관계없이 이루어짐
	- 사용자가 인스턴스에서 요청을 전송하면, 해당 요청의 응답 트래픽은 인바운드 보안 그룹 규칙과 관계없이 인바운드 흐름으로 허용됨

> **NOTE:** Dump
> - 특정 Region 및 VPC 조합에 제한됨
> - 다른 EC2 Instance라도 동일한 보안 그룹을 사용한다면, 보안 규칙이 자동 승인됨
> 	- IP를 신경쓰지 않아도 되서 편리함

### Port