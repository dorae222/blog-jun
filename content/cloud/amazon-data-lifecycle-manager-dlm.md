---
title: Amazon Data Lifecycle Manager (DLM)
slug: "amazon-data-lifecycle-manager-dlm"
category: cloud
tags: ["ami", "aws", "backup", "cloudwatch", "disaster-recovery", "dlm", "ebs", "ec2", "iam", "snapshots"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:04.979124+00:00"
---

---
aliases:
  - Amazon DLM
  - DLM
---
**Amazon Data Lifecycle Manager (DLM)**는 **Amazon EBS 볼륨 스냅샷과 Amazon EBS-backed AMI를 자동으로 생성·보관·삭제하는 관리형 서비스**입니다. 즉, 백업과 보관을 자동화하여 스토리지 비용을 절감하고 규정 준수를 지원하는 도구입니다.

---

## 🧩 Amazon DLM란?

> Amazon DLM은 EBS 리소스의 **백업 수명 주기 관리(Lifecycle Management)**를 자동화합니다. 수동으로 스냅샷을 생성하거나 삭제할 필요 없이, **정책 기반으로 자동 생성·삭제**가 이루어집니다.
> RDS 스냅샷은 직접 관리하지 않습니다.

---

## 🔧 지원 대상

|리소스 유형|설명|
|---|---|
|**Amazon EBS 볼륨 스냅샷**|정기적으로 백업할 EBS 볼륨|
|**Amazon EC2 인스턴스 이미지(AMI)**|서버 구성 상태 백업 (Amazon EBS-backed AMI)|

---

## ⚙️ 주요 기능

|기능|설명|
|---|---|
|🕒 **자동 스냅샷 생성**|일간/시간별/주간 등 주기로 스냅샷 생성|
|🗑️ **자동 스냅샷 삭제**|보존 기간이 지난 스냅샷은 자동 삭제|
|🧠 **태그 기반 대상 지정**|특정 태그를 가진 볼륨/인스턴스를 대상으로 정책 적용|
|🧾 **AMI 생성 및 만료 관리**|AMI 생성 후 일정 기간이 지나면 자동 삭제 가능|
|🛡️ **IAM 기반 접근 제어**|정책 생성, 수정, 삭제 권한 제어 가능|
|📊 **CloudWatch Events 연동**|정책 실행 상태 및 오류 알림 가능|

---

## 📌 정책 구성 요소

|요소|설명|
|---|---|
|**정책 유형**|스냅샷 정책 or AMI 정책|
|**대상 리소스**|태그 지정 방식으로 대상 지정|
|**스케줄**|언제, 얼마나 자주 실행할지 설정|
|**보존 규칙**|생성된 스냅샷/AMI를 몇 개/며칠 동안 유지할지 지정|
|**복제 옵션**|다른 리전으로 스냅샷 복사 가능 (DR 용도)|

---

## 🧪 사용 예시

1. `"backup=true"` 태그가 달린 EBS 볼륨에 대해

2. 매일 자정에 스냅샷 자동 생성

3. 7일 지난 스냅샷은 자동 삭제

4. CloudWatch 이벤트로 실행 상태 확인

---

## ✅ 요약

|항목|설명|
|---|---|
|이름|**Amazon Data Lifecycle Manager (DLM)**|
|용도|**EBS 스냅샷 및 AMI 생성/삭제 자동화**|
|방식|**태그 기반 정책**으로 스케줄, 보존, 삭제 구성|
|주요 장점|자동화, 비용 절감, 규정 준수, 관리 효율성|
|통합 서비스|Amazon EC2, Amazon EBS, IAM, CloudWatch|

---

### 🔒 추가 팁:

- 스냅샷 암호화도 자동으로 상속됩니다 (EBS가 암호화된 경우).

- DLM 정책은 **JSON 형식이 아닌 GUI 기반 설정**입니다.

- **수동 스냅샷에는 적용되지 않습니다** (정책이 생성한 리소스만 삭제 대상입니다).
