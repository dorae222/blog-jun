---
title: AWS Systems Manager Agent (SSM Agent)
slug: "aws-systems-manager-agent-ssm-agent"
category: cloud
tags: ["aws", "devops", "ec2", "iam", "inventory", "patch-management", "session-manager", "ssm-agent", "systems-manager"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:04.489198+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A


---
---
aliases:
  - SSM Agent
---
**AWS Systems Manager Agent (SSM Agent)**는 AWS Systems Manager 서비스가 EC2 인스턴스, 온프레미스 서버, 또는 가상 머신과 **통신하고 관리 작업을 실행할 수 있게 해주는 소프트웨어**입니다.

즉, **Systems Manager의 명령과 작업을 대상 시스템에서 실제로 수행하는 에이전트 역할**을 합니다.

---

## 🔧 SSM Agent란?

> **SSM Agent**는 AWS Systems Manager의 **핵심 구성 요소 중 하나**로, EC2 인스턴스나 온프레미스 서버에 설치되어 있어야 Systems Manager의 기능이 정상적으로 동작합니다.

---

## 🛠️ 주요 역할

|역할|설명|
|---|---|
|🎯 **명령 실행**|Run Command, Automation 문서 실행 등을 인스턴스에서 수행합니다.|
|🔍 **인벤토리 수집**|OS, 설치된 소프트웨어, 패치 상태 등 정보를 수집하여 Systems Manager에 전달합니다.|
|💬 **Session Manager**|SSH 없이 브라우저나 콘솔을 통해 EC2 인스턴스에 접속할 수 있으며 접속 로그가 기록됩니다.|
|🩹 **패치 관리**|Patch Manager와 연동하여 패치 적용을 자동화합니다.|
|📦 **소프트웨어 설치/제거**|State Manager와 연동해 소프트웨어 설치, 제거 및 구성 관리를 수행합니다.|

---

## 📦 설치 대상 및 방법

|항목|설명|
|---|---|
|**EC2 인스턴스**|Amazon Linux, Ubuntu, Windows 등 대부분의 OS에 **기본 설치되어 있는 경우가 많음** 또는 제공되는 AMI에 포함되어 있습니다.|
|**온프레미스 서버**|설치 스크립트나 패키지 관리자를 통해 수동으로 설치할 수 있습니다.|
|**SSM Agent 설치 확인 명령어 (Linux)**|`sudo systemctl status amazon-ssm-agent`|

> 💡 최신 AMI(예: Amazon Linux 2)에는 기본으로 포함되어 있으며, SSM Agent는 **백그라운드 서비스로 실행**됩니다.

---

## 🔐 IAM 권한 필요

SSM Agent가 정상적으로 동작하려면 EC2 인스턴스에 연결된 **IAM 역할**에 다음과 같은 권한이 포함되어야 합니다:

- `AmazonSSMManagedInstanceCore` (AWS 관리형 정책)

---

## 🔄 동작 예시

1. 사용자가 **Systems Manager 콘솔**에서 "Run Command"를 요청합니다.
2. Systems Manager가 대상 인스턴스의 **SSM Agent에 명령을 전송**합니다.
3. SSM Agent가 명령을 **로컬에서 실행**합니다.
4. 실행 결과를 **Systems Manager로 다시 전송**합니다.

---

## 📌 요약

|항목|설명|
|---|---|
|이름|**AWS Systems Manager Agent (SSM Agent)**|
|기능|Systems Manager와 EC2 인스턴스 등 대상 시스템 간 통신을 담당하는 에이전트|
|설치 위치|EC2 인스턴스, 온프레미스 서버, 가상 머신 등|
|역할|명령 실행, 소프트웨어 설치/제거, 원격 접속(Session Manager), 인벤토리 수집, 패치 관리 등|
|IAM 필요 권한|`AmazonSSMManagedInstanceCore` 정책이 포함된 역할|
