## 개요

Amazon SageMaker Canvas는 AWS가 제공하는 노코드(No-Code) 머신러닝 플랫폼입니다. 기존에 머신러닝 모델을 구축하려면 Python, R 등의 프로그래밍 언어와 ML 프레임워크에 대한 깊은 이해가 필요했습니다. SageMaker Canvas는 이러한 진입 장벽을 완전히 제거하여, 비즈니스 분석가나 도메인 전문가가 코드 한 줄 작성하지 않고도 머신러닝 모델을 구축하고 예측을 수행할 수 있도록 합니다.

SageMaker Canvas는 AutoML 기술을 기반으로 하며, 사용자가 데이터를 업로드하고 예측 대상 열을 선택하기만 하면 자동으로 최적의 모델을 탐색하고 학습합니다. 이는 데이터 과학팀의 리소스가 부족한 조직에서 특히 유용하며, ML의 민주화(Democratization of ML)라는 AWS의 비전을 구현하는 핵심 서비스입니다.

### SageMaker Canvas가 해결하는 문제

전통적인 머신러닝 워크플로우에서는 다음과 같은 단계를 거쳐야 합니다.

1. 데이터 수집 및 전처리
2. 피처 엔지니어링
3. 알고리즘 선택
4. 하이퍼파라미터 튜닝
5. 모델 학습 및 평가
6. 모델 배포

이 모든 과정에는 전문적인 ML 엔지니어링 지식이 요구됩니다. SageMaker Canvas는 이 전체 파이프라인을 시각적 인터페이스로 추상화하여, 비기술 인력도 ML 모델을 활용할 수 있게 만듭니다.

## 핵심 기능

### 1. 노코드 모델 구축

SageMaker Canvas의 가장 핵심적인 기능은 코드 없이 ML 모델을 생성할 수 있다는 것입니다. 사용자는 드래그 앤 드롭 인터페이스를 통해 데이터를 로드하고, 예측하고자 하는 타겟 열을 선택하면 됩니다. Canvas는 내부적으로 SageMaker Autopilot을 활용하여 다양한 알고리즘과 하이퍼파라미터 조합을 자동으로 탐색합니다.

지원하는 문제 유형은 다음과 같습니다.

- **이진 분류(Binary Classification)**: 고객 이탈 여부, 사기 탐지 등
- **다중 클래스 분류(Multi-class Classification)**: 제품 카테고리 분류, 감성 분석 등
- **수치 예측(Regression)**: 매출 예측, 가격 예측 등
- **시계열 예측(Time Series Forecasting)**: 수요 예측, 재고 관리 등
- **텍스트 분류(Text Classification)**: 리뷰 감성 분석, 문서 분류 등
- **이미지 분류(Image Classification)**: 제품 결함 탐지, 의료 영상 분석 등

### 2. 데이터 연결 및 준비

Canvas는 다양한 데이터 소스와 직접 연결할 수 있습니다.

- **Amazon S3**: CSV, Parquet 등 다양한 형식 지원
- **Amazon Redshift**: 데이터 웨어하우스 직접 연결
- **Amazon Athena**: S3 기반 쿼리 결과 활용
- **Snowflake**: 외부 데이터 웨어하우스 연동
- **로컬 파일 업로드**: 최대 5GB까지 직접 업로드

데이터 준비 단계에서는 다음 기능을 제공합니다.

- 결측값 처리 (자동/수동)
- 이상값 탐지 및 제거
- 데이터 타입 변환
- 열 이름 변경 및 삭제
- 데이터셋 조인 및 결합
- 필터링 및 정렬

### 3. 모델 빌드 옵션

Canvas는 두 가지 모델 빌드 옵션을 제공합니다.

**Quick Build (빠른 빌드)**
- 2~15분 이내 완료
- 데이터의 서브셋을 사용하여 빠르게 결과 확인
- 프로토타이핑 및 탐색적 분석에 적합
- 비용이 상대적으로 낮음

**Standard Build (표준 빌드)**
- 2~4시간 소요 (데이터 크기에 따라 다름)
- 전체 데이터셋을 사용하여 최적 모델 탐색
- SageMaker Autopilot이 수백 개의 모델 후보를 평가
- 프로덕션 수준의 정확도를 목표로 함

### 4. 모델 분석 및 해석

모델 학습이 완료되면 Canvas는 다음과 같은 분석 결과를 제공합니다.

- **정확도 메트릭**: RMSE, MAE, F1 Score, AUC 등
- **피처 중요도(Feature Importance)**: 각 입력 변수가 예측에 미치는 영향
- **What-if 분석**: 입력값을 변경했을 때 예측 결과가 어떻게 변하는지 시뮬레이션
- **Advanced Metrics**: Confusion Matrix, ROC Curve 등 상세 평가 지표

