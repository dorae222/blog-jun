## 개요

Amazon AppFlow는 SaaS(Software as a Service) 애플리케이션과 AWS 서비스 간에 데이터를 안전하게 전송할 수 있도록 설계된 완전관리형 통합 서비스입니다. 기업 환경에서는 Salesforce, SAP, Slack, ServiceNow, Google Analytics 등 다양한 SaaS 도구를 사용하고 있으며, 이들 사이의 데이터를 AWS 환경으로 가져오거나 반대로 AWS에서 SaaS로 내보내는 작업이 빈번합니다.

기존에는 이러한 데이터 통합을 위해 커스텀 커넥터를 개발하거나, ETL 파이프라인을 직접 구축해야 했습니다. 이 과정에서 API 인증 관리, 데이터 변환 로직, 오류 처리, 스케줄링 등 수많은 부수적인 작업이 필요했습니다. Amazon AppFlow는 이러한 복잡성을 추상화하여, 몇 번의 클릭이나 간단한 API 호출만으로 데이터 플로우를 설정할 수 있게 해줍니다.

AppFlow는 최대 100GB 규모의 데이터를 단일 플로우 실행으로 전송할 수 있으며, 전송 중 데이터 변환, 필터링, 매핑 기능을 기본 제공합니다. 또한 AWS PrivateLink를 통해 인터넷을 거치지 않는 프라이빗 데이터 전송을 지원하므로, 보안이 중요한 엔터프라이즈 환경에서도 안심하고 사용할 수 있습니다.

## 핵심 기능

### 광범위한 커넥터 지원

AppFlow는 50개 이상의 SaaS 커넥터를 기본 제공합니다. 주요 소스 커넥터로는 Salesforce, SAP OData, Google Analytics 4, Slack, Zendesk, ServiceNow, Datadog, Amplitude 등이 있습니다. AWS 측 대상으로는 Amazon S3, Amazon Redshift, Amazon EventBridge, Salesforce(양방향), Snowflake 등을 지원합니다.

커스텀 커넥터 SDK도 제공되어, 지원되지 않는 SaaS 서비스에 대해서도 자체 커넥터를 개발할 수 있습니다.

### 데이터 변환 및 매핑

AppFlow는 전송 중 다음과 같은 데이터 변환 작업을 수행할 수 있습니다.

- **필드 매핑**: 소스 필드를 대상 필드에 매핑
- **필드 검증**: 이메일, 전화번호 등 형식 검증
- **필터링**: 특정 조건에 맞는 레코드만 전송
- **마스킹**: 민감 데이터를 마스킹 처리
- **병합/분할**: 필드를 결합하거나 분리
- **산술 연산**: 수치 필드에 대한 연산 수행

### 트리거 방식

AppFlow 플로우는 세 가지 방식으로 트리거할 수 있습니다.

1. **온디맨드(On-Demand)**: 수동으로 실행하거나 API 호출로 트리거
2. **스케줄(Scheduled)**: 분/시간/일/주/월 단위로 정기 실행
3. **이벤트 기반(Event-driven)**: 소스 SaaS에서 데이터 변경이 발생하면 자동 실행 (Salesforce 등 지원)

### 보안 및 암호화

- AWS PrivateLink를 통한 프라이빗 데이터 전송
- AWS KMS 기반 저장 데이터 암호화
- 전송 중 TLS 암호화
- IAM 기반 접근 제어
- VPC 엔드포인트 지원

## 아키텍처/동작 원리

AppFlow의 동작 원리는 크게 세 단계로 구분할 수 있습니다.

### 1단계: 연결 설정 (Connection Profile)

소스 및 대상 서비스에 대한 인증 정보를 등록합니다. OAuth 2.0, API Key, Basic Auth 등 각 서비스에 맞는 인증 방식을 사용합니다. 연결 정보는 AWS Secrets Manager에 안전하게 저장됩니다.

