<!-- infographic-hero -->
![AWS CloudFormation 핵심 요약](figures/infographic.svg)

*Figure: AWS CloudFormation 한 장 요약 인포그래픽*

# AWS CloudFormation - Infrastructure as Code 서비스 개요

## 개요

AWS CloudFormation은 AWS 리소스를 코드로 정의하고 일관되게 프로비저닝하는 Infrastructure as Code(IaC) 서비스입니다. 2011년에 출시되었으며, AWS의 네이티브 IaC 솔루션으로서 모든 AWS 서비스와 가장 빠르게 통합됩니다.

수동으로 콘솔에서 리소스를 만들면 환경 간 차이가 발생하고 재현이 어렵습니다. CloudFormation은 JSON 또는 YAML 템플릿으로 인프라를 선언적으로 정의하고, 이를 Stack 단위로 배포/업데이트/삭제합니다. 코드로 인프라를 관리하면 다음과 같은 이점이 있습니다.

- **반복 가능한 배포**: 동일한 템플릿으로 Dev/Staging/Prod 환경을 일관되게 구성합니다.
- **변경 이력 관리**: Git으로 인프라 변경 이력을 추적하고 코드 리뷰를 적용할 수 있습니다.
- **자동 롤백**: Stack 업데이트 실패 시 이전 상태로 자동 복원됩니다.
- **드리프트 감지**: 콘솔로 변경된 부분을 자동으로 식별합니다.
- **비용**: CloudFormation 자체는 무료이며, 생성된 AWS 리소스 비용만 부과됩니다.

---

## 핵심 기능

### 1. Template 구조

Template는 JSON 또는 YAML로 작성되며 다음 섹션으로 구성됩니다.

| 섹션 | 필수 | 용도 |
|------|------|------|
| AWSTemplateFormatVersion | 선택 | 템플릿 버전 (현재 `2010-09-09`만 사용) |
| Description | 선택 | 템플릿 설명 |
| Metadata | 선택 | 추가 메타데이터 (콘솔 UI 그룹화 등) |
| Parameters | 선택 | 배포 시 입력값 |
| Mappings | 선택 | 정적 매핑 (예: 리전별 AMI ID) |
| Conditions | 선택 | 조건부 리소스 생성 |
| Transform | 선택 | 매크로/Serverless 변환 |
| Resources | 필수 | 실제 AWS 리소스 정의 |
| Outputs | 선택 | 다른 Stack에서 참조 가능한 출력값 |

```yaml
AWSTemplateFormatVersion: "2010-09-09"
Description: "VPC + EC2 sample stack"

Parameters:
  EnvironmentName:
    Type: String
    Default: dev
    AllowedValues: [dev, staging, prod]
  InstanceType:
    Type: String
    Default: t3.micro

Mappings:
  RegionMap:
    ap-northeast-2:
      AMI: ami-0c9c942bd7bf113a2
    us-east-1:
      AMI: ami-0c55b159cbfafe1f0

Conditions:
  IsProduction: !Equals [!Ref EnvironmentName, prod]

Resources:
  MyVPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsHostnames: true
      Tags:
        - Key: Name
          Value: !Sub "${EnvironmentName}-vpc"

  MyEC2:
    Type: AWS::EC2::Instance
    Properties:
      InstanceType: !Ref InstanceType
      ImageId: !FindInMap [RegionMap, !Ref "AWS::Region", AMI]

  ProductionBackup:
    Type: AWS::Backup::BackupPlan
    Condition: IsProduction
    Properties:
      BackupPlan:
        BackupPlanName: production-backup
        BackupPlanRule:
          - RuleName: DailyBackup
            TargetBackupVault: Default
            ScheduleExpression: cron(0 5 ? * * *)

Outputs:
  VPCId:
    Description: "VPC ID"
    Value: !Ref MyVPC
    Export:
      Name: !Sub "${EnvironmentName}-vpc-id"
```

### 2. Stack

