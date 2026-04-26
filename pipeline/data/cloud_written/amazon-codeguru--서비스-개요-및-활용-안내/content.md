<!-- infographic-hero -->
![Amazon CodeGuru 핵심 요약](figures/infographic.svg)

*Figure: Amazon CodeGuru 한 장 요약 인포그래픽*

## 개요

Amazon CodeGuru는 머신러닝을 활용하여 코드 품질을 향상시키고 애플리케이션 성능을 최적화하는 개발자 도구입니다. Amazon 내부에서 수십 년간 축적된 코드 리뷰 경험과 수백만 개의 코드 리뷰 데이터를 학습한 ML 모델을 기반으로 합니다.

CodeGuru는 두 가지 핵심 구성 요소로 이루어져 있습니다.

1. **CodeGuru Reviewer**: 코드의 결함, 보안 취약점, 성능 문제, AWS API 모범 사례 위반 등을 자동으로 탐지하고 개선 권장사항을 제공합니다.
2. **CodeGuru Profiler**: 프로덕션 환경에서 실행 중인 애플리케이션의 런타임 동작을 분석하여 가장 비용이 높은 코드 라인을 식별하고 최적화 권장사항을 제공합니다.

CodeGuru는 Java와 Python 애플리케이션을 주요 대상으로 하며, GitHub, GitHub Enterprise, Bitbucket, AWS CodeCommit 등 주요 소스 코드 저장소와 통합됩니다. Pull Request 생성 시 자동으로 코드 리뷰가 실행되어 개발 워크플로에 자연스럽게 통합됩니다.

## 핵심 기능

### CodeGuru Reviewer

CodeGuru Reviewer는 정적 코드 분석과 ML 기반 패턴 인식을 결합하여 다음 유형의 문제를 탐지합니다.

#### 탐지 가능한 문제 유형

1. **AWS API 모범 사례**: AWS SDK 사용 시 흔히 발생하는 실수를 탐지합니다.
   - S3 클라이언트의 리전 미지정
   - DynamoDB 페이지네이션 누락
   - Lambda 핸들러 외부의 SDK 클라이언트 초기화 누락

2. **동시성 문제**: 멀티스레드 환경에서의 잠재적 문제를 탐지합니다.
   - 레이스 컨디션
   - 데드락 가능성
   - 스레드 안전하지 않은 컬렉션 사용

3. **리소스 누수**: 닫히지 않은 리소스를 탐지합니다.
   - DB 커넥션 미반환
   - 파일 핸들 미닫힘
   - 스트림 리소스 누수

4. **보안 취약점**: 보안 관련 문제를 탐지합니다.
   - 하드코딩된 자격 증명
   - SQL 인젝션 가능성
   - 부적절한 입력 검증

5. **코드 품질**: 일반적인 코드 품질 문제를 탐지합니다.
   - 불필요한 코드 복잡도
   - 비효율적인 알고리즘 패턴
   - 에러 처리 누락

#### 리포지토리 연결

```bash
# CodeGuru Reviewer에 리포지토리 연결
aws codeguru-reviewer associate-repository \
    --repository '{"CodeCommit": {"Name": "my-java-project"}}'

# GitHub 리포지토리 연결
aws codeguru-reviewer associate-repository \
    --repository '{"GitHubEnterpriseServer": {"Name": "my-project", "ConnectionArn": "arn:aws:codestar-connections:ap-northeast-2:123456789012:connection/abcd-1234", "Owner": "my-org"}}'

# 연결된 리포지토리 목록 확인
aws codeguru-reviewer list-repository-associations \
    --query 'RepositoryAssociationSummaries[*].{Name:Name,State:State,Provider:ProviderType}'
```

#### 코드 리뷰 실행

PR 기반 자동 리뷰 외에도 전체 리포지토리에 대한 코드 리뷰를 수동으로 실행할 수 있습니다.

```bash
# 전체 리포지토리 코드 리뷰 생성
aws codeguru-reviewer create-code-review \
    --name full-repository-review \
    --repository-association-arn arn:aws:codeguru-reviewer:ap-northeast-2:123456789012:association:abcd-1234 \
    --type '{"RepositoryAnalysis": {"RepositoryHead": {"BranchName": "main"}}}'

# 코드 리뷰 상태 확인
aws codeguru-reviewer describe-code-review \
    --code-review-arn arn:aws:codeguru-reviewer:ap-northeast-2:123456789012:association:abcd-1234:code-review:review-id

# 코드 리뷰 결과(권장사항) 조회
aws codeguru-reviewer list-recommendations \
    --code-review-arn arn:aws:codeguru-reviewer:ap-northeast-2:123456789012:association:abcd-1234:code-review:review-id
```

