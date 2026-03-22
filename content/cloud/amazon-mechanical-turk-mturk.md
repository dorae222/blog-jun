---
title: Amazon Mechanical Turk (MTurk)
slug: "amazon-mechanical-turk-mturk"
category: cloud
tags: ["amazon-mechanical-turk", "aws", "content-moderation", "crowdsourcing", "data-labeling", "human-in-the-loop", "mturk", "nlp", "survey"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:05.417707+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---

---
aliases:
  - Mechanical Turk
  - MTurk
---
## 🧩 Quick Overview

| 항목              | 설명 |
|-------------------|------|
| **서비스명**       | Amazon Mechanical Turk (MTurk) |
| **종류**           | 크라우드소싱 플랫폼 (Crowdsourcing Marketplace) |
| **역할**           | 전 세계 사람들에게 **작은 작업 단위(HITs)**를 분산 수행시켜 **사람의 판단이 필요한 문제를 해결**하는 서비스

> 🧠 **목적**: 사람이 수행해야 하는 **정성적 작업(예: 이미지 라벨링, 텍스트 분류, 콘텐츠 검토 등)**을 빠르게 처리할 수 있도록 돕는 **분산형 작업 플랫폼**

---

## 🧬 핵심 개념

| 개념 | 설명 |
|------|------|
| **Requester** | 작업을 등록하는 사용자 또는 조직 (예: 기업, 연구자) |
| **Worker (Turker)** | 실제 작업을 수행하는 사람 |
| **HIT (Human Intelligence Task)** | 사람이 수행하는 단위 작업 |
| **Assignment** | 특정 Worker가 하나의 HIT을 수행하는 행위 |

---

## ✅ 대표 활용 사례

- **데이터 라벨링**: 이미지에 객체 박스 지정, 텍스트 감성 분석, 번역 품질 평가 등
- **AI 학습용 데이터 수집**: 자연어 처리(NLP), 음성 인식, 챗봇 훈련 등
- **콘텐츠 모더레이션**: 사용자 리뷰나 댓글의 부적절성 평가
- **설문 조사**: 학술 연구, UX 평가 등

---

## 🧪 예시 사용 흐름

1. **Requester가 HIT 생성** (예: "이 리뷰가 긍정적인가요?")
2. MTurk 마켓플레이스에 게시
3. **Worker가 작업 수락 및 수행**
4. 결과 제출 → 품질 확인 → 보상 지급

---

## ✅ 장점

| 항목 | 설명 |
|------|------|
| **확장성** | 수천 명의 작업자에게 대량 작업을 병렬로 분산 가능 |
| **빠른 수행** | 짧은 시간에 대규모 수작업 처리 가능 |
| **비용 절감** | 자동화가 어려운 작업을 상대적으로 낮은 비용으로 처리 가능 |
| **유연성** | 설문, 라벨링, 검토 등 다양한 작업 유형 구성 가능 |

---

## ⚠️ 유의사항

| 항목 | 설명 |
|------|------|
| **품질 편차** | 작업자 수준이 다양하므로 검증 메커니즘이 필요 |
| **보상 설정 중요** | 보상액에 따라 작업 속도 및 품질에 큰 영향을 미침 |
| **개인정보 주의 필요** | 민감한 데이터 노출 방지 필수 |

---

## 🧾 요약

| 항목 | 설명 |
|------|------|
| **정의** | 사람의 판단이 필요한 작업을 전 세계 크라우드소싱 인력을 통해 처리하는 AWS 서비스 |
| **핵심 구성** | Requester, Worker, HIT, Assignment |
| **활용 분야** | ML 데이터 라벨링, 콘텐츠 평가, 사용자 연구 등 |
| **장점** | 빠르고 확장 가능한 수작업 처리 시스템 |
