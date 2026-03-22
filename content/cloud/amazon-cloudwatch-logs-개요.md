---
title: Amazon CloudWatch Logs 개요
slug: "amazon-cloudwatch-logs-개요"
category: cloud
tags: ["aws", "aws-kms", "cloudwatch", "cloudwatch-logs", "logging", "logs-insights", "metric-filter", "monitoring", "subscription-filter"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:04.907394+00:00"
---

- 직접적으로 Amazon OpenSearch Service로 스트리밍할 수 있는 기능을 제공하지 않음

**Amazon CloudWatch Logs**는 AWS의 **로그 수집, 모니터링, 분석 서비스**입니다.  
애플리케이션, 시스템, AWS 서비스로부터 생성되는 로그 데이터를 **중앙에서 수집하고 실시간으로 조회, 저장, 경보 설정**할 수 있게 해줍니다.

---

## 🔍 Amazon CloudWatch Logs란?

> **Amazon CloudWatch Logs**는  
> **EC2 인스턴스, Lambda, CloudTrail, VPC, RDS, EKS** 등에서 발생하는 로그 데이터를  
> **집중적으로 수집하고 분석하며**, 필요시 **경보(Alert) 및 실시간 추적**까지 가능한 로그 서비스입니다.

---

## 🧩 주요 기능

|기능|설명|
|---|---|
|📥 **로그 수집**|EC2, Lambda, ECS, VPC Flow Logs, RDS 로그 등 다양한 소스에서 로그를 수집함|
|🔎 **로그 실시간 검색**|CloudWatch 콘솔 또는 CLI를 통해 실시간으로 로그를 검색할 수 있음|
|🧠 **지표 필터(Metric Filter)**|로그 내 특정 패턴을 지표로 추출하여 **경보(Alert) 설정**이 가능함|
|📊 **대시보드 통합**|추출한 로그 지표를 **CloudWatch Dashboard**에 시각화할 수 있음|
|🗂 **Log Group / Log Stream 구조**|계층화된 로그 저장 구조로 서비스별 또는 인스턴스별로 로그를 구분하여 저장함|
|🛡 **보안 및 암호화**|AWS KMS를 통한 **서버 측 암호화(SSE)**를 지원함|
|🗑 **보존 정책 설정**|로그 그룹별로 **보존 기간(1일 ~ 무제한)**을 설정할 수 있음|

---

## 🧱 핵심 구성 요소

|구성 요소|설명|
|---|---|
|**Log Group**|같은 성격의 로그 스트림을 묶는 단위 (예: `/aws/lambda/my-function`)|
|**Log Stream**|시간순으로 정렬된 로그 이벤트 모음 (인스턴스, 컨테이너별로 생성 가능)|
|**Log Event**|실제 단일 로그 메시지 (타임스탬프 + 메시지)|
|**Metric Filter**|로그의 특정 텍스트 패턴을 추출해 **CloudWatch Metric으로 전환**함|
|**Subscription Filter**|로그 데이터를 **Kinesis, Lambda, S3 등 외부로 스트리밍**할 수 있게 함|

---

## 🎯 사용 예시

|사용 사례|설명|
|---|---|
|Lambda 함수 디버깅|`console.log()` 출력 내용을 자동 수집하여 콘솔에서 확인|
|VPC Flow Logs 분석|네트워크 흐름 로그를 수집하여 보안 분석 및 트래픽 진단에 활용|
|EC2 애플리케이션 로그 수집|SSM Agent + CloudWatch Agent를 통해 서버 로그를 전송|
|오류 경보|"ERROR" 문자열 발생 시 알림 생성 (Metric Filter + Alarm)|

---

## 💰 요금

- **로그 수집 및 저장량**, **검색 요청**, **지표 추출량**에 따라 과금됨
    
- 오래된 로그 보관은 압축 저장되며 비용이 감소함
    
> 참고: CloudWatch Logs Insights로 **로그 쿼리 및 분석**도 가능 (요금 별도)

---

## ✅ 요약

|항목|설명|
|---|---|
|서비스명|**Amazon CloudWatch Logs**|
|주요 기능|**로그 수집, 검색, 지표화, 경보, 분석**|
|사용 대상|EC2, Lambda, VPC, RDS, ECS, EKS 등|
|지표화|로그 내 패턴을 CloudWatch Metric으로 변환 가능|
|분석 도구|**Logs Insights**, **Subscription Filter** 활용 가능|
|보안|KMS 기반 암호화 + IAM 정책 제어 지원|