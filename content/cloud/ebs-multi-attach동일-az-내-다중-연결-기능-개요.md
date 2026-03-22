---
title: "EBS Multi-Attach(동일 AZ 내 다중 연결) 기능 개요"
slug: "ebs-multi-attach동일-az-내-다중-연결-기능-개요"
category: cloud
tags: ["availability-zone", "aws", "clustered-file-system", "ebs", "ec2", "high-availability", "linux", "multi-attach", "teradata", "xfs"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:06.628060+00:00"
---

##### 기능 개요

- **동일한 AZ 내 여러 EC2 Instance 에 동일한 EBS 볼륨 연결**
- **각 인스턴스는 고성능 볼륨에 대한 완전한 읽기 및 쓰기 권한** 보유

##### 사용 사례

- **클러스터된 Linux 애플리케이션에서 더 높은 애플리케이션 가용성** 달성
  (예: Teradata)
- **애플리케이션이 동시 쓰기 작업을 관리**해야 함

##### 제한사항

- **최대 16개 EC2 인스턴스까지** 동시 연결 가능
- **클러스터 인식 파일 시스템 사용 필수** (XFS, EXT4 등 사용 불가)

##### 아키텍처

```
Availability Zone 1
     EC2      EC2      EC2
      |        |        |
       \       |       /
        \      |      /
         io2 volume with Multi-Attach
```