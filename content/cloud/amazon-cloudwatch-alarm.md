---
title: Amazon CloudWatch Alarm
slug: "amazon-cloudwatch-alarm"
category: cloud
tags: ["auto-scaling", "aws", "cloudwatch", "cloudwatch-alarm", "lambda", "metrics", "monitoring", "sns"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:06.388823+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A


---

---
aliases:
  - CW Alarm
---
**Amazon CloudWatch Alarm**은
AWS 리소스나 사용자 정의 지표의 상태를 모니터링하고, **사전 정의된 임계값(threshold)을 초과하거나 충족할 때 자동으로 알림을 보내거나 작업을 트리거하는 기능**입니다.

쉽게 말해, **지표(metric)가 설정한 조건을 만족하면 경보를 울려주는 자동 감시 시스템**입니다.

---

## 🔔 CloudWatch Alarm이란?

> **CloudWatch Alarm**은 **CloudWatch Metric(지표)** 값을 지속적으로 모니터링하고,
> 정해진 조건(예: CPU 사용률 > 80%)이 만족되면 **SNS 알림, EC2 Auto Scaling, Lambda 호출 등**
> 특정 **조치를 자동으로 수행**할 수 있게 해줍니다.

---

## 📦 주요 특징

|기능|설명|
|---|---|
|📊 **지표 기반 트리거**|CPU 사용률, 네트워크, S3 요청 수 등 다양한 지표를 기반으로 알람 트리거 가능|
|🧾 **사용자 정의 지표도 지원**|애플리케이션 지표나 커스텀 로그 지표를 기반으로 알람 설정 가능|
|🔂 **Auto Scaling과 통합**|알람을 통해 EC2 인스턴스 수를 자동으로 조정할 수 있음|
|📣 **SNS 알림 발송**|이메일, SMS, Lambda 등으로 경보 메시지를 전송 가능|
|🔄 **상태 전이 감지**|OK → ALARM, ALARM → OK, INSUFFICIENT_DATA 등의 상태 전이를 추적|
|🛠 **조치 연계 가능**|예: EC2 재시작, Auto Recovery, Lambda 호출, SNS 전송 등과 연계 가능|

---

## 🔧 작동 방식

```text
[CloudWatch Metric] → [Alarm Condition 평가] → [상태 전이 (OK / ALARM / INSUFFICIENT)]  
         ↓  
   [SNS 알림 or 조치 트리거]
```

---

## 🎯 예시 알람 조건

|지표|조건|설명|
|---|---|---|
|CPUUtilization|> 80% for 5 minutes|EC2 인스턴스 과부하 시 알림|
|S3NumberOfObjects|> 1,000,000|S3 버킷에 객체가 과도하게 쌓였을 때|
|LambdaErrors|> 0 for 3 datapoints|Lambda 함수에서 오류가 발생했을 때 알림|

---

## ✅ 알람 상태 설명

|상태|의미|
|---|---|
|**OK**|설정한 조건을 만족하지 않음 (정상 상태)|
|**ALARM**|설정한 조건을 만족함 (경보 상태)|
|**INSUFFICIENT_DATA**|최근 지표 데이터가 부족함 (예: 새 리소스 등)|

---

## 📌 사용 사례

- **Auto Scaling 트리거**  
    → EC2 CPU가 80% 초과하면 인스턴스 수 증가
    
- **운영 알림 전송**  
    → RDS 연결 수가 임계값을 넘으면 운영팀에 이메일 전송
    
- **비정상 탐지 및 대응**  
    → Lambda 오류 발생 시 자동으로 오류 로그 분석 Lambda 호출
    

---

## 🛡️ 보안 및 비용

- IAM 정책으로 **알람 생성/조회/삭제 권한을 제어**할 수 있습니다.
    
- **CloudWatch Alarm 자체에는 요금이 발생하지 않습니다**,
    다만 **지표 수집(커스텀 지표 포함)**과 **알림 전송(SNS 등)**에는 소액의 요금이 부과될 수 있습니다.
    

---

## ✅ 요약

|항목|설명|
|---|---|
|서비스|**Amazon CloudWatch Alarm**|
|용도|**지표 기반 조건 감지 및 자동 알림/조치**|
|상태|OK / ALARM / INSUFFICIENT_DATA|
|주요 연동|SNS, Auto Scaling, Lambda 등|
|지원 지표|AWS 기본 지표 + 사용자 정의 지표|
