## 개요

Amazon Q Developer는 소프트웨어 개발의 전체 생명주기를 지원하는 AI 기반 개발 도우미 서비스입니다. IDE에서의 코드 작성, AWS 인프라 관리, 코드 리뷰, 보안 스캔, 레거시 코드 마이그레이션 등 개발자가 수행하는 거의 모든 작업을 AI로 가속화합니다.

Amazon Q Developer는 기존의 Amazon CodeWhisperer를 포함하여 확장된 서비스로, 단순한 코드 자동 완성을 넘어 다음과 같은 포괄적인 개발 지원을 제공합니다.

- **코드 생성 및 자동 완성**: IDE에서 실시간으로 코드를 제안합니다.
- **채팅 기반 개발 지원**: 자연어로 코딩 질문을 하고, 코드 설명과 디버깅 도움을 받습니다.
- **코드 변환 (Transform)**: Java 8에서 17로의 업그레이드 등 대규모 코드 마이그레이션을 자동화합니다.
- **보안 스캔**: 코드의 보안 취약점과 모범 사례 위반을 감지합니다.
- **AWS 콘솔 통합**: AWS 서비스에 대한 질문에 답변하고, 트러블슈팅을 지원합니다.
- **/dev 에이전트**: 자연어 태스크 설명을 기반으로 에이전트가 자율적으로 코드를 작성하고 테스트합니다.

---

## 핵심 기능

### 1. IDE 통합 - 코드 생성 및 자동 완성

Amazon Q Developer는 VS Code, JetBrains IDE, Visual Studio, AWS Cloud9 등 주요 IDE와 통합됩니다.

```bash
# VS Code에 Amazon Q 확장 설치
code --install-extension amazonwebservices.amazon-q-vscode

# JetBrains IDE 플러그인은 Marketplace에서 "Amazon Q" 검색하여 설치
```

코드 자동 완성은 개발자가 코드를 작성하는 동안 실시간으로 다음 코드를 제안합니다. 주석으로 의도를 기술하면 해당 의도에 맞는 코드를 생성합니다.

```python
# 예시: 주석 기반 코드 생성
# S3 버킷에서 최근 24시간 내 업로드된 파일 목록을 조회하는 함수
# Amazon Q가 아래와 같은 코드를 자동 제안합니다

import boto3
from datetime import datetime, timedelta

def get_recent_s3_objects(bucket_name, hours=24):
    s3 = boto3.client('s3')
    cutoff_time = datetime.now() - timedelta(hours=hours)
    
    response = s3.list_objects_v2(Bucket=bucket_name)
    recent_objects = []
    
    for obj in response.get('Contents', []):
        if obj['LastModified'].replace(tzinfo=None) > cutoff_time:
            recent_objects.append({
                'key': obj['Key'],
                'size': obj['Size'],
                'last_modified': obj['LastModified'].isoformat()
            })
    
    return recent_objects
```

지원하는 프로그래밍 언어는 Python, JavaScript, TypeScript, Java, C#, Go, Rust, PHP, Ruby, Kotlin, Swift, SQL, Shell/Bash, Terraform(HCL), CloudFormation(YAML/JSON) 등 15개 이상입니다.

### 2. 채팅 기반 개발 지원

IDE 내 채팅 패널에서 자연어로 개발 관련 질문을 할 수 있습니다.

활용 예시는 다음과 같습니다.

- "이 함수의 시간 복잡도를 분석해 주십시오"
- "이 코드에서 메모리 누수가 발생할 수 있는 부분을 찾아 주십시오"
- "DynamoDB에서 GSI를 사용한 쿼리 패턴을 설명해 주십시오"
- "이 Lambda 함수를 최적화해 주십시오"
- "이 에러 메시지의 원인과 해결 방법을 알려 주십시오"

채팅에서 `@workspace`를 사용하면 전체 프로젝트 컨텍스트를 참조하여 더 정확한 답변을 받을 수 있습니다.

### 3. 코드 변환 (Amazon Q Transform)

Amazon Q Transform은 대규모 코드 마이그레이션을 자동화합니다. 현재 지원하는 변환 유형은 다음과 같습니다.

- **Java 업그레이드**: Java 8/11에서 Java 17로 자동 업그레이드
- **.NET 업그레이드**: .NET Framework에서 .NET Core/6+로 마이그레이션
- **SQL 변환**: 상용 DB SQL을 Amazon Aurora PostgreSQL SQL로 변환

