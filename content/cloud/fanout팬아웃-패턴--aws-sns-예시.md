---
title: Fanout(팬아웃) 패턴 — AWS SNS 예시
slug: "fanout팬아웃-패턴--aws-sns-예시"
category: cloud
tags: ["amazon-sns", "aws", "event-driven", "fanout", "lambda", "messaging", "pub-sub", "serverless", "sqs"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:08.085019+00:00"
---

### 🔁 Fanout이란?

**Fanout(팬아웃)**은 AWS에서 **한 메시지를 여러 대상으로 동시에 브로드캐스트(전파)**하는 **메시징 패턴**입니다. 즉, **하나의 이벤트나 메시지를 발행(publish)하면 여러 구독자(subscriber)가 동시에 이를 수신**하는 구조를 말합니다.

---

## 📦 예: Amazon SNS에서의 Fanout 패턴

Amazon SNS(단순 알림 서비스)는 **주제(topic)** 기반의 메시징 서비스입니다. **Fanout**은 SNS에서 자주 사용되는 패턴으로 다음과 같이 동작합니다:

```
            [Publisher (애플리케이션)]
                        │
                        ▼
              [SNS Topic (중앙 허브)]
                 ├────────────┬─────────────┐
                 ▼            ▼             ▼
         [SQS Queue A]   [Lambda 함수]   [HTTPS 엔드포인트]
```

- 하나의 **SNS 주제(topic)**에 여러 **엔드포인트(subscriber)**를 연결합니다.
- **메시지를 한 번만 발행(publish)**하면,
- 연결된 **모든 대상(subscriber)**에게 메시지가 **푸시(push)** 방식으로 전달됩니다.

이 방식은 **확장성**, **비동기 처리**, 그리고 **독립적인 소비자 처리**를 보장하는 데 유리합니다.

---

## ✅ Fanout의 특징

|항목|설명|
|---|---|
|**다중 수신자 지원**|메시지를 여러 구독자에게 동시에 전송|
|**비동기 처리**|각 수신자는 독립적으로 메시지를 처리|
|**유연한 아키텍처 구성**|예: SQS + Lambda + HTTPS 엔드포인트 조합 가능|
|**확장성**|신규 구독자 추가 시 코드 수정 없이 확장 가능|

---
## 📝 요약

|개념|설명|
|---|---|
|**Fanout**|하나의 메시지를 여러 대상으로 동시에 브로드캐스트하는 메시징 패턴|
|**사용 서비스**|주로 Amazon SNS + SQS, Lambda, HTTP/S 등|
|**장점**|확장성, 독립성, 비동기 처리|
|**적용 예시**|알림 전송, 이벤트 분기 처리, 분산 아키텍처 구현 등|