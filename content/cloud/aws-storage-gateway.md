---
title: AWS Storage Gateway
slug: "aws-storage-gateway"
category: cloud
tags: ["aws", "aws-storage-gateway", "backup", "disaster-recovery", "file-gateway", "hybrid-cloud", "s3", "storage", "tape-gateway", "volume-gateway"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:04.476784+00:00"
---

**AWS Storage Gateway**는 온프레미스 환경과 AWS 클라우드를 안전하게 연결해주는 **하이브리드 클라우드 스토리지 서비스**입니다.  
이를 통해 기업은 기존 데이터 센터 애플리케이션에서 **클라우드 기반 스토리지를 사용할 수 있게 하며**,  
**백업, 아카이빙, 재해 복구(DR), 클라우드 마이그레이션** 등 다양한 워크로드를 효율적으로 처리할 수 있습니다.

---

## 🧩 AWS Storage Gateway란?

> **Storage Gateway**는 온프레미스 애플리케이션이  
> **로컬 인터페이스(SMB/NFS/iSCSI)를 통해 AWS 클라우드 스토리지**를  
> 사용할 수 있도록 연결해주는 **하이브리드 스토리지 브리지**입니다.

---

## 🧰 주요 사용 사례

|용도|설명|
|---|---|
|🗄️ **백업 및 복원**|기존 백업 애플리케이션의 대상 위치를 Amazon S3로 전환|
|🧊 **아카이빙**|오래된 데이터를 Amazon S3 Glacier 등으로 자동 이전|
|🛠️ **온프레미스 캐시**|자주 사용하는 데이터는 로컬에 캐싱, 나머지는 AWS 저장|
|🌐 **재해 복구 (DR)**|백업된 VM 이미지를 EC2로 빠르게 복구|
|📦 **클라우드 마이그레이션**|파일, 볼륨, 테이프를 클라우드로 점진적 전환|

---

## 🧱 유형별 구성

|유형|설명|프로토콜|백엔드|
|---|---|---|---|
|**File Gateway**|온프레미스 파일 공유를 Amazon S3로 연결|NFS / SMB|Amazon S3|
|**Volume Gateway**|iSCSI 블록 디바이스 제공 (SnapShot 연동)|iSCSI|Amazon EBS, S3|
|**Tape Gateway**|가상 테이프 라이브러리(VTL)로 백업|iSCSI|Amazon S3 / Glacier|

---

## 🔐 보안 및 관리

- 데이터 전송 시 **TLS 암호화**

- 저장 데이터는 **SSE-S3 또는 SSE-KMS로 암호화**

- **CloudWatch, AWS Backup, AWS IAM**과 연동하여 모니터링 및 제어

---

## 💻 배포 방식

- AWS에서 제공하는 **가상 어플라이언스(VM)**

- 또는 **AWS Snow Family**를 통한 엣지 환경 배포

- 로컬에 설치된 후, AWS에 연결되는 구조

---

## ✅ 요약

|항목|설명|
|---|---|
|서비스 이름|**AWS Storage Gateway**|
|목적|**온프레미스 ↔ AWS 스토리지 연동**|
|주요 유형|File, Volume, Tape Gateway|
|통신 방식|NFS, SMB, iSCSI|
|백엔드 스토리지|Amazon S3, Glacier, EBS 등|
|활용 예시|백업, DR, 마이그레이션, 로컬 캐싱 등|
|보안|전송 및 저장 암호화, IAM 연동|

---

## 📌 예시 시나리오

- 기존 백업 솔루션이 사용하는 **테이프 라이브러리(VTL)**를 클라우드 기반으로 전환하고 싶은 경우 → **Tape Gateway**

- NAS 같은 파일 서버를 유지하면서도 데이터를 Amazon S3로 자동 업로드 → **File Gateway**

- 온프레미스 DB의 블록 스토리지를 백업하면서 스냅샷을 EC2로 복구할 수 있게 하고 싶을 때 → **Volume Gateway**