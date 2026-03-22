---
title: AWS Step Functions 정리 (내 공부 기록)
slug: "aws-step-functions-개요-및-사용-사례"
category: cloud
tags: ["aws", "mlops", "serverless", "step-functions", "workflow"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:04.462821+00:00"
---

## Quick Overview

|항목|설명|
|---|---|
|**서비스명**|AWS Step Functions|
|**기능**|서버리스 워크플로우 조정 및 상태 머신 실행|
|**워크플로우 타입**|Standard / Express|
|**주요 구성 요소**|`State`, `Task`, `Choice`, `Parallel`, `Map`, `Wait`, `Fail` 등|
|**통합 서비스**|Lambda, SageMaker, ECS, DynamoDB, EventBridge 등 200+ AWS 서비스|

> **목적**: 여러 AWS 서비스 또는 사용자 작업을 **순차/병렬/조건 기반으로 자동 실행**하는 **서버리스 워크플로우 오케스트레이션 도구**

---

- 결론부터 말하면, 처음엔 "워플로우 오케스트레이션"이 추상적으로 다가왔는데 실제로 여러 서비스 연결해 보니 내가 관리해야 할 상태와 오류 처리가 훨씬 명확해졌습니다.
- 해보니까 Standard/Express의 비용·지속성·지연 특성 차이를 미리 파악하는 게 설계에서 핵심입니다.

## AWS Step Functions란?

**AWS Step Functions**는 여러 작업(task)을 순차적 또는 병렬적으로 실행하는 시각적 워크플로우 관리 서비스입니다. 각 작업은 상태(state)로 표현되며, JSON 기반으로 정의한 **상태 머신(state machine)**에 따라 정의된 흐름대로 자동으로 실행됩니다.

프로그래밍 없이 AWS 콘솔에서 시각적으로 설계할 수 있고, Python SDK, CDK, CloudFormation 등 코드로도 정의할 수 있습니다.

- 내가 처음 설정할 땐 콘솔 드래그앤드롭이 이해에 큰 도움이 됐습니다. 코드로 정의하는 건 재현성과 버전 관리 측면에서 훨씬 좋았습니다.
- 실무에선 콘솔로 빠르게 프로토타입 만들고, 안정화되면 CDK/CloudFormation으로 옮기는 방식이 편합니다.

---

## 구성 요소

|구성 요소|설명|
|---|---|
|**State Machine**|전체 워크플로우 정의|
|**State**|각 단계 (예: Task, Choice, Wait, Parallel 등)|
|**Task**|실제 작업 수행 (예: Lambda 함수 호출, SageMaker 작업 실행 등)|
|**Choice**|조건 분기 처리|
|**Parallel**|여러 작업을 동시에 실행|
|**Wait**|일정 시간 대기|
|**Fail / Succeed**|성공 또는 실패로 상태 머신 종료|

- 각 구성 요소의 역할을 직접 구현해 보니, 특히 Choice와 Retry 전략 설계에서 실수가 많았습니다. 기본 재시도 정책을 그대로 쓰면 의도치 않은 반복 호출이 발생하기도 했습니다.

---

## 워크플로우 유형

|유형|특징|적합 시나리오|
|---|---|---|
|**Standard**|상태 저장, 실행 이력 보관, 최대 1년 지속|장기 실행 또는 복원이 필요한 워크플로우|
|**Express**|초고속 처리, 짧은 실행 시간(최대 5분), 로그 기반 트래킹|고빈도 이벤트 처리나 실시간 처리(예: IoT, API 요청 흐름)|

- 처음엔 둘의 차이가 단순히 속도 차이인 줄 알았는데, 실행 이력 보관과 비용 모델, 실패 복구 가능성에서 큰 차이가 있었습니다.
- 해보니까 Express는 고빈도 이벤트에 좋고, Standard는 긴 작업·장기 추적에 필수입니다.

---

## 주요 통합 서비스

|통합 서비스|활용 예|
|---|---|
|**AWS Lambda**|함수 기반 로직 실행|
|**Amazon SageMaker**|학습, 배포, 추론 단계 자동화|
|**AWS Glue**|데이터 추출/변환 파이프라인 연결|
|**Amazon ECS / Fargate**|컨테이너 기반 작업 수행|
|**SNS / SQS**|메시징, 알림, 큐 기반 제어|
|**Step Functions 자체**|중첩 상태 머신 실행 (nested workflows)|

- 실무에서 여러 서비스를 연결해 보니, Lambda는 간단한 유틸리티에, ECS/SageMaker는 무거운 작업에 잘 맞았습니다.
- 중첩 워크플로우(nested workflows)를 이용하면 복잡한 흐름을 모듈화하기 좋았습니다.

---

## 장점

|항목|설명|
|---|---|
|**시각적 설계**|AWS 콘솔에서 드래그 앤 드롭으로 구성 가능|
|**에러 핸들링 내장**|재시도, 실패 분기, 타임아웃 제어 기능 제공|
|**확장성 & 유지관리 용이성**|코드 없이도 복잡한 워크플로우 구성 가능|
|**비용 절감**|서버리스 기반으로 유휴 인프라 비용 없음|
|**추적 및 디버깅 지원**|실행 이력과 CloudWatch Logs 연동으로 추적 가능|

- 개인적으로 가장 편했던 건 에러 핸들링 정책을 상태 머신 레벨에서 관리할 수 있다는 점이었습니다. 서비스별로 분산된 로직 대신 한곳에서 재시도/백오프를 제어하니 운영 부담이 줄었습니다.

---

## 예시 워크플로우 (JSON 상태 머신)

```json
{
  "StartAt": "PreprocessData",
  "States": {
    "PreprocessData": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-west-2:123456789:function:preprocess",
      "Next": "TrainModel"
    },
    "TrainModel": {
      "Type": "Task",
      "Resource": "arn:aws:sagemaker:train-job",
      "Next": "EvaluateModel"
    },
    "EvaluateModel": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.accuracy",
          "NumericGreaterThan": 0.9,
          "Next": "DeployModel"
        }
      ],
      "Default": "FailState"
    },
    "DeployModel": {
      "Type": "Task",
      "Resource": "arn:aws:sagemaker:deploy",
      "End": true
    },
    "FailState": {
      "Type": "Fail",
      "Error": "ModelNotGoodEnough",
      "Cause": "Accuracy < 90%"
    }
  }
}
```

- 이 예시는 내가 MLOps 파이프라인을 만들면서 가장 먼저 써본 패턴입니다. 성능 기준에 따라 분기하는 구조가 직관적이라 여러 프로젝트에서 반복 사용했습니다.

---

## 사용 사례

|분야|사용 예|
|---|---|
|**MLOps**|SageMaker로 모델 학습 → 성능 평가 → 자동 배포|
|**ETL 자동화**|Glue, Lambda, S3, Redshift 등으로 데이터 파이프라인 구성|
|**DevOps 배포 흐름**|테스트 → 승인 → 배포까지 자동화|
|**IoT 이벤트 흐름 제어**|센서 이벤트 → 필터링 → 알림 발송|

- 실제로는 MLOps와 ETL 자동화에 가장 자주 사용했고, 특히 모델 학습-평가-배포의 자동화에 큰 이점이 있었습니다.

---

## 요약

|항목|설명|
|---|---|
|**정의**|AWS 서비스 및 사용자 작업을 연결하는 시각적/코드 기반 서버리스 워크플로우|
|**형태**|JSON 상태 머신 정의|
|**주요 기능**|조건 분기, 병렬 처리, 실패 처리, 재시도|
|**워크플로우 유형**|Standard (장기), Express (단기/고속)|
|**적합 용도**|MLOps, ETL, DevOps, 비즈니스 프로세스 자동화 등|

- 정리하면, 처음엔 복잡해 보였지만 직접 만들어보고 운영하면서 워크플로우 설계·오류 처리·비용 모델을 이해하게 됐습니다. 지금은 서비스 연동이 필요할 때 가장 먼저 고려하는 도구 중 하나입니다.

[원본 노션/옵시디언 — 이 내용 기준으로 빠짐없이 반영]
(원본 파일 없음 — draft 기준으로 수정)