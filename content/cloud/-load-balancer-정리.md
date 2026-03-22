---
title: 🌐 Load Balancer 정리
slug: "-load-balancer-정리"
category: cloud
tags: ["alb", "auto-scaling", "aws", "elastic-load-balancing", "gwlb", "health-checks", "nlb", "route53", "security-groups"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:06.750934+00:00"
---

---

## 📌 What is Load Balancing?

- **Load Balancers**는 트래픽을 여러 다운스트림 서버(예: EC2 인스턴스)로 분산시키는 **중간 서버**입니다.
- Elastic Load Balancer(ELB)는 클라이언트 요청을 여러 EC2 인스턴스에 자동으로 분산합니다.

```
사용자 요청
   ↓
[Elastic Load Balancer]
   ↓      ↓      ↓
[EC2]  [EC2]  [EC2]
```

---

## ✅ Why Use a Load Balancer?

- 여러 인스턴스에 부하 분산
- DNS를 통한 **단일 접근 지점 제공**
- 다운스트림 인스턴스 장애 자동 처리
- 인스턴스에 대한 **정기적인 헬스 체크 수행**
- SSL 종료 지점(HTTPS) 제공
- 쿠키 기반 세션 유지(stickiness) 지원
- 가용 영역(AZ) 간 고가용성 지원
- **퍼블릭 트래픽과 프라이빗 트래픽 분리** 가능

> **NOTE:**
> Elastic Load Balancer가 관리하는 10개의 EC2 인스턴스에서 웹사이트를 운영 중입니다. 사용자들이 페이지 이동마다 새로 인증해야 한다고 불만을 제기하고 있습니다. 하지만 개발 환경(단일 EC2 인스턴스)에서는 문제가 없습니다. 원인은 무엇일까요?
> 
> - Elastic Load Balancer의 Sticky Session이 활성화되어 있지 않음
>   - ELB의 Sticky Session 기능은 동일한 클라이언트의 트래픽을 항상 동일한 대상으로 라우팅하도록 해줍니다(예: 특정 EC2 인스턴스). 이를 통해 클라이언트가 세션 데이터를 잃지 않게 합니다.

---

## ☁️ Why Use an Elastic Load Balancer (ELB)?

- **Managed Load Balancer**로 AWS가 운영 및 가용성을 보장
  - 유지보수, 업그레이드, 고가용성을 AWS가 책임
- 설정이 간단하며 필요한 설정 옵션만 제공
    
### ➕ AWS 통합 서비스

- EC2, Auto Scaling Groups, Amazon ECS
- AWS ACM(인증서), CloudWatch
- Route 53, WAF, Global Accelerator 등과 통합
    

> ⚠️ 자가 구축 로드밸런서는 비용이 더 저렴할 수 있지만, 관리 복잡도가 크게 증가합니다.

---

## ❤️ Health Checks

- 인스턴스가 **정상 동작 중인지 확인**하는 절차
- 정해진 **port**와 **route (/health 등)**에 주기적으로 HTTP 요청 전송
- 응답이 `200 OK`가 아니면 **unhealthy 상태**로 간주되어 트래픽이 전달되지 않음
    

```plaintext
ELB --(Health Check)--> EC2:4567/health
```

---

## 🧱 Types of Load Balancer on AWS

![](/media/posts/imported/aws/Pasted%20image%2020250706150513.png)

| 타입                                                   | 설명            | 주요 프로토콜                |
| ---------------------------------------------------- | ------------- | ---------------------- |
| **ALB** (Application) | 2016년, L7 기반  | HTTP, HTTPS, WebSocket |
| **NLB** (Network)         | 2017년, L4 기반  | TCP, TLS, UDP          |
| **GWLB** (Gateway)        | 2020년, L3 기반  | IP 기반 (네트워크 계층)        |

- 최신 세대(ALB, NLB, GWLB) 사용 권장(더 많은 기능 제공)
- 내부(private) 또는 외부(public) 설정 가능
    

---

## 🔐 Load Balancer Security Group

### 구성 요약

#### Load Balancer SG (퍼블릭 접근 허용)

|Type|Protocol|Port|Source|설명|
|---|---|---|---|---|
|HTTP|TCP|80|0.0.0.0/0|모든 IP에서 HTTP 허용|
|HTTPS|TCP|443|0.0.0.0/0|모든 IP에서 HTTPS 허용|

#### EC2 Instance SG (ELB만 허용)

|Type|Protocol|Port|Source (ELB SG)|설명|
|---|---|---|---|---|
|HTTP|TCP|80|sg-xxxxxxxxxxxxxxxxx|ELB에서 들어오는 요청만 허용|

- EC2 보안 그룹의 인바운드 소스를 Load Balancer의 보안 그룹으로 설정

---

## ✅ 요약

| 구성 요소                                         | 역할                         |
| --------------------------------------------- | -------------------------- |
| **ELB**                                       | 트래픽 분산, 고가용성 확보            |
| **Health Check**                              | 인스턴스 상태 모니터링               |
| **Security Group**                            | 네트워크 접근 제어                 |
| **ALB/NLB**                                   | 계층에 따라 로드밸런싱 방식 선택         |
| **Auto Scaling** | Horizontal Scalability에 핵심 |

---