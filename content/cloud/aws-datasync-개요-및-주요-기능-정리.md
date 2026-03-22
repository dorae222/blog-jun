---
title: AWS DataSync 개요 및 주요 기능 정리
slug: "aws-datasync-개요-및-주요-기능-정리"
category: cloud
tags: ["amazon-s3", "aws-datasync", "cloudwatch", "data-migration", "data-transfer", "efs", "fsx", "nfs", "smb", "snowcone"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:03.692176+00:00"
---

**AWS DataSync**는 데이터를 빠르고 안전하게 **온프레미스 ↔ AWS 또는 AWS ↔ AWS 간에 복제 및 전송**할 수 있도록 도와주는 **완전관리형 데이터 이동 서비스**입니다.

---

## 🚀 AWS DataSync란?

> **AWS DataSync**는 온프레미스 스토리지, 다른 클라우드, 또는 AWS 서비스 간에 **대규모 파일 데이터**를 **자동화된 방식으로 이동 또는 복제**할 수 있도록 지원하는 서비스입니다.

주로 **NFS, SMB, Amazon S3, EFS, FSx 등** 다양한 스토리지 간에 데이터를 전송할 수 있습니다.

- 파일 권한 및 메타데이터 보존
  - NFS(Posix) 및 SMB 지원
- DataSync Agent를 사용하거나 AWS Snowcone을 통해 DataSync 수행 가능
  - 온프레미스와 AWS 서비스 간에 양방향으로 동기화 가능
- 연속 실시간 동기화는 지원하지 않으며, 스케줄링을 통해 주기적 복제가 가능

---

## 🎯 사용 사례

| 사용 시나리오                       | 설명                                |
| ----------------------------- | --------------------------------- |
| **온프레미스 NAS → Amazon S3로 백업** | 로컬 파일 서버 데이터를 클라우드로 이전            |
| **Amazon EFS → FSx 간 이동**     | AWS 내 파일 시스템 간 마이그레이션             |
| **지속적인 데이터 복제**               | 주기적으로 변경된 파일만 복사 (증분 복사)          |
| **데이터 분석 준비**                 | 빅데이터를 Amazon S3로 복사하여 분석 파이프라인 구성 |
| **타 클라우드 스토리지**                   | GCP 및 Azure의 스토리지와 데이터 전송 구성 가능    |

---

## 🔐 주요 기능

|기능|설명|
|---|---|
|**고속 데이터 전송**|최대 10Gbps 이상 전송 성능 제공|
|**암호화 및 보안**|TLS 암호화 및 IAM 연동|
|**증분 복사**|변경된 파일만 전송하여 비용/시간 절감|
|**정책 기반 제어**|포함/제외 필터, 일정 지정 가능|
|**CloudWatch 통합**|상태, 경고, 로깅 기능 제공|

---

## 🏗️ 구성 요소

| 구성 요소                  | 설명                                     |                                                          |
| ---------------------- | -------------------------------------- | -------------------------------------------------------- |
| **DataSync Agent**     | 온프레미스에서 실행되는 VM 또는 EC2 인스턴스 (NFS/SMB용) | DataSync 에이전트를 설치한 VM 어플라이언스에서 DataSync가 실행됨 |
| **Source/Destination** | Amazon S3, EFS, FSx, NFS, SMB          | 데이터를 복사할 소스와 목적지 위치                                      |
| **Task**               | 복사 작업 단위 (데이터 이동 정의)                   | 데이터를 어떻게 복사할지에 대한 세부 정보                                   |

---

## 🆚 DataSync vs 다른 서비스

|항목|AWS DataSync|AWS DMS|S3 Transfer Acceleration|
|---|---|---|---|
|목적|**파일 데이터 전송**|관계형 DB 마이그레이션|S3 전송 가속|
|형식|NFS, SMB, S3, EFS 등|RDS, Oracle, PostgreSQL 등|S3 PUT/GET|
|지원 방식|Agent 또는 AWS 내 연동|DMS 인스턴스|글로벌 엣지 네트워크|

---

## ✅ 요약

> **AWS DataSync**는 파일 기반 데이터를 빠르고 안전하게 **온프레미스 ↔ AWS 또는 AWS 서비스 간에 이동**할 수 있게 해주는 **완전관리형 전송 서비스**입니다.  
> 데이터 백업, 마이그레이션, 분석 준비, DR 구성 등에 적합합니다.