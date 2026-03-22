---
title: Amazon Detective
slug: "amazon-detective"
category: cloud
tags: ["amazon-detective", "aws", "cloud-security", "cloudtrail", "forensics", "guardduty", "incident-response", "security-analytics", "vpc-flow-logs"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:05.003365+00:00"
---

**Amazon Detective**는 AWS에서 보안 이벤트나 의심스러운 활동을 조사하고 시각화하는 보안 분석 서비스입니다.

---

## 🕵️ Amazon Detective란?

> **Amazon Detective**는 AWS 리소스에서 발생하는 **보안 관련 로그와 이벤트를 수집·분석하고, 이를 시각화하여 보안 인시던트를 조사할 수 있도록 돕는 서비스**입니다.

즉, **이상 행동 탐지 이후의 조사 단계**를 간소화해 주는 **보안 포렌식 도구**입니다.

---

## 🔍 어떤 일을 하나요?

|기능|설명|
|---|---|
|**보안 이벤트 시각화**|IP, 계정, 리소스 간의 관계와 활동 흐름을 그래프로 보여줌|
|**이상 행동 분석**|IAM 활동, 네트워크 흐름, API 호출 등의 이상 패턴을 분석|
|**자동 데이터 수집**|AWS CloudTrail, VPC Flow Logs, GuardDuty 결과를 자동으로 수집|
|**장기 데이터 보관**|최대 1년 동안의 데이터 분석 가능|
|**클릭 기반 탐색**|의심스러운 사용자나 리소스를 클릭하면 관련 활동 이력을 확인 가능|

---

## 🧱 어떤 서비스와 통합되나요?

|통합 서비스|역할|
|---|---|
|**AWS GuardDuty**|탐지한 보안 위협을 조사할 수 있도록 연동|
|**AWS CloudTrail**|API 호출 기록 수집|
|**Amazon VPC Flow Logs**|네트워크 트래픽 분석|
|**AWS Security Hub**|종합 보안 알림에서 바로 Detective로 이동 가능|

---

## 🧪 예시 시나리오

> GuardDuty가 IAM 사용자 계정에서 **이상한 API 호출**을 탐지함  
> → Amazon Detective에서 해당 사용자에 대한 과거 활동, 연결된 IP, 자주 사용한 리소스 등을 **시각적으로 추적**  
> → 내부 사용자 오용인지 외부 침입인지 분석

---

## ✅ 주요 장점

|항목|설명|
|---|---|
|**보안 분석 자동화**|로그 수집과 관계 분석을 자동화|
|**시각화 기반 분석**|텍스트 로그 대신 **그래프 기반의 관계 시각화** 제공|
|**조사 시간 단축**|클릭만으로 보안 사고의 원인과 흐름 파악 가능|
|**Agent 설치 불필요**|기존 로그 기반으로 동작하므로 인프라 변경 불필요|

---

## 🔒 비용 관련

- 사용량 기반 요금: **분석된 데이터 양(GB)**에 따라 과금
- 별도의 데이터 저장 공간 필요 없음

---

## ✅ 요약

> **Amazon Detective**는 AWS 환경에서 발생한 보안 이벤트에 대해 **누가, 언제, 어떤 행동을 했는지 시각적으로 분석**할 수 있는 **보안 인시던트 조사 전용 서비스**입니다. GuardDuty, CloudTrail, VPC 로그와 통합되어 **효율적인 보안 포렌식**을 지원합니다.