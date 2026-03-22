---
title: NACLs (네트워크 ACL)
slug: "nacls-네트워크-acl"
category: cloud
tags: ["aws", "ephemeral-ports", "firewall", "nacl", "network-acl", "networking", "security", "subnets"]
status: published
post_type: til
quality_score: 7.0
created_at: "2026-03-02T01:08:07.162678+00:00"
---

> **NOTE:**
> - NACL은 서브넷 수준에서 들어오고 나가는 트래픽을 제어하는 방화벽과 유사합니다. (<mark style="background: #FFF3A3A6;">subnets</mark>)
> - 서브넷당 하나의 NACL이 존재합니다.
> - 서브넷 레벨에서 특정 IP 주소를 차단할 수 있습니다.

![](/media/posts/imported/aws/Pasted%20image%2020250708085805.png)

![](/media/posts/imported/aws/Pasted%20image%2020250708085834.png)

### NACL with Ephemeral Ports

![](/media/posts/imported/aws/Pasted%20image%2020250708090005.png)