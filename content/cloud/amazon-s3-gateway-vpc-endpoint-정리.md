---
title: Amazon S3 Gateway VPC Endpoint 정리
slug: "amazon-s3-gateway-vpc-endpoint-정리"
category: cloud
tags: ["amazon-s3", "aws", "aws-networking", "dynamodb", "nat-gateway", "s3-gateway-endpoint", "security", "vpc", "vpc-endpoint"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:06.836245+00:00"
---

- NAT 게이트웨이를 통한 아웃바운드 인터넷 트래픽을 줄일 수 있습니다. 이는 NAT 게이트웨이의 데이터 전송 비용을 절감합니다.

- **Amazon S3 Gateway Endpoint**는 **프라이빗 VPC 네트워크 안에서 S3에 직접 접근할 수 있도록 해주는 엔드포인트**입니다.
	- **인터넷 게이트웨이(IGW)나 NAT 게이트웨이 없이도 S3에 안전하게 연결**할 수 있습니다.

---

## 🌐 S3 Gateway Endpoint란?

> **S3 Gateway Endpoint**는 **VPC에서 Amazon S3로 가는 트래픽을 AWS 내부 네트워크 경로로 전달**하는 **VPC 엔드포인트(VPC Endpoint)** 유형 중 하나입니다.  
> 즉, **퍼블릭 인터넷을 우회하여 S3에 비공개로 연결**할 수 있게 합니다.

---

## ✅ 왜 사용하는가?

| 필요성              | 설명                                                      |
| ---------------- | ------------------------------------------------------- |
| **보안 강화**        | 인터넷을 통하지 않고 S3에 접근 가능 (공인 IP 필요 없음)                     |
| **비용 절감**        | NAT Gateway 사용 비용 절감 (트래픽 요금 포함) → 아웃바운드 인터넷 트래픽 감소 |
| **내부 네트워크 설계**   | S3 접근을 프라이빗한 환경에서 구성 가능                                 |
| **IAM 정책 제어 가능** | 특정 리소스만 접근 허용하는 정책 적용 가능                                |

---

## 🧱 구성 방식

|구성 요소|설명|
|---|---|
|**VPC**|Private 서브넷 또는 전체 네트워크|
|**S3 Gateway Endpoint**|VPC 라우팅 테이블에 등록되어 트래픽을 내부로 전송|
|**라우팅 테이블**|S3 CIDR 범위 (`pl-68a54001` 등)를 Gateway Endpoint로 연결|
|**IAM 정책 (선택)**|어떤 S3 버킷/프리픽스에 접근 가능한지 제어 가능|

---

## 🔁 S3 Gateway Endpoint vs Interface Endpoint

|항목|Gateway Endpoint (S3, DynamoDB)|Interface Endpoint (다른 서비스용)|
|---|---|---|
|**작동 방식**|라우팅 테이블 기반|ENI(Elastic Network Interface) 생성|
|**지원 서비스**|S3, DynamoDB만|대부분의 AWS 서비스|
|**비용**|**무료**|ENI당 비용 발생|
|**설정 위치**|VPC Route Table|VPC Subnet 내부 (ENI)|

---

## ✅ 예시 사용 시나리오

> 어떤 회사가 EC2 인스턴스를 **Private Subnet에 배치**하고, S3 버킷에 애플리케이션 로그를 업로드하려고 한다.  
> NAT Gateway 없이 S3에 접속해야 하므로 → **S3 Gateway Endpoint 사용**이 가장 효율적.

---

## 📌 요약

|항목|내용|
|---|---|
|정식 이름|**Amazon S3 Gateway VPC Endpoint**|
|목적|**VPC 내부에서 S3에 안전하게 연결**|
|장점|인터넷 게이트웨이 없이 연결 가능, 비용 절감, 보안 강화|
|제한|S3 및 DynamoDB 전용|
|요금|**무료** (트래픽 요금은 별도)|

---

필요하시면 설정 예시, Terraform 코드, IAM 정책 샘플도 도와드릴게요!