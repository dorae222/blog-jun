---
title: ALB (Application Load Balancer) 개요
slug: "alb-application-load-balancer-개요"
category: cloud
tags: ["alb", "application-load-balancer", "aws", "ecs", "health-check", "http2", "lambda", "load-balancing", "websocket"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:06.195354+00:00"
---

## 📌 개요

- **ALB (v2)**는 **L7 (HTTP/HTTPS) 계층**의 로드 밸런서입니다.

- 다양한 애플리케이션으로 트래픽을 라우팅할 수 있으며, 특히 컨테이너 기반 환경에 최적화되어 있습니다.

---

## 🚀 주요 기능

- 여러 머신의 **HTTP 애플리케이션으로 분산** (target groups)

- 하나의 머신에서 여러 애플리케이션으로도 분산 가능 (예: Docker container), ECS

- **HTTP/2, WebSocket 지원**

- HTTP → HTTPS 리디렉션 기능

---

## 🔁 라우팅 방식 (Target Group 분기 기준)


| 기준               | 예시                                       |
| ---------------- | ---------------------------------------- |
| URL 경로(Path)     | `example.com/users`, `example.com/posts` |
| 호스트 이름(Hostname) | `one.example.com`, `other.example.com`   |
| 쿼리 문자열 및 헤더      | `example.com/users?id=123&order=false`   |

- <mark style="background: #FFF3A3A6;">여러 애플리케이션을 하나의 ALB로 라우팅 가능</mark>
- 요청 URL 경로, 호스트 이름, HTTP 헤더 및 쿼리 문자열(또는 소스 IP 주소)을 기준으로 트래픽을 다른 Target Group(대상 그룹)으로 라우팅할 수 있습니다.
- <mark style="background: #FFF3A3A6;">ALB는 주로 인바운드 트래픽을 로드 밸런싱하는 데 사용</mark>
- Elastic IP에 연결할 수 없습니다.

---

## 🧱 타겟 그룹 (Target Groups) → 예시) 내가 만든 EC2

![](/media/posts/imported/aws/Pasted%20image%2020250706143517.png)

ALB는 다음의 대상(Targets)으로 트래픽을 라우팅할 수 있습니다:

- EC2 Instance (Auto Scaling Group 가능)

- **ECS Tasks** (컨테이너 기반)

- **Lambda Functions** (HTTP → JSON 이벤트로 변환)

- **Private IP 기반 서버**


📍 <mark style="background: #FFF3A3A6;">Health Check는 Target Group 수준에서 설정</mark>

---

## 🌐 라우팅 예시: URL 기반

```plaintext
요청: /user → Users Application Target Group
요청: /search → Search Application Target Group
```

- 각각의 타겟 그룹은 자체적인 EC2 인스턴스 세트를 가집니다.

- 각 타겟 그룹별로 Health Check를 수행합니다.

---

## 🔎 라우팅 예시: Query String / Parameter 기반

![](/media/posts/imported/aws/Pasted%20image%2020250706144456.png)

```plaintext
?platform=Mobile → Target Group 1 (AWS 기반 EC2)
?platform=Desktop → Target Group 2 (온프레미스 서버)
```

- 쿼리 파라미터 값에 따라 트래픽을 나눠 전달할 수 있습니다.

---

## 📬 기타 알아둘 점

![](/media/posts/imported/aws/Pasted%20image%2020250706144803.png)

- **고정 호스트네임** 사용: `xxx.region.elb.amazonaws.com`

- 실제 클라이언트 IP는 애플리케이션에서 바로 보이지 않습니다.

    - 대신, 다음 헤더를 통해 전달됩니다:
        - `X-Forwarded-For` → 클라이언트 IP
        - `X-Forwarded-Port` → 포트 정보
        - `X-Forwarded-Proto` → HTTP/HTTPS 구분

```plaintext
Client IP: 12.34.56.78
↓
[Application Load Balancer]
↓ (Private IP)
EC2 Instance
```