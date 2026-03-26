## 개요

AWS Step Functions는 분산 애플리케이션의 구성 요소를 시각적 워크플로우로 조율(orchestrate)할 수 있는 서버리스 서비스입니다. Lambda 함수, ECS 태스크, SQS 메시지, DynamoDB 작업 등 다양한 AWS 서비스를 순차적 또는 병렬로 연결하여, 복잡한 비즈니스 프로세스를 자동화할 수 있습니다.

마이크로서비스 아키텍처에서는 여러 서비스가 협력하여 하나의 비즈니스 프로세스를 완수합니다. 예를 들어, 주문 처리 워크플로우는 재고 확인, 결제 처리, 배송 준비, 알림 발송 등 여러 단계로 구성됩니다. 이러한 단계들의 실행 순서, 조건 분기, 병렬 처리, 오류 처리를 코드로 직접 구현하면 복잡도가 급격히 증가합니다.

Step Functions는 이러한 오케스트레이션 로직을 워크플로우(상태 머신)로 선언적으로 정의합니다. Amazon States Language(ASL)라는 JSON 기반 언어로 워크플로우를 정의하며, 각 단계의 실행, 재시도, 오류 처리, 타임아웃 등을 Step Functions 엔진이 관리합니다.

또한 Step Functions는 200개 이상의 AWS 서비스와 직접 통합(SDK Integration)을 지원합니다. 기존에는 Lambda 함수를 중간에 두고 AWS 서비스를 호출해야 했지만, SDK 통합을 사용하면 Lambda 없이도 DynamoDB에 데이터를 쓰거나, SQS에 메시지를 보내거나, ECS 태스크를 실행할 수 있습니다.

## 핵심 기능

### 워크플로우 유형

**Standard Workflow**

장기 실행(최대 1년) 워크플로우에 적합합니다. 정확히 한 번(exactly-once) 실행을 보장하며, 실행 이력이 완전히 기록됩니다. 상태 전환당 과금됩니다.

**Express Workflow**

짧은 시간(최대 5분) 내에 완료되는 고빈도 워크플로우에 적합합니다. 최소 한 번(at-least-once) 또는 최대 한 번(at-most-once) 실행을 보장하며, 실행 시간과 요청 수 기반으로 과금됩니다. IoT 데이터 처리, API 요청 처리 등에 적합합니다.

| 항목 | Standard | Express |
|------|----------|----------|
| 최대 실행 시간 | 1년 | 5분 |
| 실행 보장 | exactly-once | at-least-once / at-most-once |
| 실행 이력 | 완전 기록 | CloudWatch Logs |
| 과금 | 상태 전환 수 | 실행 수 + 시간 + 메모리 |
| 초당 실행 수 | 낮음 (기본 2,000) | 높음 (기본 100,000) |
| 적합한 사용 사례 | ETL, 주문처리, 승인 워크플로우 | IoT, API 처리, 스트리밍 |

### 상태 유형 (State Types)

ASL에서 사용할 수 있는 상태 유형은 다음과 같습니다.

- **Task**: AWS 서비스를 호출하거나 작업을 수행합니다.
- **Choice**: 조건에 따라 분기합니다.
- **Parallel**: 여러 분기를 동시에 실행합니다.
- **Map**: 배열의 각 요소에 대해 반복 실행합니다.
- **Wait**: 지정된 시간만큼 대기합니다.
- **Pass**: 입력을 출력으로 전달하거나 데이터를 변환합니다.
- **Succeed**: 워크플로우를 성공으로 종료합니다.
- **Fail**: 워크플로우를 실패로 종료합니다.

### SDK 통합 (AWS SDK Integration)

Step Functions는 200개 이상의 AWS 서비스에 대해 직접 API 호출을 지원합니다. 세 가지 통합 패턴을 제공합니다.

1. **Request Response**: API를 호출하고 즉시 응답을 받습니다.
2. **Run a Job (.sync)**: 비동기 작업(ECS Task, Glue Job 등)의 완료를 기다립니다.
3. **Wait for Callback (.waitForTaskToken)**: 외부 시스템의 콜백을 기다립니다.

## 아키텍처/동작 원리

### 상태 머신 정의 (ASL)

