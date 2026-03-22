---
title: "TIL: View의 의미 (데이터 맥락에서)"
slug: "view-데이터-맥락에서"
category: cloud
tags: ["athena", "aws-glue", "data-catalog", "sql", "TIL", "view"]
status: published
post_type: til
quality_score: 8.0
created_at: "2026-03-02T01:08:08.255518+00:00"
---

> **NOTE:**
> 데이터베이스나 데이터 카탈로그에서 사용하는 **논리적인 가상 테이블**을 의미합니다.

---

## 📘 View의 의미 (데이터 맥락에서)

- **View**는 **기존 테이블에 대한 SELECT 쿼리를 기반으로 정의된 가상의 테이블**입니다. 결론부터 말하면, 실무에서 쿼리 재사용이나 접근 편의를 위해 자주 만들게 되었습니다.

- 데이터는 실제로 저장되지 않지만, 마치 테이블처럼 조회할 수 있습니다. 처음엔 몰랐는데, 성능 특성이나 권한 관점에서 테이블과 차이가 있다는 점에서 주의가 필요했습니다.

- 예를 들어:

```sql
CREATE VIEW korean_users AS
SELECT * FROM users WHERE country = 'KR';
```

---

## 📌 Glue와 View

- AWS Glue에서 생성한 **View**는 Glue Data Catalog에 등록되며,
  **Athena, Redshift Spectrum, EMR 등에서 사용할 수 있습니다.** 제가 직접 Glue에 View를 만들어서 Athena에서 바로 조회해봤습니다.

- 다만, 이 View 자체는 **실제 데이터에 대한 접근 권한을 강제하지 못합니다.** 그래서 보안 목적이라면 IAM/S3 권한 같은 별도 통제가 필요했습니다.

---

## ✅ 요약

- SQL 문법이나 데이터 레이크 카탈로그에서 사용하는 **가상 테이블 개념**입니다. 해보니까 개념은 단순하지만 운영에서는 고려할 점이 꽤 있었습니다.

- Glue에 등록된 View는 유용하지만 **보안 또는 권한 통제 수단으로는 한계**가 있습니다. 권한은 별도로 설계해야 안전합니다.

(원본 노션/옵시디언 — 이 내용 기준으로 빠짐없이 반영)
