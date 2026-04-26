<!-- infographic-hero -->
![AWS CodePipeline 핵심 요약](figures/infographic.svg)

*Figure: AWS CodePipeline 한 장 요약 인포그래픽*

## 개요

AWS CodePipeline은 소프트웨어 릴리스 프로세스를 시각적으로 모델링하고 자동화하는 완전관리형 CI/CD(지속적 통합/지속적 배포) 서비스입니다. 코드 변경이 발생하면 소스 가져오기, 빌드, 테스트, 배포까지의 전체 과정을 자동으로 실행합니다.

현대 소프트웨어 개발에서 CI/CD 파이프라인은 필수 인프라입니다. 수동 빌드/배포 프로세스는 속도가 느리고, 휴먼 에러가 발생하기 쉬우며, 팀 규모가 커질수록 관리가 어려워집니다. CodePipeline은 이러한 문제를 해결하기 위해 다음과 같은 가치를 제공합니다.

1. **완전 자동화**: 코드 커밋부터 프로덕션 배포까지 사람의 개입 없이 자동으로 진행됩니다.
2. **시각적 워크플로**: AWS 콘솔에서 파이프라인의 각 스테이지 상태를 실시간으로 확인할 수 있습니다.
3. **유연한 통합**: AWS 서비스뿐 아니라 GitHub, Jenkins, CloudBees 등 서드파티 도구와도 통합됩니다.
4. **품질 게이트**: 수동 승인 단계, 테스트 단계를 삽입하여 품질을 보장합니다.
5. **종량제 과금**: 활성 파이프라인당 월 1 USD (V1 타입), V2 타입은 액션 실행 횟수 기반으로 과금됩니다.

## 핵심 기능

### 파이프라인 구성 요소

#### Pipeline (파이프라인)

전체 릴리스 워크플로를 정의하는 최상위 컨테이너입니다. 하나 이상의 스테이지로 구성됩니다.

#### Stage (스테이지)

파이프라인의 논리적 단계입니다. 일반적으로 Source, Build, Test, Deploy 등의 스테이지를 포함합니다. 스테이지 내의 액션은 순차 또는 병렬로 실행할 수 있습니다.

#### Action (액션)

스테이지 내에서 실행되는 개별 작업입니다. 소스 가져오기, 빌드 실행, 배포, 승인 요청 등이 있습니다.

#### Artifact (아티팩트)

스테이지 간에 전달되는 데이터입니다. 소스 코드, 빌드 결과물 등이 S3에 저장됩니다.

### 파이프라인 생성

```bash
# AWS CLI로 파이프라인 생성
aws codepipeline create-pipeline \
    --cli-input-json file://pipeline-definition.json
```

파이프라인 정의 파일(pipeline-definition.json) 예시는 다음과 같습니다.

```json
{
    "pipeline": {
        "name": "my-app-pipeline",
        "roleArn": "arn:aws:iam::123456789012:role/CodePipelineServiceRole",
        "artifactStore": {
            "type": "S3",
            "location": "my-pipeline-artifacts-bucket"
        },
        "stages": [
            {
                "name": "Source",
                "actions": [
                    {
                        "name": "SourceAction",
                        "actionTypeId": {
                            "category": "Source",
                            "owner": "AWS",
                            "provider": "CodeStarSourceConnection",
                            "version": "1"
                        },
                        "configuration": {
                            "ConnectionArn": "arn:aws:codestar-connections:ap-northeast-2:123456789012:connection/abcd-1234",
                            "FullRepositoryId": "my-org/my-repo",
                            "BranchName": "main",
                            "OutputArtifactFormat": "CODE_ZIP"
                        },
                        "outputArtifacts": [{"name": "SourceOutput"}]
                    }
                ]
            },
            {
                "name": "Build",
                "actions": [
                    {
                        "name": "BuildAction",
                        "actionTypeId": {
                            "category": "Build",
                            "owner": "AWS",
                            "provider": "CodeBuild",
                            "version": "1"
                        },
                        "configuration": {
                            "ProjectName": "my-build-project"
                        },
                        "inputArtifacts": [{"name": "SourceOutput"}],
                        "outputArtifacts": [{"name": "BuildOutput"}]
                    }
                ]
            },
            {
                "name": "Deploy",
                "actions": [
                    {
                        "name": "DeployAction",
                        "actionTypeId": {
                            "category": "Deploy",
                            "owner": "AWS",
                            "provider": "CodeDeploy",
                            "version": "1"
                        },
                        "configuration": {
                            "ApplicationName": "my-web-app",
                            "DeploymentGroupName": "production"
                        },
                        "inputArtifacts": [{"name": "BuildOutput"}]
                    }
                ]
            }
        ]
    }
}
```