```json
{
  "Comment": "주문 처리 워크플로우",
  "StartAt": "ValidateOrder",
  "States": {
    "ValidateOrder": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:ap-northeast-2:123456789012:function:validate-order",
      "Next": "CheckInventory",
      "Catch": [{
        "ErrorEquals": ["ValidationError"],
        "Next": "OrderFailed",
        "ResultPath": "$.error"
      }],
      "Retry": [{
        "ErrorEquals": ["States.TaskFailed"],
        "IntervalSeconds": 2,
        "MaxAttempts": 3,
        "BackoffRate": 2.0
      }]
    },
    "CheckInventory": {
      "Type": "Task",
      "Resource": "arn:aws:states:::dynamodb:getItem",
      "Parameters": {
        "TableName": "Inventory",
        "Key": {
          "productId": {"S.$": "$.productId"}
        }
      },
      "ResultPath": "$.inventory",
      "Next": "IsInStock"
    },
    "IsInStock": {
      "Type": "Choice",
      "Choices": [{
        "Variable": "$.inventory.Item.quantity.N",
        "NumericGreaterThan": 0,
        "Next": "ProcessPaymentAndUpdateInventory"
      }],
      "Default": "OutOfStock"
    },
    "ProcessPaymentAndUpdateInventory": {
      "Type": "Parallel",
      "Branches": [
        {
          "StartAt": "ProcessPayment",
          "States": {
            "ProcessPayment": {
              "Type": "Task",
              "Resource": "arn:aws:lambda:ap-northeast-2:123456789012:function:process-payment",
              "End": true
            }
          }
        },
        {
          "StartAt": "UpdateInventory",
          "States": {
            "UpdateInventory": {
              "Type": "Task",
              "Resource": "arn:aws:states:::dynamodb:updateItem",
              "Parameters": {
                "TableName": "Inventory",
                "Key": {
                  "productId": {"S.$": "$.productId"}
                },
                "UpdateExpression": "SET quantity = quantity - :qty",
                "ExpressionAttributeValues": {
                  ":qty": {"N.$": "$.quantity"}
                }
              },
              "End": true
            }
          }
        }
      ],
      "Next": "SendConfirmation"
    },
    "SendConfirmation": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {
        "TopicArn": "arn:aws:sns:ap-northeast-2:123456789012:order-notifications",
        "Message.$": "States.Format('Order {} confirmed', $.orderId)"
      },
      "Next": "OrderCompleted"
    },
    "OutOfStock": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {
        "TopicArn": "arn:aws:sns:ap-northeast-2:123456789012:order-notifications",
        "Message.$": "States.Format('Order {} - Out of stock for product {}', $.orderId, $.productId)"
      },
      "Next": "OrderFailed"
    },
    "OrderCompleted": {
      "Type": "Succeed"
    },
    "OrderFailed": {
      "Type": "Fail",
      "Error": "OrderProcessingFailed",
      "Cause": "Order could not be processed"
    }
  }
}
```

### Step Functions 생성 및 실행

```bash
# 상태 머신 생성
aws stepfunctions create-state-machine \
  --name order-processing-workflow \
  --definition file://order-workflow.json \
  --role-arn arn:aws:iam::123456789012:role/StepFunctionsExecutionRole \
  --type STANDARD \
  --logging-configuration '{
    "level": "ALL",
    "includeExecutionData": true,
    "destinations": [{
      "cloudWatchLogsLogGroup": {
        "logGroupArn": "arn:aws:logs:ap-northeast-2:123456789012:log-group:/aws/vendedlogs/states/order-processing:*"
      }
    }]
  }' \
  --tracing-configuration '{"enabled": true}'
```

```bash
# 상태 머신 실행
aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:ap-northeast-2:123456789012:stateMachine:order-processing-workflow \
  --name "order-2024-001" \
  --input '{"orderId": "ORD-2024-001", "productId": "PROD-100", "quantity": "1", "amount": 29900}'
```

```bash
# 실행 상태 확인
aws stepfunctions describe-execution \
  --execution-arn arn:aws:states:ap-northeast-2:123456789012:execution:order-processing-workflow:order-2024-001

# 실행 이력 조회
aws stepfunctions get-execution-history \
  --execution-arn arn:aws:states:ap-northeast-2:123456789012:execution:order-processing-workflow:order-2024-001 \
  --max-results 20
```

### Map 상태를 활용한 대규모 병렬 처리

Step Functions의 Distributed Map 상태를 사용하면 S3의 대규모 데이터셋을 병렬로 처리할 수 있습니다. 최대 10,000개의 병렬 실행을 지원합니다.

