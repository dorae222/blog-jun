---
title: EBS vs EFS 비교
slug: "ebs-vs-efs-비교"
category: cloud
tags: ["aws", "az", "block-storage", "ebs", "ec2", "efs", "file-storage", "instance-store", "storage"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:06.664726+00:00"
---

# EBS vs EFS 비교

## EBS - Elastic Block Storage

### 주요 특징

- **단일 인스턴스 연결**: 기본적으로 하나의 인스턴스에만 연결 가능(예외: multi-attach을 사용하는 io1/io2)
- **AZ 제한**: 가용 영역(AZ) 단위로 제공
- **성능 특성**:
    - **gp2**: 디스크 크기가 증가하면 I/O 성능도 증가
    - **gp3 & io1**: I/O 성능을 독립적으로 증가 가능

### AZ 간 마이그레이션

EBS 볼륨을 다른 AZ로 마이그레이션하려면:

1. 스냅샷 생성
2. 다른 AZ에서 스냅샷 복원
3. **주의사항**: EBS 백업(스냅샷 생성)은 I/O를 사용하므로 애플리케이션에 트래픽이 많을 때는 실행하지 않는 것이 좋음

### 인스턴스 종료 시 동작

- **루트 EBS 볼륨**: EC2 인스턴스가 종료되면 기본적으로 함께 삭제됨(해제 가능)

---
## EFS - Elastic File System

### 주요 특징

- **멀티 인스턴스 지원**: 여러 AZ에 걸쳐 수백 개의 인스턴스에 마운트 가능
- **파일 공유**: 웹사이트 파일 공유(예: WordPress)에 적합
- **Linux 전용**: Linux 인스턴스(POSIX)에서만 사용 가능

### 비용 및 성능

- **가격**: 일반적으로 EBS보다 높은 가격대
- **비용 절감**: 저장소 계층(storage classes)을 활용해 비용을 절감 가능

---
## 기억해야 할 포인트

EFS vs EBS vs Instance Store 각각의 특징과 사용 사례를 구분하여 이해하는 것이 중요합니다.

### 사용 사례 비교

- **EBS**: 단일 인스턴스에 대한 영구 블록 스토리지
- **EFS**: 여러 인스턴스 간 파일 공유가 필요한 경우
- **Instance Store**: 임시 고성능 스토리지가 필요한 경우