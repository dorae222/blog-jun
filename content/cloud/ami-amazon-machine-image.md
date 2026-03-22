---
title: AMI (Amazon Machine Image)
slug: "ami-amazon-machine-image"
category: cloud
tags: ["ami", "aws", "aws-marketplace", "aws-regions", "custom-ami", "ebs-snapshot", "ec2", "security-groups"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:05.374864+00:00"
---

- EC2 인스턴스를 시작하는 데 필요한 소프트웨어 구성(운영체제, 애플리케이션 서버 및 애플리케이션)이 포함된 템플릿
- EC2 인스턴스를 시작할 때 AMI를 지정해야 하며, 인스턴스 시작 시 별도로 OS 설치나 서버 소프트웨어 설정 등을 할 필요가 없음
- 운영 중인 EC2 인스턴스를 Custom AMI로 만들어 동일한 환경의 EC2를 빠르게 시작할 수 있음
- AMI는 특정 리전(Region)에서 생성되어야 함
	- 또한 리전 간 복사 가능
- AMI는 EC2 인스턴스의 커스터마이징을 포함함
	- 사용자 소프트웨어, 설정(Configuration), OS, 모니터링 등 추가 가능
	- 필요한 소프트웨어를 AMI가 미리 pre-packged해 두어 부팅 및 설정에 드는 시간을 줄일 수 있음
- AMI 생성 프로세스(EC2 인스턴스로부터)
	- EC2 인스턴스 시작 및 커스터마이즈
	- 데이터 무결성을 위해 EC2 인스턴스 중지
	- 해당 EC2 인스턴스를 바탕으로 EBS 스냅샷을 생성하여 AMI 구축
	- 생성된 AMI로부터 다른 AMI에서 EC2 인스턴스를 실행 가능
		- Security Group을 통해 보안 설정 가능
- 다음 출처로부터 EC2 인스턴스를 런치(launch)할 수 있음
	- Quickstart AMI (A Public AMI)
		- AWS에서 제공하는 자주 사용하는 소프트웨어로 구성된 AMI
	- 내 AMI (Custom AMI)
		- 사용자가 직접 만든 AMI
	- AWS Marketplace AMI
		- 서드파티 회사가 등록한 AMI(온라인 소프트웨어 상점)
	- 커뮤니티(Community AMI)
		- AWS 개발자 커뮤니티 회원들이 올린 AMI