```json
{
  "Comment": "S3 대규모 데이터 처리",
  "StartAt": "ProcessS3Objects",
  "States": {
    "ProcessS3Objects": {
      "Type": "Map",
      "ItemProcessor": {
        "ProcessorConfig": {
          "Mode": "DISTRIBUTED",
          "ExecutionType": "EXPRESS"
        },
        "StartAt": "ProcessItem",
        "States": {
          "ProcessItem": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:ap-northeast-2:123456789012:function:process-item",
            "End": true
          }
        }
      },
      "ItemReader": {
        "Resource": "arn:aws:states:::s3:getObject",
        "ReaderConfig": {
          "InputType": "CSV",
          "CSVHeaderLocation": "FIRST_ROW"
        },
        "Parameters": {
          "Bucket": "my-data-bucket",
          "Key": "input/large-dataset.csv"
        }
      },
      "MaxConcurrency": 1000,
      "End": true
    }
  }
}
```

## 실전 활용

### 사례 1: ETL 파이프라인 오케스트레이션

```bash
# Glue Job을 Step Functions에서 동기적으로 실행 (.sync 패턴)
# 상태 머신 내에서 Glue Job 완료를 기다린 후 다음 단계 진행
aws stepfunctions list-state-machines \
  --query 'stateMachines[?contains(name, `etl`)].{Name:name,Arn:stateMachineArn,Type:type}' \
  --output table
```

### 사례 2: 인간 승인 워크플로우 (Human Approval)

`.waitForTaskToken` 패턴을 사용하면 외부 시스템(이메일 승인, Slack 버튼 클릭 등)의 응답을 기다릴 수 있습니다.

```json
{
  "WaitForApproval": {
    "Type": "Task",
    "Resource": "arn:aws:states:::sqs:sendMessage.waitForTaskToken",
    "Parameters": {
      "QueueUrl": "https://sqs.ap-northeast-2.amazonaws.com/123456789012/approval-queue",
      "MessageBody": {
        "taskToken.$": "$$.Task.Token",
        "requestDetails.$": "$.request"
      }
    },
    "TimeoutSeconds": 86400,
    "Next": "ProcessApproval"
  }
}
```

승인 처리 Lambda에서 콜백을 보내는 코드입니다.

```python
import boto3

def handle_approval(event, context):
    """승인/거부 처리 후 Step Functions에 콜백"""
    sfn_client = boto3.client('stepfunctions')
    
    task_token = event['taskToken']
    approved = event['approved']
    
    if approved:
        sfn_client.send_task_success(
            taskToken=task_token,
            output='{"status": "approved", "approver": "' + event['approver'] + '"}'
        )
    else:
        sfn_client.send_task_failure(
            taskToken=task_token,
            error='ApprovalDenied',
            cause='Request was denied by ' + event['approver']
        )
```

### 사례 3: API Gateway + Express Workflow

API Gateway와 Express Workflow를 결합하면, 복잡한 API 로직을 Step Functions로 오케스트레이션할 수 있습니다.

```bash
# Express 상태 머신 생성
aws stepfunctions create-state-machine \
  --name api-order-express \
  --definition file://api-order-express.json \
  --role-arn arn:aws:iam::123456789012:role/StepFunctionsExpressRole \
  --type EXPRESS

# API Gateway에서 동기식 Express Workflow 호출 테스트
aws stepfunctions start-sync-execution \
  --state-machine-arn arn:aws:states:ap-northeast-2:123456789012:stateMachine:api-order-express \
  --input '{"orderId": "ORD-001", "items": [{"id": "PROD-1", "qty": 2}]}'
```

## 모범 사례/보안

### 오류 처리 전략

1. **Retry 설정**: 일시적 오류에 대해 지수 백오프 재시도를 설정합니다.
2. **Catch 설정**: 재시도 후에도 실패하면 대체 경로로 분기합니다.
3. **TimeoutSeconds**: 각 Task 상태에 타임아웃을 설정하여 무한 대기를 방지합니다.
4. **HeartbeatSeconds**: 장기 실행 태스크에 하트비트를 설정하여 중단된 태스크를 감지합니다.

