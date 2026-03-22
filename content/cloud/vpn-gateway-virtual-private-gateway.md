---
title: VPN Gateway (Virtual Private Gateway)
slug: "vpn-gateway-virtual-private-gateway"
category: cloud
tags: ["aws", "bgp", "customer-gateway", "hybrid-cloud", "ipsec", "transit-gateway", "vgw", "virtual-private-gateway", "vpn"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:08.025168+00:00"
---

**VPN Gateway**는 AWS에서 제공하는 **Virtual Private Network (VPN)** 연결을 위한 **가상 게이트웨이(Virtual Private Gateway, VGW)**로, 온프레미스 네트워크 또는 다른 클라우드 환경을 **AWS VPC와 안전하게 연결하는 암호화된 터널**을 생성하는 데 사용됩니다.

---

## 🌐 VPN Gateway란?

> **AWS VPN Gateway**는 온프레미스 데이터 센터 또는 다른 클라우드 환경을 **IPSec VPN 터널을 통해 AWS의 VPC와 연결**할 수 있도록 해주는
> **가상 네트워크 게이트웨이**입니다. 내부적으로는 **Virtual Private Gateway (VGW)** 또는 **Transit Gateway와 연결된 VPN Attachment**를 사용합니다.

---

## 🔧 구성 방식

AWS에서 VPN 연결을 만들기 위해 다음 두 가지 구성 요소가 필요합니다:

|구성 요소|설명|
|---|---|
|**Virtual Private Gateway (VGW)**|AWS 쪽에 배치된 가상 장비 (VPC에 연결됨)|
|**Customer Gateway (CGW)**|고객 쪽(온프레미스 또는 외부 클라우드)의 VPN 디바이스 (라우터, 방화벽 등)|

→ 이 둘 사이에 **IPSec 기반 암호화 터널 1~2개**가 생성됩니다.

---

## 🔐 특징 및 기능

|기능|설명|
|---|---|
|**IPSec 암호화**|모든 데이터는 **암호화된 터널을 통해 전송**|
|**HA 구성 지원**|기본적으로 **2개의 터널**을 생성하여 고가용성 제공|
|**라우팅 지원**|**동적 라우팅 (BGP)** 또는 **정적 라우팅** 모두 가능|
|**CloudWatch 연동**|트래픽 및 연결 상태 모니터링 가능|
|**멀티 리전 지원**|여러 리전 간 VPN 연결 구성 가능|

---

## 🧭 사용 사례

- 온프레미스 데이터센터 ↔ AWS VPC 연결 (하이브리드 클라우드)
- AWS ↔ 타 클라우드 환경 연결
- 테스트용 보안 네트워크 통신
- Direct Connect와 결합한 백업 경로 구성

---

## 🆚 VPN Gateway vs Transit Gateway

|항목|Virtual Private Gateway (VGW)|AWS Transit Gateway (TGW)|
|---|---|---|
|확장성|1:1 연결 중심|N:1 연결 가능 (허브 앤 스포크 구조)|
|복잡성|간단|복잡하지만 유연|
|사용 대상|소규모 또는 단일 VPC 연결|대규모 네트워크 통합 필요 시|

---

## 📌 참고 명령어 예시 (CLI)

```bash
aws ec2 create-vpn-connection \
  --type ipsec.1 \
  --customer-gateway-id cgw-123456 \
  --vpn-gateway-id vgw-abcdef \
  --options '{"StaticRoutesOnly":false}'
```

---

## ✅ 요약

|항목|내용|
|---|---|
|이름|**VPN Gateway (Virtual Private Gateway)**|
|목적|온프레미스 또는 외부 네트워크와 **AWS VPC 간 보안 연결** 구성|
|프로토콜|**IPSec VPN (암호화된 터널)**|
|구성 요소|**VGW (AWS 측)** + **CGW (고객 측)**|
|주요 사용|하이브리드 클라우드, 보안 네트워크 통신, 백업 경로|