Stack은 Template를 인스턴스화한 것으로, AWS 리소스의 모음입니다.

```bash
# Stack 생성
aws cloudformation create-stack \
  --stack-name my-vpc-stack \
  --template-body file://vpc-template.yaml \
  --parameters ParameterKey=EnvironmentName,ParameterValue=prod \
  --capabilities CAPABILITY_IAM \
  --region ap-northeast-2

# Stack 상태 조회
aws cloudformation describe-stacks \
  --stack-name my-vpc-stack \
  --region ap-northeast-2

# Stack 이벤트 (배포 진행 상황)
aws cloudformation describe-stack-events \
  --stack-name my-vpc-stack \
  --region ap-northeast-2

# Stack 삭제
aws cloudformation delete-stack \
  --stack-name my-vpc-stack \
  --region ap-northeast-2
```

**Stack 상태**

| 상태 | 의미 |
|------|------|
| CREATE_IN_PROGRESS / CREATE_COMPLETE | 생성 진행/완료 |
| UPDATE_IN_PROGRESS / UPDATE_COMPLETE | 업데이트 진행/완료 |
| ROLLBACK_IN_PROGRESS / ROLLBACK_COMPLETE | 롤백 진행/완료 |
| DELETE_IN_PROGRESS / DELETE_COMPLETE | 삭제 진행/완료 |
| UPDATE_ROLLBACK_FAILED | 업데이트 후 롤백도 실패 |

### 3. Change Set

Change Set은 Stack 업데이트 전에 어떤 변경이 발생할지 미리 보여주는 dry-run 기능입니다. 프로덕션 환경에서는 반드시 Change Set으로 검토 후 적용해야 합니다.

```bash
# Change Set 생성
aws cloudformation create-change-set \
  --stack-name my-vpc-stack \
  --change-set-name my-changes \
  --template-body file://vpc-template-v2.yaml \
  --parameters ParameterKey=EnvironmentName,ParameterValue=prod \
  --capabilities CAPABILITY_IAM \
  --region ap-northeast-2

# Change Set 검토
aws cloudformation describe-change-set \
  --change-set-name my-changes \
  --stack-name my-vpc-stack \
  --region ap-northeast-2

# 적용
aws cloudformation execute-change-set \
  --change-set-name my-changes \
  --stack-name my-vpc-stack \
  --region ap-northeast-2
```

**중요한 변경 분류**

- **Replacement: True**: 리소스가 삭제되고 재생성됩니다 (가령 RDS 인스턴스 식별자 변경). 데이터 손실 위험이 있습니다.
- **Replacement: False**: 같은 리소스를 in-place로 수정합니다.
- **Replacement: Conditional**: 다른 속성에 따라 결정됩니다.

### 4. StackSet

StackSet은 단일 Template를 다수의 AWS 계정과 리전에 동시에 배포하는 기능입니다. AWS Organizations와 통합하면 OU(Organizational Unit) 단위로 거버넌스 정책을 일관되게 적용할 수 있습니다.

```bash
# StackSet 생성
aws cloudformation create-stack-set \
  --stack-set-name security-baseline \
  --template-body file://security-baseline.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --auto-deployment Enabled=true,RetainStacksOnAccountRemoval=false \
  --permission-model SERVICE_MANAGED \
  --region us-east-1

# 모든 OU에 배포
aws cloudformation create-stack-instances \
  --stack-set-name security-baseline \
  --deployment-targets OrganizationalUnitIds=ou-abcd-12345678 \
  --regions ap-northeast-2 us-east-1 eu-west-1 \
  --operation-preferences MaxConcurrentPercentage=100,FailureTolerancePercentage=10 \
  --region us-east-1
```

### 5. Drift Detection

Drift Detection은 Stack 외부에서 (콘솔, 다른 도구) 리소스가 수정되었는지 감지합니다.

