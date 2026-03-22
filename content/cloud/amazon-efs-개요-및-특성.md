---
title: Amazon EFS 개요 및 특성
slug: "amazon-efs-개요-및-특성"
category: cloud
tags: ["aws", "cloud-storage", "ec2", "efs", "efs-performance", "kms", "nfs", "posix"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:05.147445+00:00"
---

## 개요

Amazon EFS는 여러 EC2 인스턴스에 마운트할 수 있는 관리형 NFS(네트워크 파일 시스템)입니다.

### 주요 특징

- **멀티 AZ 지원**: EFS는 여러 AZ에 배포된 EC2 인스턴스와 함께 동작합니다.
- **고가용성**: 확장 가능하며 고가(대략 EBS gp2의 3배)이고, 사용량 기반 결제 모델입니다.
- <mark style="background: #FFF3A3A6;">보안</mark>: Security Group을 사용하여 EFS 액세스를 제어합니다.

## 기술 사양

- **프로토콜**: <mark style="background: #FFF3A3A6;">NFSv4.1 프로토콜</mark>을 사용합니다.
- **호환성**: <mark style="background: #FFF3A3A6;">Linux 기반 AMI와 호환됩니다 (Windows 불가)</mark>.
- **암호화**: <mark style="background: #FFF3A3A6;">KMS</mark>를 사용한 저장 중 암호화 지원.
- **파일 시스템**: 표준 파일 API를 가지는 POSIX 파일 시스템(유사 Linux).
- **자동 확장**: 파일 시스템이 자동으로 확장되며, <mark style="background: #FFF3A3A6;">사용량에 따른 지불, 용량 계획 불필요</mark>합니다.

## 사용 사례

콘텐츠 관리, 웹 서빙, 데이터 공유, WordPress 등에 활용됩니다.

## 성능 및 저장소 클래스

### 1. EFS 확장성

- **동시 클라이언트**: 수천 개의 동시 NFS 클라이언트를 지원합니다.
- **처리량**: 10GB+/s 수준의 처리량을 제공합니다.
- **자동 확장**: 페타바이트 규모의 네트워크 파일 시스템으로 자동 확장됩니다.

### 2. 성능 모드 (EFS 생성 시 설정)

- **General Purpose (기본값)**: 지연 시간에 민감한 사용 사례(웹 서버, CMS 등)에 적합합니다.
- **Max I/O**: 지연 시간은 더 높지만 처리량이 큰, 고도로 병렬화된 작업(빅 데이터, 미디어 처리)에 적합합니다.

### 3. 처리량 모드 (Throughput Mode)

- **Bursting**: 1TB = 50MiB/s + 최대 100MiB/s까지 버스트 가능합니다.
- **Provisioned**: 저장소 크기와 관계없이 처리량을 설정할 수 있습니다(예: 1TB 저장소에 1GiB/s).
- **Elastic**: 워크로드에 따라 처리량이 자동으로 증가 또는 감소합니다.
    - 읽기 최대 3GiB/s, 쓰기 최대 1GiB/s
    - 예측 불가능한 워크로드에 사용합니다.

## 스토리지 클래스

### 스토리지 계층 (생명주기 관리 기능)

- **Standard**: 자주 액세스되는 파일용.
- **Infrequent Access (EFS-IA)**: 파일 접근 시 비용이 발생하지만 저장 비용을 절감합니다.
- **Archive**: 거의 액세스되지 않는 데이터(연간 몇 번)용으로, 약 50% 저렴합니다.
- **생명주기 정책**: N일 후 파일을 저장소 계층 간 이동하는 정책을 구현할 수 있습니다.

### 가용성 및 내구성

- **Standard**: 멀티 AZ 지원으로 프로덕션 환경에 적합합니다.
- **One Zone**: 단일 AZ에 위치하며 개발 환경에 적합합니다. 기본적으로 백업 활성화, IA와 호환(EFS One Zone-IA).

### 비용 절감

90% 이상의 비용 절감이 가능합니다.

---
### EBS vs EFS vs Instance Store