```bash
# AppFlow 커넥터 프로필 생성 (Salesforce 예시)
aws appflow create-connector-profile \
  --connector-profile-name my-salesforce-profile \
  --connector-type Salesforce \
  --connection-mode Public \
  --connector-profile-config '{
    "connectorProfileProperties": {
      "Salesforce": {
        "instanceUrl": "https://mycompany.salesforce.com",
        "isSandboxEnvironment": false
      }
    },
    "connectorProfileCredentials": {
      "Salesforce": {
        "accessToken": "YOUR_ACCESS_TOKEN",
        "refreshToken": "YOUR_REFRESH_TOKEN",
        "clientCredentialsArn": "arn:aws:secretsmanager:us-east-1:123456789012:secret:sf-creds"
      }
    }
  }'
```

### 2단계: 플로우 정의 (Flow Configuration)

소스, 대상, 트리거, 변환 규칙을 정의합니다. 각 플로우는 하나의 소스에서 하나 이상의 대상으로 데이터를 전송합니다.

```bash
# AppFlow 플로우 생성 (Salesforce -> S3)
aws appflow create-flow \
  --flow-name salesforce-to-s3-accounts \
  --trigger-config '{
    "triggerType": "Scheduled",
    "triggerProperties": {
      "Scheduled": {
        "scheduleExpression": "rate(1day)",
        "dataPullMode": "Incremental",
        "scheduleStartTime": "2024-01-01T00:00:00Z"
      }
    }
  }' \
  --source-flow-config '{
    "connectorType": "Salesforce",
    "connectorProfileName": "my-salesforce-profile",
    "sourceConnectorProperties": {
      "Salesforce": {
        "object": "Account",
        "enableDynamicFieldUpdate": true
      }
    }
  }' \
  --destination-flow-config-list '[{
    "connectorType": "S3",
    "destinationConnectorProperties": {
      "S3": {
        "bucketName": "my-data-lake-bucket",
        "bucketPrefix": "salesforce/accounts",
        "s3OutputFormatConfig": {
          "fileType": "PARQUET",
          "aggregationConfig": {
            "aggregationType": "None"
          }
        }
      }
    }
  }]' \
  --tasks '[{
    "sourceFields": ["Id", "Name", "Industry", "AnnualRevenue"],
    "connectorOperator": {"Salesforce": "PROJECTION"},
    "taskType": "Filter"
  }, {
    "sourceFields": ["Id"],
    "destinationField": "account_id",
    "taskType": "Map",
    "connectorOperator": {"Salesforce": "NO_OP"},
    "taskProperties": {"DESTINATION_DATA_TYPE": "string", "SOURCE_DATA_TYPE": "id"}
  }]'
```

### 3단계: 실행 및 모니터링

플로우가 실행되면 AppFlow는 소스에서 데이터를 추출하고, 정의된 변환 규칙을 적용한 후, 대상에 적재합니다. 각 실행의 상태, 전송된 레코드 수, 오류 정보 등을 CloudWatch와 AppFlow 콘솔에서 확인할 수 있습니다.

```bash
# 플로우 실행 상태 확인
aws appflow describe-flow-execution-records \
  --flow-name salesforce-to-s3-accounts \
  --max-results 5
```

```bash
# 플로우 수동 실행
aws appflow start-flow \
  --flow-name salesforce-to-s3-accounts
```

내부적으로 AppFlow는 다음과 같은 아키텍처로 동작합니다.

1. **커넥터 레이어**: 각 SaaS 서비스의 API와 통신하는 어댑터 계층
2. **변환 엔진**: 필드 매핑, 필터링, 변환 로직을 처리하는 엔진
3. **전송 엔진**: 대용량 데이터를 효율적으로 병렬 전송하는 엔진
4. **메타데이터 저장소**: 플로우 정의, 커넥터 프로필, 스키마 정보를 관리
5. **모니터링 시스템**: 실행 이력, 메트릭, 로그를 수집/관리

## 실전 활용

### 사례 1: Salesforce 데이터를 데이터 레이크로 통합

가장 흔한 사용 사례는 Salesforce의 고객, 거래, 기회 데이터를 S3 기반 데이터 레이크로 가져오는 것입니다. 이를 통해 Athena, Redshift Spectrum, QuickSight 등으로 분석할 수 있습니다.

```bash
# 플로우 목록 조회
aws appflow list-flows

# 특정 플로우의 상세 정보 확인
aws appflow describe-flow \
  --flow-name salesforce-to-s3-accounts
```

