---
title: Instance Store 개요
slug: "instance-store-개요"
category: cloud
tags: ["aws", "ebs", "ec2", "efs", "ephemeral-storage", "instance-store", "performance", "storage"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:06.702120+00:00"
---

### EBS vs Instance Store 비교

- **EBS 볼륨**: 네트워크 기반 스토리지로서 준수한 성능을 제공하지만, 고성능 로컬 디스크가 필요한 워크로드에서는 성능이 제한적일 수 있음
- <u>고성능 하드웨어 디스크가 필요한 경우: EC2 Instance Store 사용</u>

---

## Instance Store 특징

### 성능 장점

- **향상된 I/O 성능** 제공
- 물리적으로 EC2 인스턴스에 직접 연결된 하드웨어

### 데이터 지속성

- **EC2 인스턴스 중지(또는 종료) 시 스토리지 손실** (ephemeral - 임시적)
- 인스턴스 재시작(재부팅) 시에는 데이터가 유지됨
- 인스턴스 종료 또는 중지 시 **모든 데이터 영구 손실**

### 적합한 사용 사례

- **버퍼 / 캐시 / 스크래치 데이터 / 임시 콘텐츠용**
- 빠른 임시 처리가 필요한 워크로드

### 위험 요소

- **하드웨어 장애 시 데이터 손실 위험**
- 인프라 장애에 대한 내성 부족

### 책임 사항

- **백업 및 복제는 사용자 책임**
- 중요한 데이터는 별도 백업 전략 필요

---

## 사용 권장사항

### Instance Store 사용 시기

- 최고 성능의 임시 스토리지가 필요한 경우
- 캐시, 버퍼, 임시 작업 파일 저장
- 데이터 손실이 허용되는 워크로드

### Instance Store 사용 주의사항

- 영구 데이터 저장 목적에는 부적절
- 반드시 백업 및 복제 전략을 수립할 것
- 하드웨어 장애에 대한 대비책 필요

---

### EBS vs EFS vs Instance Store