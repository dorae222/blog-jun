---
title: VPC Flow Logs
slug: "vpc-flow-logs"
category: cloud
tags: ["aws", "cloud", "cloudwatch-logs", "networking", "network-monitoring", "s3", "security", "vpc", "vpc-flow-logs"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:07.995903+00:00"
---

**VPC Flow Logs**는 AWS Virtual Private Cloud(VPC)에서 네트워크 트래픽의 흐름을 기록하는 기능입니다. 즉, VPC 내부에서 어떤 트래픽이 오고 가는지를 모니터링하고 분석할 수 있게 해주는 로깅 서비스입니다.

---

## 🌐 VPC Flow Logs란?

> **VPC Flow Logs**는 VPC, 서브넷 또는 네트워크 인터페이스(ENI) 수준에서 발생하는 **IP 트래픽 정보**를
> **Amazon CloudWatch Logs 또는 S3에 저장**하여
> **보안 분석, 트래픽 감시, 문제 해결 및 감사** 등에 활용할 수 있는 기능입니다.

---

## 📦 어떤 정보가 기록되나요?

각 로그 항목은 다음과 같은 정보를 포함합니다:

|항목|설명|
|---|---|
|`srcaddr`|소스 IP 주소|
|`dstaddr`|목적지 IP 주소|
|`srcport` / `dstport`|포트 정보|
|`protocol`|사용된 프로토콜 (TCP, UDP 등)|
|`action`|`ACCEPT` 또는 `REJECT`|
|`bytes` / `packets`|송수신된 바이트와 패킷 수|
|`interface-id`|ENI (네트워크 인터페이스 ID)|
|`log-status`|정상 기록 여부 (`OK`, `NODATA`, `SKIPDATA`) 등|

---

## 🎯 주요 사용 사례

|목적|설명|
|---|---|
|**보안 분석**|예: 비정상적인 IP로부터의 접근 시도 탐지|
|**트래픽 모니터링**|어떤 서비스가 얼마나 네트워크를 사용 중인지 확인|
|**운영 문제 해결**|인스턴스 간 통신 문제나 라우팅 오류 추적|
|**컴플라이언스 감사**|규정상 트래픽 기록이 필요한 경우 사용|

---

## 🛠️ 설정 위치

VPC Flow Logs는 다음 대상에 대해 설정할 수 있습니다:

- **VPC 전체**
- **개별 서브넷**
- **개별 ENI (Elastic Network Interface)**

📍 로그는 **CloudWatch Logs 그룹** 또는 **S3 버킷**으로 전송 가능합니다.

---

## ⚠️ 주의사항

- **암호화된 트래픽의 콘텐츠**는 로깅되지 않습니다 (IP 헤더 수준 정보만 기록됩니다).
- **로그 생성에는 지연이 발생**할 수 있습니다 (보통 수분 내에 기록됨).
- Flow Logs는 **INBOUND**, **OUTBOUND** 방향을 선택하여 생성할 수 있습니다.
- **CloudWatch Logs 사용 시 과금**이 발생합니다 (로그 저장 및 전송 비용).

---

## ✅ 요약

|항목|내용|
|---|---|
|이름|**VPC Flow Logs**|
|목적|**VPC 내 네트워크 트래픽을 모니터링하고 분석**|
|기록 대상|VPC, 서브넷, ENI|
|저장 위치|CloudWatch Logs, S3|
|사용 용도|보안, 운영 문제 해결, 감사 등|