### 소스 프로바이더

CodePipeline은 다양한 소스 저장소를 지원합니다.

| 프로바이더 | 연결 방식 | 트리거 |
|-----------|----------|--------|
| GitHub / GitHub Enterprise | CodeStar Connection | 웹훅 |
| Bitbucket | CodeStar Connection | 웹훅 |
| AWS CodeCommit | 직접 통합 | CloudWatch Event |
| Amazon S3 | 직접 통합 | CloudWatch Event |
| Amazon ECR | 직접 통합 | CloudWatch Event |

```bash
# CodeStar Connection 생성 (GitHub 연결)
aws codestar-connections create-connection \
    --provider-type GitHub \
    --connection-name my-github-connection

# 연결 상태 확인
aws codestar-connections list-connections \
    --query 'Connections[*].{Name:ConnectionName,Status:ConnectionStatus,Provider:ProviderType}' \
    --output table
```

### 수동 승인 액션

프로덕션 배포 전에 수동 승인 게이트를 추가하여 배포를 제어할 수 있습니다.

```json
{
    "name": "ManualApproval",
    "actions": [
        {
            "name": "ApproveDeployment",
            "actionTypeId": {
                "category": "Approval",
                "owner": "AWS",
                "provider": "Manual",
                "version": "1"
            },
            "configuration": {
                "NotificationArn": "arn:aws:sns:ap-northeast-2:123456789012:pipeline-approval",
                "CustomData": "프로덕션 배포를 승인해 주세요. 변경사항: 주문 처리 API 업데이트",
                "ExternalEntityLink": "https://github.com/my-org/my-repo/pull/123"
            }
        }
    ]
}
```

```bash
# 수동 승인 요청 처리
aws codepipeline put-approval-result \
    --pipeline-name my-app-pipeline \
    --stage-name ManualApproval \
    --action-name ApproveDeployment \
    --result '{"summary": "변경사항 확인 완료, 배포 승인", "status": "Approved"}' \
    --token "승인-토큰"
```

### V2 파이프라인 타입

CodePipeline V2는 다음과 같은 향상된 기능을 제공합니다.

- **파이프라인 변수**: 런타임에 동적 값을 전달할 수 있습니다.
- **Git 태그 트리거**: 특정 Git 태그가 푸시될 때 파이프라인을 트리거합니다.
- **PR 기반 트리거**: Pull Request 이벤트에 의한 트리거를 지원합니다.
- **파이프라인 수준 변수**: 스테이지 간에 값을 전달할 수 있습니다.

```bash
# V2 파이프라인 생성 시 트리거 설정
aws codepipeline create-pipeline \
    --cli-input-json file://v2-pipeline.json
```

## 아키텍처/동작 원리

### 파이프라인 실행 흐름

1. **트리거**: 소스 변경이 감지되면(웹훅, CloudWatch Event) 파이프라인이 자동으로 시작됩니다.
2. **소스 스테이지**: 소스 코드를 가져와 S3 아티팩트 버킷에 저장합니다.
3. **빌드 스테이지**: CodeBuild 등이 소스 아티팩트를 입력으로 받아 빌드를 실행합니다.
4. **테스트 스테이지** (선택): 자동화된 테스트를 실행합니다.
5. **승인 스테이지** (선택): 지정된 승인자가 수동으로 승인합니다.
6. **배포 스테이지**: CodeDeploy, ECS, Elastic Beanstalk 등으로 배포합니다.

### 아티팩트 관리