```bash
# Drift Detection 시작
aws cloudformation detect-stack-drift \
  --stack-name my-vpc-stack \
  --region ap-northeast-2

# 결과 확인
aws cloudformation describe-stack-resource-drifts \
  --stack-name my-vpc-stack \
  --region ap-northeast-2
```

Drift가 감지되면 Template를 실제 상태에 맞게 업데이트하거나, 콘솔 변경을 되돌려야 합니다. EventBridge와 결합하면 정기 Drift 검사 및 [[amazon-sns-simple-notification-service-개요|SNS]] 알림 자동화가 가능합니다.

### 6. Nested Stack vs Cross-Stack Reference

복잡한 인프라를 분리하는 두 가지 패턴이 있습니다.

**Nested Stack** - 부모 스택이 자식 스택을 직접 포함

```yaml
Resources:
  NetworkStack:
    Type: AWS::CloudFormation::Stack
    Properties:
      TemplateURL: https://s3.amazonaws.com/my-bucket/network.yaml
      Parameters:
        VpcCidr: 10.0.0.0/16

  AppStack:
    Type: AWS::CloudFormation::Stack
    Properties:
      TemplateURL: https://s3.amazonaws.com/my-bucket/app.yaml
      Parameters:
        VpcId: !GetAtt NetworkStack.Outputs.VpcId
```

**Cross-Stack Reference** - Outputs Export를 다른 Stack이 ImportValue로 참조

```yaml
# Stack A (export)
Outputs:
  VPCId:
    Value: !Ref MyVPC
    Export:
      Name: prod-vpc-id

# Stack B (import)
Resources:
  MySubnet:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !ImportValue prod-vpc-id
```

**선택 기준**

| 항목 | Nested Stack | Cross-Stack Reference |
|------|--------------|------------------------|
| 라이프사이클 | 부모와 함께 배포/삭제 | 독립적 |
| 결합도 | 강함 | 약함 |
| 재사용성 | 낮음 (부모 컨텍스트) | 높음 (조직 전체 공유) |
| 추천 사례 | 단일 애플리케이션 모듈화 | 네트워크 등 공통 인프라 |

### 7. Custom Resource

CloudFormation이 직접 지원하지 않는 자원이나 외부 시스템 연동이 필요할 때 Lambda를 백엔드로 두는 Custom Resource를 사용합니다.

```yaml
Resources:
  MyCustomResource:
    Type: Custom::DnsRegistration
    Properties:
      ServiceToken: !GetAtt DnsRegistrationLambda.Arn
      DomainName: example.com
      RecordType: A

  DnsRegistrationLambda:
    Type: AWS::Lambda::Function
    Properties:
      Runtime: python3.11
      Handler: index.handler
      Role: !GetAtt LambdaExecutionRole.Arn
      Code:
        ZipFile: |
          import json
          import urllib3
          def handler(event, context):
              # CloudFormation에 응답 전송
              response = {
                  "Status": "SUCCESS",
                  "PhysicalResourceId": "my-dns-record",
                  "Data": {"RecordName": event["ResourceProperties"]["DomainName"]}
              }
              urllib3.PoolManager().request("PUT", event["ResponseURL"], body=json.dumps(response))
```

### 8. EC2 부트스트래핑 - cfn-init

`AWS::CloudFormation::Init` 메타데이터와 cfn-init 헬퍼 스크립트로 EC2 인스턴스 부트스트래핑을 선언적으로 정의할 수 있습니다.

```yaml
Resources:
  WebServer:
    Type: AWS::EC2::Instance
    Metadata:
      AWS::CloudFormation::Init:
        config:
          packages:
            yum:
              nginx: []
          files:
            /etc/nginx/nginx.conf:
              content: !Sub |
                server { listen 80; root /var/www; }
              mode: "000644"
          services:
            sysvinit:
              nginx:
                enabled: true
                ensureRunning: true
    Properties:
      ImageId: ami-0c9c942bd7bf113a2
      InstanceType: t3.micro
      UserData:
        Fn::Base64: !Sub |
          #!/bin/bash
          /opt/aws/bin/cfn-init -v --stack ${AWS::StackName} --resource WebServer --region ${AWS::Region}
          /opt/aws/bin/cfn-signal -e $? --stack ${AWS::StackName} --resource WebServer --region ${AWS::Region}

    CreationPolicy:
      ResourceSignal:
        Timeout: PT15M
```

