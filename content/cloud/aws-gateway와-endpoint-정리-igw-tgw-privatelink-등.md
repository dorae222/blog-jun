---
title: "AWS Gateway와 Endpoint 정리 (IGW, TGW, PrivateLink 등)"
slug: "aws-gateway와-endpoint-정리-igw-tgw-privatelink-등"
category: cloud
tags: ["api-gateway", "aws", "direct-connect", "internet-gateway", "nat-gateway", "private-link", "storage-gateway", "transit-gateway", "vpc"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:03.819707+00:00"
---

AWS에서는 **네트워크 경계 및 내부 연결 경로를 통제**하기 위해 다양한 **Gateway** 및 **Endpoint** 서비스를 제공합니다. 이를 **역할 기반 + 동작 방식 + 연결 대상**에 따라 세 영역으로 나누어 설명합니다.

---

## 1. 인터넷 & 온프레미스 통신 게이트웨이

이들은 AWS와 **외부 세계(인터넷, 온프레미스 데이터센터, 외부 네트워크 등)** 간의 **입출구 역할**을 하는 네트워크 경계 장치입니다.

| 서비스                                    | 역할                       | 설명                                                              | 비고                             |
| -------------------------------------- | ------------------------ | --------------------------------------------------------------- | ------------------------------ |
| **Internet Gateway (IGW)**             | 공용 인터넷 접근                | VPC의 **퍼블릭 서브넷**이 인터넷과 통신할 수 있도록 해주는 게이트웨이. **인바운드/아웃바운드 트래픽을 허용** | 퍼블릭 IP 또는 Elastic IP 필요        |
| **NAT Gateway**                        | 프라이빗 → 인터넷 아웃바운드 전용      | **프라이빗 서브넷의 리소스가 인터넷으로 나갈 수 있도록** 해주며, 외부에서의 인바운드 연결은 허용하지 않음                        | 고정 IP 제공, 관리형 서비스              |
| **NAT 인스턴스**                           | 위와 유사하나 EC2 기반 수동 NAT 구성 | 비용 절감이나 커스터마이징이 필요할 때 사용하는 EC2 기반 NAT 구성                                                | 고가용성은 수동 구성 필요                  |
| **Virtual Private Gateway (VGW)**      | AWS VPC 쪽의 **VPN 터널 끝단** | 온프레미스와의 **Site-to-Site VPN 연결에서 AWS측의 종단점** 역할                | 일반적으로 Customer Gateway와 페어링      |
| **Customer Gateway (CGW)**             | 온프레미스 쪽의 **VPN 라우터**     | 고객 네트워크 장비 또는 가상 장비로, VGW와 VPN 터널을 구성하는 쪽                           | 공인 IP 주소 필요                    |
| **AWS Direct Connect Gateway (DX GW)** | 여러 리전에 있는 VPC 연결용        | Direct Connect 회선을 통해 **멀티리전 VPC 연결** 시 사용                      | Transit Gateway와 연동 가능        |
| **Transit Gateway (TGW)**              | 네트워크 허브                  | 여러 VPC, 온프레미스, VPN, DX 등을 **중앙 허브에서 연결 및 라우팅**하는 관리형 게이트웨이    | TGW Attachment 및 라우트 테이블 구성 필요 |
| **VPN CloudHub**                       | 다중 온프레미스 VPN 허브          | 여러 지사(온프레미스)를 **Site-to-Site VPN으로 상호 연결**하여 통신하도록 함                | VGW 기반 구조 사용                   |

---

## 2. AWS 서비스 접근을 위한 VPC 엔드포인트 (PrivateLink 포함)

VPC 내부에서 퍼블릭 AWS 서비스(S3, DynamoDB 등)에 접근할 때, **인터넷을 거치지 않고 프라이빗 경로로 연결**하기 위해 사용합니다. 이는 **보안 강화와 비용 최적화**에 중요합니다.

| 서비스                             | 유형                | 설명                                                             | 특징                                   |
| ------------------------------- | ----------------- | -------------------------------------------------------------- | ------------------------------------ |
| **Gateway Endpoint**        | 게이트웨이 기반          | **S3, DynamoDB 전용**. 라우팅 테이블에 목적지로 등록하여 VPC에서 직접 접근              | 가장 비용 효율적. S3 접근 제어에 유용            |
| **Interface Endpoint**          | 프라이빗 IP 기반 ENI    | 대부분 AWS 서비스에 대해 ENI(Elastic Network Interface) 형태로 프라이빗 연결 제공 | PrivateLink라고도 불림. 보안 그룹 적용 가능, 고도화된 보안 제공 |
| **VPC Endpoint Service**        | 서비스 제공자 역할        | 내가 만든 서비스(예: NLB 뒤의 서비스)를 **다른 VPC/계정에 프라이빗하게 노출/공유**             | 서비스 제공자는 `PrivateLink Provider` 역할 수행 |
| **Interface Endpoint Consumer** | 외부 PrivateLink 사용 | 다른 계정의 PrivateLink Endpoint Service에 **프라이빗하게 접근**             | SaaS 통합 시 자주 사용                     |

> 🔒 **모든 Endpoint는 기본적으로 퍼블릭 IP 없이 AWS 서비스에 접근할 수 있도록 구성되어, 인터넷 노출 없이 통신이 가능**합니다.

---

## 3. 특수 목적 Gateway (전송, 스토리지, API 등)

이 그룹은 **파일 전송, 온프레미스 연동, API 중계** 등 특정 기능을 수행하는 게이트웨이들입니다.

|서비스|역할|설명|특징|
|---|---|---|---|
|**AWS Storage Gateway**|온프레미스 ↔ AWS 스토리지 브리지|온프레미스 애플리케이션이 AWS 스토리지를 로컬처럼 사용할 수 있도록 연결|File/Volume/Tape 3가지 모드|
|**AWS Transfer Family**|SFTP/FTPS/FTP 전송 인터페이스|기업 내부 시스템이 SFTP 등을 통해 **Amazon S3로 데이터를 전송/수신**할 수 있도록 지원|인증 연동(OIDC, IAM, LDAP 등)|
|**API Gateway**|API 트래픽 제어|서버리스 또는 백엔드 앞에서 **API 요청을 인증, 라우팅, 제한**하는 관리형 서비스|CORS, 캐시, 키 관리, 모니터링 제공|
|**CloudFront Origin Access**|CDN 보안 경로 설정|CloudFront가 S3 오리진에 안전하게 접근하도록 허용하는 전용 설정|OAC(Origin Access Control) 또는 OAI 사용|
|**Amazon AppFlow Gateway 구성**|SaaS 앱 ↔ AWS 데이터 흐름 자동화|Salesforce, Slack, Google Workspace 등과의 **보안 연결 기반 데이터 흐름 자동화**|Glue 기반 동작, 암호화 지원|

---

## 정리: Gateway & Endpoint 분류 트리

```
▶ 외부 연결 게이트웨이
   ├─ Internet Gateway
   ├─ NAT Gateway / NAT Instance
   ├─ Virtual Private Gateway ↔ Customer Gateway
   ├─ Transit Gateway
   └─ Direct Connect Gateway

▶ 서비스 접근용 엔드포인트
   ├─ Gateway Endpoint (S3, DynamoDB)
   ├─ Interface Endpoint (PrivateLink)
   └─ VPC Endpoint Service / Consumer

▶ 특수 기능 게이트웨이
   ├─ AWS Storage Gateway
   ├─ AWS Transfer Family
   ├─ API Gateway
   └─ 기타 (CloudFront OAC, AppFlow 등)
```

---

## 추가 Tip: 실전 사용 예

|상황|사용 게이트웨이 / 엔드포인트|
|---|---|
|EC2에서 S3에 비용 효율적으로 접근|**Gateway Endpoint (S3)**|
|EC2에서 S3에 보안그룹 기반 접근|**Interface Endpoint**|
|다수의 VPC 및 온프레미스 간 연결|**Transit Gateway**|
|하이브리드 스토리지 구성|**AWS Storage Gateway**|
|인터넷 없이 SFTP로 S3 접근|**AWS Transfer Family**|
|SaaS 앱 연동 및 ETL|**AppFlow + Interface Endpoint**|

---

## 요약 표

| 분류         | 서비스                        | 주요 사용 목적             |
| ---------- | -------------------------- | -------------------- |
| 🌐 네트워크 경계 | IGW, NAT GW, VGW, TGW 등    | 인터넷 및 온프레미스 통신       |
| 🔒 서비스 연결  | Gateway/Interface Endpoint | 프라이빗한 AWS 서비스 접근     |
| 📦 특수 목적   | Transfer, Storage, API GW  | 파일 전송, 하이브리드, API 중계 |
