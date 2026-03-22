---
title: Amazon Kinesis Agent
slug: "amazon-kinesis-agent"
category: cloud
tags: ["amazon-kinesis", "aws", "data-streams", "ec2", "firehose", "kinesis-agent", "log-collection", "on-premises", "streaming"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:05.243562+00:00"
---

**NOTE:**

- **서버(Log/File) 기반 데이터를 Kinesis로 전송**하기 위한 경량 에이전트

- **파일(Log) → 스트리밍 서비스** 자동 전송

- **Amazon Kinesis Data Streams / Firehose** 지원

- **설치·설정이 간단** (JSON 설정 파일)

- 체크포인트 기반으로 **중복 전송 방지**

- **EC2 / 온프레미스 서버**에서 사용 가능

- **Amazon Linux, Red Hat, Ubuntu** 지원


**Amazon Kinesis Agent**는
**서버에서 생성되는 로그 및 파일 데이터를 자동으로 수집해 Kinesis로 스트리밍 전송하는 에이전트**이다.

---

## 🌊 Amazon Kinesis Agent란?

> **Amazon Kinesis Agent**는
> **웹 서버, 애플리케이션 서버, 온프레미스 서버**에서 생성되는
> **로그 파일 데이터를 실시간으로 수집하여 Kinesis 서비스로 전송**하는 도구이다.

- 로그 수집 → 전송 자동화

- 스트리밍 파이프라인의 **Producer 역할**

---

## 🏗️ 동작 방식

```text
[Server / EC2 / On-Prem]
   (Log Files)
        │
        ▼
[Amazon Kinesis Agent]
        │
        ▼
[Kinesis Data Streams / Firehose]
        │
        ▼
[Consumer / S3 / Analytics]
```

- 파일 변경 감지

- 신규 로그 라인만 전송

- 장애 발생 시 재시도

---

## 🚀 주요 특징

|기능|설명|
|---|---|
|**파일 기반 수집**|Log, Text 파일 Tail 방식|
|**자동 체크포인트**|전송 위치 기록|
|**재시도 로직**|네트워크/서비스 장애 대응|
|**간단한 설정**|JSON 설정 파일|
|**보안 연동**|IAM Role 사용|
|**저지연 전송**|Near Real-time|

---

## 📦 핵심 구성 요소

|구성 요소|설명|
|---|---|
|**Agent 프로세스**|서버에서 실행되는 데몬|
|**Config 파일**|수집 대상, 대상 스트림 정의|
|**Checkpoint 파일**|마지막 전송 위치 저장|
|**IAM Role**|Kinesis 접근 권한|

---

## 🧑‍💻 지원 대상

### Source

- 애플리케이션 로그

- 웹 서버 로그 (Apache, Nginx)

- 시스템 로그


### Destination

- **Amazon Kinesis Data Streams**

- **Amazon Kinesis Data Firehose**


---

## 📝 설정 예시 (개념)

```json
{
  "flows": [
    {
      "filePattern": "/var/log/app.log",
      "deliveryStream": "my-firehose-stream"
    }
  ]
}
```

- `filePattern`: 수집할 로그 파일

- `deliveryStream` 또는 `streamName`: 전송 대상

---

## 🆚 다른 수집 방식과 비교

### vs CloudWatch Logs Agent

|항목|Kinesis Agent|CloudWatch Agent|
|---|---|---|
|목적|스트리밍 처리|모니터링|
|대상|로그 → Kinesis|로그/메트릭 → CloudWatch|
|실시간 분석|O|제한적|
|Firehose 연계|O|X|

---

### vs Fluentd / Fluent Bit

|항목|Kinesis Agent|Fluent Bit|
|---|---|---|
|관리 복잡도|매우 낮음|중간|
|유연성|낮음|매우 높음|
|플러그인|제한적|풍부|
|멀티 대상|제한적|가능|

---

## ⚠️ 제약 사항

- **파일 기반 입력만 지원** (네트워크/메시지 큐 X)

- **고급 변환/필터링 기능 부족**

- 컨테이너 환경에는 부적합

- Firehose 또는 Streams 전용

---

## ✅ 사용 사례

- 📄 EC2 로그 실시간 수집

- 🖥️ 온프레미스 서버 로그 스트리밍

- 📊 실시간 로그 분석 파이프라인

- 🪣 S3 로그 적재 (Firehose 연계)

---

## ✅ 요약

|항목|설명|
|---|---|
|이름|**Amazon Kinesis Agent**|
|역할|**로그/파일 → Kinesis Producer**|
|입력|파일(Log)|
|출력|Kinesis Streams / Firehose|
|장점|단순, 경량, 자동화|
|한계|유연성 낮음|

- Amazon Kinesis Data Streams

- Amazon Kinesis Data Firehose

- Amazon Managed Service for Apache Flink


원하면 다음도 같이 정리해줄게 👇

- **Kinesis Agent vs CloudWatch vs Fluent Bit 한 장 비교**

- **로그 수집 → 분석 → 저장 전체 파이프라인 예제**