파이프라인의 아티팩트는 지정된 S3 버킷에 저장됩니다. 각 스테이지의 출력 아티팩트는 다음 스테이지의 입력으로 사용됩니다.

```bash
# 아티팩트 버킷 내용 확인
aws s3 ls s3://my-pipeline-artifacts-bucket/ --recursive
```

아티팩트는 기본적으로 SSE-S3로 암호화됩니다. KMS 키를 사용한 암호화도 설정할 수 있습니다.

### 이벤트 기반 트리거

CodePipeline은 Amazon EventBridge(CloudWatch Events)를 통해 이벤트 기반으로 동작합니다.

- CodeCommit 리포지토리에 커밋이 푸시되면 EventBridge 규칙이 파이프라인을 트리거합니다.
- S3 버킷에 새 객체가 업로드되면 EventBridge를 통해 파이프라인이 시작됩니다.
- ECR에 새 이미지가 푸시되면 파이프라인이 트리거됩니다.

## 실전 활용

### 완전한 CI/CD 파이프라인 구성

실무에서 일반적으로 사용하는 파이프라인 구성은 다음과 같습니다.

```
Source (GitHub) -> Build (CodeBuild) -> Unit Test (CodeBuild)
    -> Staging Deploy (CodeDeploy) -> Integration Test (CodeBuild)
    -> Manual Approval -> Production Deploy (CodeDeploy)
```

### 병렬 액션 실행

동일 스테이지 내에서 여러 액션을 병렬로 실행하여 파이프라인 실행 시간을 단축할 수 있습니다.

```json
{
    "name": "Test",
    "actions": [
        {
            "name": "UnitTest",
            "actionTypeId": {
                "category": "Test",
                "owner": "AWS",
                "provider": "CodeBuild",
                "version": "1"
            },
            "configuration": {"ProjectName": "unit-test-project"},
            "inputArtifacts": [{"name": "BuildOutput"}],
            "runOrder": 1
        },
        {
            "name": "IntegrationTest",
            "actionTypeId": {
                "category": "Test",
                "owner": "AWS",
                "provider": "CodeBuild",
                "version": "1"
            },
            "configuration": {"ProjectName": "integration-test-project"},
            "inputArtifacts": [{"name": "BuildOutput"}],
            "runOrder": 1
        },
        {
            "name": "SecurityScan",
            "actionTypeId": {
                "category": "Test",
                "owner": "AWS",
                "provider": "CodeBuild",
                "version": "1"
            },
            "configuration": {"ProjectName": "security-scan-project"},
            "inputArtifacts": [{"name": "SourceOutput"}],
            "runOrder": 1
        }
    ]
}
```

`runOrder`가 동일한 액션은 병렬로 실행됩니다.

### 크로스 리전 배포

CodePipeline은 여러 리전에 동시에 배포하는 크로스 리전 액션을 지원합니다.

```json
{
    "name": "DeployToMultipleRegions",
    "actions": [
        {
            "name": "DeployToSeoul",
            "region": "ap-northeast-2",
            "actionTypeId": {
                "category": "Deploy",
                "owner": "AWS",
                "provider": "CodeDeploy",
                "version": "1"
            },
            "configuration": {
                "ApplicationName": "my-app",
                "DeploymentGroupName": "production-seoul"
            },
            "inputArtifacts": [{"name": "BuildOutput"}],
            "runOrder": 1
        },
        {
            "name": "DeployToTokyo",
            "region": "ap-northeast-1",
            "actionTypeId": {
                "category": "Deploy",
                "owner": "AWS",
                "provider": "CodeDeploy",
                "version": "1"
            },
            "configuration": {
                "ApplicationName": "my-app",
                "DeploymentGroupName": "production-tokyo"
            },
            "inputArtifacts": [{"name": "BuildOutput"}],
            "runOrder": 1
        }
    ]
}
```

### AWS CLI를 활용한 파이프라인 운영

