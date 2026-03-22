---
title: 단순(Simple) 라우팅 정책
slug: "단순simple-라우팅-정책"
category: cloud
tags: ["aws", "aws-route53", "dns", "dns-routing", "high-availability", "load-balancing", "route53", "routing", "simple-routing"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:08.213014+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---
---
aliases:
  - Simple Routing
  - Simple Routing Policy
---
**단순(Simple) 라우팅 정책**은 **Amazon Route 53**에서 제공하는 가장 기본적인 **DNS 라우팅 정책**으로,  
**하나의 도메인 이름에 대해 단일 리소스(IP, 로드 밸런서, S3 웹 사이트 등)** 를 연결할 때 사용하는 **기본값 정책**입니다.

---

## 🧾 단순 라우팅 정책(Simple Routing)이란?

> **단순 라우팅(Simple Routing)** 은 하나의 도메인 이름(예: `example.com`)에 대해  
> **하나의 레코드 값(IP 주소나 별칭 등)** 을 반환하는 **가장 기본적인 라우팅 방식**입니다.

---

## 🧠 어떤 상황에서 쓰나요?

- **단일 웹 서버, 단일 EC2, 단일 ALB** 등을 사용하는 단순한 애플리케이션
- 라우팅 정책이 필요 없는 기본적인 DNS 매핑
- 가용성 확인, 위치 기반 라우팅, 복잡한 분산이 필요 없는 경우

---

## ✅ 특징 요약

|항목|설명|
|---|---|
|**하나의 IP 또는 리소스 반환**|복수 리소스 사용 불가 (로드 밸런싱 불가)|
|**헬스 체크 연동 가능**|상태 비정상 시 DNS 응답 제거 가능|
|**가중치/위치 기반 불가**|단일 경로만 허용|
|**기본 정책(Default)**|Route 53에서 기본으로 설정되는 라우팅 방식|

---

## 🛠️ 예시 구성

```plaintext
도메인: www.example.com
→ 연결 대상: 203.0.113.25 (EC2 인스턴스의 IP)
라우팅 정책: 단순(Simple)
```

또는:

```plaintext
도메인: www.example.com
→ 연결 대상: ALB 또는 S3 웹 호스팅의 DNS 이름
라우팅 정책: 단순(Simple)
```

---

## ⚠️ 한계점

- **고가용성 지원 어려움**: 인스턴스가 다운되면 연결 실패
- **로드 밸런싱 불가**: 복수 IP 또는 리전 간 분산 불가
- **스케일 아웃 불가**: 수평 확장이 필요한 구조에서는 부적절

→ 이런 경우엔 `다중값 응답`, `가중 라우팅`, `지연 라우팅`, `지리 기반 라우팅` 등을 사용해야 합니다.

---

## ✅ 요약

|항목|내용|
|---|---|
|정책 이름|**단순 라우팅(Simple Routing)**|
|목적|하나의 도메인 → 하나의 리소스 매핑|
|특징|가장 기본적인 Route 53 라우팅 방식|
|권장 사용|단일 서버, 테스트 환경, 정적 웹 사이트 등|
|비적합 대상|고가용성, 글로벌 사용자, 로드 밸런싱 필요 환경|