### 사례 2: Google Analytics 데이터를 Redshift로 적재

마케팅 분석을 위해 Google Analytics 4의 세션, 이벤트, 전환 데이터를 Amazon Redshift로 직접 적재할 수 있습니다. 이를 통해 웹 분석 데이터와 내부 비즈니스 데이터를 결합한 통합 분석이 가능합니다.

### 사례 3: 이벤트 기반 실시간 데이터 동기화

Salesforce에서 고객 레코드가 변경될 때마다 EventBridge로 이벤트를 전송하고, 이를 기반으로 후속 처리 파이프라인을 트리거하는 구성이 가능합니다.

```bash
# EventBridge 대상으로 이벤트 기반 플로우 생성
aws appflow create-flow \
  --flow-name sf-event-to-eventbridge \
  --trigger-config '{"triggerType": "Event"}' \
  --source-flow-config '{
    "connectorType": "Salesforce",
    "connectorProfileName": "my-salesforce-profile",
    "sourceConnectorProperties": {
      "Salesforce": {
        "object": "Account",
        "enableDynamicFieldUpdate": true
      }
    }
  }' \
  --destination-flow-config-list '[{
    "connectorType": "EventBridge",
    "destinationConnectorProperties": {
      "EventBridge": {
        "object": "SalesforceAccountChange"
      }
    }
  }]' \
  --tasks '[{
    "sourceFields": ["Id", "Name", "Industry"],
    "connectorOperator": {"Salesforce": "PROJECTION"},
    "taskType": "Filter"
  }]'
```

### 사례 4: 커스텀 커넥터를 활용한 내부 API 통합

AppFlow Custom Connector SDK를 사용하면 자체 REST API나 지원되지 않는 SaaS에 대한 커넥터를 Lambda 함수로 구현할 수 있습니다.

```python
# Lambda 기반 커스텀 커넥터 핸들러 예시
import json

def lambda_handler(event, context):
    request_type = event.get('type')
    
    if request_type == 'DescribeConnectorEntity':
        return {
            'connectorEntityFields': [
                {
                    'identifier': 'id',
                    'label': 'Record ID',
                    'supportedFieldTypeDetails': {
                        'v1': {
                            'fieldType': 'String',
                            'filterOperators': ['EQUAL_TO']
                        }
                    }
                },
                {
                    'identifier': 'name',
                    'label': 'Name',
                    'supportedFieldTypeDetails': {
                        'v1': {
                            'fieldType': 'String',
                            'filterOperators': ['EQUAL_TO', 'CONTAINS']
                        }
                    }
                }
            ]
        }
    elif request_type == 'RetrieveData':
        # 외부 API에서 데이터를 가져오는 로직
        records = fetch_data_from_api(event['entityName'])
        return {
            'records': records,
            'isSuccess': True
        }
```

## 모범 사례/보안

### 보안 모범 사례

1. **PrivateLink 사용**: 가능한 경우 항상 Private 연결 모드를 사용하여 데이터가 공용 인터넷을 통하지 않도록 합니다.
2. **KMS 암호화**: 고객 관리형 KMS 키를 사용하여 저장 데이터를 암호화합니다.
3. **최소 권한 원칙**: AppFlow 실행 역할에 필요한 최소한의 IAM 권한만 부여합니다.
4. **VPC 엔드포인트**: S3, Redshift 등 대상 서비스에 VPC 엔드포인트를 설정하여 트래픽이 AWS 네트워크 내에서만 흐르도록 합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "appflow:CreateFlow",
        "appflow:DescribeFlow",
        "appflow:StartFlow"
      ],
      "Resource": "arn:aws:appflow:us-east-1:123456789012:flow/salesforce-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetBucketAcl"
      ],
      "Resource": [
        "arn:aws:s3:::my-data-lake-bucket",
        "arn:aws:s3:::my-data-lake-bucket/salesforce/*"
      ]
    }
  ]
}
```

### 운영 모범 사례

1. **증분 전송 활용**: 전체 데이터 덤프 대신 증분(Incremental) 모드를 사용하여 변경된 데이터만 전송합니다. 이를 통해 비용과 처리 시간을 절감할 수 있습니다.
2. **오류 처리 구성**: 플로우 실행 실패 시 SNS 알림을 설정하고, CloudWatch Alarms를 통해 모니터링합니다.
3. **데이터 파티셔닝**: S3 대상의 경우 날짜/시간 기반 파티셔닝을 활용하여 이후 쿼리 성능을 최적화합니다.
4. **스키마 변경 대응**: 소스 SaaS의 스키마가 변경될 수 있으므로, `enableDynamicFieldUpdate`를 활성화하고 정기적으로 스키마를 검증합니다.

```bash
# CloudWatch 알람 설정 (플로우 실패 감지)
aws cloudwatch put-metric-alarm \
  --alarm-name appflow-salesforce-failure \
  --metric-name FlowExecutionsFailed \
  --namespace AWS/AppFlow \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:ops-alerts \
  --dimensions Name=FlowName,Value=salesforce-to-s3-accounts
