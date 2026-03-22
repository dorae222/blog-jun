---
title: "EBS Volume이란?"
slug: "ebs-volume이란"
category: cloud
tags: ["aws", "aws-s3", "block-storage", "cloud-storage", "ebs", "ec2", "fast-snapshot-restore", "snapshot", "storage"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:05.117055+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A


---
---
aliases:
  - EBS
---

## EBS Volume이란?

EBS (Elastic Block Store) Volume은 인스턴스 실행 중에 연결할 수 있는 **<mark style="background: #FFF3A3A6;">네트워크 드라이브</mark>**입니다.

### 주요 특징

- EC2 인스턴스 종료 후에도 **데이터 지속성**을 보장합니다.
- 한 번에 **하나의 인스턴스에만 마운트**할 수 있습니다 (CCP 레벨 기준).
- **특정 가용 영역(AZ)에 종속**됩니다.
- 비유하자면 "네트워크 USB 스틱"과 같은 개념입니다.

### 무료 제공량

- 월 30GB의 General Purpose (SSD) 또는 Magnetic 타입 EBS 스토리지를 무료로 제공합니다.

---

## EBS Volume 세부 특성

### 네트워크 드라이브 특성

- **물리적 드라이브가 아니라 네트워크 드라이브**입니다.
- 네트워크를 통해 인스턴스와 통신하므로 **약간의 지연 시간**이 발생할 수 있습니다.
- EC2 인스턴스에서 **빠르게 분리한 뒤 다른 인스턴스에 연결**할 수 있습니다.

### 가용 영역(AZ) 제약

- **특정 가용 영역에 고정**됩니다.
- us-east-1a에 있는 EBS Volume은 us-east-1b에 연결할 수 없습니다.
- 다른 영역으로 이동하려면 **먼저 스냅샷을 생성**해야 합니다.

### 용량 및 과금

- **프로비저닝된 용량에 대해 과금**됩니다 (크기 GB 및 IOPS 기준).
- 프로비저닝된 모든 용량에 대해 요금이 부과됩니다.
- 시간이 지나면서 **드라이브 용량을 증설**할 수 있습니다.

---

## Delete on Termination 속성

### 기본 동작

- **EC2 인스턴스 종료 시 EBS 동작을 제어**하는 속성입니다.
- **루트( Root ) EBS 볼륨**: 기본적으로 삭제됩니다 (속성 활성화 상태).
- **추가 연결된 EBS 볼륨**: 기본적으로 삭제되지 않습니다 (속성 비활성화 상태).

### 제어 방법

- AWS 콘솔 또는 AWS CLI를 통해 제어할 수 있습니다.
- **사용 사례**: 인스턴스 종료 시 루트 볼륨을 보존하려는 경우에 사용합니다.

---

## EBS 스냅샷(EBS Snapshot)

### 기본 개념

- 특정 시점의 **EBS 볼륨 백업(스냅샷) 생성**입니다.
- 스냅샷 생성 시 볼륨 분리가 필수는 아니지만 **권장사항**입니다.
- <mark style="background: #FFF3A3A6;">AZ 또는 리전 간 스냅샷 복사</mark>가 가능합니다.
- 애플리케이션이 많은 트래픽을 처리하는 동안에는 성능에 영향을 줄 수 있으므로 스냅샷을 실행하지 않는 것이 좋습니다.

### 스냅샷 워크플로우

```
US-EAST-1A        EBS Snapshot        US-EAST-1B
   EBS      →    snapshot    →         EBS
  (50 GB)                            (50 GB)
```

---

## EBS 스냅샷 고급 기능

### EBS Snapshot Archive

- 스냅샷을 **75% 저렴한 "아카이브 티어"로 이동**할 수 있습니다.
- 아카이브에서 복원하는 데는 **24~72시간**이 소요됩니다.

### Recycle Bin for EBS Snapshots

- **실수로 삭제된 스냅샷을 복구**하기 위한 규칙을 설정할 수 있습니다.
- **1일~1년** 범위의 보존 기간을 지정할 수 있습니다.

### Fast Snapshot Restore (FSR)

- 스냅샷의 **완전 초기화를 강제**하여 첫 사용 시 발생하는 지연 시간을 제거합니다.
- **비용이 높은 서비스**입니다.

---

### EBS Encryption


---

### EBS Volume Types