```bash
# AWS CLI를 통한 변환 작업 상태 확인
aws q get-transformation \
  --transformation-id "transform-abc123" \
  --region us-east-1

# 변환 작업 목록 조회
aws q list-transformations \
  --region us-east-1
```

IDE에서의 변환 워크플로는 다음과 같습니다.

1. IDE에서 Amazon Q 채팅 패널을 열고 `/transform` 명령을 입력합니다.
2. 변환할 프로젝트와 대상 버전을 선택합니다.
3. Amazon Q가 코드를 분석하고, 의존성을 확인하고, 변환 계획을 생성합니다.
4. 자동으로 코드를 변환하고, 빌드/테스트를 수행합니다.
5. 변환 결과를 diff 형식으로 제공하여 개발자가 검토하고 적용합니다.

### 4. 보안 스캔

Amazon Q Developer는 코드의 보안 취약점을 자동으로 감지합니다.

```bash
# CLI를 통한 프로젝트 보안 스캔
aws q start-code-analysis \
  --source-code-type REPOSITORY \
  --source-code-location '{"repositoryUrl": "https://github.com/myorg/myrepo"}' \
  --region us-east-1
```

감지하는 보안 이슈 유형은 다음과 같습니다.

- SQL 인젝션
- XSS(Cross-Site Scripting)
- 하드코딩된 비밀번호/API 키
- 안전하지 않은 암호화 알고리즘
- 부적절한 입력 검증
- 과도한 권한의 IAM 정책
- 의존성 취약점
- OWASP Top 10 관련 이슈

IDE에서는 개발 중 실시간으로 보안 이슈를 감지하여 경고하며, Auto Scan 기능으로 파일 저장 시마다 자동 스캔을 수행합니다.

### 5. /dev 에이전트 (Autonomous Feature Development)

`/dev` 명령은 Amazon Q Developer의 가장 혁신적인 기능으로, 자연어 태스크 설명을 기반으로 에이전트가 자율적으로 코드를 작성합니다.

사용 예시는 다음과 같습니다.

- `/dev API 엔드포인트에 페이지네이션 기능을 추가해 주십시오. cursor 기반 페이지네이션을 구현하고, 각 페이지는 20개의 결과를 반환하도록 하십시오.`
- `/dev 현재 프로젝트에 단위 테스트를 추가해 주십시오. pytest를 사용하고, 주요 함수에 대해 정상 케이스와 에러 케이스를 모두 포함하십시오.`
- `/dev 사용자 인증에 JWT 리프레시 토큰 메커니즘을 추가해 주십시오.`

/dev 에이전트의 동작 과정은 다음과 같습니다.

1. 태스크 설명을 분석하여 구현 계획을 수립합니다.
2. 프로젝트 구조와 기존 코드를 분석합니다.
3. 필요한 파일을 생성하거나 수정합니다.
4. 변경 사항을 diff 형식으로 제시합니다.
5. 개발자가 검토하고 승인/수정합니다.

### 6. AWS 콘솔 통합

AWS Management Console에서 Amazon Q를 사용하여 AWS 서비스에 대한 질문과 트러블슈팅을 수행합니다.

```bash
# 콘솔에서 사용 가능한 질문 예시:
# - "이 EC2 인스턴스의 CPU 사용률이 높은 이유는 무엇입니까?"
# - "이 Lambda 함수의 타임아웃 에러를 해결하려면 어떻게 해야 합니까?"
# - "이 S3 버킷의 비용을 최적화하는 방법을 알려 주십시오."
# - "VPC 피어링 설정 방법을 단계별로 안내해 주십시오."

# CLI에서 Amazon Q에게 질문하기
aws q chat \
  --message "Lambda 함수가 VPC 내에서 인터넷에 접근하려면 어떻게 설정해야 합니까?" \
  --region us-east-1
```

### 7. Amazon Q Developer Agent for CLI

터미널에서 자연어로 명령을 생성하고 실행합니다.

```bash
# 자연어를 CLI 명령으로 변환
# 사용자: "us-east-1 리전에서 실행 중인 모든 EC2 인스턴스의 ID와 유형을 조회해 주십시오"
# Amazon Q가 다음 명령을 생성합니다:
aws ec2 describe-instances \
  --region us-east-1 \
  --filters "Name=instance-state-name,Values=running" \
  --query 'Reservations[*].Instances[*].[InstanceId,InstanceType]' \
  --output table

# 자연어: "30일 이상 된 CloudWatch 로그 그룹을 삭제해 주십시오"
# Amazon Q가 안전한 스크립트를 생성합니다
```

---

## 아키텍처/동작 원리

