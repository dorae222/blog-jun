---
title: 여러 리소스의 IP를 반환하여 클라이언트가 무작위로 선택
slug: "여러-리소스의-ip를-반환하여-클라이언트가-무작위로-선택"
category: cloud
tags: ["aws", "client-side-selection", "cloud", "ip-address", "load-balancing", "networking", "random-selection", "traffic-distribution"]
status: published
post_type: til
quality_score: 4.0
created_at: "2026-03-02T01:08:08.194629+00:00"
---

여러 리소스의 IP 주소를 반환하면 클라이언트는 그중 하나를 무작위로 선택합니다.

- 클라이언트가 반환된 IP 목록 중 하나를 임의로 선택합니다.
  - 이 방식은 트래픽을 무작위로 분산시키는 데 적합합니다.