### 5. 생성형 AI 통합

2023년 이후 Canvas는 생성형 AI 기능을 통합하여 다음을 지원합니다.

- **자연어 데이터 탐색**: 데이터에 대한 질문을 자연어로 수행
- **Ready-to-use 모델**: Amazon Bedrock 기반의 파운데이션 모델 직접 활용
- **자동 데이터 준비 추천**: AI가 데이터 전처리 방법을 제안

## 아키텍처/동작 원리

### 내부 아키텍처

SageMaker Canvas의 내부 동작은 다음과 같은 구조로 이루어집니다.

```
[사용자 인터페이스 (Canvas UI)]
        |
        v
[데이터 수집 계층]
  - S3 Connector
  - Redshift Connector
  - Athena Connector
  - Snowflake Connector
        |
        v
[데이터 전처리 엔진]
  - SageMaker Data Wrangler (내부)
  - 결측값 처리
  - 피처 엔지니어링
        |
        v
[AutoML 엔진]
  - SageMaker Autopilot
  - 알고리즘 탐색
  - 하이퍼파라미터 최적화
        |
        v
[모델 레지스트리]
  - SageMaker Model Registry
  - 버전 관리
  - 승인 워크플로우
        |
        v
[추론 엔진]
  - 배치 예측
  - 실시간 추론 (SageMaker Endpoint)
```

### AutoML 프로세스 상세

Canvas가 내부적으로 사용하는 SageMaker Autopilot의 AutoML 프로세스는 다음 단계로 구성됩니다.

1. **데이터 분석(Data Analysis)**: 데이터의 통계적 특성, 분포, 상관관계를 분석합니다.
2. **후보 파이프라인 생성(Candidate Generation)**: 다양한 전처리-알고리즘 조합의 후보 파이프라인을 생성합니다.
3. **피처 엔지니어링(Feature Engineering)**: 원본 피처에서 파생 피처를 자동으로 생성합니다.
4. **모델 튜닝(Model Tuning)**: Bayesian Optimization을 사용하여 각 후보 모델의 하이퍼파라미터를 최적화합니다.
5. **모델 선택(Model Selection)**: 교차 검증을 통해 최적의 모델을 선택합니다.

### 보안 아키텍처

Canvas는 다음과 같은 보안 체계를 갖추고 있습니다.

- **네트워크 격리**: VPC 내에서 실행되며, 인터넷 액세스 없이도 운영 가능
- **데이터 암호화**: 전송 중(TLS) 및 저장 시(KMS) 암호화
- **IAM 통합**: 세분화된 액세스 제어
- **감사 로깅**: CloudTrail을 통한 모든 API 호출 기록

## 실전 활용

### 사용 사례 1: 고객 이탈 예측

비즈니스 분석가가 Canvas를 사용하여 고객 이탈을 예측하는 전체 워크플로우를 살펴보겠습니다.

먼저 AWS CLI를 사용하여 S3에 학습 데이터를 업로드합니다.

```bash
# 학습 데이터를 S3에 업로드
aws s3 cp customer_churn_data.csv s3://my-canvas-bucket/datasets/churn/

# 데이터가 정상적으로 업로드되었는지 확인
aws s3 ls s3://my-canvas-bucket/datasets/churn/

# 파일 크기 및 상세 정보 확인
aws s3api head-object \
  --bucket my-canvas-bucket \
  --key datasets/churn/customer_churn_data.csv
```

Canvas에서 SageMaker 도메인을 확인하고 설정하는 CLI 명령어입니다.

```bash
# SageMaker 도메인 목록 확인
aws sagemaker list-domains

# Canvas 사용자 프로필 생성
aws sagemaker create-user-profile \
  --domain-id d-xxxxxxxxxxxx \
  --user-profile-name canvas-analyst-user \
  --user-settings '{
    "CanvasAppSettings": {
      "TimeSeriesForecastingSettings": {
        "Status": "ENABLED"
      },
      "ModelRegisterSettings": {
        "Status": "ENABLED"
      },
      "DirectDeploySettings": {
        "Status": "ENABLED"
      }
    }
  }'

# Canvas 앱 실행 상태 확인
aws sagemaker list-apps \
  --domain-id-equals d-xxxxxxxxxxxx \
  --user-profile-name-equals canvas-analyst-user
```

### 사용 사례 2: 시계열 수요 예측

소매업에서 제품 수요를 예측하는 시나리오입니다.