### CodeGuru Profiler

CodeGuru Profiler는 프로덕션 환경에서 실행 중인 애플리케이션의 CPU 사용량과 힙 메모리 사용량을 지속적으로 수집하고 분석합니다.

#### 프로파일링 그룹 생성

```bash
# 프로파일링 그룹 생성
aws codeguruprofiler create-profiling-group \
    --profiling-group-name my-java-app \
    --compute-platform Default

# Lambda 함수용 프로파일링 그룹
aws codeguruprofiler create-profiling-group \
    --profiling-group-name my-lambda-function \
    --compute-platform AWSLambda

# 프로파일링 그룹 목록 조회
aws codeguruprofiler list-profiling-groups \
    --query 'profilingGroups[*].{Name:profilingGroupName,ComputePlatform:computePlatform,Status:profilingStatus.latestAgentProfileReportedAt}'
```

#### Java 에이전트 설정

```bash
# Java 애플리케이션에 CodeGuru Profiler 에이전트 추가
java -javaagent:codeguru-profiler-java-agent-standalone-1.2.jar \
    -Dcom.amazonaws.codeguru.profiler.group.name=my-java-app \
    -Dcom.amazonaws.codeguru.profiler.region=ap-northeast-2 \
    -jar my-application.jar
```

#### Python 에이전트 설정

```python
# Python 애플리케이션에 CodeGuru Profiler 추가
from codeguru_profiler_agent import Profiler

def main():
    profiler = Profiler(
        profiling_group_name='my-python-app',
        region_name='ap-northeast-2'
    )
    profiler.start()

    # 애플리케이션 로직
    run_application()

if __name__ == '__main__':
    main()
```

#### Lambda 함수 통합

```python
# Lambda 함수에 CodeGuru Profiler 통합
import json
from codeguru_profiler_agent import with_lambda_profiler

@with_lambda_profiler(
    profiling_group_name='my-lambda-function',
    region_name='ap-northeast-2'
)
def lambda_handler(event, context):
    # Lambda 함수 로직
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
```

### CodeGuru Security

CodeGuru Security는 코드의 보안 취약점을 전문적으로 탐지하는 기능입니다.

```bash
# CodeGuru Security 스캔 생성
aws codeguru-security create-scan \
    --scan-name security-scan-001 \
    --resource-id '{"codeArtifactId": "arn:aws:codeguru-security:ap-northeast-2:123456789012:scans/my-scan"}' \
    --scan-type Standard \
    --analysis-type Security

# 스캔 결과 조회
aws codeguru-security get-findings \
    --scan-name security-scan-001 \
    --query 'findings[*].{Title:title,Severity:severity,FilePath:filePath}'
```

## 아키텍처/동작 원리

### CodeGuru Reviewer 동작 원리

1. **리포지토리 연결**: CodeGuru가 소스 코드 저장소에 접근할 수 있도록 연결합니다.
2. **PR 트리거**: Pull Request가 생성되면 웹훅을 통해 CodeGuru에 알림이 전달됩니다.
3. **코드 분석**: ML 모델이 변경된 코드를 분석합니다.
   - 정적 분석 엔진이 코드 구조를 파싱합니다.
   - ML 모델이 Amazon 내부 코드 리뷰 데이터를 기반으로 패턴을 매칭합니다.
   - 보안 분석 엔진이 취약점을 스캔합니다.
4. **결과 전달**: 발견된 문제가 PR 코멘트로 직접 게시됩니다.
5. **피드백 학습**: 개발자의 피드백(유용함/유용하지 않음)이 모델 개선에 반영됩니다.

### CodeGuru Profiler 동작 원리

