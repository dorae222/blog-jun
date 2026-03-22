---
title: Amazon DynamoDB Streams
slug: "amazon-dynamodb-streams"
category: cloud
tags: ["aws", "aws-lambda", "dynamodb", "elasticsearch", "event-driven", "kinesis", "sns", "sqs", "streams"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:06.605867+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---

**Amazon DynamoDB Streams**는 **DynamoDB 테이블에서 발생하는 변경 사항(삽입, 수정, 삭제)을 시간 순으로 캡처하여 스트림으로 제공하는 기능**입니다.

---

## 🔄 DynamoDB Streams란?

> **DynamoDB Streams**는 DynamoDB 테이블에서 발생한 모든 **데이터 변경 이벤트를**
> **실시간 스트림 형태로 캡처**하여 **다른 AWS 서비스와 연동하거나 후속 작업을 수행**할 수 있도록 해주는 기능입니다.

---

## 🎯 무엇을 할 수 있나요?

|용도|설명|
|---|---|
|**변경 이벤트 추적**|어떤 항목이 언제 추가/수정/삭제되었는지 기록|
|**Lambda 트리거 사용**|데이터 변경 시 Lambda 함수 자동 실행 가능|
|**이중 쓰기 처리**|두 개의 테이블 동기화 또는 아카이빙|
|**비동기 작업**|변경사항을 기반으로 알림, 인덱싱, 분석 파이프라인 구성|

---

## 🔍 어떤 정보가 스트림에 담기나요?

스트림에 포함되는 레코드는 아래와 같은 구조를 가집니다:

|정보|설명|
|---|---|
|**eventName**|`INSERT`, `MODIFY`, `REMOVE`|
|**dynamodb.Keys**|파티션 키/정렬 키|
|**NewImage**|변경 후 전체 아이템 (선택 옵션)|
|**OldImage**|변경 전 전체 아이템 (선택 옵션)|

> 스트림 설정 시, 포함할 정보 수준(예: New only, Old only, both 등)을 선택할 수 있습니다.

---

## 🛠️ 구성 예시: Lambda와 연동

1. **DynamoDB 스트림 활성화**
    
2. **"New and old images"** 선택
    
3. Lambda 함수를 생성하고, 해당 스트림을 **이벤트 소스로 등록**
    
4. 데이터가 변경되면 자동으로 Lambda가 실행됨
    

---

## ✅ 사용 사례 예시

|시나리오|설명|
|---|---|
|**실시간 감사 로그 기록**|변경 이력을 DynamoDB 또는 S3에 저장|
|**알림 전송**|데이터 변경 시 SNS로 알림 발송|
|**데이터 복제**|DynamoDB A 테이블의 변경 사항을 B 테이블에 복제|
|**Elasticsearch 동기화**|신규 문서가 등록되면 Elasticsearch에 색인|

---

## 🔒 주의 사항

- **스트림 데이터는 최대 24시간 동안 보관됨**
    
- 소비자는 **ShardIterator**를 통해 스트림 데이터 순차 처리
    
- **요금 없음**, 단지 데이터 소비(Lambda 등)에 따라 과금 발생
    

---

## ✅ 요약

|항목|내용|
|---|---|
|이름|**Amazon DynamoDB Streams**|
|목적|**DynamoDB 데이터 변경을 실시간 스트림으로 추적**|
|주요 연동|AWS Lambda, Kinesis, SQS, SNS 등|
|보관 기간|**최대 24시간**|
|실시간성|✅ 이벤트 중심 아키텍처 구성 가능|