```bash
# 파이프라인 목록 조회
aws codepipeline list-pipelines \
    --query 'pipelines[*].{Name:name,Created:created,Updated:updated}' \
    --output table

# 파이프라인 상태 확인
aws codepipeline get-pipeline-state \
    --name my-app-pipeline \
    --query 'stageStates[*].{Stage:stageName,Status:latestExecution.status}' \
    --output table

# 파이프라인 수동 실행
aws codepipeline start-pipeline-execution \
    --name my-app-pipeline

# 특정 스테이지 재시도
aws codepipeline retry-stage-execution \
    --pipeline-name my-app-pipeline \
    --stage-name Build \
    --pipeline-execution-id "실행-ID" \
    --retry-mode FAILED_ACTIONS

# 파이프라인 실행 이력 조회
aws codepipeline list-pipeline-executions \
    --pipeline-name my-app-pipeline \
    --max-results 10 \
    --query 'pipelineExecutionSummaries[*].{Id:pipelineExecutionId,Status:status,Trigger:trigger.triggerType,Time:lastUpdateTime}' \
    --output table

# 파이프라인 비활성화
aws codepipeline disable-stage-transition \
    --pipeline-name my-app-pipeline \
    --stage-name Deploy \
    --transition-type Inbound \
    --reason "프로덕션 점검 중"

# 파이프라인 재활성화
aws codepipeline enable-stage-transition \
    --pipeline-name my-app-pipeline \
    --stage-name Deploy \
    --transition-type Inbound

# 파이프라인 정의 내보내기
aws codepipeline get-pipeline \
    --name my-app-pipeline \
    --query 'pipeline' > pipeline-export.json

# 파이프라인 삭제
aws codepipeline delete-pipeline \
    --name my-app-pipeline
```

### 알림 설정

```bash
# SNS 토픽 생성
aws sns create-topic --name pipeline-notifications

# 파이프라인 알림 규칙 생성
aws codestar-notifications create-notification-rule \
    --name pipeline-failure-alert \
    --resource "arn:aws:codepipeline:ap-northeast-2:123456789012:my-app-pipeline" \
    --detail-type FULL \
    --event-type-ids \
        codepipeline-pipeline-pipeline-execution-failed \
        codepipeline-pipeline-pipeline-execution-succeeded \
        codepipeline-pipeline-manual-approval-needed \
    --targets '[{"TargetType": "SNS", "TargetAddress": "arn:aws:sns:ap-northeast-2:123456789012:pipeline-notifications"}]'
```

## 모범 사례/보안

### 파이프라인 설계 모범 사례

1. **스테이지를 명확히 분리합니다.** Source, Build, Test, Staging, Approval, Production 등 논리적 단계별로 스테이지를 구성합니다.

2. **테스트 스테이지를 반드시 포함합니다.** 단위 테스트, 통합 테스트, 보안 스캔을 별도 액션으로 병렬 실행하여 품질 게이트를 구축합니다.

3. **프로덕션 배포 전 수동 승인을 추가합니다.** SNS 알림과 함께 수동 승인 단계를 두어 프로덕션 배포를 통제합니다.

4. **환경별 파이프라인을 분리합니다.** 개발/스테이징/프로덕션 환경에 대한 배포를 단일 파이프라인의 순차 스테이지로 구성하되, 환경 간 게이트를 설정합니다.

5. **파이프라인 정의를 코드로 관리합니다.** CloudFormation, CDK, Terraform 등으로 파이프라인을 IaC(Infrastructure as Code)로 관리합니다.

6. **V2 파이프라인 타입을 활용합니다.** 파이프라인 변수, Git 태그 트리거 등 V2의 향상된 기능을 활용합니다.

### 보안 모범 사례