### Amazon Q Developer 아키텍처

```
[개발자]
    |
    +---> [IDE Plugin (VS Code/JetBrains)]
    |       +--- 코드 자동 완성
    |       +--- 인라인 채팅
    |       +--- /dev 에이전트
    |       +--- /transform 변환
    |       +--- 보안 스캔
    |
    +---> [AWS Management Console]
    |       +--- 서비스 질의응답
    |       +--- 트러블슈팅
    |       +--- 네트워크 분석
    |
    +---> [CLI 통합]
    |       +--- 자연어 -> CLI 명령 변환
    |       +--- 명령 설명 및 수정
    |
    +---> [Amazon Q Developer Agent]
            +--- 코드 리뷰 (GitHub/GitLab)
            +--- 자동화된 기능 개발
            +--- 단위 테스트 생성

           [모든 상호작용]
                |
                v
        [Amazon Q AI 엔진]
          +--- 코드 이해 모델
          +--- AWS 서비스 지식 베이스
          +--- 보안 패턴 데이터베이스
          +--- 코드 변환 엔진
```

### 코드 자동 완성 동작 원리

```
[개발자가 코드 작성]
    |
    v
[IDE Plugin이 컨텍스트 수집]
  - 현재 파일 내용
  - 커서 위치
  - 열려 있는 관련 파일
  - 프로젝트 구조
  - import 문
    |
    v
[Amazon Q 서비스로 요청]
    |
    v
[코드 생성 모델 추론]
  - 컨텍스트 기반 코드 생성
  - 여러 후보 생성
  - 보안 필터 적용
  - 라이선스 필터 적용
    |
    v
[IDE에 제안 표시]
  - Tab: 수락
  - Esc: 거부
  - Alt+]: 다음 제안
```

### /dev 에이전트 동작 원리

```
[자연어 태스크 설명]
    |
    v
[태스크 분석 및 계획 수립]
  - 요구사항 파싱
  - 구현 범위 결정
  - 단계별 계획 생성
    |
    v
[프로젝트 분석]
  - 파일 구조 분석
  - 기존 코드 이해
  - 의존성 확인
  - 코딩 스타일 파악
    |
    v
[코드 생성/수정]
  - 계획에 따라 파일 생성/수정
  - 일관된 코딩 스타일 유지
  - 테스트 코드 포함
    |
    v
[결과 제시 (Diff 형식)]
  - 변경 사항 요약
  - 파일별 diff 표시
  - 개발자 검토 대기
    |
    v
[개발자 승인/수정/거부]
```

---

## 실전 활용

### 사례 1: Infrastructure as Code 생성

```python
# Amazon Q Developer 채팅 예시
# 질문: "프로덕션용 ECS Fargate 서비스를 Terraform으로 작성해 주십시오.
#         ALB, Auto Scaling, CloudWatch 로깅을 포함해야 합니다."

# Amazon Q가 생성하는 Terraform 코드 예시:
```

```hcl
# ecs.tf - Amazon Q Developer가 생성한 코드
resource "aws_ecs_cluster" "main" {
  name = var.cluster_name

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_ecs_task_definition" "app" {
  family                   = var.service_name
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name  = var.service_name
    image = var.container_image
    portMappings = [{
      containerPort = var.container_port
      protocol      = "tcp"
    }]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.app.name
        "awslogs-region"        = var.region
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
}

resource "aws_ecs_service" "app" {
  name            = var.service_name
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = var.service_name
    container_port   = var.container_port
  }
}

resource "aws_appautoscaling_target" "ecs" {
  max_capacity       = var.max_capacity
  min_capacity       = var.min_capacity
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.app.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "cpu" {
  name               = "${var.service_name}-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 70.0
  }
}
```

### 사례 2: 코드 리뷰 자동화 (CI/CD 통합)

GitHub Actions에서 PR에 대해 Amazon Q Developer의 자동 코드 리뷰를 수행합니다.

```yaml
# .github/workflows/q-review.yml
name: Amazon Q Code Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Amazon Q Security Scan
        uses: aws/amazon-q-developer-action@v1
        with:
          scan-type: security
          languages: python,javascript
```

### 사례 3: 레거시 Java 애플리케이션 마이그레이션

IDE에서 `/transform` 명령을 사용하여 Java 8 프로젝트를 Java 17로 업그레이드하는 과정입니다.

