---
title: Route 53 — VPC 내 DNS 요청 처리 서비스
slug: "route-53--vpc-내-dns-요청-처리-서비스"
category: cloud
tags: ["aws", "aws-direct-connect", "aws-vpn", "dns", "ip-based-routing", "route53", "routing-policies", "vpc", "weighted-routing"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.735191+00:00"
---

- VPC 내에서 DNS 요청을 처리하는 서비스
- 대표적으로 AWS Direct Connect 또는 AWS VPN과 연결된 온프레미스 네트워크 간의 Domain Name System 쿼리용도로 사용

> **NOTE:** Simple & Weighted & IP-based Routing Policy
> 
> 
> - 1) 단순 라우팅
> 	- 도메인 네임 → IP주소로 라우팅
> 	- 라우팅 대상이 여러개(예: 2개의 IP 주소)인 경우 요청이 무작위로 분배될 수 있음
> 	- ![](/media/posts/imported/aws/Pasted%20image%2020250617085854.png)
> - 2) 가중치 기반 라우팅
> 	- 접속자 요청의 비율(%)을 기준으로 트래픽을 분산하는 라우팅 방법
> 	- 트래픽 분산이나 버전이 다른 애플리케이션을 테스트(A/B 테스트)할 때 유용
> 	- ![](/media/posts/imported/aws/Pasted%20image%2020250617090126.png)
> - 3) IP 기반 라우팅
> 	- 사용자(Client)의 IP 주소를 기반으로 라우팅하는 정책
> 	- 네트워크 전송비용이나 성능을 최적화하고자 할 때 사용
> 	- ![](/media/posts/imported/aws/Pasted%20image%2020250617090221.png)