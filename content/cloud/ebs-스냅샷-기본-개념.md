---
title: EBS 스냅샷 기본 개념
slug: "ebs-스냅샷-기본-개념"
category: cloud
tags: ["availability-zones", "aws", "aws-ec2", "backup", "cross-region", "ebs", "ebs-snapshot", "snapshots"]
status: published
post_type: til
quality_score: 7.0
created_at: "2026-03-02T01:08:06.637395+00:00"
---

### 기본 개념

- 특정 시점의 **EBS 볼륨 백업(스냅샷) 생성**
- 스냅샷 생성 시 볼륨 분리가 필수는 아니지만 **권장사항**
- **AZ 또는 리전 간 스냅샷 복사** 가능
- 애플리케이션이 많은 트래픽을 처리하는 동안에는 성능에 영향을 줄 수 있으므로 실행하지 않는 것이 좋음

### 스냅샷 워크플로우

```
US-EAST-1A        EBS Snapshot        US-EAST-1B
   EBS      →       snapshot    →         EBS
(50 GB)                                 (50 GB)   
```