```bash
# 변환 전 프로젝트 빌드 확인
mvn clean compile -f /path/to/legacy-project/pom.xml

# IDE에서 /transform 실행 후 Amazon Q가 수행하는 작업:
# 1. pom.xml의 Java 버전, 의존성 업데이트
# 2. deprecated API를 새로운 API로 교체
# 3. Java 17 새 기능 적용 (record, sealed class, pattern matching 등)
# 4. javax -> jakarta 네임스페이스 변경 (필요 시)
# 5. 테스트 실행 및 결과 보고

# 변환 후 빌드 확인
mvn clean compile -f /path/to/legacy-project/pom.xml
```

---

## 모범 사례/보안

### 코드 보안

- Amazon Q Developer는 제안된 코드에서 오픈소스 참조를 감지하여 라이선스 정보를 표시합니다.
- 보안 스캔을 CI/CD 파이프라인에 통합하여 모든 PR에 대해 자동 검사를 수행합니다.
- 코드 자동 완성 제안을 무조건 수락하지 말고 항상 검토합니다.

### 데이터 프라이버시

- Professional 계층에서는 사용자의 코드가 모델 학습에 사용되지 않습니다.
- AWS가 코드 콘텐츠를 저장하거나 공유하지 않습니다.
- 조직 관리자가 Amazon Q Developer 기능별 활성화/비활성화를 제어할 수 있습니다.

```bash
# 조직 수준의 Amazon Q 설정 확인
aws q list-profiles \
  --region us-east-1
```

### 효과적인 사용 팁

- 코드 자동 완성: 명확한 함수명과 주석을 작성하면 더 정확한 제안을 받을 수 있습니다.
- 채팅: `@workspace`를 사용하여 프로젝트 전체 컨텍스트를 제공합니다.
- /dev 에이전트: 태스크를 작고 구체적으로 분할하면 더 정확한 결과를 얻습니다.
- Transform: 변환 전에 충분한 테스트 커버리지를 확보합니다.

### 비용 구조

| 계층 | 가격 | 주요 기능 |
|------|------|----------|
| Free | 무료 | 코드 자동 완성, 채팅, 보안 스캔 (월 제한) |
| Pro | $19/월/사용자 | 무제한 코드 제안, /dev 에이전트, /transform, 고급 보안 스캔 |

---

## 관련 서비스 비교

| 항목 | Amazon Q Developer | GitHub Copilot | Cursor | Cline |
|------|-------------------|----------------|--------|-------|
| 코드 자동 완성 | 지원 | 지원 | 지원 | 미지원 |
| 채팅 | 지원 | 지원 | 지원 | 지원 |
| 자율 에이전트 | /dev | Copilot Workspace | Composer | 기본 지원 |
| 코드 변환 | Transform (Java, .NET) | 미지원 | 미지원 | 미지원 |
| 보안 스캔 | 내장 | 별도 (Advanced Security) | 미지원 | 미지원 |
| AWS 통합 | 네이티브 (콘솔, CLI, IaC) | 미지원 | 미지원 | 미지원 |
| CLI 지원 | 자연어 -> CLI 변환 | CLI 미지원 | 미지원 | 미지원 |
| 데이터 프라이버시 | Pro 계층: 학습 미사용 | Business 계층: 학습 미사용 | 요청 시 | 로컬 전용 옵션 |
| 가격 | 무료/Pro $19 | 개인 $10/Business $19 | Pro $20 | 무료 (토큰 비용 별도) |

---

## 요약

Amazon Q Developer는 소프트웨어 개발 전체 생명주기를 지원하는 포괄적인 AI 개발 도우미입니다. 주요 특징을 정리하면 다음과 같습니다.

- IDE(VS Code, JetBrains 등)에서 실시간 코드 자동 완성과 채팅 기반 개발 지원을 제공합니다.
- /dev 에이전트를 통해 자연어 태스크 설명만으로 자율적으로 코드를 작성하고 테스트합니다.
- /transform을 통해 Java 8에서 17로의 업그레이드, .NET Framework에서 .NET Core로의 마이그레이션 등 대규모 코드 변환을 자동화합니다.
- 내장 보안 스캔으로 SQL 인젝션, XSS, 하드코딩된 시크릿 등 보안 취약점을 실시간으로 감지합니다.
- AWS 콘솔과 CLI에서 자연어로 AWS 서비스 질문, 트러블슈팅, 인프라 관리를 수행합니다.
- Professional 계층에서는 사용자 코드가 모델 학습에 사용되지 않아 데이터 프라이버시가 보장됩니다.

Amazon Q Developer는 특히 AWS 환경에서 개발하는 팀에게 코드 작성부터 인프라 관리까지 전방위적인 AI 지원을 제공하는 최적의 도구입니다.