---
title: AWS 가용 영역(Availability Zones) 개요
slug: "aws-가용-영역availability-zones-개요"
category: cloud
tags: ["availability-zones", "aws", "az", "cloud-architecture", "data-centers", "high-availability", "networking", "regions"]
status: published
post_type: til
quality_score: 7.0
created_at: "2026-03-02T01:08:06.231427+00:00"
---

- 각 리전(region)은 여러 개의 가용 영역(Availability Zones, AZ)을 가집니다.
  - 일반적으로 3개
  - 최소 3개
  - 최대 6개
- 각 AZ는 중복 전원, 네트워킹, 연결성을 갖춘 하나 이상의 독립된 데이터 센터입니다.
- AZ들은 서로 분리되어 있어 재해 발생 시 격리될 수 있도록 설계되어 있습니다.
- AZ들 간에는 고대역폭, 초저지연 네트워킹으로 연결되어 있습니다.