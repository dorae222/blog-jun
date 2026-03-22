---
title: 지리적 위치 라우팅(Geolocation Routing)
slug: "지리적-위치-라우팅geolocation-routing"
category: cloud
tags: ["aws", "cloud", "dns-routing", "geoip", "geolocation", "load-balancing", "route53", "terraform"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:08.346719+00:00"
---

---
aliases:
  - Geolocation Routing
---

**지리적 위치 라우팅(Geolocation Routing)**은 **Amazon Route 53**에서 제공하는 **DNS 라우팅 정책 중 하나**로, **사용자의 위치(국가, 대륙 또는 특정 IP 범위)**를 기준으로 트래픽을 **특정 리소스로 라우팅**할 수 있게 해주는 기능입니다.

---

## 🗺️ 지리적 위치 라우팅(Geolocation Routing)이란?

> **Geolocation Routing**은 DNS 쿼리를 요청한 **사용자의 지리적 위치(Region)**를 바탕으로,
> 미리 지정한 **리소스(예: EC2, ALB/ELB, S3 웹 호스팅 등)**로 트래픽을 분산하는 **Route 53의 라우팅 정책**입니다.

---

## 🧠 작동 방식

- 사용자의 **IP 주소**를 기반으로 어느 **국가/대륙**에서 요청이 들어왔는지 판단합니다.
- Route 53 설정에 따라 해당 위치에 매핑된 **레코드(IP 또는 엔드포인트)**를 반환합니다.
- 결과적으로 사용자는 위치에 맞게 할당된 리소스에 연결됩니다.

---

## ✅ 사용 예시

|사용 위치|응답되는 서버|
|---|---|
|미국 사용자|미국 리전 EC2 인스턴스|
|일본 사용자|도쿄 리전 ALB|
|유럽 사용자|프랑크푸르트 리전의 S3 버킷|

→ 각 사용자에게 **가장 적합한(또는 정책상 지정한)** 리소스를 수동으로 지정할 수 있습니다.

---

## 🔒 특징과 장점

|항목|설명|
|---|---|
|**지역 제어**|국가, 대륙 또는 글로벌 단위로 라우팅을 설정할 수 있습니다.|
|**비즈니스/규제 대응**|특정 국가의 트래픽을 특정 리전으로 제한하는 등 규제 대응이 가능합니다.|
|**디폴트 라우팅**|설정되지 않은 지역에서 오는 요청은 기본 경로(기본 레코드)로 지정할 수 있습니다.|
|**정확도**|IP → 위치 매핑(GeoIP)을 사용하므로 일반적으로 높은 정확도를 보입니다.|

---

## ⚠️ 유사 개념 비교

|라우팅 정책|기준|특징|
|---|---|---|
|**Geolocation**|사용자 **국가/위치**|✅ **명시적 제어**가 가능함|
|**Latency**|AWS 리전까지의 **지연 시간**|🟡 실제 거리와 무관할 수 있음|
|**Geoproximity**|사용자 ↔ 리소스 간 거리|✅ bias 설정 가능, Traffic Flow 전용|
|**Multivalue Answer**|상태 체크 기반 복수 IP 반환|✅ 복수 IP 응답 및 상태 체크 기능 포함|

---

## 📝 예시 JSON (Terraform 등에서 설정 시)

```hcl
resource "aws_route53_record" "jp_record" {
  zone_id = "Z123456789"
  name    = "example.com"
  type    = "A"
  set_identifier = "tokyo-server"
  geolocation {
    country = "JP"
  }
  ttl     = 300
  records = ["192.0.2.44"]
}
```

---

## ✅ 요약

|항목|내용|
|---|---|
|이름|**지리적 위치 라우팅 (Geolocation Routing)**|
|서비스|Amazon Route 53|
|기준|**사용자의 지리적 위치(IP 기반)**|
|목적|위치 기반으로 트래픽을 특정 리소스로 라우팅|
|사용 예|국가별 서버 연결, 법적 요구사항 대응 등|
