---
title: EC2 배치 그룹(Batch Group) 유형
slug: "ec2-배치-그룹batch-group-유형"
category: cloud
tags: ["aws", "batch-group", "big-data", "cluster-batch-group", "ec2", "hpc", "partition-batch-group", "spread-batch-group"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:07.240858+00:00"
---

배치 그룹을 사용하면 EC2 인스턴스 그룹의 배치 구성을 사용자가 제어할 수 있다.

### 배치 그룹(Batch Group) 유형

#### 클러스터 배치 그룹 (Cluster Batch Group)
- 단일 가용 영역 내의 인스턴스를 고속 네트워크로 연결하여 그룹화한 것
- 짧은 네트워크 지연 시간과 높은 네트워크 처리량을 제공한다
- 고성능 컴퓨팅(HPC) 애플리케이션에 적합

#### 파티션 배치 그룹 (Partition Batch Group)
- 하드웨어를 파티션 단위로 그룹화한다
- 하나의 하드웨어 장애가 발생해도 다른 파티션에는 영향이 없다 (파티션 간 장애를 분리할 수 있음)
- 각 파티션은 별도의 서버, 네트워크, 전원으로 구성된 서로 다른 하드웨어를 사용한다(배치 그룹 내 파티션이 동일한 하드웨어를 공유하지 않음)
- 가용 영역당 최대 7개의 파티션을 가질 수 있다
- HDFS, HBase, Cassandra, 하둡 등의 빅데이터 분산처리 시스템에 사용된다

#### 분산형 배치 (Spread Batch Group)
- 각각 고유한 하드웨어에 배치된 인스턴스 그룹
- 각 개별 인스턴스가 서로 다른 하드웨어에 배치된다
- 한 그룹당 가용 영역별로 최대 7개의 실행 중인 인스턴스를 가질 수 있다
- 분산형 배치의 인스턴스는 동일한 하드웨어를 사용하지 않으므로 장애 발생 시 영향이 적다
- 매우 중요하고 <mark style="background: #FFF3A3A6;">고가용성</mark>이 필요한 애플리케이션에 적합
- 개별 인스턴스가 실패해도 영향이 없도록 서로 분리되어야 하는 중요한 애플리케이션에 사용된다