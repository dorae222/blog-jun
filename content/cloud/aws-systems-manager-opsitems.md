---
title: AWS Systems Manager OpsItems
slug: "aws-systems-manager-opsitems"
category: cloud
tags: ["automation", "aws", "aws-config", "aws-systems-manager", "cloudwatch", "incident-management", "opscenter", "opsitems", "runbook"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:04.500526+00:00"
---

## 📌 **AWS Systems Manager란?**

AWS Systems Manager(SSM)는 여러 AWS 리소스를 운영·관리하기 위한 통합 관리 서비스입니다. 그 안에는 다양한 기능이 있고, 그중 OpsCenter라는 콘솔이 있습니다. 👉 OpsCenter에서 관리되는 개별 항목이 바로 OpsItem(Ops 아이템)입니다.

---

## 🔎 **OpsItems란 무엇?**

**OpsItem** = **운영 이슈(Operational Issue)를 표준화된 티켓처럼 모아놓은 항목**

- AWS 계정에서 발생한 **경고, 알림, 비정상 상태, 이벤트**를 모아 한눈에 보고 관리할 수 있도록 하는 항목입니다.
- 예를 들어 CloudWatch 알람, Config 규정 위반, AWS Health 이벤트 등이 발생하면 **OpsItem으로 자동 생성**될 수 있습니다.

👉 OpsCenter 콘솔에서 OpsItem을 확인하고,
👉 해당 이슈를 트래킹하며,
👉 필요한 경우 Automation runbook 등을 실행해서 대응할 수 있습니다.

---

## ✨ **OpsItems가 왜 필요할까?**

기존에는 운영 중에 알람이 울리면 이메일, Slack, 다른 티켓 시스템 등에서 따로따로 관리해야 했습니다. OpsItems를 사용하면:

✅ **중앙화된 관리**

- 여러 AWS 리소스의 이슈를 **한 곳에서 통합 관리**할 수 있습니다.

✅ **추적과 히스토리**

- 누가, 언제, 어떤 조치를 했는지 OpsItem 안에서 기록됩니다.

✅ **자동화된 대응**

- OpsItem에서 바로 **Automation runbook**을 실행하거나,
- 관련된 리소스를 OpsCenter에서 바로 확인할 수 있습니다.

✅ **우선순위와 상태 관리**

- OpsItem은 **심각도(Severity)**, 상태(Open/In progress/Resolved), 담당자(Assignee) 등을 지정해 실제 운영 티켓처럼 관리할 수 있습니다.

---

## 🛠️ **OpsItems가 어떻게 생성되나?**

- **자동 생성:**
  - CloudWatch 알람이 발생했을 때
  - AWS Config 규칙 위반이 감지됐을 때
  - AWS Health 이벤트가 발생했을 때
  - 다른 SSM Automation에서 오류가 발생했을 때
    → OpsItem이 자동으로 생성됩니다.

- **수동 생성:**
  - 운영자가 OpsCenter에서 "새 OpsItem 만들기"로 이슈를 직접 등록할 수 있습니다.

---

## 💡 **OpsItem에 담기는 정보**

|항목|설명|
|---|---|
|Title|이슈의 제목|
|Description|이슈 내용|
|Severity|심각도 (예: 1-Critical, 2-High 등)|
|Source|이 OpsItem을 만든 서비스 (CloudWatch, Config 등)|
|Related Resources|연결된 EC2, S3 등 리소스 정보|
|Status|Open / In progress / Resolved|
|Automation|실행한 Runbook 기록|

---

## 📦 **활용 예시**

✔ **예시 1: EC2 인스턴스 상태 이상**

- CloudWatch 알람 발생 → OpsItem 생성 →
  OpsCenter에서 인스턴스 ID 확인 → Automation 실행으로 재부팅

✔ **예시 2: Config 규칙 위반**

- S3 버킷이 퍼블릭하게 열림 → Config가 위반 감지 → OpsItem 생성 →
  OpsCenter에서 위반된 리소스를 확인 → Remediation runbook 실행

---

## 🎯 **비유로 쉽게 이해하기**

🗂️ **OpsItems = AWS 운영용 티켓 시스템의 개별 티켓**

- 이슈가 생기면 티켓이 자동 발행되고,
- 그 티켓 안에서 원인, 리소스, 조치 내역을 관리하며,
- 필요하면 자동화된 해결(runbook)을 바로 실행할 수 있습니다.

---

## ✅ **정리**

|항목|설명|
|---|---|
|무엇인가?|AWS Systems Manager OpsCenter에서 관리하는 **운영 이슈 항목**|
|주요 기능|이슈를 중앙에서 수집, 추적, 자동화 대응|
|생성 방식|CloudWatch/Config 등에서 자동 생성 또는 수동 등록|
|장점|한 곳에서 이슈 관리, Runbook으로 신속한 대응, 히스토리 관리|