---
title: 동적 데이터 마스킹(Dynamic Data Masking)
slug: "동적-데이터-마스킹dynamic-data-masking"
category: cloud
tags: ["access-control", "amazon-redshift", "data-masking", "data-protection", "dynamic-data-masking", "policy-based-security", "security", "sql"]
status: published
post_type: tutorial
quality_score: 9.0
created_at: "2026-03-02T01:08:07.429902+00:00"
---

## 🧩 Quick Overview

| 항목         | 설명                                                            |
| ---------- | ------------------------------------------------------------- |
| **기능명**    | 동적 데이터 마스킹 (Dynamic Data Masking)                             |
| **관련 서비스** | Amazon Redshift (2023년부터 정식 지원)                               |
| **역할**     | **민감한 데이터 컬럼에 대해 사용자의 역할 또는 권한에 따라 마스킹된 값만 제공**하는 정책 기반 보안 기능 |

> 🛡️ **목적**: 민감 정보(예: 주민번호, 이메일, 카드번호 등)를 **원본 데이터 변형 없이 실시간으로 자동 마스킹**하여, 불필요한 정보 노출을 방지

---

## 🧬 작동 방식

- **Redshift 내부 정책을 기반으로** SELECT 쿼리 실행 시점에 데이터 마스킹을 수행합니다.
- **사용자 또는 역할(Role)**에 따라 마스킹 적용 여부를 동적으로 결정합니다.
- **데이터 자체는 변경되지 않음** → 조회 시점에만 마스킹된 값으로 노출됩니다.

---

## 🛡️ 마스킹 유형 예시

| 마스킹 함수         | 설명 |
|---------------------|------|
| `NULL`              | 데이터 완전 숨김 |
| `DEFAULT()`         | 컬럼 타입에 따른 기본값 반환 |
| `PARTIAL()`         | 일부는 그대로, 나머지는 마스킹 (예: 신용카드 번호 앞 4자리만 노출) |
| `CUSTOM EXPRESSION` | 사용자 정의 SQL 표현식 사용 가능 |

---

## ✅ 사용 예시

```sql
CREATE MASKING POLICY mask_email
AS (val string) ->
  CASE
    WHEN current_user IN ('trusted_user1', 'admin') THEN val
    ELSE '*****@****.com'
  END;

-- 정책 적용
ALTER TABLE users ALTER COLUMN email
SET MASKING POLICY mask_email;
```