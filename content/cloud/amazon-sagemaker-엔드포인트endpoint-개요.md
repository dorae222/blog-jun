---
title: Amazon SageMaker 엔드포인트(Endpoint) 개요
slug: "amazon-sagemaker-엔드포인트endpoint-개요"
category: cloud
tags: ["amazon-sagemaker", "asynchronous-inference", "aws", "boto3", "inference", "ml-deployment", "real-time-inference", "sagemaker-endpoint", "serverless"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.940542+00:00"
---

**Amazon SageMaker 엔드포인트(Endpoint)**는 훈련된 머신러닝(ML) 모델을 **실시간 또는 비동기 추론용 API로 배포**하기 위한 **호출 가능한 HTTP 엔드포인트**입니다. 즉, 모델이 학습된 후 사용자나 애플리케이션이 이를 통해 **예측을 요청하고 응답을 받을 수 있게 하는 접근 지점**입니다.

---

## 🧩 SageMaker Endpoint란?

|항목|설명|
|---|---|
|**정의**|배포된 ML 모델을 외부에서 HTTP API로 호출할 수 있도록 해주는 AWS 리소스|
|**역할**|모델을 실행 가능한 상태로 만들어 추론 요청을 받을 수 있도록 함|
|**호출 방식**|SageMaker SDK, AWS CLI, 또는 일반 HTTPS 요청|
|**연동 대상**|웹 서비스, 모바일 앱, 백엔드 서버, Lambda, Step Functions 등|

---

## ⚙️ Endpoint의 종류

### 1. **Real-time Inference Endpoint**

- **지속 실행 중**이며, API 호출 시 **즉시 응답**합니다.
- 낮은 지연 시간과 빠른 응답이 필요한 서비스에 적합합니다.
- 항상 실행되므로 **비용이 상시 발생**합니다.


### 2. **SageMaker Serverless Inference Endpoint**

- 요청이 들어올 때만 리소스를 할당합니다.
- 트래픽이 적거나 간헐적인 워크로드에 적합합니다.
- **요청 수 기반 과금**이며, 다만 **콜드 스타트 발생 가능**합니다.


### 3. **SageMaker Asynchronous Inference Endpoint**

- 요청을 큐에 넣고 나중에 **결과를 S3에 저장**합니다.
- 예측 시간이 길거나 대용량 입력 파일에 적합합니다.
- 응답 지연을 감수할 수 있는 경우에 활용합니다.

---

## 🛠️ 엔드포인트 구성 흐름

1. **모델 훈련 완료**
2. **모델 아티팩트(S3)와 이미지 URI 등록 → SageMaker Model 생성**
3. **엔드포인트 Configuration 작성**
4. **엔드포인트 생성 (`create_endpoint`)**
5. **예측 요청 (`invoke_endpoint`)**

---

## 🔍 예시 (Python SDK – boto3 or sagemaker)

```python
import boto3

client = boto3.client('sagemaker-runtime')

response = client.invoke_endpoint(
    EndpointName='my-endpoint',
    ContentType='text/csv',
    Body='5.1,3.5,1.4,0.2'
)

print(response['Body'].read())
```

---

## ✅ 장점

|항목|설명|
|---|---|
|**유연한 추론 옵션**|실시간, 서버리스, 비동기 등 다양한 방식 지원|
|**자동 확장 가능**|Real-time Endpoint는 Auto Scaling 설정 가능|
|**보안 및 인증**|IAM, VPC, TLS, 엔드포인트 정책 통합|
|**A/B 테스트 및 배포 전략**|모델 버전 간 트래픽 분할 설정 가능|

---

## ⚠️ 고려할 점

- Real-time Endpoint는 항상 켜져 있어 **비용이 지속적으로 발생**합니다.
- Serverless와 Async는 일부 **지연 시간이 존재하거나 결과 수신 방식이 다름**을 염두에 둬야 합니다.
- 추론에 필요한 리소스 설정(인스턴스 유형/메모리 등)은 워크로드 특성에 맞게 조정해야 합니다.

---

## 📦 사용 사례

|사례|설명|
|---|---|
|실시간 추천 시스템|사용자 클릭 또는 조회 시 즉시 예측|
|챗봇 응답 생성|대화형 AI 응답 모델 추론|
|이미지 분류 API|모바일 앱에서 이미지 업로드 후 분류|
|대용량 문서 분석|비동기 방식으로 문서 텍스트 분류|

---

## 🧾 요약

|항목|설명|
|---|---|
|**SageMaker Endpoint란?**|AWS에서 ML 모델을 실시간 또는 비동기 추론을 위해 HTTP API 형태로 배포한 접근 지점|
|**주요 타입**|Real-time, Serverless, Asynchronous|
|**호출 방법**|SDK, CLI, HTTP|
|**비용 구조**|사용 방식에 따라 인스턴스 시간 또는 요청 기반 과금|