```

## 관련 서비스 비교

| 항목 | Amazon AppFlow | AWS Glue | AWS Data Pipeline | Amazon EventBridge |
|------|---------------|----------|-------------------|--------------------|
| 주요 용도 | SaaS-AWS 데이터 통합 | ETL/데이터 변환 | 데이터 이동 워크플로우 | 이벤트 라우팅 |
| 코드 필요 여부 | 노코드/로우코드 | 코드 필요 (Python/Scala) | 정의 기반 | 규칙 기반 |
| SaaS 커넥터 | 50개 이상 기본 제공 | 제한적 | 없음 | SaaS 이벤트 수신 |
| 데이터 변환 | 기본 변환 | 고급 변환 | 제한적 | 변환 없음 |
| 실시간 지원 | 이벤트 기반 (일부 소스) | 배치/스트리밍 | 배치 | 실시간 |
| 최대 데이터 크기 | 100GB/실행 | 제한 없음 | 제한 없음 | 256KB/이벤트 |
| 비용 모델 | 플로우 실행 + 레코드 수 | 크롤러/잡 시간 | 활동 + 인스턴스 | 이벤트 수 |

**AppFlow를 선택해야 하는 경우**: SaaS 데이터를 AWS로 가져오는 것이 주 목적이고, 복잡한 변환 로직이 필요 없으며, 빠르게 구성하고 싶을 때 적합합니다.

**Glue를 선택해야 하는 경우**: AWS 내부 데이터 소스 간의 복잡한 ETL 처리가 필요하거나, 대규모 데이터 변환이 요구될 때 적합합니다.

두 서비스를 조합하여 사용하는 것이 일반적입니다. AppFlow로 SaaS 데이터를 S3에 적재한 후, Glue로 정제/변환하여 데이터 웨어하우스에 적재하는 파이프라인 구성이 대표적입니다.

## 요약

Amazon AppFlow는 SaaS 애플리케이션과 AWS 서비스 간의 데이터 통합을 간소화하는 완전관리형 서비스입니다. 50개 이상의 기본 제공 커넥터와 커스텀 커넥터 SDK를 통해 다양한 SaaS 소스의 데이터를 코드 없이 AWS 환경으로 가져올 수 있습니다. PrivateLink 기반의 프라이빗 전송, KMS 암호화, IAM 접근 제어 등 엔터프라이즈급 보안 기능을 기본 제공하며, 온디맨드, 스케줄, 이벤트 기반 트리거를 통해 다양한 데이터 통합 시나리오에 대응할 수 있습니다.

핵심 포인트를 정리하면 다음과 같습니다.

- **완전관리형**: 인프라 관리 없이 데이터 통합에 집중할 수 있습니다.
- **보안 우선**: PrivateLink, KMS, IAM을 통한 다층 보안을 제공합니다.
- **유연한 트리거**: 온디맨드, 스케줄, 이벤트 기반 실행을 지원합니다.
- **데이터 변환**: 전송 중 필터링, 매핑, 마스킹 등 기본 변환이 가능합니다.
- **비용 효율**: 사용한 만큼만 과금되는 서버리스 모델입니다.
- **확장 가능**: 커스텀 커넥터 SDK로 지원 범위를 확장할 수 있습니다.