1. **에이전트 실행**: 애플리케이션에 포함된 에이전트가 5분 간격으로 스택 트레이스를 샘플링합니다.
2. **데이터 전송**: 수집된 프로파일 데이터가 CodeGuru Profiler 서비스로 전송됩니다.
3. **프로파일 집계**: 서비스가 여러 인스턴스의 프로파일을 집계하여 통합 뷰를 생성합니다.
4. **이상 탐지**: ML 모델이 정상 패턴 대비 비정상적인 CPU/메모리 사용 패턴을 탐지합니다.
5. **권장사항 생성**: 분석 결과를 바탕으로 구체적인 코드 최적화 권장사항을 생성합니다.

프로파일러의 오버헤드는 CPU 기준 약 1% 미만으로, 프로덕션 환경에서도 안전하게 실행할 수 있습니다.

## 실전 활용

### CI/CD 파이프라인 통합

CodePipeline/CodeBuild와 통합하여 빌드 단계에서 자동으로 코드 리뷰를 실행할 수 있습니다.

```yaml
# buildspec.yml 예시
version: 0.2

phases:
  pre_build:
    commands:
      - echo "Running CodeGuru Reviewer..."
  build:
    commands:
      - echo "Building application..."
      - mvn clean package
  post_build:
    commands:
      - echo "Triggering CodeGuru Security scan..."
      - aws codeguru-security create-scan --scan-name "build-${CODEBUILD_BUILD_NUMBER}" --resource-id '{"codeArtifactId": "my-artifact"}' --scan-type Standard
```

### 프로파일링 결과 분석 및 활용

```bash
# 프로파일링 권장사항 조회
aws codeguruprofiler get-recommendations \
    --profiling-group-name my-java-app \
    --start-time 2024-01-01T00:00:00Z \
    --end-time 2024-01-02T00:00:00Z

# 프로파일 데이터 조회
aws codeguruprofiler get-profile \
    --profiling-group-name my-java-app \
    --start-time 2024-01-01T00:00:00Z \
    --end-time 2024-01-01T01:00:00Z \
    --period PT1H \
    output-profile.json

# 이상 탐지 알림 설정
aws codeguruprofiler add-notification-channels \
    --profiling-group-name my-java-app \
    --channels '[{"id": "anomaly-channel", "uri": "arn:aws:sns:ap-northeast-2:123456789012:codeguru-alerts", "eventPublishers": ["AnomalyDetection"]}]'
```

### AWS CLI를 활용한 CodeGuru 운영

```bash
# Reviewer 연결 상태 확인
aws codeguru-reviewer list-repository-associations \
    --states Associated \
    --query 'RepositoryAssociationSummaries[*].{Name:Name,Provider:ProviderType,State:State}' \
    --output table

# 최근 코드 리뷰 목록
aws codeguru-reviewer list-code-reviews \
    --type PullRequest \
    --max-results 10 \
    --query 'CodeReviewSummaries[*].{Name:Name,State:State,CreatedAt:CreatedTimeStamp}'

# Profiler 메트릭 데이터 확인
aws codeguruprofiler list-profile-times \
    --profiling-group-name my-java-app \
    --start-time 2024-01-01T00:00:00Z \
    --end-time 2024-01-02T00:00:00Z \
    --period PT5M

# Profiler 에이전트 설정 조회
aws codeguruprofiler describe-profiling-group \
    --profiling-group-name my-java-app
```

## 모범 사례/보안

### CodeGuru Reviewer 모범 사례

1. **PR 기반 자동 리뷰를 활성화합니다.** 모든 PR에 대해 자동으로 코드 리뷰가 실행되도록 설정하여 코드 품질 게이트를 구축합니다.

2. **피드백을 적극적으로 제공합니다.** CodeGuru의 권장사항에 대해 '유용함/유용하지 않음' 피드백을 제공하면 ML 모델이 팀의 코딩 패턴에 맞게 개선됩니다.

3. **전체 리포지토리 스캔을 정기적으로 실행합니다.** PR 리뷰는 변경된 코드만 검사하므로, 기존 코드베이스의 문제를 발견하려면 정기적인 전체 스캔이 필요합니다.

4. **보안 스캔을 CI/CD에 통합합니다.** 배포 전 보안 스캔을 필수 단계로 포함하여 보안 취약점이 프로덕션에 도달하지 않도록 합니다.

### CodeGuru Profiler 모범 사례

1. **프로덕션 환경에서 프로파일링을 실행합니다.** 개발/테스트 환경의 워크로드는 프로덕션과 다르므로, 실제 트래픽 패턴에서의 성능을 분석해야 합니다.

