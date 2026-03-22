---
title: AWS Systems Manager 개요 및 주요 기능
slug: "aws-systems-manager-개요-및-주요-기능"
category: cloud
tags: ["aws", "opscenter", "parameter-store", "patch-manager", "session-manager", "ssm", "ssm-agent", "systems-manager"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:04.517427+00:00"
---

- AWS Systems Manager OpsItems
- Parameter Store
- Amazon SSM Managed Instance Core

**AWS Systems Manager**는
AWS에서 제공하는 **인프라스트럭처 운영 및 관리를 위한 통합 서비스**입니다.
서버, 가상 머신, 컨테이너 등 다양한 **AWS 및 온프레미스 자원**을 **자동화, 관찰, 패치, 설정 관리**할 수 있게 도와줍니다.

---

## 🔍 AWS Systems Manager란?

> **AWS Systems Manager**는 하나의 인터페이스에서
> AWS 및 온프레미스 리소스를 **중앙에서 관리하고 운영 자동화**를 구현할 수 있는 서비스입니다.
> 서버의 상태 모니터링, 원격 명령 실행, 패치 적용, 구성 추적 등 **운영자의 반복 작업을 자동화하고 보안적으로 수행**하게 해줍니다.

---

## 🧩 주요 기능 구성 요소

| 기능                                                           | 설명                                              |
| ------------------------------------------------------------ | ----------------------------------------------- |
| **Session Manager**                 | EC2에 SSH 없이 **웹 브라우저 기반 안전한 원격 접속** 제공          |
| **Parameter Store** | **암호, 구성 값, 문자열 매개변수**를 안전하게 저장 및 관리            |
| **Patch Manager**                                        | OS 및 소프트웨어 **보안 패치 자동화 및 관리**                   |
| **Systems Manager Automation**                                           | 운영 작업(예: 백업, 리소스 리부팅 등)의 **워크플로우 자동화**          |
| **Inventory**                                                | 인스턴스의 **소프트웨어 및 설정 정보 수집** 및 조회                 |
| **State Manager**                                            | **EC2 초기 설정/구성 상태 유지** 자동화 (예: 에이전트 설치, 크론잡 등록) |
| **OpsCenter**                                                | 인시던트 및 운영 이슈를 통합적으로 관리하고 분석하는 대시보드              |
| **Fleet Manager**                                            | 모든 인스턴스를 **한 곳에서 UI로 중앙 관리** (파일, 로그, 사용자 등 탐색) |
| **Maintenance Windows**                                  | 특정 시간에만 **패치, 명령 실행, 자동화 작업을 예약 실행**할 수 있도록 지원  |

---

## 🏗️ 아키텍처 예시

```text
[관리 대상 인스턴스 (EC2/온프레미스)] ← SSM Agent
         │
         ▼
 [AWS Systems Manager 콘솔 / CLI / SDK]
         │
         ▼
 [SSM 서비스: Session Manager, Patch Manager, Parameter Store 등]
```

- **SSM Agent**: EC2나 온프레미스 서버에 설치되어 명령을 수신하고 실행
    
- **IAM Role**: SSM 기능을 수행하기 위한 적절한 권한 필요 (예: AmazonSSMManagedInstanceCore)
    

---

## 🔐 보안 측면 장점

|항목|설명|
|---|---|
|**SSH 키 없이 접속**|Session Manager로 **프라이빗 네트워크 내부에서도 안전하게 원격 연결** 가능|
|**로그 기록**|CloudTrail 및 CloudWatch Logs로 모든 명령 실행 내역 기록|
|**IAM 기반 제어**|누구에게 어떤 인스턴스 접근 권한을 줄지 명확하게 통제 가능|

---

## ✅ 요약

|항목|내용|
|---|---|
|이름|**AWS Systems Manager**|
|역할|**AWS 및 온프레미스 리소스 운영 및 자동화 관리 도구**|
|주 대상|EC2, 하이브리드 서버, IoT 디바이스 등|
|핵심 기능|Session Manager, Parameter Store, Patch Manager, Automation 등|
|필요 구성|IAM Role + SSM Agent + VPC Endpoint (옵션)|
|주요 이점|운영 자동화, 중앙 통제, 보안 강화, 로그 추적성 확보|