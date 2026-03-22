---
title: Apache Zeppelin
slug: "apache-zeppelin"
category: cloud
tags: ["analytics", "apache-zeppelin", "big-data", "data-science", "flink", "hive", "multi-language", "notebook", "spark", "visualization"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:06.177012+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---
---
aliases:
  - Zeppelin
---
## 🧩 Quick Overview

| 항목              | 설명 |
|-------------------|------|
| **이름**           | Apache Zeppelin |
| **유형**           | **웹 기반 데이터 분석·시각화 노트북** |
| **주요 목적**       | 데이터 과학자와 엔지니어가 **코드, 쿼리, 시각화 작업을 한 환경에서 수행**할 수 있는 대화형 분석 도구 |

> 💻 **Zeppelin**은 주피터 노트북과 유사하지만,
> **다양한 언어와 분산 데이터 처리 엔진(Spark 등)**을 지원하는
> **멀티 언어 기반의 웹 노트북 플랫폼**입니다.

---

## 🔧 주요 특징

| 항목 | 설명 |
|------|------|
| **멀티 언어 지원** | Python, Scala, SQL, R, Julia, Shell 등 |
| **분산 처리 엔진 연계** | Apache Spark, Flink, Hive, Presto, Kylin 등과 통합 |
| **시각화** | 테이블, 차트, 히트맵, 동적 대시보드 제공 |
| **노트북 공유** | 웹 기반 인터페이스로 협업 가능 |
| **플러그인 아키텍처** | Interpreter 기반 확장 가능 |

---

## 🛠️ 활용 예시

1. **데이터 탐색 및 전처리**
   ```sql
   %spark.sql
   SELECT category, COUNT(*) 
   FROM sales
   GROUP BY category;
   ```