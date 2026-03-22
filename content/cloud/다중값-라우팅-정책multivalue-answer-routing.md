---
title: 다중값 라우팅 정책(Multivalue Answer Routing)
slug: "다중값-라우팅-정책multivalue-answer-routing"
category: cloud
tags: ["aws", "dns", "dns-routing", "ec2", "health-check", "load-balancing", "multivalue-answer-routing", "route53"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:08.203650+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---
---
aliases:
  - 다중값 답변 라우팅
  - Multivalue Answer Routing policy
---
- 여러 리소스의 IP 주소를 반환할 수 있으며, 헬스 체크를 통해 정상적인 리소스만 반환

**다중값 라우팅 정책(Multivalue Answer Routing policy)**은 **Amazon Route 53**에서 제공하는 **DNS 라우팅 정책 중 하나**로,
**여러 IP 주소(또는 엔드포인트)를 동시에 반환**하고, **헬스 체크(Health Check)**를 결합할 수 있는 간단하면서도 유용한 라우팅 방식입니다.

---

## 🔁 다중값 라우팅 정책(Multivalue Answer Routing)이란?

> **Multivalue Answer Routing**은 Route 53이 **DNS 쿼리에 대해 최대 8개의 리소스 레코드(IP 등)를 반환**하도록 설정하는 정책으로,
> **로드 밸런싱처럼 동작하지만**, **간단한 DNS 기반 분산 처리 및 헬스 체크 기능**을 제공합니다.

---

## ✅ 어떤 상황에서 쓰나요?

- 간단한 **DNS 기반 로드 밸런싱**이 필요할 때
- 여러 리소스(예: IP 주소) 중 **정상인 것만 응답**하고 싶을 때
- **ELB 없이 가벼운 트래픽 분산**이 필요할 때

---

## 🔍 특징 요약

|항목|설명|
|---|---|
|**최대 응답 개수**|최대 8개 IP 주소 반환|
|**헬스 체크 통합**|✅ 헬스 체크에 통과한 리소스만 응답|
|**라우터 수준 로드 밸런싱 없음**|DNS만 반환 → 클라이언트(또는 브라우저)가 응답 중 하나를 선택|
|**단순 구성**|복잡한 설정 없이 IP 목록만 등록하면 사용 가능|
|**가중치 불가능**|가중 분산(Weighted Routing)은 별도 정책 사용 필요|

---

## 📌 예시 시나리오

> 회사가 웹 애플리케이션을 7개의 EC2 인스턴스에서 운영하고 있으며,
> Route 53이 DNS 조회 시 **정상 상태의 모든 EC2 IP를 반환**해야 하는 경우
> → ✅ **Multivalue Answer Routing 정책 사용**

---

## 🛠️ 작동 방식 예시

- 사용자가 `example.com`을 조회합니다.
- Route 53이 **헬스 체크에 통과한 IP 3~8개를 응답**합니다.
- 클라이언트는 응답받은 목록 중 하나를 선택해 연결을 시도합니다.
- 응답은 무작위 순서로 반환되므로 **자연스러운 분산 효과**가 발생합니다.

---

## 🧱 설정 옵션 예

|옵션|설명|
|---|---|
|TTL|DNS 응답의 캐시 시간|
|Health check|개별 IP에 대해 상태 확인 여부|
|Record type|A(IPv4), AAAA(IPv6), CNAME 등 가능|

---

## ✅ 요약

|항목|내용|
|---|---|
|정식 명칭|**Multivalue Answer Routing Policy**|
|위치|Amazon Route 53의 라우팅 정책 중 하나|
|주요 기능|✅ 여러 IP 반환, ✅ 헬스 체크 통합|
|목적|간단한 트래픽 분산 및 고가용성 지원|
|제한 사항|가중치나 위치 기반 라우팅 불가 → 필요 시 다른 정책 사용|
