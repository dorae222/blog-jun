---
title: Internet Small Computer Systems Interface (iSCSI)
slug: "internet-small-computer-systems-interface-iscsi"
category: cloud
tags: ["aws", "block-storage", "chap", "ebs", "fibre-channel", "iscsi", "network-storage", "san", "storage", "tcp-ip"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:07.029241+00:00"
---

**Internet Small Computer Systems Interface (iSCSI)**는
**TCP/IP 네트워크를 통해 원격 저장 장치(디스크)를 로컬 디스크처럼 사용할 수 있게 해주는 스토리지 프로토콜**입니다. 즉, 네트워크를 통해 **SCSI(저장 장치 명령어)를 주고받을 수 있도록 만든 표준**입니다.

---

## 🔍 iSCSI란?

> **iSCSI(아이-스커지)**는
> **SCSI(Storage Command Protocol)를 TCP/IP 네트워크 위에서 전달하는 프로토콜**입니다.
> 이를 통해 **스토리지 장치를 이더넷 네트워크를 통해 서버와 연결**할 수 있습니다.
> 일반적인 이더넷을 통해 **SAN(Storage Area Network)** 환경을 구축할 수 있게 하며,
> **비교적 저렴하고 손쉽게 네트워크 스토리지를 구성**할 수 있다는 장점이 있습니다.

---

## 🏗️ 작동 구조

```plaintext
[서버 또는 클라이언트 (iSCSI Initiator)]
            │ (TCP/IP)
            ▼
[스토리지 디바이스 (iSCSI Target)]
```

- **Initiator**: iSCSI 요청을 보내는 주체 (서버, EC2 인스턴스 등)
- **Target**: 디스크 역할을 하는 저장소 (NAS, SAN 또는 EBS 볼륨 등)

---

## 📚 주요 특징

|항목|설명|
|---|---|
|프로토콜|TCP 포트 3260 사용|
|네트워크|기존 이더넷 기반 네트워크 사용 가능|
|호환성|기존 스토리지 장치 및 운영체제와 호환|
|사용 사례|SAN 구성, 클라우드 블록 스토리지, VM 디스크 공유 등|
|보안 옵션|CHAP 인증, IPsec, ACL 지원 가능|

---

## ✅ iSCSI의 장점

- ✅ **일반 이더넷 네트워크로 SAN 구현 가능** (전용 파이버 채널 불필요)
- ✅ **블록 수준 스토리지 제공** (파일 시스템보다 유연)
- ✅ **AWS EC2에서 iSCSI 사용** → Amazon EBS가 내부적으로 사용

---

## ❗ 유의사항

- **네트워크 성능에 따라 I/O 지연 발생 가능**
- 고성능 환경에서는 전용 스토리지 네트워크(예: Fibre Channel)가 필요할 수 있음

---

## ✅ 요약

|항목|내용|
|---|---|
|이름|Internet Small Computer Systems Interface (**iSCSI**)|
|목적|**TCP/IP 위에서 SCSI 명령 전송 → 원격 스토리지 사용**|
|구성 요소|**Initiator (요청자)** ↔ **Target (저장소)**|
|사용 예시|SAN 구성, AWS EBS 내부 프로토콜 등|
|포트|TCP 3260|