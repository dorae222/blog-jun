---
title: AWS Direct Connect 정리
slug: "aws-direct-connect-정리"
category: cloud
tags: ["aws", "direct-connect", "dx", "hybrid-cloud", "networking", "site-to-site-vpn", "transit-gateway", "vpc"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:03.734070+00:00"
---

> **NOTE:**
> - AWS와 온프레미스 간에 DX(Direct Connect) Location을 통한 전용선을 통해 프라이빗 네트워크 연결 생성
> - 포트당 1Gbps, 10Gbps, 100Gbps 연결 속도 사용 가능
> - 물리적인 구성을 해야 하기에 설치 시간이 오래 걸림
> - VPN보다 가격이 비싸며 인터넷을 통하지 않기에 인터넷 전송 비용이 들지 않음
> - 기본적으로 암호화를 지원하지 않음
> 	- 암호화를 위해 Direct Connect에 VPN을 구성 가능
> - 트래픽이 인터넷 연결을 사용하는 AWS Site-to-Site VPN보다 안정적

**AWS Direct Connect**는 **온프레미스 네트워크와 AWS 간에 전용 물리 회선을 통해 고속·저지연 연결을 제공하는 서비스**입니다. 

- <mark style="background: #FFF3A3A6;">설치 기간이 한 달 이상 걸린다.</mark>
- 암호화는 기본적으로 제공되지 않지만, Private Connect이므로 물리적 분리로 보안성이 높습니다.
  - 암호화가 필요하면 Direct Connect 상에 VPN(IPsec 암호화된 프라이빗 연결)을 구성할 수 있습니다.

---

## 🌐 AWS Direct Connect란?

> **AWS Direct Connect**는 사용자의 **데이터센터, 지사, 코로케이션 환경과 AWS 간을 직접 연결**해 주는  
> **전용 네트워크 서비스**입니다.  
> 이 연결은 **인터넷을 거치지 않고 AWS 네트워크와 직접 연결**되므로,  
> **더 안정적이고 빠르며 보안성이 높습니다.**

---

## 🏗️ 동작 방식

```text
[온프레미스 네트워크]
        │  (전용 선로)
        ▼
[Direct Connect 로케이션]
        ▼
[AWS Direct Connect 라우터]
        ▼
[VPC / AWS 리소스]
```

사용자는 **AWS가 제공하는 Direct Connect 로케이션에 라우터를 설치하거나 연결**하고,  
그를 통해 AWS VPC 또는 다른 서비스에 연결합니다.

---

## 🚀 주요 특징

|기능|설명|
|---|---|
|**전용 연결**|인터넷이 아닌 **전용 물리적 선로** 사용|
|**높은 대역폭**|1Gbps ~ 100Gbps 지원|
|**안정성**|인터넷보다 **지연 시간 짧고 안정적**|
|**보안성**|**공용 인터넷을 우회**하므로 보안 우수|
|**하이브리드 클라우드**|온프레미스와 AWS 간 **통합 네트워크 아키텍처 구현** 가능|

---

## 📦 용어 정리

| 용어                               | 설명                                                            |
| -------------------------------- | ------------------------------------------------------------- |
| **DX 로케이션**                  | Direct Connect를 물리적으로 제공하는 글로벌 장소 (데이터센터 등)                   |
| **Virtual Interface (VIF)**      | Direct Connect 회선을 통해 AWS 서비스에 연결하는 가상 인터페이스 (Private/Public) |
| **LAG (Link Aggregation Group)** | 여러 연결을 묶어서 고가용성 및 대역폭 확보                                      |

---

## 🧩 Direct Connect 연결 방식

|방식|설명|
|---|---|
|**Private VIF**|AWS VPC 내부에 직접 연결 (예: EC2, RDS 등)|
|**Public VIF**|S3, DynamoDB 등 **퍼블릭 AWS 서비스에 직접 연결**|
|**Transit VIF**|**Transit Gateway를 통해 여러 VPC에 연결**|

---

## 🆚 Direct Connect vs VPN

|항목|AWS Direct Connect|AWS VPN|
|---|---|---|
|경로|**전용 회선**|**인터넷 경유 (IPSec 암호화)**|
|지연 시간|낮음|상대적으로 높음|
|속도|최대 100Gbps|제한적|
|안정성|매우 높음|인터넷 품질에 따라 달라짐|
|보안성|물리적 경로 + 선택적 암호화|암호화 필수|
|비용|높음 (회선 비용 포함)|상대적으로 저렴|

---

## ✅ 요약

|항목|설명|
|---|---|
|이름|**AWS Direct Connect**|
|목적|**온프레미스 ↔ AWS 간 고속, 안정적, 보안성 높은 전용 연결**|
|연결 방식|**물리적 전용선 + 가상 인터페이스(VIF)**|
|주요 이점|낮은 지연, 높은 대역폭, 안정성, 보안성|
|활용 예|금융, 게임, 대기업, 하이브리드 클라우드 환경|

- AWS Direct Connect Gateway

---

## 🔗 Connection Types (연결 유형)

| 유형                                        | 설명                                                                | 대역폭                            | 주체          |
| ----------------------------------------- | ----------------------------------------------------------------- | ------------------------------ | ----------- |
| **Dedicated Connection**                  | 고객이 AWS와 **직접 계약**하여 **물리적 포트(1G/10G/100G)**를 프로비저닝               | 1Gbps, 10Gbps, 100Gbps         | **고객 직접**   |
| **Hosted Connection**                     | **AWS 파트너(Direct Connect 파트너)**를 통해 **가상 포트** 제공. 고객은 **파트너와 계약** | 50Mbps ~ 10Gbps (1Gbps 이하도 가능) | **AWS 파트너** |
| **Hosted Virtual Interface (Hosted VIF)** | Direct Connect 파트너가 고객에게 **VIF만 제공**. 실제 포트는 공유됨                  | 50Mbps ~ 5Gbps                 | **AWS 파트너** |
| **Link Aggregation Group (LAG)**          | 여러 개의 Dedicated Connection을 **하나의 논리 연결**로 묶어 고가용성과 확장성 확보        | 여러 포트를 묶음                      | 고객 직접       |

---

## 🎯 선택 기준 요약

|목적|추천 연결 유형|
|---|---|
|대기업, 고대역폭, 독립 관리|**Dedicated Connection**|
|빠른 구축, 유연한 속도, 파트너 이용|**Hosted Connection**|
|비용 절감, 소규모 연결|**Hosted VIF**|
|고가용성 및 이중화|**LAG (Link Aggregation Group)**|
