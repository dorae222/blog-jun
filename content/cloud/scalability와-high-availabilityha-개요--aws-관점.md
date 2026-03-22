---
title: Scalability와 High Availability(HA) 개요 — AWS 관점
slug: "scalability와-high-availabilityha-개요--aws-관점"
category: cloud
tags: ["auto-scaling", "aws", "ec2", "high-availability", "horizontal-scaling", "load-balancer", "rds", "scalability", "vertical-scaling"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:07.745462+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---

---
aliases:
  - 확장성과 고가용성
---
## ✔️ Scalability

- **정의**: 시스템이 증가하는 부하에 적응하여 처리할 수 있는 능력.
    
- **종류**
    - **Vertical Scalability (수직 확장)**: 더 큰 인스턴스로 업그레이드.
    - **Horizontal Scalability (수평 확장 / 탄력성)**: 인스턴스 수를 늘려 분산 처리.
        
- **참고**: Scalability는 High Availability와 관련이 있지만 **동일한 개념은 아님**.
    

## ✔️ Vertical Scalability

- **정의**: 인스턴스의 **사이즈(성능)**를 증가시키는 것.
    
- **예시**: `t2.micro` → `t2.large` 로 업그레이드.
    
- **특징**
    
    - 비분산 시스템(DB 등)에 흔히 사용됨.
    - RDS, ElastiCache는 수직 확장이 가능.
    - **하드웨어 한계**가 존재함.
        

## ✔️ Horizontal Scalability

- **정의**: 인스턴스 개수를 늘려 처리 능력을 높이는 방법.
    
- **특징**
    - 분산 시스템에서 일반적.
    - 웹 애플리케이션과 현대적인 아키텍처에서 자주 사용됨.
    - AWS EC2 같은 클라우드 서비스로 쉽게 구현 가능.

## ✔️ High Availability

- **정의**: 시스템을 **2개 이상의 데이터 센터(Availability Zones)**에 배포하여 **장애 발생 시에도 서비스가 지속 운영되도록 보장**하는 설계.
    
- **목표**: 한 데이터 센터가 다운되어도 서비스가 계속 동작하도록 하는 것.
    
- **유형**
    
    - **Passive HA**: RDS Multi-AZ처럼 대기 인스턴스가 준비되어 있는 구성.
        
    - **Active HA**: 여러 인스턴스가 동시에 운영되는 구성(주로 수평 확장 기반).
        

---

# 🛠 High Availability & Scalability for EC2

## 🔼 Vertical Scaling

- **인스턴스 크기 증가** (scale up/down)
- 예:
    - From: `t2.nano` – 0.5G RAM, 1 vCPU
        
    - To: `u-12tb1.metal` – 12.3TB RAM, 448 vCPUs
        

## ↔️ Horizontal Scaling

- **인스턴스 개수 증가** (scale out/in)
- 구성:
    
    - Auto Scaling Group
        
    - Load Balancer
        

## 🟢 High Availability

- **여러 AZ에 동일한 애플리케이션 인스턴스 배포**
- 구성:
    
    - Auto Scaling Group with Multi-AZ
        
    - Load Balancer with Multi-AZ
        

---

## ✅ 핵심 비교 요약

| 개념                 | 목적    | 방법         | 장점          | 단점     |
| ------------------ | ----- | ---------- | ----------- | ------ |
| Vertical Scaling   | 성능 증가 | 인스턴스 업그레이드 | 설정 간단       | 확장 한계  |
| Horizontal Scaling | 부하 분산 | 인스턴스 수 증가  | 무한 확장 가능    | 복잡성 증가 |
| High Availability  | 장애 대응 | 다중 AZ 배포   | 장애 시 서비스 유지 | 비용 증가  |