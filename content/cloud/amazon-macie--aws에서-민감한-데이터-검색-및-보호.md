---
title: Amazon Macie — AWS에서 민감한 데이터 검색 및 보호
slug: "amazon-macie--aws에서-민감한-데이터-검색-및-보호"
category: cloud
tags: ["amazon-macie", "aws", "aws-eventbridge", "aws-security-hub", "data-privacy", "data-security", "machine-learning", "pii", "s3", "security"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.385534+00:00"
---

> **NOTE:**
> - 데이터 보안 및 데이터 프라이버시 서비스로서, 기계학습 및 패턴 일치를 활용하여 AWS에서 민감한 데이터를 검색하고 보호
> - 이름, 주소, 신용 카드 번호와 같은 개인 식별 정보(PII)를 포함하여 대규모의 점점 증가하는 민감 데이터 유형 목록을 자동으로 감지
> - S3 버킷에 기계학습 및 패턴 매칭 기법을 적용하여 개인 식별 정보(PII)와 같은 민감한 데이터를 식별하고 사용자에게 알릴 수 있음

Amazon Macie는 기계 학습과 패턴 일치를 사용하여 민감한 데이터를 검색하고, 데이터 보안 위험에 대한 가시성을 제공하며, 이러한 위험에 대한 자동 보호를 지원하는 데이터 보안 서비스입니다.

조직의 Amazon Simple Storage Service(Amazon S3) 데이터 자산의 보안 태세를 관리할 수 있도록 Macie는 S3 범용 버킷의 인벤토리를 제공하며, 보안 및 액세스 제어를 위해 버킷을 자동으로 평가하고 모니터링합니다. 예를 들어 버킷에 퍼블릭 액세스가 허용되는 등의 보안 또는 프라이버시 관련 잠재적 문제를 Macie가 탐지하면 Macie는 조사 결과(findings)를 생성하며, 사용자는 필요에 따라 이를 검토하고 수정할 수 있습니다.

또한 Macie는 민감한 데이터의 검색 및 보고를 자동화하여 조직이 Amazon S3에 저장하는 데이터를 더 잘 이해하도록 돕습니다. 민감한 데이터를 탐지하기 위해 Macie에서는 기본 제공 기준과 기법, 사용자가 정의한 사용자 지정 기준 또는 이 둘의 조합을 사용할 수 있습니다. Macie가 S3 객체에서 민감한 데이터를 감지하면 조사 결과를 생성하여 사용자가 발견 내용을 파악할 수 있게 알립니다.

조사 결과 외에도 Macie는 Amazon S3 데이터의 보안 상태와 민감한 데이터가 데이터 자산에 존재할 수 있는 위치에 대한 통계 및 인사이트를 제공합니다. 이러한 통계와 인사이트는 특정 S3 버킷 및 객체를 심층적으로 조사하기 위한 결정을 내리는 데 유용한 지침이 됩니다. Amazon Macie 콘솔 또는 Amazon Macie API를 통해 조사 결과, 통계 및 기타 정보를 검토하고 분석할 수 있습니다. 또한 Macie는 Amazon EventBridge 및 AWS Security Hub와 통합되어 다른 서비스, 애플리케이션 및 시스템을 사용해 결과를 모니터링, 처리 및 수정할 수 있습니다.

참고: https://docs.aws.amazon.com/ko_kr/macie/latest/user/what-is-macie.html