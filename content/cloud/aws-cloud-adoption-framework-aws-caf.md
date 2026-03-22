---
title: AWS Cloud Adoption Framework (AWS CAF)
slug: "aws-cloud-adoption-framework-aws-caf"
category: cloud
tags: ["aws", "cloud-adoption", "cloud-governance", "cloud-migration", "cloud-operations", "cloud-security", "landing-zone", "well-architected"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:03.477847+00:00"
---

## 🧩 Quick Overview

| 항목        | 설명                                                                            |
| --------- | ----------------------------------------------------------------------------- |
| **이름**    | AWS Cloud Adoption Framework (AWS CAF)                                        |
| **유형**    | **클라우드 도입 전략·운영 가이드 프레임워크**                                                   |
| **주요 목적** | 조직이 **클라우드 전환을 체계적·효율적·안전하게 진행**할 수 있도록 역량(능력)과 관점(Perspective)을 정의한 참조 모델 제공 |

> ☁️ **AWS CAF**는 단순한 기술 가이드가 아니라,  
> **조직의 인력·프로세스·거버넌스·보안·운영**을 포함한 **전사적 클라우드 전환 로드맵**을 지원합니다.

---

## 🔧 핵심 구성

AWS CAF는 **6가지 Perspective**와 **Capability**로 구성됩니다.

### **① 비즈니스 (Business)**

- **키워드:** ROI, KPI, 민첩성, 비즈니스 가치
    
- **예시 문제:**
    
    > 회사는 클라우드 도입으로 **시장 출시 속도를 높이고 투자 수익을 극대화**하고자 한다.  
    > → **정답: Business Perspective**
    
---

### **② 인적 (People)**

- **키워드:** 조직, 교육, 역할 재정의, 변화 관리(Change Management)
    
- **예시 문제:**
    
    > 회사는 클라우드 전환을 위해 **직원 교육과 새로운 역할 정의**를 진행하려 한다.  
    > → **정답: People Perspective**
    
---

### **③ 거버넌스 (Governance)**

- **키워드:** 규정 준수, 재무 통제, 위험 관리
    
- **예시 문제:**
    
    > 회사는 클라우드 비용과 사용량을 **모니터링하고 규정 준수를 보장**하려 한다.  
    > → **정답: Governance Perspective**
    
---

### **④ 플랫폼 (Platform)**

- **키워드:** 인프라, 아키텍처, Landing Zone, 네트워크/컴퓨팅/스토리지
    
- **예시 문제:**
    
    > 회사는 클라우드 전환을 위해 **네트워크와 컴퓨팅, 스토리지 아키텍처를 설계**하고 있다.  
    > → **정답: Platform Perspective**
    
---

### **⑤ 보안 (Security)**

- **키워드:** 데이터 보호, IAM, 규제 준수, 감사
    
- **예시 문제:**
    
    > 회사는 클라우드 환경에서 **데이터 암호화 및 접근 제어**를 강화하고자 한다.  
    > → **정답: Security Perspective**
    
---

### **⑥ 운영 (Operations)**

- **키워드:** 모니터링, 운영 효율화, SLA 보장, 인시던트 대응
    
- **예시 문제 (사용자 질문과 동일):**
    
    > 회사는 워크로드 **성능을 모니터링**하고, 서비스가 **비즈니스 요구를 충족하는 수준**으로 제공되도록 하려 한다.  
    > → **정답: Operations Perspective (D)**

- **문제에서 나오는 키워드를 잡으면 바로 관점 연결**
    
    - 모니터링, 운영, SLA → **Operations**
        
    - 아키텍처, 네트워크 → **Platform**
        
    - 보안, 접근제어 → **Security**
        
    - 규정 준수, 비용 관리 → **Governance**
        
    - 교육, 역할 정의 → **People**
        
    - ROI, KPI, 시장 출시 → **Business**
        
- **유사 관점 혼동 주의**
    
    - **Operations vs Platform**
        
        - Platform: **설계·배포**
            
        - Operations: **운영·모니터링**
            
    - **Security vs Governance**
        
        - Security: **데이터·접근 제어**
            
        - Governance: **규정 준수·리스크·비용 통제**

---

## 🧪 활용 시나리오

- **클라우드 도입 초기 로드맵 설계**
- **온프레미스 → 클라우드 마이그레이션 전략 수립**
- **조직별 클라우드 역량/준비도 진단**
- **거버넌스, 보안, 운영 체계 사전 설계**

---

## ✅ 장점

| 항목 | 설명 |
|------|------|
| **체계적 전환 지원** | 조직·프로세스·기술을 통합적으로 고려 |
| **리스크 최소화** | 거버넌스·보안·컴플라이언스 사전 설계 |
| **전사적 정렬** | 비즈니스·기술팀 간 공감대 형성 |
| **클라우드 ROI 극대화** | 불필요한 반복 작업·리스크 최소화 |

---

## ⚠️ 유의사항

| 항목 | 설명 |
|------|------|
| **단계적 적용 필요** | 모든 관점을 한 번에 구현하기보단 점진적 적용 권장 |
| **조직 문화 영향** | 변화 관리(Change Management)가 성공 핵심 |
| **AWS 도구와 병행 권장** | Well-Architected Framework, Landing Zone 등과 연계 |

---

## 🧾 요약

| 항목       | 설명 |
|------------|------|
| **정의**     | 조직의 **클라우드 도입·운영을 체계화**하기 위한 AWS 제공 프레임워크 |
| **구성**     | 6가지 Perspective (Business, People, Governance, Platform, Security, Operations) |
| **목적**     | 효율적 전환, 보안·거버넌스 확보, ROI 극대화 |
| **활용 예** | 마이그레이션 전략 수립, 조직 준비도 진단, 전사적 클라우드 로드맵 |