### 9. DeletionPolicy와 UpdateReplacePolicy

리소스 보호 메커니즘입니다.

| Policy 값 | 의미 |
|-----------|------|
| Delete (기본) | Stack 삭제 시 리소스도 삭제 |
| Retain | Stack 삭제 시 리소스는 유지 |
| Snapshot | RDS, EBS 등에서 삭제 전 스냅샷 생성 |

```yaml
Resources:
  ProductionDB:
    Type: AWS::RDS::DBInstance
    DeletionPolicy: Snapshot
    UpdateReplacePolicy: Snapshot
    Properties:
      Engine: postgres
      DBInstanceClass: db.r6g.large
```

### 10. 내장 함수 (Intrinsic Functions)

| 함수 | 용도 | 예시 |
|------|------|------|
| !Ref | Parameter / 리소스 참조 | `!Ref MyVPC` |
| !GetAtt | 리소스 속성 참조 | `!GetAtt MyEC2.PrivateIp` |
| !Sub | 변수 치환 | `!Sub "${EnvironmentName}-vpc"` |
| !Join | 문자열 결합 | `!Join ["-", [!Ref Env, "vpc"]]` |
| !If | 조건 분기 | `!If [IsProduction, "m5.large", "t3.micro"]` |
| !FindInMap | Mappings 조회 | `!FindInMap [RegionMap, !Ref "AWS::Region", AMI]` |
| !ImportValue | Cross-Stack export 참조 | `!ImportValue prod-vpc-id` |
| !GetAZs | AZ 목록 조회 | `!GetAZs ap-northeast-2` |

---

## 아키텍처 / 동작 원리

### 배포 흐름

```text
[Template (YAML/JSON)]
        |
        v  CreateStack / UpdateStack API
[CloudFormation Service]
        |
        +--> Template 검증
        |
        +--> Change Set 생성 (Update 시)
        |
        +--> 의존 그래프 분석 (DependsOn / 암묵적 의존성)
        |
        +--> 리소스를 순서대로 생성/수정
        |       |
        |       v  실패 시
        |     [Rollback 또는 ROLLBACK_FAILED]
        |
        v
[Stack 완성]
```

CloudFormation은 리소스 간 의존성을 자동으로 추론합니다. `!Ref`, `!GetAtt`로 참조된 리소스는 먼저 생성되며, 명시적인 순서가 필요할 때는 `DependsOn` 속성을 사용합니다.

```yaml
Resources:
  MyEC2:
    Type: AWS::EC2::Instance
    DependsOn: MyVPCEndpoint  # 명시적 의존성
    Properties:
      ...
```

### 롤백과 복구

업데이트 실패 시 두 가지 모드가 있습니다.

- **Roll Back on Failure (기본)**: 실패 시 자동으로 이전 상태로 복원
- **Disable Rollback**: 실패 상태 유지 (디버깅 시 유용)

업데이트 후 롤백마저 실패한 경우 (UPDATE_ROLLBACK_FAILED) `continue-update-rollback` API로 문제 리소스를 skip하면서 복구를 진행할 수 있습니다.

### 리소스 가져오기 (Import)

기존에 콘솔로 만든 리소스를 CloudFormation 관리 하에 두는 import 기능이 있습니다.

```bash
aws cloudformation create-change-set \
  --stack-name imported-stack \
  --change-set-name import-resources \
  --change-set-type IMPORT \
  --resources-to-import file://import.json \
  --template-body file://template.yaml
```

---

## 실전 사용

### 1. 다중 환경 관리

환경별 Parameter 파일을 사용하여 동일 Template를 여러 환경에 배포합니다.

