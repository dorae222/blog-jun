---
title: EBS Volume Types 개요
slug: "ebs-volume-types-개요"
category: cloud
tags: ["aws", "ebs", "gp3", "hdd", "io2", "multi-attach", "provisioned-iops", "ssd", "storage"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:06.654605+00:00"
---

### EBS Volume Types 개요

##### 6가지 EBS Volume Types

- **gp2/gp3 (SSD)**: 다양한 워크로드에 대해 가격과 성능의 균형을 맞춘 범용 SSD 볼륨
- **io1/io2 Block Express (SSD)**: 미션 크리티컬한 저지연 또는 고처리량 워크로드를 위한 최고 성능 SSD 볼륨
- **st1 (HDD)**: 자주 액세스되는 처리량 집약적 워크로드를 위한 저비용 HDD 볼륨
- **sc1 (HDD)**: 덜 자주 액세스되는 워크로드를 위한 최저 비용 HDD 볼륨

##### 주요 특성

- **EBS 볼륨 특성**: 크기 | 처리량 | IOPS (I/O Ops Per Sec)로 구분
- **의심스러울 때**: 항상 AWS 공식 문서 참조 권장
- **부팅 볼륨**: **gp2/gp3**와 **io1/io2 Block Express**만 사용 가능

---

### General Purpose SSD 사용 사례

### 공통 특성

- **비용 효율적인 스토리지, 저지연**
- **시스템 부팅 볼륨, 가상 데스크톱, 개발 및 테스트 환경**
- **볼륨 크기**: 1 GiB - 16 TiB
- <mark style="background: #FFF3A3A6;">gp3에서는 IOP와 처리량을 독립적으로 설정할 수 있지만, gp2에서는 서로 연결됨</mark>
##### gp3 (권장)

- **기준 성능**: 3,000 IOPS 및 125 MiB/s 처리량
- **독립적 성능 확장**:
    - IOPS: 최대 16,000까지 증가 가능
    - 처리량: 최대 1,000 MiB/s까지 증가 가능

##### gp2 (이전 세대)

- **소형 gp2 볼륨**: 3,000 IOPS까지 버스트 가능
- **볼륨 크기와 IOPS 연동**: 최대 IOPS 16,000
- **비율**: 3 IOPS per GB (5,334 GB에서 최대 IOPS 달성)

---

### Provisioned IOPS (PIOPS) SSD 사용 사례

##### 적용 분야

- **지속적인 IOPS 성능이 필요한 중요한 비즈니스 애플리케이션**
- **16,000 IOPS 이상이 필요한 애플리케이션**
- **데이터베이스 워크로드** (스토리지 성능 및 일관성에 민감)

##### io1 (4 GiB - 16 TiB)

- **최대 PIOPS**:
    - Nitro EC2 인스턴스: 64,000
    - 기타 인스턴스: 32,000
- **스토리지 크기와 독립적으로 PIOPS 증가 가능**

##### io2 Block Express (4 GiB - 64 TiB)

- **서브 밀리초 지연시간**
- **최대 PIOPS**: 256,000
- **IOPS:GiB 비율**: 1,000:1
- **EBS Multi-attach 지원**

---

### Hard Disk Drives (HDD) 사용 사례

##### 공통 특성

- **부팅 볼륨으로 사용 불가**
- **볼륨 크기**: 125 GiB - 16 TiB

##### Throughput Optimized HDD (st1)

- **사용 분야**: 빅데이터, 데이터 웨어하우스, 로그 처리
- **최대 처리량**: 500 MiB/s
- **최대 IOPS**: 500

##### Cold HDD (sc1)

- **사용 분야**:
    - 자주 액세스하지 않는 데이터
    - 최저 비용이 중요한 시나리오
- **최대 처리량**: 250 MiB/s
- **최대 IOPS**: 250

---

### EBS Volume Types 요약 테이블

|항목|gp3|gp2|io2 Block Express|io1|st1|sc1|
|---|---|---|---|---|---|---|
|**내구성**|99.8% - 99.9%|99.999%|99.8% - 99.9%|99.8% - 99.9%|99.8% - 99.9%|99.8% - 99.9%|
|**볼륨 크기**|1 GiB - 16 TiB|1 GiB - 16 TiB|4 GiB - 64 TiB|4 GiB - 16 TiB|125 GiB - 16 TiB|125 GiB - 16 TiB|
|**최대 IOPS**|16,000|16,000|256,000|64,000|500|250|
|**최대 처리량**|1,000 MiB/s|250 MiB/s|4,000 MiB/s|1,000 MiB/s|500 MiB/s|250 MiB/s|
|**Multi-attach**|지원 안함|지원 안함|지원|지원 안함|지원 안함|지원 안함|
|**부팅 볼륨**|지원|지원|지원|지원|지원 안함|지원 안함|

---

### EBS Multi-Attach (io1/io2 계열)
