---
title: Amazon Kinesis 요약 (KPU 기반 과금 및 주요 특징)
slug: "amazon-kinesis-요약-kpu-기반-과금-및-주요-특징"
category: cloud
tags: ["aws", "iam", "kinesis", "kinesis-processing-units", "kpu", "schema-discovery", "serverless", "streaming"]
status: published
post_type: til
quality_score: 7.0
created_at: "2026-03-02T01:08:07.079860+00:00"
---

주요 포인트:

- 사용한 만큼만 비용 지불(다만 비용이 낮지는 않음)
  - 비용은 시간당 소비된 Kinesis Processing Units (KPU)에 따라 청구됩니다
  - 1 KPU = 1 vCPU + 4GB
- 서버리스: 자동으로 스케일링됩니다
- 스트리밍 소스와 대상에 접근하려면 IAM 권한을 사용하세요
- 스키마 검색(Schema discovery)