```bash
# parameters/dev.json
[
  {"ParameterKey": "EnvironmentName", "ParameterValue": "dev"},
  {"ParameterKey": "InstanceType", "ParameterValue": "t3.micro"}
]

# parameters/prod.json
[
  {"ParameterKey": "EnvironmentName", "ParameterValue": "prod"},
  {"ParameterKey": "InstanceType", "ParameterValue": "m5.large"}
]

# 배포 스크립트
ENV=$1
aws cloudformation deploy \
  --stack-name my-app-${ENV} \
  --template-file template.yaml \
  --parameter-overrides file://parameters/${ENV}.json \
  --capabilities CAPABILITY_IAM \
  --region ap-northeast-2
```

### 2. CI/CD 파이프라인 통합

GitHub Actions로 Template 변경을 자동 검증하고 배포합니다.

```yaml
name: CloudFormation Deploy

on:
  pull_request:
    paths: ['infra/**']
  push:
    branches: [main]
    paths: ['infra/**']

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Validate Template
        run: |
          aws cloudformation validate-template \
            --template-body file://infra/template.yaml
      - name: Lint with cfn-lint
        run: |
          pip install cfn-lint
          cfn-lint infra/template.yaml

  deploy-prod:
    if: github.ref == 'refs/heads/main'
    needs: validate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Create Change Set
        run: |
          aws cloudformation create-change-set \
            --stack-name my-app-prod \
            --change-set-name auto-${{ github.sha }} \
            --template-body file://infra/template.yaml \
            --capabilities CAPABILITY_IAM
      - name: Apply Change Set
        run: |
          aws cloudformation execute-change-set \
            --stack-name my-app-prod \
            --change-set-name auto-${{ github.sha }}
```

### 3. SAM (Serverless Application Model)

SAM은 CloudFormation의 Serverless 워크로드 전용 확장입니다. `Transform: AWS::Serverless-2016-10-31`을 추가하면 Lambda, API Gateway, DynamoDB를 간결한 문법으로 정의할 수 있습니다.

```yaml
AWSTemplateFormatVersion: "2010-09-09"
Transform: AWS::Serverless-2016-10-31

Resources:
  MyFunction:
    Type: AWS::Serverless::Function
    Properties:
      Runtime: python3.11
      Handler: app.handler
      CodeUri: ./src/
      Events:
        Api:
          Type: Api
          Properties:
            Path: /hello
            Method: get
```

`sam deploy`는 내부적으로 CloudFormation을 호출합니다.

### 4. CloudWatch Alarm을 IaC로 관리

[[amazon-cloudwatch-모니터링-서비스-개요|CloudWatch]] Alarm과 [[amazon-sns-simple-notification-service-개요|SNS]] Topic을 함께 정의합니다.

```yaml
Resources:
  AlertsTopic:
    Type: AWS::SNS::Topic
    Properties:
      TopicName: ops-alerts
      Subscription:
        - Endpoint: ops@example.com
          Protocol: email

  HighCPUAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: ec2-high-cpu
      MetricName: CPUUtilization
      Namespace: AWS/EC2
      Statistic: Average
      Period: 60
      EvaluationPeriods: 5
      Threshold: 80
      ComparisonOperator: GreaterThanThreshold
      AlarmActions:
        - !Ref AlertsTopic
      Dimensions:
        - Name: InstanceId
          Value: !Ref MyEC2
```

---

## 가격 / 한도

### 가격

CloudFormation 자체는 다음 리소스에 한해 무료입니다.

- AWS::* (모든 AWS 네이티브 리소스)
- Custom::* (Lambda 백엔드)

다음 자원은 추가 과금됩니다.

- **Third-party 리소스 (Public Extensions)**: 핸들러 작업당 $0.0009 + 등록된 시간당 비용
- **Hooks (Pre/Post)**: 핸들러 작업당 $0.0009