```bash
# 시계열 데이터 준비 및 업로드
aws s3 sync ./demand_forecast_data/ s3://my-canvas-bucket/datasets/demand/

# Canvas에서 생성한 모델의 배치 추론 작업 확인
aws sagemaker list-transform-jobs \
  --name-contains canvas-demand \
  --sort-by CreationTime \
  --sort-order Descending \
  --max-results 5

# 배치 추론 결과 다운로드
aws s3 cp s3://my-canvas-bucket/canvas-output/demand-predictions/ \
  ./predictions/ --recursive
```

### 사용 사례 3: Canvas에서 학습한 모델을 SageMaker Studio로 공유

Canvas에서 만든 모델을 데이터 과학자와 공유하여 추가 개선을 수행할 수 있습니다.

```bash
# Canvas에서 생성된 Autopilot 작업 확인
aws sagemaker list-auto-ml-jobs \
  --sort-by CreationTime \
  --sort-order Descending \
  --max-results 10

# 특정 AutoML 작업의 상세 정보 조회
aws sagemaker describe-auto-ml-job \
  --auto-ml-job-name canvas-churn-prediction-2024

# 최적 모델 후보(Best Candidate) 정보 확인
aws sagemaker describe-auto-ml-job \
  --auto-ml-job-name canvas-churn-prediction-2024 \
  --query 'BestCandidate.{ModelName: CandidateName, Objective: FinalAutoMLJobObjectiveMetric}'

# 모델을 Model Registry에 등록
aws sagemaker create-model-package \
  --model-package-group-name churn-prediction-models \
  --inference-specification '{
    "Containers": [{
      "Image": "<autopilot-container-image>",
      "ModelDataUrl": "s3://my-canvas-bucket/models/churn/model.tar.gz"
    }],
    "SupportedContentTypes": ["text/csv"],
    "SupportedResponseMIMETypes": ["text/csv"]
  }' \
  --model-approval-status PendingManualApproval
```

### Canvas 워크스페이스 관리

```bash
# Canvas 워크스페이스 세션 시간 확인
aws sagemaker describe-app \
  --domain-id d-xxxxxxxxxxxx \
  --user-profile-name canvas-analyst-user \
  --app-type Canvas \
  --app-name default

# Canvas 앱 삭제 (비용 절감을 위해 미사용 시)
aws sagemaker delete-app \
  --domain-id d-xxxxxxxxxxxx \
  --user-profile-name canvas-analyst-user \
  --app-type Canvas \
  --app-name default
```

## 모범 사례/보안

### 비용 최적화

SageMaker Canvas의 비용은 세션 시간과 모델 학습 시간에 따라 결정됩니다. 다음은 비용을 최적화하기 위한 모범 사례입니다.

1. **Quick Build를 먼저 사용**: 데이터 탐색 및 프로토타이핑 단계에서는 Quick Build를 활용하여 비용을 절감합니다. Standard Build는 최종 프로덕션 모델 생성 시에만 사용합니다.

2. **세션 관리**: Canvas 세션은 사용하지 않을 때 로그아웃하여 세션 비용을 절감합니다. Canvas는 시간당 세션 요금이 부과되므로, 불필요한 세션을 유지하지 않는 것이 중요합니다.

3. **데이터 크기 최적화**: 학습에 필요한 최소한의 데이터만 사용합니다. 불필요한 열을 제거하고, 적절한 샘플링을 수행하면 학습 시간과 비용을 줄일 수 있습니다.

4. **예약 인스턴스 활용**: Canvas가 내부적으로 사용하는 SageMaker 인스턴스에 대해 Savings Plans를 적용할 수 있습니다.

### 보안 모범 사례

1. **최소 권한 원칙 적용**: Canvas 사용자에게는 필요한 최소한의 IAM 권한만 부여합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sagemaker:CreatePresignedDomainUrl",
        "sagemaker:DescribeDomain",
        "sagemaker:ListApps"
      ],
      "Resource": "arn:aws:sagemaker:ap-northeast-2:123456789012:domain/d-xxxxxxxxxxxx"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::my-canvas-bucket",
        "arn:aws:s3:::my-canvas-bucket/*"
      ]
    }
  ]
}
```

2. **VPC 격리**: Canvas를 VPC 내에서 실행하여 데이터가 퍼블릭 인터넷을 거치지 않도록 합니다.

3. **데이터 암호화**: S3 버킷에 저장되는 모든 데이터에 KMS 암호화를 적용합니다.

```bash
# KMS 키 생성
aws kms create-key \
  --description "SageMaker Canvas 데이터 암호화 키" \
  --key-usage ENCRYPT_DECRYPT \
  --key-spec SYMMETRIC_DEFAULT

# S3 버킷 기본 암호화 설정
aws s3api put-bucket-encryption \
  --bucket my-canvas-bucket \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "aws:kms",
        "KMSMasterKeyID": "arn:aws:kms:ap-northeast-2:123456789012:key/key-id"
      },
      "BucketKeyEnabled": true
    }]
  }'
