---
title: "🛡️ AWS Network Firewall란?"
slug: "-aws-network-firewall란"
category: cloud
tags: ["aws", "cloudwatch", "firewall-manager", "gateway-load-balancer", "ips", "network-firewall", "s3", "security", "vpc"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:04.171045+00:00"
---

AWS Network Firewall은 Amazon VPC 환경에서 동작하는 관리형 네트워크 보안 서비스로, VPC 트래픽을 세밀하게 제어하고 L3~L7까지의 트래픽 보호 및 필터링을 제공합니다.

### ✅ 핵심 목적

- VPC 전체 보호
- 인바운드/아웃바운드 및 VPC 간 트래픽 제어
- 악성 트래픽 탐지 및 차단
- 규칙 기반 제어와 상태 기반(Stateful) 검사 병행

![](/media/posts/imported/aws/Pasted%20image%2020250708083045.png)

---

## 🔍 특징 요약

|항목|설명|
|---|---|
|**보호 범위**|VPC 전체 (VPC 간, 인터넷, Direct Connect, VPN 포함)|
|**계층**|**Layer 3 ~ Layer 7** (IP부터 애플리케이션 계층까지)|
|**트래픽 방향**|VPC ↔ VPC, VPC ↔ Internet, VPC ↔ Direct Connect, VPN 등|
|**구성 요소**|AWS Gateway Load Balancer 내부에서 동작|
|**운영 방식**|AWS 관리형, 자동 확장 지원|
|**관리**|AWS Firewall Manager로 여러 계정·VPC에 중앙 관리 가능|

---

## 🎯 제어 기능 – AWS Network Firewall Fine-Grained Controls

| 기능                             | 설명                                                           |
| ------------------------------ | ------------------------------------------------------------ |
| **수천 개 규칙**                    | IP, 포트, 프로토콜 기반 필터링                                          |
| **정책 기반 필터링**                  | SMB, DNS, 커스텀 도메인 등 차단 또는 허용                                 |
| **Regex 필터**                   | 정규 표현식으로 패턴 매칭 트래픽 제어                                        |
| **상태 기반 룰 그룹**                 | 예: `*.mycorp.com`만 허용                                        |
| **==Traffic Filtering==**      | Allow / Drop / Alert 설정 가능                                   |
| **==Active Flow Inspection==** | 침입 방지용 흐름 분석 (IPS 기능 포함)                                     |
| **로그 전송**                      | Amazon S3, CloudWatch Logs, Kinesis Data Firehose 로 로그 전송 가능 |

---

## 🧱 아키텍처 예시 (이미지 참고)

- VPC 경계에 Network Firewall 배치
- Private Subnet 보호
- 인터넷, Direct Connect, Site-to-Site VPN, Peered VPC 등 외부와 통신하는 경로에 방화벽 적용
- 내부적으로 Gateway Load Balancer를 사용하여 자동 확장 및 고가용성 유지

---

## ✅ 요약 정리

|항목|내용|
|---|---|
|서비스 이름|**AWS Network Firewall**|
|보호 범위|**Amazon VPC 전체 트래픽** (양방향)|
|지원 계층|**Layer 3 ~ Layer 7**|
|주요 기능|상태 기반 검사, 프로토콜/IP 필터링, 도메인 제한, Regex 매칭|
|통합|**AWS Firewall Manager, Gateway Load Balancer**|
|활용 사례|보안 경계 강화, 내부/외부 트래픽 제어, 중앙 집중 보안 관리|

---

필요하시면 실습 예제, 정책 구성 가이드, CloudWatch와 연동하는 로깅 예시도 알려드릴게요!