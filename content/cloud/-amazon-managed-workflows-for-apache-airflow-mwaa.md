---
title: 📘 Amazon Managed Workflows for Apache Airflow (MWAA)
slug: "-amazon-managed-workflows-for-apache-airflow-mwaa"
category: cloud
tags: ["apache-airflow", "aws", "cloudwatch", "data-pipelines", "etl", "glue", "mwaa", "redshift", "sagemaker"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.395203+00:00"
---

## 🧾 개요

**Amazon MWAA**는 **Apache Airflow**의 기능을 그대로 사용하면서도, **AWS가 설치·구성·확장·모니터링·보안·유지보수 등을 완전히 관리해 주는 서비스**입니다. 워크플로우(예: 데이터 처리, ETL, ML 학습/배포 등)를 코드로 정의하고, 시간 또는 이벤트 기반으로 실행 및 관리할 수 있습니다.

---

## 🧱 Apache Airflow란?

[Apache Airflow](https://airflow.apache.org/)는 **워크플로우 스케줄링 및 오케스트레이션 플랫폼**입니다. 작업 단계를 DAG(Airflow Directed Acyclic Graphs)로 정의하여 복잡한 워크플로우를 시각적으로 구성하고 모니터링할 수 있습니다.

예:

- 데이터 수집 → 전처리 → 저장 → 알림 전송
- 머신러닝 모델 학습 → 테스트 → 배포

---

## 🚀 Amazon MWAA의 주요 구성 요소

### 1. **DAGs (Directed Acyclic Graphs)**

- 워크플로우 정의 파일로, Python 코드로 작성됩니다.
- S3 버킷에 저장되며 MWAA 환경에서 주기적으로 로드됩니다.


### 2. **Scheduler**

- DAG의 실행 조건(예: `@daily`, `@hourly`)에 따라 작업을 트리거합니다.
- MWAA가 해당 컴포넌트를 자동으로 관리합니다.


### 3. **Web UI**

- 기본 제공되는 Apache Airflow UI입니다.
- 작업 상태 확인, 로그 조회, 수동 실행 등 다양한 기능을 제공합니다.


### 4. **Workers**

- 각 Task를 실제로 실행하는 EC2 기반의 컨테이너 인프라입니다.
- 워크로드에 따라 자동으로 스케일링됩니다.


### 5. **환경 구성**

- DAGs, requirements.txt, plugins 등을 S3로 관리합니다.
- VPC, IAM, 로그(S3, CloudWatch) 등 AWS 리소스와 연동 가능합니다.

---

## 🛠️ 실제 DAG 코드 예시

```python
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG('hello_mwaa_dag',
         description='MWAA 테스트 DAG',
         schedule_interval='@daily',
         start_date=datetime(2025, 1, 1),
         catchup=False) as dag:

    hello_task = BashOperator(
        task_id='print_hello',
        bash_command='echo "Hello from Amazon MWAA!"'
    )
```

---

## 💡 MWAA 특징 및 장점

|특징|설명|
|---|---|
|✅ **완전관리형**|Airflow 환경 설치, 유지보수, 보안 패치, 업그레이드가 자동 처리됩니다.|
|✅ **서버리스 확장성**|작업량에 따라 워커가 자동으로 증감합니다.|
|✅ **S3 중심 구성**|DAG, 의존성 패키지, 플러그인을 S3에 업로드하는 구조입니다.|
|✅ **Airflow 100% 호환**|기존 Airflow DAG, Operator, Plugin을 그대로 사용할 수 있습니다.|
|✅ **AWS 서비스 연동**|S3, Redshift, Glue, EMR, Lambda 등과 손쉽게 통합됩니다.|
|✅ **IAM 기반 보안**|각 태스크에 적절한 권한을 부여할 수 있습니다.|
|✅ **모니터링**|CloudWatch 및 Airflow UI를 통한 로그 제공으로 운영 관찰이 가능합니다.|
|✅ **VPC 통합**|프라이빗 네트워크 환경에서 안전하게 실행할 수 있습니다.|

---

## 📦 MWAA 주요 사용 사례

### 📊 데이터 파이프라인 자동화

- S3 → Glue → Redshift → 이메일 보고서 전송


### 🧪 머신러닝 워크플로우

- SageMaker 모델 훈련 → 테스트 → 배포 자동화


### 🏭 배치 작업 관리

- 대규모 배치 ETL 워크플로우 스케줄링


### 🔄 이벤트 기반 프로세싱

- 데이터 업로드 이벤트 발생 시 DAG 자동 실행

---

## 🔐 보안 구성

- **IAM Role**: DAG 실행에 필요한 최소 권한만 부여합니다.
- **KMS 암호화**: S3 및 환경 변수 암호화를 사용합니다.
- **VPC 구성**: 프라이빗 서브넷 내에서 MWAA를 실행할 수 있습니다.
- **CloudWatch Logs**: 감사용 및 디버깅용 로그를 관리합니다.

---

## ⚙️ 구성 아키텍처 다이어그램 (텍스트로 표현)

```
[S3 - DAGs, plugins]      [CloudWatch - Logs]
          |                       |
          v                       v
   [Amazon MWAA Environment] ---> [Airflow Web UI]
          |
   +------|------+
   |     VPC     |
   |   (Private) |
   +-------------+
          |
   [Glue / Redshift / Lambda / SageMaker 등]
```

---

## 📊 MWAA vs 기타 워크플로우 오케스트레이터

|항목|MWAA|EKS + Airflow|Step Functions|
|---|---|---|---|
|관리형 여부|✅ 완전관리형|❌ 직접 구성 필요|✅ 완전관리형|
|비용 구조|Pay-as-you-go|EC2 기반|상태 전이 기반|
|유연성|매우 높음|매우 높음|제한적|
|시각화|Airflow UI|Airflow UI|AWS Console|
|코드 기반 정의|Python|Python|JSON/YAML|

---

## 💰 요금 구조

MWAA는 다음 항목에 따라 요금이 청구됩니다:

- **Environment 요금**: 환경이 실행 중인 시간 기준 (vCPU, memory)
- **워크로드 요금**: DAG 실행 수, 작업 수
- **추가 요금**: S3, CloudWatch, KMS, VPC NAT Gateway 등

> 참고: [AWS MWAA 요금 페이지](https://aws.amazon.com/mwaa/pricing/)

---

## 🧪 시작을 위한 빠른 가이드

1. **S3 버킷 준비**: DAG 코드 및 플러그인 업로드용
2. **IAM Role 설정**: MWAA 실행을 위한 권한 구성
3. **MWAA 환경 생성**: AWS Console 또는 Terraform/CDK 사용
4. **Airflow Web UI 접속**: DAG 확인 및 실행 테스트
5. **모니터링**: CloudWatch 로그 확인

---

## 🔗 유용한 참고 링크

- [MWAA 공식 문서 (한국어)](https://docs.aws.amazon.com/ko_kr/mwaa/latest/userguide/what-is-mwaa.html)
- [Airflow 공식 홈페이지](https://airflow.apache.org/)
- [Airflow Operator 목록](https://registry.astronomer.io/)
- [CDK로 MWAA 구축 예제](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_mwaa-readme.html)
