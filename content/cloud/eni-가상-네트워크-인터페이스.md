---
title: ENI (가상 네트워크 인터페이스)
slug: "eni-가상-네트워크-인터페이스"
category: cloud
tags: ["availability-zone", "aws", "cloud-networking", "ebs", "ec2", "eni", "network-interface", "security-groups"]
status: published
post_type: article
quality_score: 7.0
created_at: "2026-03-02T01:08:06.770261+00:00"
---

- 가상 네트워크 인터페이스(ENI)
- IP 주소, MAC 주소 등이 할당됨
- 인스턴스에 연결되어 네트워크 통신을 담당함
- 인스턴스 생성 시 기본(Primary) 네트워크 인터페이스가 IP 주소 등 정보와 함께 생성됨
- EC2 인스턴스에 여러 개의 네트워크 인터페이스를 추가로 연결할 수 있음
- 인스턴스 유형에 따라 사용할 수 있는 최대 네트워크 인터페이스 개수와 IP 주소 개수가 다름
- 하나 이상의 보안 그룹을 연결할 수 있음
- 네트워크 인터페이스는 동일한 가용 영역(Availability Zone)에 있는 인스턴스에만 연결 가능
- EC2 인스턴스의 RAM은 150GB 미만이어야 함
- 온디맨드(ondemand) 및 예약(reserved) 인스턴스를 지원함
- EC2 인스턴스의 볼륨 유형은 EBS 볼륨이어야 함
- 민감한 내용을 보호하기 위해 암호화되어야 함