생성된 AWS 리소스 (EC2, RDS, S3 등)는 정상 가격이 부과됩니다.

### 주요 한도

| 항목 | 한도 |
|------|------|
| Template 크기 | 1 MB (S3 업로드 시) / 51,200 bytes (직접 전달 시) |
| Stack당 리소스 수 | 500 |
| Stack당 Parameter 수 | 200 |
| Stack당 Output 수 | 200 |
| Stack당 Mapping 수 | 200 |
| Cross-Stack Export 수 | 1,000 / 리전당 |
| Stack 동시 실행 | 2,500 / 리전당 |
| StackSet의 Stack Instance 수 | 5,000 |

---

## Best Practice

### 1. 모듈화

- **단일 책임 분리**: 네트워크, IAM, 애플리케이션을 별도 Stack으로 분리합니다.
- **Cross-Stack Reference**: 공통 인프라(VPC 등)는 Output Export로 공유합니다.
- **Nested Stack**: 강하게 결합된 컴포넌트는 Nested Stack으로 묶어 부모와 함께 라이프사이클 관리합니다.

### 2. 보안

- **CAPABILITY_IAM / CAPABILITY_NAMED_IAM**: IAM 리소스를 만들 때 명시적 confirm이 필요합니다.
- **DeletionPolicy: Retain / Snapshot**: 데이터 자원은 절대 자동 삭제되지 않도록 설정합니다.
- **Stack Policy**: 특정 리소스의 변경을 차단하는 Stack Policy를 적용합니다.
- **Service Role**: CloudFormation이 사용할 IAM Role을 별도로 정의하여 최소 권한을 적용합니다.

```bash
# Stack Policy 예시 - 데이터베이스 변경 차단
aws cloudformation set-stack-policy \
  --stack-name my-app \
  --stack-policy-body '{
    "Statement": [
      {"Effect": "Allow", "Action": "Update:*", "Principal": "*", "Resource": "*"},
      {"Effect": "Deny", "Action": "Update:Replace", "Principal": "*", "Resource": "LogicalResourceId/ProductionDB"}
    ]
  }'
```

### 3. 검증과 린팅

- **`aws cloudformation validate-template`**: 기본 문법 검증
- **`cfn-lint`**: 더 엄격한 정책 검증 (필수 속성, AWS 베스트 프랙티스)
- **`cfn_nag`**: 보안 취약점 감지
- **TaskCat**: 테스트 자동화 (실제 배포 후 검증)

```bash
# cfn-lint
pip install cfn-lint
cfn-lint template.yaml

# cfn_nag (Ruby gem)
gem install cfn-nag
cfn_nag_scan --input-path template.yaml
```

### 4. Drift 정기 검사

EventBridge Scheduler로 매일 새벽 모든 Stack의 Drift를 검사하고 결과를 SNS로 알림합니다.

### 5. Change Set 필수 사용

프로덕션에서는 `update-stack` 직접 호출을 금지하고 반드시 `create-change-set` → 검토 → `execute-change-set` 흐름을 따릅니다. CI/CD 파이프라인에 강제하는 것이 안전합니다.

---

## 관련 서비스 비교

### CloudFormation vs Terraform

| 항목 | CloudFormation | Terraform |
|------|----------------|-----------|
| 멀티 클라우드 | X (AWS 전용) | O (AWS, GCP, Azure, K8s 등) |
| 언어 | YAML/JSON | HCL (HashiCorp Configuration Language) |
| State 관리 | AWS가 자동 관리 | 사용자가 S3/DynamoDB로 관리 |
| 신규 AWS 서비스 지원 | 가장 빠름 (AWS 네이티브) | AWS Provider 업데이트 후 (보통 며칠 ~ 몇 주) |
| 모듈 시스템 | Nested Stack | Module (강력) |
| 변경 미리보기 | Change Set | terraform plan |
| 커뮤니티 | AWS 공식 | 매우 활발 (Registry 수만 개 모듈) |
| Drift Detection | 내장 | terraform plan으로 감지 |
| 비용 | 무료 (AWS 리소스만 과금) | OSS 무료, Terraform Cloud 유료 |
| 학습 곡선 | 중 | 중-고 |