```

4. **감사 및 모니터링**: CloudTrail과 CloudWatch를 활용하여 Canvas 활동을 모니터링합니다.

5. **데이터 거버넌스**: 민감한 데이터가 Canvas에 로드되지 않도록 데이터 분류 체계를 수립하고, AWS Lake Formation과 연동하여 세분화된 데이터 접근 제어를 구현합니다.

### 조직 도입 모범 사례

1. **교육 프로그램 운영**: 비즈니스 사용자를 대상으로 Canvas 사용법과 ML 기본 개념에 대한 교육을 제공합니다.
2. **거버넌스 프레임워크 수립**: 모델 승인 프로세스, 데이터 사용 정책, 모델 모니터링 체계를 수립합니다.
3. **단계적 도입**: 파일럿 프로젝트로 시작하여 점진적으로 사용 범위를 확대합니다.
4. **데이터 과학팀과의 협업**: Canvas에서 생성한 모델을 데이터 과학팀이 검토하고 개선할 수 있는 워크플로우를 구축합니다.

## 관련 서비스 비교

### SageMaker Canvas vs SageMaker Studio

| 항목 | SageMaker Canvas | SageMaker Studio |
|------|-----------------|------------------|
| 대상 사용자 | 비즈니스 분석가 | 데이터 과학자/ML 엔지니어 |
| 코딩 필요 여부 | 불필요 | 필요 (Python/R) |
| 커스터마이징 | 제한적 | 완전한 자유도 |
| 모델 정확도 | 좋음 (AutoML 기반) | 최상 (수동 최적화 가능) |
| 학습 곡선 | 낮음 | 높음 |
| 배포 옵션 | 배치/실시간 (제한적) | 다양한 배포 옵션 |

### SageMaker Canvas vs Amazon QuickSight ML Insights

| 항목 | SageMaker Canvas | QuickSight ML Insights |
|------|-----------------|------------------------|
| 주요 목적 | ML 모델 구축 | BI 대시보드 + ML 인사이트 |
| 커스텀 모델 | 지원 | 제한적 (내장 ML만) |
| 데이터 탐색 | 기본적 | 풍부한 시각화 |
| 예측 유형 | 분류/회귀/시계열/이미지/텍스트 | 이상 탐지/예측/자연어 서술 |
| 모델 공유 | SageMaker Studio로 공유 | 대시보드 공유 |

### SageMaker Canvas vs Google AutoML Tables / Azure ML Designer

| 항목 | SageMaker Canvas | Google AutoML Tables | Azure ML Designer |
|------|-----------------|---------------------|--------------------|
| 노코드 | 완전 노코드 | 노코드 | 로우코드/드래그앤드롭 |
| AutoML | SageMaker Autopilot | Google AutoML | Azure AutoML |
| 생성형 AI | Bedrock 통합 | Vertex AI 통합 | Azure OpenAI 통합 |
| 데이터 소스 | S3, Redshift, Snowflake | BigQuery, GCS | Azure Blob, SQL |
| 가격 모델 | 시간당 과금 | 노드 시간당 과금 | 컴퓨팅 시간당 과금 |

## 요약

Amazon SageMaker Canvas는 머신러닝의 민주화를 실현하는 강력한 노코드 도구입니다. 비즈니스 분석가가 코드 작성 없이도 다양한 유형의 ML 모델을 구축하고, 예측을 수행하며, 결과를 해석할 수 있습니다.

핵심 특징을 정리하면 다음과 같습니다.

- **완전한 노코드 환경**: 드래그 앤 드롭 인터페이스로 ML 모델 구축
- **다양한 데이터 소스 지원**: S3, Redshift, Athena, Snowflake 등과 직접 연동
- **AutoML 기반 모델 최적화**: SageMaker Autopilot이 최적의 모델을 자동 탐색
- **생성형 AI 통합**: Amazon Bedrock 기반의 파운데이션 모델 활용 가능
- **협업 워크플로우**: Canvas에서 만든 모델을 SageMaker Studio로 공유하여 추가 개선 가능
- **엔터프라이즈급 보안**: VPC 격리, KMS 암호화, IAM 통합 등 강력한 보안 체계

SageMaker Canvas는 특히 데이터 과학 인력이 부족하지만 ML을 활용하고자 하는 조직, ML 프로토타이핑을 빠르게 수행하고자 하는 팀, 비즈니스 분석가가 직접 예측 모델을 생성해야 하는 환경에서 높은 가치를 제공합니다. 다만, 고도로 커스터마이징된 모델이 필요하거나 복잡한 피처 엔지니어링이 요구되는 경우에는 SageMaker Studio와 병행하여 사용하는 것이 바람직합니다.