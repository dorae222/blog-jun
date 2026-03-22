---
title: ECMP
slug: ecmp
category: cloud
tags: ["aws", "ecmp", "high-availability", "networking", "routing", "tgw", "transit-gateway", "vpn"]
status: published
post_type: til
quality_score: 7.0
created_at: "2026-03-02T01:08:06.778160+00:00"
---

> 목적지까지의 **라우팅 경로가 여러 개 존재하고 그 비용이 같을 때**, 이를 **동시에 사용하여 트래픽을 분산**하는 라우팅 기법입니다.
>
> AWS에서는 **Transit Gateway(TGW)**에서 ECMP를 통해 **여러 VPN 터널을 동시에 활성화**하여 **성능과 내구성**을 모두 높일 수 있습니다.