**선택 기준**

- **CloudFormation**: AWS 단독 사용, AWS 네이티브 통합 우선, State 관리 부담 회피
- **Terraform**: 멀티 클라우드, 더 풍부한 모듈 생태계, HCL 선호

### CloudFormation vs CDK (Cloud Development Kit)

CDK는 CloudFormation의 상위 추상화로, TypeScript/Python/Java/Go/.NET으로 인프라를 코드로 작성한 후 CloudFormation Template로 합성(synthesize)됩니다.

| 항목 | CloudFormation | CDK |
|------|----------------|-----|
| 언어 | YAML/JSON | TypeScript/Python/Java/Go/C# |
| 추상화 | 낮음 (선언적) | 높음 (객체지향) |
| 재사용 | Nested Stack, 매크로 | Construct (강력) |
| 학습 곡선 | 낮음 | 중 (프로그래밍 언어 + AWS) |
| 디버깅 | 직관적 | synthesize 결과를 봐야 함 |
| 단위 테스트 | 어려움 | 가능 (Jest 등) |

```typescript
// CDK 예시 (TypeScript)
import { Stack, StackProps } from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';

export class MyStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    const vpc = new ec2.Vpc(this, 'MyVPC', {
      maxAzs: 3,
      natGateways: 1,
    });
  }
}
```

CDK는 Construct 라이브러리를 통해 베스트 프랙티스가 기본 적용된 패턴을 제공합니다. 복잡한 인프라일수록 CDK의 생산성이 높고, 단순한 정적 인프라는 순수 CloudFormation YAML이 직관적입니다.

### CloudFormation vs AWS Proton

Proton은 플랫폼 팀이 표준 환경/서비스 템플릿을 정의하면 개발자가 Self-service로 배포할 수 있는 거버넌스 도구입니다. 내부적으로 CloudFormation 또는 Terraform을 사용합니다. 대규모 조직에서 IaC 표준화가 필요한 경우 적합합니다.

---

## 관련 문서

- [[amazon-cloudwatch-모니터링-서비스-개요|Amazon CloudWatch]] - CloudFormation으로 Alarm/Dashboard 관리
- [[amazon-sns-simple-notification-service-개요|Amazon SNS]] - Stack 이벤트 알림 채널
- [[amazon-sqs-simple-queue-service-개요|Amazon SQS]] - 큐를 IaC로 정의하여 환경 일관성 확보

---

## 요약

AWS CloudFormation은 AWS 네이티브 IaC 서비스로, 인프라를 코드로 관리하기 위한 가장 기본적이고 강력한 도구입니다. 핵심 포인트를 정리하면 다음과 같습니다.

1. **Template (YAML/JSON)** 로 인프라를 선언적으로 정의하고 **Stack** 단위로 배포합니다.
2. **Change Set**으로 변경을 미리 검토하고 안전하게 적용합니다.
3. **StackSet**으로 멀티 계정/리전에 동일 표준을 일관되게 배포합니다.
4. **Drift Detection**으로 외부 변경을 감지하고 IaC 거버넌스를 유지합니다.
5. **DeletionPolicy / UpdateReplacePolicy**로 데이터 자원 손실을 방지합니다.
6. AWS 단독 환경에서는 CloudFormation, 멀티 클라우드는 **Terraform**, 코드 기반 추상화는 **CDK**로 선택합니다.
7. CloudFormation 자체는 무료이며, **state 관리도 AWS가 자동 처리**하는 것이 큰 장점입니다.

CloudFormation은 AWS 인프라 표준화의 출발점이며, CI/CD 파이프라인에 통합하면 인프라 변경 이력 관리, 자동 검증, 자동 롤백을 모두 갖춘 견고한 운영 체계를 구축할 수 있습니다.
