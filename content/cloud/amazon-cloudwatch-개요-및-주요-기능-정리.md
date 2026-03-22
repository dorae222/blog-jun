---
title: Amazon CloudWatch 개요 및 주요 기능 정리
slug: "amazon-cloudwatch-개요-및-주요-기능-정리"
category: cloud
tags: ["amazon-cloudwatch", "aws", "aws-lambda", "cloudwatch-alarms", "cloudwatch-logs", "cloudwatch-metrics", "logs-insights", "monitoring", "observability"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:04.918407+00:00"
---

**Amazon CloudWatch**는 AWS에서 제공하는 **모니터링 및 관찰(Observability) 서비스**로, **AWS 리소스 및 애플리케이션의 로그, 지표, 이벤트, 알람 등을 수집하고 시각화**하여 **시스템 상태를 실시간으로 모니터링하고 문제를 빠르게 감지·대응**할 수 있도록 도와줍니다.

---

## 📊 Amazon CloudWatch란?

> **Amazon CloudWatch**는 AWS 리소스와 온프레미스 애플리케이션에서 발생하는 **운영 데이터(메트릭, 로그, 이벤트)**를 수집하고,
> 이를 기반으로 **대시보드, 알람, 자동화된 대응, 인사이트 분석**까지 지원하는 **완전관리형 모니터링 서비스**입니다.

---

## 🔍 주요 기능

| 기능                                                   | 설명                                                   |
| ---------------------------------------------------- | ---------------------------------------------------- |
| **CloudWatch Metrics (지표)**                      | EC2, Lambda, RDS, ELB 등 리소스의 CPU, 네트워크, 메모리 사용률 등 지표를 수집합니다. |
| **CloudWatch Logs (로그)** | 애플리케이션 로그, 시스템 로그, VPC Flow Logs 등 로그를 저장하고 분석할 수 있습니다.           |
| **CloudWatch Alarm (알람)**                       | 특정 조건(CPU > 80% 등) 충족 시 알림을 전송하거나 자동 조치를 트리거합니다.             |
| **CloudWatch Events (이벤트)**                      | 리소스 상태 변경을 감지하고 대응할 수 있도록 이벤트를 처리합니다 (예: EC2 종료 시 알림).                   |
| **CloudWatch Dashboards**                        | 실시간 지표를 시각화하는 커스터마이징 가능한 대시보드를 제공합니다.                        |
| **CloudWatch Synthetics**                        | 실제 사용자 대신 작동하는 '가짜 사용자'로 웹 애플리케이션의 가용성과 성능을 모니터링합니다.            |
| **CloudWatch Logs Insights**                     | 로그에 대해 쿼리를 실행하여 패턴, 오류, 추세 등을 분석할 수 있습니다.                     |
| **CloudWatch Agent**                             | EC2 및 온프레미스 서버에서 메모리, 디스크 등 OS 레벨 지표를 수집합니다.              |

---

## 🧪 예시 사용 시나리오

* **EC2 인스턴스의 CPU 사용률이 90% 초과** → CloudWatch Alarm → SNS 알림 또는 Auto Scaling 수행
* **Lambda 함수 오류 로그 분석** → CloudWatch Logs로 수집 → Logs Insights로 쿼리
* **운영 대시보드**로 서비스 헬스 상태를 한눈에 확인

---

## 🔐 통합 서비스 예

| 연동 대상                     | 설명                          |
| ------------------------- | --------------------------- |
| **EC2, RDS, ELB, Lambda** | 기본 지표를 자동으로 수집합니다.                 |
| **AWS Lambda**            | 호출 수, 지연 시간, 오류 수 등을 추적합니다.        |
| **SNS**                   | 알람 트리거 시 자동으로 알림을 발송합니다.           |
| **Auto Scaling**          | 지표 기반으로 자동 확장/축소 조치를 수행합니다.              |
| **AWS X-Ray**             | 추적 데이터를 CloudWatch에서 시각화할 수 있습니다. |

---

## 💰 요금 구조 (요약)

| 항목                 | 요금              |
| ------------------ | --------------- |
| 기본 지표 (EC2 등)      | 무료 제공           |
| 커스텀 지표             | 건당 과금           |
| 로그 수집/보관           | 저장량 및 조회량 기준 과금 |
| 알람, 대시보드, Insights | 사용량 기반 요금       |

---

## ✅ 요약

| 항목    | 설명                                            |
| ----- | --------------------------------------------- |
| 이름    | **Amazon CloudWatch**                         |
| 역할    | **AWS 리소스 및 애플리케이션을 모니터링하고 운영 상태를 시각화/자동 대응** |
| 주요 기능 | 지표, 로그, 알람, 대시보드, 이벤트 분석                      |
| 사용 목적 | 실시간 상태 확인, 문제 탐지, 자동화된 대응, 비용 최적화             |