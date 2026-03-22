---
title: ALBRequestCountPerTarget 메트릭 — ALB 타겟별 요청 수
slug: "albrequestcountpertarget-메트릭--alb-타겟별-요청-수"
category: cloud
tags: ["alb", "application-load-balancer", "auto-scaling", "aws", "cloudwatch", "load-balancing", "metrics", "monitoring"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:03.235575+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A


---

---
aliases:
  - ALBRequestCountPerTarget metric
  - ALBRequestCountPerTarget
---
## 🧩 빠른 개요

| 항목               | 설명 |
|--------------------|------|
| **메트릭 이름**     | `ALBRequestCountPerTarget` |
| **서비스 대상**     | Application Load Balancer (ALB) |
| **측정 단위**       | Count |
| **측정 대상**       | **대상 그룹(Target Group)** 내 개별 **타겟(예: EC2, Lambda)**에 전달된 요청 수 |

> 📈 **의미**: Application Load Balancer가 **각 타겟(서버)에 얼마나 많은 요청을 전달했는지**를 측정하는 지표입니다.
> → **트래픽 분산 상태 확인, 과부하 탐지, Auto Scaling 정책 설계** 등에 핵심적으로 활용됩니다.

---

## 🔍 상세 설명

| 항목 | 설명 |
|------|------|
| **메트릭 위치** | CloudWatch > AWS/ApplicationELB 네임스페이스 |
| **집계 기준** | 개별 타겟별 요청 수의 평균 (Target Group 단위) |
| **계산 방식** | `(총 요청 수) / (타겟 수)` |
| **지원 리소스** | EC2, ECS, Lambda, IP 기반 타겟 등 |

---

## ✅ 활용 예

- **Auto Scaling 연계 지표**
  - 특정 요청 수를 초과하면 EC2 인스턴스 수를 늘리는 스케일 아웃 트리거로 활용
- **타겟 간 부하 불균형 탐지**
  - 예상과 다른 요청 분포를 확인해 특정 타겟에 과도한 트래픽이 집중되는지 탐지
- **성능 병목 분석**
  - 특정 시간대에 요청이 집중되어 성능 저하가 발생하는 구간을 파악

---

## 🧪 예시: CloudWatch 경보 구성 조건

```txt
Metric: AWS/ApplicationELB - ALBRequestCountPerTarget
TargetGroup: my-target-group
Condition: > 1000 requests per minute
Alarm: Trigger scale-out action
```