### IAM 역할 설계

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "lambda:InvokeFunction",
      "Resource": [
        "arn:aws:lambda:ap-northeast-2:123456789012:function:validate-order",
        "arn:aws:lambda:ap-northeast-2:123456789012:function:process-payment"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:UpdateItem"
      ],
      "Resource": "arn:aws:dynamodb:ap-northeast-2:123456789012:table/Inventory"
    },
    {
      "Effect": "Allow",
      "Action": "sns:Publish",
      "Resource": "arn:aws:sns:ap-northeast-2:123456789012:order-notifications"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogDelivery",
        "logs:GetLogDelivery",
        "logs:UpdateLogDelivery",
        "logs:DeleteLogDelivery",
        "logs:ListLogDeliveries",
        "logs:PutResourcePolicy",
        "logs:DescribeResourcePolicies",
        "logs:DescribeLogGroups"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "xray:PutTraceSegments",
        "xray:PutTelemetryRecords"
      ],
      "Resource": "*"
    }
  ]
}
```

### 비용 최적화

```bash
# 실행 이력 조회로 상태 전환 수 파악
aws stepfunctions list-executions \
  --state-machine-arn arn:aws:states:ap-northeast-2:123456789012:stateMachine:order-processing-workflow \
  --status-filter SUCCEEDED \
  --max-results 10 \
  --query 'executions[*].{Name:name,Start:startDate,Stop:stopDate}' \
  --output table
```

1. **Express vs Standard**: 5분 이내에 완료되는 고빈도 워크플로우는 Express를 사용합니다.
2. **SDK 통합 활용**: Lambda를 거치지 않고 AWS 서비스를 직접 호출하여 비용과 지연 시간을 줄입니다.
3. **Pass 상태 활용**: 데이터 변환에 Lambda 대신 Pass 상태의 Parameters를 사용합니다.
4. **상태 수 최소화**: 불필요한 상태를 줄여 상태 전환 비용을 절감합니다.

## 관련 서비스 비교

| 항목 | Step Functions | Amazon MWAA (Airflow) | EventBridge + Lambda | SQS + Lambda |
|------|---------------|----------------------|---------------------|--------------|
| 패턴 | 오케스트레이션 | 오케스트레이션 | 코레오그래피 | 코레오그래피 |
| 워크플로우 정의 | ASL (JSON) | Python DAG | 규칙 + 코드 | 코드 |
| 시각화 | 내장 (실시간) | Airflow UI | 미지원 | 미지원 |
| 최대 실행 시간 | 1년 / 5분 | 무제한 | 15분 (Lambda) | 15분 (Lambda) |
| 인간 승인 | waitForTaskToken | Sensor | 미지원 | 미지원 |
| 서버리스 | 완전 서버리스 | 관리형 (인스턴스) | 완전 서버리스 | 완전 서버리스 |
| 복잡도 관리 | 우수 | 우수 | 복잡도 증가 | 복잡도 증가 |
| 비용 | 상태 전환 기반 | 환경 시간 기반 | 이벤트 + Lambda 기반 | 요청 + Lambda 기반 |

## 요약

AWS Step Functions는 분산 시스템의 워크플로우를 시각적으로 설계하고 안정적으로 실행할 수 있는 서버리스 오케스트레이션 서비스입니다. 핵심 포인트를 정리하면 다음과 같습니다.

- **선언적 워크플로우**: ASL로 워크플로우를 JSON으로 정의하여, 코드에서 오케스트레이션 로직을 분리합니다.
- **두 가지 워크플로우 유형**: Standard(장기, exactly-once)와 Express(단기, 고빈도)를 상황에 맞게 선택합니다.
- **200+ AWS 서비스 직접 통합**: Lambda 없이도 DynamoDB, SQS, SNS, ECS 등을 직접 호출할 수 있습니다.
- **강력한 오류 처리**: 재시도, 캐치, 타임아웃, 하트비트를 통해 안정적인 실행을 보장합니다.
- **대규모 병렬 처리**: Distributed Map으로 최대 10,000개의 병렬 실행을 지원합니다.
- **인간 승인 패턴**: waitForTaskToken으로 외부 시스템의 응답을 기다리는 워크플로우를 구현합니다.
- **시각적 모니터링**: 실행 중인 워크플로우의 진행 상태를 실시간으로 시각화합니다.

Step Functions는 마이크로서비스 오케스트레이션, ETL 파이프라인, 주문 처리, 승인 워크플로우 등 다양한 사용 사례에서 핵심적인 역할을 수행하는 서비스입니다.