1. **최소 권한 서비스 역할을 사용합니다.**

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:GetBucketVersioning"
            ],
            "Resource": [
                "arn:aws:s3:::my-pipeline-artifacts-bucket",
                "arn:aws:s3:::my-pipeline-artifacts-bucket/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "codebuild:StartBuild",
                "codebuild:BatchGetBuilds"
            ],
            "Resource": "arn:aws:codebuild:ap-northeast-2:123456789012:project/my-build-project"
        },
        {
            "Effect": "Allow",
            "Action": [
                "codedeploy:CreateDeployment",
                "codedeploy:GetDeployment",
                "codedeploy:GetApplication",
                "codedeploy:GetApplicationRevision",
                "codedeploy:RegisterApplicationRevision",
                "codedeploy:GetDeploymentConfig"
            ],
            "Resource": "*"
        }
    ]
}
```

2. **아티팩트 버킷의 암호화를 적용합니다.** KMS 고객 관리형 키를 사용하여 아티팩트를 암호화합니다.

3. **크로스 계정 배포 시 assume role을 사용합니다.** 다른 AWS 계정에 배포할 때는 크로스 계정 IAM 역할을 활용합니다.

4. **파이프라인 변경을 감사합니다.** CloudTrail을 통해 파이프라인 생성, 수정, 삭제 이벤트를 추적합니다.

5. **민감 정보를 파이프라인 변수에 저장하지 않습니다.** 비밀 값은 AWS Secrets Manager나 SSM Parameter Store에 저장하고 CodeBuild에서 참조합니다.

## 관련 서비스 비교

### CodePipeline vs GitHub Actions

| 항목 | CodePipeline | GitHub Actions |
|------|-------------|----------------|
| 소스 관리 | 다양한 소스 지원 | GitHub 중심 |
| AWS 통합 | 네이티브 (30+ 서비스) | 별도 Action 필요 |
| 시각적 편집기 | AWS 콘솔 | YAML 편집 |
| 수동 승인 | 내장 | 커스텀 구현 필요 |
| 크로스 리전 | 내장 지원 | 수동 구성 |
| 비용 | 파이프라인당 월 $1 (V1) | 분 단위 과금 |
| 러너 | AWS 관리 | GitHub/Self-hosted |

### CodePipeline vs Jenkins

| 항목 | CodePipeline | Jenkins |
|------|-------------|--------|
| 운영 모델 | 완전관리형 | 자체 호스팅 |
| 확장성 | 자동 스케일링 | 수동 관리 |
| 플러그인 생태계 | AWS 서비스 중심 | 1,800+ 플러그인 |
| 유지보수 | 불필요 | 업데이트/패치 필요 |
| 비용 | 종량제 | 인프라 비용 + 운영 비용 |
| 유연성 | AWS 생태계 최적화 | 높은 커스텀 자유도 |

### CodePipeline vs GitLab CI/CD

| 항목 | CodePipeline | GitLab CI/CD |
|------|-------------|---------------|
| 소스 관리 | 외부 소스 연동 | GitLab 내장 |
| 설정 방식 | JSON/콘솔 | .gitlab-ci.yml |
| 컨테이너 레지스트리 | ECR 연동 | GitLab Registry 내장 |
| AWS 배포 | 네이티브 | 별도 설정 |
| 올인원 | CI/CD만 | SCM+CI/CD+Registry |

## 요약

AWS CodePipeline은 소프트웨어 릴리스 프로세스를 완전히 자동화하는 CI/CD 서비스입니다. 소스 가져오기, 빌드, 테스트, 승인, 배포의 전체 워크플로를 시각적으로 모델링하고 자동으로 실행합니다.

CodePipeline은 CodeCommit, CodeBuild, CodeDeploy 등 AWS 네이티브 도구뿐 아니라 GitHub, Jenkins 등 서드파티 도구와도 유연하게 통합됩니다. 병렬 액션, 크로스 리전 배포, 수동 승인 게이트 등을 통해 복잡한 릴리스 요구사항을 충족할 수 있습니다.

V2 파이프라인 타입은 파이프라인 변수, Git 태그 트리거, PR 기반 트리거 등 향상된 기능을 제공하며, 액션 실행 횟수 기반의 유연한 과금 모델을 적용합니다.

파이프라인 설계 시 테스트 스테이지를 반드시 포함하고, 프로덕션 배포 전 수동 승인 게이트를 설정하며, IaC로 파이프라인 정의를 관리하는 것이 핵심 모범 사례입니다. 최소 권한 IAM 역할, 아티팩트 암호화, CloudTrail 감사 로깅으로 보안을 강화해야 합니다.