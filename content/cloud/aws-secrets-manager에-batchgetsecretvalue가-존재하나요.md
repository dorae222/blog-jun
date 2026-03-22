---
title: "AWS Secrets Manager에 `BatchGetSecretValue`가 존재하나요?"
slug: "aws-secrets-manager에-batchgetsecretvalue가-존재하나요"
category: cloud
tags: ["api", "aws", "aws-secrets-manager", "best-practices", "cloud", "secrets", "security"]
status: published
post_type: til
quality_score: 9.0
created_at: "2026-03-02T01:08:06.283336+00:00"
---

## 📌 먼저, AWS의 비밀(Secrets) 관련 API

AWS에서 비밀 정보를 안전하게 저장하고 읽어오는 서비스는 **AWS Secrets Manager**입니다. 일반적으로 자격 증명이나 민감한 정보는 `GetSecretValue` API를 통해 가져옵니다.

> **하지만 현재 AWS Secrets Manager에는 공식적으로 `BatchGetSecretValue`라는 API는 존재하지 않습니다.**

공식 문서에 나오는 주요 API는 다음과 같습니다.

- `CreateSecret` : 비밀 생성
- `UpdateSecret` : 비밀 업데이트
- `GetSecretValue` : 단일 비밀 조회
- `ListSecrets` : 비밀 목록 조회
- `DeleteSecret` : 비밀 삭제

👉 **따라서 AWS 표준 API로서 “BatchGetSecretValue”는 존재하지 않습니다.**

---

## 🔎 그러면 BatchGetSecretValue가 뭐지?

이 이름은 종종 두 가지 상황 중 하나에서 등장합니다.

### 1️⃣ 오해하거나 잘못된 번역 / 비공식 코드 예시

- “한꺼번에 여러 비밀을 가져온다”라는 맥락에서 비공식적으로 쓰이는 용어일 수 있습니다.
- 그러나 AWS Secrets Manager는 현재 **단일 호출로 여러 비밀을 한꺼번에 가져오는 API를 제공하지 않습니다.**
  → 여러 개를 가져오려면 `GetSecretValue`를 여러 번 호출하거나, 캐싱·병렬 처리를 직접 구현해야 합니다.

### 2️⃣ 회사 내부 라이브러리나 래퍼 함수 이름일 가능성

- 어떤 회사의 내부 코드나 SDK에서, 여러 Secret을 가져오기 위해 만든 커스텀 래퍼나 헬퍼 함수에 `BatchGetSecretValue`라는 이름을 붙였을 수 있습니다.
  (예: 사내 공용 라이브러리에서 `BatchGetSecretValue`라는 함수를 만들어 `GetSecretValue`를 반복 호출하도록 구현한 경우)

---

## ✅ 시험 및 공식 AWS 기준으로 정리

|질문|답변|
|---|---|
|AWS 공식 Secrets Manager API에 `BatchGetSecretValue`가 있는가?|❌ 없음|
|여러 비밀을 가져오려면?|`ListSecrets`로 목록 조회 후, 각 항목에 대해 `GetSecretValue` 호출|
|“BatchGetSecretValue”라는 이름이 나온다면?|✔️ **비공식적인 사내 API이거나, 오해된 명칭**일 가능성 큼|

---

## ✨ 정리

> ✅ **공식 AWS API:** `GetSecretValue` (단일 비밀을 가져옴)  
> 🚫 **BatchGetSecretValue:** AWS 공식 Secrets Manager API에 없음.  
> 👉 여러 개를 한 번에 가져오려면 직접 코드에서 반복 호출하거나 사내에서 제공하는 별도 함수(래퍼)를 사용해야 합니다.