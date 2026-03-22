---
title: AWS PrivateLink 개요
slug: "aws-privatelink-개요"
category: cloud
tags: ["amazon-bedrock", "aws", "aws-privatelink", "compliance", "networking", "private-connectivity", "security", "vpc"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:04.252217+00:00"
---

> **NOTE:**
> - VPC와 AWS 서비스 간에 프라이빗 연결을 제공하는 기술
> - <mark style="background: #FFF3A3A6;">Interface Endpoint,</mark> Gateway Load Balancer Endpoint에서 사용
> - Gateway Endpoint, Gateway Load Balancer Endpoint에서 사용
> - Gateway Endpoint는 PrivateLink를 사용하지 않음

AWS PrivateLink 는 ==VPC에 있는 것처럼 VPC를 서비스 및 리소스에 비공개로 연결하는 데 사용할 수 있는 가용성과 확장성이 뛰어난 기술==입니다. 프라이빗 서브넷에서 서비스 또는 AWS Site-to-Site VPN 리소스와의 통신을 허용하기 위해 인터넷 게이트웨이, NAT 디바이스, 퍼블릭 IP 주소, AWS Direct Connect 연결 또는 연결을 사용할 필요가 없습니다. 따라서 VPC에서 연결할 수 있는 특정 API 엔드포인트, 사이트, 서비스 및 리소스를 제어합니다.
https://docs.aws.amazon.com/ko_kr/vpc/latest/privatelink/what-is-privatelink.html

---

금융 기관은 Amazon Bedrock을 사용하여 AI 애플리케이션을 개발하고 있습니다. 애플리케이션은 VPC에 호스팅됩니다. 규정 준수 표준을 충족하기 위해 VPC는 인터넷 트래픽에 대한 액세스가 허용되지 않아야 합니다. AWS PrivateLink는 트래픽을 공용 인터넷에 노출시키지 않고도 VPC와 AWS 서비스 간의 개인 연결을 가능하게 합니다. 이 기능은 공용 인터넷 트래픽으로부터 격리해야 하는 규정 준수 기준을 충족하는 데 매우 중요합니다.