2. **이상 탐지 알림을 설정합니다.** SNS 채널을 연결하여 성능 이상이 감지되면 즉시 알림을 받을 수 있도록 합니다.

3. **권장사항의 예상 비용 절감 효과를 확인합니다.** CodeGuru Profiler는 각 권장사항의 예상 비용 절감 효과를 제시하므로, 영향도가 큰 항목부터 처리합니다.

### 보안 고려사항

1. **최소 권한 IAM 정책을 적용합니다.**

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "codeguru-reviewer:ListCodeReviews",
                "codeguru-reviewer:ListRecommendations",
                "codeguru-reviewer:DescribeCodeReview"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "codeguru-profiler:GetProfile",
                "codeguru-profiler:GetRecommendations"
            ],
            "Resource": "arn:aws:codeguruprofiler:ap-northeast-2:123456789012:profilingGroup/my-java-app"
        }
    ]
}
```

2. **소스 코드 접근을 안전하게 관리합니다.** CodeGuru Reviewer가 소스 코드에 접근하기 위한 연결 권한은 최소한으로 유지합니다.

3. **프로파일 데이터의 보존 기간을 설정합니다.** 프로파일 데이터에는 메서드 이름, 클래스 구조 등 코드 구조 정보가 포함되므로 보존 기간을 적절히 관리합니다.

## 관련 서비스 비교

### CodeGuru Reviewer vs SonarQube

| 항목 | CodeGuru Reviewer | SonarQube |
|------|-------------------|----------|
| 분석 방식 | ML 기반 + 정적 분석 | 규칙 기반 정적 분석 |
| AWS 특화 | AWS API 모범 사례 탐지 | 범용 |
| 운영 모델 | 완전관리형 | 자체 호스팅 또는 SaaS |
| 지원 언어 | Java, Python 중심 | 30+ 언어 |
| 학습 능력 | 피드백 기반 개선 | 규칙 수동 관리 |
| 비용 | 코드 라인 기반 | 라이선스 비용 |

### CodeGuru Profiler vs AWS X-Ray

| 항목 | CodeGuru Profiler | AWS X-Ray |
|------|-------------------|-----------|
| 분석 대상 | CPU/메모리 사용 패턴 | 분산 트레이싱 |
| 분석 수준 | 메서드/코드 라인 수준 | 서비스/API 수준 |
| 목적 | 코드 수준 최적화 | 서비스 간 지연 분석 |
| 오버헤드 | 약 1% CPU | 샘플링 비율 의존 |
| 권장사항 | ML 기반 자동 생성 | 수동 분석 필요 |

### CodeGuru vs Amazon Inspector

| 항목 | CodeGuru | Amazon Inspector |
|------|----------|------------------|
| 분석 대상 | 소스 코드 | 실행 환경 (EC2, Lambda, ECR) |
| 탐지 유형 | 코드 결함 + 보안 | CVE 취약점 |
| 분석 시점 | 개발 단계 (shift-left) | 배포 후 |
| 통합 | VCS, CI/CD | AWS 인프라 |

## 요약

Amazon CodeGuru는 ML 기반 코드 리뷰(Reviewer)와 애플리케이션 프로파일링(Profiler)을 통해 코드 품질과 런타임 성능을 동시에 개선하는 개발자 도구입니다.

CodeGuru Reviewer는 PR 기반 자동 코드 리뷰를 통해 AWS API 오용, 동시성 문제, 리소스 누수, 보안 취약점 등을 개발 초기 단계에서 탐지합니다. Amazon 내부 코드 리뷰 데이터를 학습한 ML 모델이 단순한 규칙 기반 도구로는 발견하기 어려운 패턴까지 식별합니다.

CodeGuru Profiler는 프로덕션 환경에서 1% 미만의 오버헤드로 CPU/메모리 사용 패턴을 수집하고, 가장 비용이 높은 코드 영역을 식별하여 구체적인 최적화 권장사항을 제공합니다. 이상 탐지 기능으로 성능 저하를 조기에 감지할 수 있습니다.

CodeGuru는 CI/CD 파이프라인에 통합하여 개발 워크플로의 자연스러운 일부로 운영하는 것이 가장 효과적입니다.