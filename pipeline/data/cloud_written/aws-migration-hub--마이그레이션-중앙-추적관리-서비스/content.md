## 개요

AWS Migration Hub는 AWS로의 마이그레이션 프로젝트를 계획, 추적, 관리할 수 있는 중앙 집중식 서비스입니다. 마이그레이션은 복잡하고 장기적인 프로젝트이며, 수십에서 수천 대의 서버와 데이터베이스를 이동해야 하는 경우가 많습니다. Migration Hub는 이러한 대규모 마이그레이션의 전체 과정을 하나의 대시보드에서 관리할 수 있게 해줍니다.

Migration Hub 자체는 무료 서비스이며, 추가 비용 없이 AWS의 마이그레이션 도구들과 서드파티 마이그레이션 도구의 진행 상황을 통합 추적할 수 있습니다.

### 마이그레이션 프로젝트의 과제

대규모 마이그레이션 프로젝트에서 흔히 직면하는 과제들은 다음과 같습니다.

- 온프레미스 인프라의 전체 목록과 종속성 파악이 어렵습니다.
- 여러 마이그레이션 도구를 동시에 사용하면 진행 상황 추적이 복잡해집니다.
- 애플리케이션 단위의 마이그레이션 상태를 파악하기 어렵습니다.
- 마이그레이션 전략(Rehost, Replatform, Refactor 등) 결정에 필요한 데이터가 부족합니다.

Migration Hub는 이러한 과제를 해결하기 위해 디스커버리(Discovery), 마이그레이션 추적(Migration Tracking), 리팩토링 권장(Refactor Spaces) 기능을 제공합니다.

## 핵심 기능

### 1. Discover (검색)

Migration Hub의 디스커버리 기능은 AWS Application Discovery Service와 통합되어 온프레미스 인프라를 자동으로 스캔하고 인벤토리를 생성합니다.

**에이전트 기반 검색 (AWS Application Discovery Agent)**
- 각 서버에 에이전트를 설치하여 상세한 정보를 수집합니다.
- CPU, 메모리, 디스크, 네트워크 사용량 등 성능 데이터를 수집합니다.
- 프로세스 정보와 네트워크 연결 정보를 통해 서버 간 종속성을 자동으로 매핑합니다.

**에이전트리스 검색 (Agentless Collector)**
- VMware vCenter에 연결하여 VM 인벤토리를 수집합니다.
- 에이전트 설치 없이 기본적인 서버 정보를 수집합니다.
- 빠른 초기 평가에 적합합니다.

```bash
# Application Discovery Service 에이전트 목록 확인
aws discovery describe-agents \
  --query 'agentsInfo[*].{AgentId:agentId,HostName:hostName,Health:health,CollectionStatus:collectionStatus}' \
  --output table \
  --region us-west-2

# 데이터 수집 시작
aws discovery start-data-collection-by-agent-ids \
  --agent-ids "agent-001" "agent-002" "agent-003" \
  --region us-west-2

# 검색된 서버 목록 조회
aws discovery describe-configurations \
  --configuration-ids "d-server-001" "d-server-002" \
  --region us-west-2

# 서버 인벤토리 내보내기
aws discovery start-export-task \
  --export-data-format CSV \
  --region us-west-2
```

### 2. Migrate (마이그레이션)

Migration Hub는 다양한 마이그레이션 도구의 진행 상황을 통합 추적합니다.

**지원하는 AWS 마이그레이션 도구**
- AWS Application Migration Service (MGN): 서버 마이그레이션 (Rehost)
- AWS Database Migration Service (DMS): 데이터베이스 마이그레이션
- AWS DataSync: 데이터 전송
- AWS Server Migration Service (SMS): 레거시 서버 마이그레이션

**지원하는 서드파티 도구**
- CloudEndure Migration
- ATADATA
- Racemi
- RiverMeadow
- Turbonomic

```bash
# Migration Hub 홈 리전 설정 (최초 1회)
aws migrationhub-config create-home-region-control \
  --home-region "ap-northeast-2" \
  --target '{"Type":"ACCOUNT"}'

# 마이그레이션 태스크 상태 조회
aws mgh list-migration-tasks \
  --query 'MigrationTaskSummaryList[*].{Task:MigrationTaskName,Status:Status,Progress:ProgressPercent,UpdateTime:UpdateDateTime}' \
  --output table \
  --region ap-northeast-2

# 특정 마이그레이션 태스크 상세 정보
aws mgh describe-migration-task \
  --progress-update-stream "AWS-ApplicationMigrationService" \
  --migration-task-name "server-migration-001" \
  --region ap-northeast-2
```

### 3. Migration Hub Strategy Recommendations

Strategy Recommendations는 온프레미스 애플리케이션에 대해 최적의 마이그레이션 전략을 권장하는 기능입니다.

**7R 마이그레이션 전략**

| 전략 | 설명 | 사용 사례 |
|------|------|----------|
| Rehost | 있는 그대로 클라우드로 이전 (Lift & Shift) | 빠른 마이그레이션이 필요한 경우 |
| Replatform | 일부 최적화 후 이전 (Lift & Reshape) | 관리형 서비스 활용 시 |
| Refactor | 아키텍처를 재설계하여 이전 | 클라우드 네이티브 전환 시 |
| Repurchase | SaaS 제품으로 대체 | CRM, ERP 등 상용 솔루션 |
| Retire | 사용 중단 | 더 이상 필요 없는 시스템 |
| Retain | 현재 상태 유지 | 마이그레이션 불가 또는 불필요 |
| Relocate | VMware Cloud on AWS로 이전 | VMware 환경 유지 시 |

```bash
# Strategy Recommendations 수집기 배포 후 분석 시작
aws migrationhubstrategy start-assessment \
  --region us-east-1

# 서버별 권장 전략 조회
aws migrationhubstrategy list-servers \
  --query 'serverInfos[*].{Name:name,Strategy:recommendedStrategy,AntipatternCount:antipatternReportStatusMessage}' \
  --output table \
  --region us-east-1

# 애플리케이션별 권장 전략 조회
aws migrationhubstrategy list-application-components \
  --query 'applicationComponentInfos[*].{Name:name,AppType:appType,Strategy:recommendedStrategy}' \
  --output table \
  --region us-east-1
```

### 4. Migration Hub Refactor Spaces

Refactor Spaces는 점진적인 애플리케이션 리팩토링을 지원하는 기능입니다. Strangler Fig 패턴을 쉽게 구현할 수 있도록 API Gateway와 Lambda 기반의 라우팅 인프라를 자동으로 구성합니다.

```bash
# Refactor Spaces 환경 생성
aws migration-hub-refactor-spaces create-environment \
  --name "app-modernization" \
  --network-fabric-type TRANSIT_GATEWAY \
  --region ap-northeast-2

# 애플리케이션 생성 (라우팅 프록시)
aws migration-hub-refactor-spaces create-application \
  --environment-identifier "env-abc123" \
  --name "legacy-app-proxy" \
  --proxy-type API_GATEWAY \
  --vpc-id "vpc-abc123" \
  --region ap-northeast-2

# 서비스 라우트 생성 (레거시 → 신규 서비스)
aws migration-hub-refactor-spaces create-route \
  --application-identifier "app-abc123" \
  --environment-identifier "env-abc123" \
  --service-identifier "svc-newservice" \
  --route-type URI_PATH \
  --uri-path-route '{"sourcePath":"/api/orders","activationState":"ACTIVE","methods":["GET","POST"]}' \
  --region ap-northeast-2
```

## 아키텍처/동작 원리

### Migration Hub 통합 아키텍처

```
┌─────────────────────────────────────────────────┐
│               Migration Hub Console              │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ Discover │  │ Migrate  │  │   Strategy    │  │
│  │          │  │          │  │ Recommendations│  │
│  └────┬─────┘  └────┬─────┘  └───────┬───────┘  │
└───────┼─────────────┼────────────────┼───────────┘
        │             │                │
        ▼             ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌────────────────┐
│ Application  │ │ AWS MGN      │ │ Strategy       │
│ Discovery    │ │ (App         │ │ Recommendations│
│ Service      │ │ Migration)   │ │ Collector      │
├──────────────┤ ├──────────────┤ └────────────────┘
│ Discovery    │ │ AWS DMS      │
│ Agent        │ │ (Database    │
│              │ │ Migration)   │
│ Agentless    │ ├──────────────┤
│ Collector    │ │ AWS DataSync │
│              │ │ (Data        │
│              │ │ Transfer)    │
└──────────────┘ └──────────────┘

온프레미스 환경                    AWS 클라우드
┌──────────────┐              ┌──────────────┐
│ 물리 서버    │              │ EC2          │
│ VM (VMware)  │  ────────►   │ RDS          │
│ 데이터베이스 │              │ S3           │
│ 애플리케이션 │              │ ECS/EKS      │
└──────────────┘              └──────────────┘
```

### 마이그레이션 워크플로우

대규모 마이그레이션 프로젝트의 일반적인 워크플로우는 다음과 같습니다.

```
Phase 1: Assessment (평가)
├── Application Discovery Service로 인벤토리 수집
├── 서버 간 종속성 매핑
├── Strategy Recommendations로 마이그레이션 전략 분석
└── 마이그레이션 웨이브(Wave) 계획 수립

Phase 2: Mobilize (준비)
├── Migration Hub에 애플리케이션 그룹 정의
├── 마이그레이션 도구 선택 및 구성
├── 네트워크 연결 설정 (Direct Connect/VPN)
└── 파일럿 마이그레이션 실행

Phase 3: Migrate & Modernize (실행)
├── 웨이브별 서버 마이그레이션 (MGN)
├── 데이터베이스 마이그레이션 (DMS)
├── 데이터 전송 (DataSync)
├── Migration Hub에서 진행 상황 추적
└── 테스트 및 검증

Phase 4: Operate & Optimize (운영)
├── 마이그레이션 완료 확인
├── 온프레미스 리소스 폐기
├── 클라우드 최적화 (비용, 성능)
└── Refactor Spaces로 점진적 현대화
```

### 애플리케이션 그룹핑

Migration Hub에서는 서버와 데이터베이스를 애플리케이션 단위로 그룹화하여 관리합니다. 이를 통해 서버 단위가 아닌 애플리케이션 단위의 마이그레이션 상태를 추적할 수 있습니다.

```bash
# 애플리케이션 생성 (서버 그룹핑)
aws discovery create-application \
  --name "E-Commerce Platform" \
  --description "Web servers, app servers, and database for e-commerce" \
  --region us-west-2

# 서버를 애플리케이션에 할당
aws discovery associate-configuration-items-to-application \
  --application-configuration-id "app-001" \
  --configuration-ids "d-server-web01" "d-server-web02" "d-server-app01" "d-server-db01" \
  --region us-west-2
```

## 실전 활용

### 대규모 마이그레이션 프로젝트 설정

500대 이상의 서버를 AWS로 마이그레이션하는 프로젝트의 초기 설정 예시입니다.

```bash
# 1. Migration Hub 홈 리전 설정
aws migrationhub-config create-home-region-control \
  --home-region "ap-northeast-2" \
  --target '{"Type":"ACCOUNT"}'

# 2. Discovery Agent 설치 후 수집 시작
aws discovery start-data-collection-by-agent-ids \
  --agent-ids $(aws discovery describe-agents \
    --query 'agentsInfo[?health==`HEALTHY`].agentId' \
    --output text \
    --region us-west-2) \
  --region us-west-2

# 3. 2주간 데이터 수집 후 인벤토리 내보내기
aws discovery start-export-task \
  --export-data-format CSV \
  --filters '[{"name":"agentIds","values":["*"],"condition":"CONTAINS"}]' \
  --region us-west-2

# 4. 내보내기 상태 확인
aws discovery describe-export-tasks \
  --query 'exportsInfo[*].{ExportId:exportId,Status:exportStatus,URL:configurationsDownloadUrl}' \
  --output table \
  --region us-west-2
```

### 웨이브 기반 마이그레이션 추적

마이그레이션을 웨이브(그룹) 단위로 나누어 순차적으로 진행하는 방법입니다.

```bash
# 웨이브별 애플리케이션 태깅
aws discovery create-tags \
  --configuration-ids "app-ecommerce" \
  --tags '[{"key":"MigrationWave","value":"Wave-1"},{"key":"MigrationPriority","value":"High"}]' \
  --region us-west-2

# 웨이브별 마이그레이션 상태 조회 (태그 기반 필터링)
aws mgh list-migration-tasks \
  --resource-attribute-list '[{"Type":"MIGRATION_WAVE","Value":"Wave-1"}]' \
  --region ap-northeast-2
```

### Application Migration Service (MGN)와 연동

MGN은 서버 마이그레이션의 핵심 도구이며, Migration Hub와 자동으로 통합됩니다.

```bash
# MGN 복제 시작
aws mgn start-replication \
  --source-server-id "s-abc123" \
  --region ap-northeast-2

# MGN 소스 서버 상태 확인
aws mgn describe-source-servers \
  --filters '{"isArchived":false}' \
  --query 'items[*].{ServerID:sourceServerID,Hostname:sourceProperties.identificationHints.hostname,State:lifeCycle.state,ReplicationState:dataReplicationInfo.dataReplicationState}' \
  --output table \
  --region ap-northeast-2

# 테스트 인스턴스 시작
aws mgn start-test \
  --source-server-ids "s-abc123" "s-def456" \
  --region ap-northeast-2

# 컷오버 실행
aws mgn start-cutover \
  --source-server-ids "s-abc123" "s-def456" \
  --region ap-northeast-2
```

### 마이그레이션 진행률 보고서 생성

마이그레이션 진행 상황을 정기적으로 보고하기 위한 스크립트 예시입니다.

```python
import boto3
import json
from datetime import datetime

def generate_migration_report():
    """마이그레이션 진행률 보고서 생성"""
    mgh_client = boto3.client('mgh', region_name='ap-northeast-2')
    
    # 전체 마이그레이션 태스크 조회
    tasks = mgh_client.list_migration_tasks()
    
    status_count = {
        'NOT_STARTED': 0,
        'IN_PROGRESS': 0,
        'COMPLETED': 0,
        'FAILED': 0
    }
    
    for task in tasks.get('MigrationTaskSummaryList', []):
        status = task.get('Status', 'NOT_STARTED')
        if status in status_count:
            status_count[status] += 1
    
    total = sum(status_count.values())
    completed_pct = (status_count['COMPLETED'] / total * 100) if total > 0 else 0
    
    report = {
        'report_date': datetime.now().isoformat(),
        'total_tasks': total,
        'status_breakdown': status_count,
        'completion_percentage': round(completed_pct, 1),
        'summary': f"Total: {total}, Completed: {status_count['COMPLETED']} ({completed_pct:.1f}%), In Progress: {status_count['IN_PROGRESS']}, Failed: {status_count['FAILED']}"
    }
    
    return report

if __name__ == '__main__':
    report = generate_migration_report()
    print(json.dumps(report, indent=2))
```

## 모범 사례/보안

### 마이그레이션 계획 모범 사례

1. **충분한 디스커버리 기간을 확보하십시오.** 최소 2-4주간 Discovery Agent를 실행하여 성능 데이터와 종속성 정보를 수집해야 합니다. 짧은 수집 기간은 피크 타임이나 배치 작업을 놓칠 수 있습니다.

2. **애플리케이션 단위로 그룹화하십시오.** 서버 단위가 아닌 애플리케이션 단위로 마이그레이션을 계획해야 합니다. 종속성이 있는 서버들은 반드시 같은 웨이브에서 마이그레이션해야 합니다.

3. **웨이브 전략을 수립하십시오.** 우선순위, 종속성, 비즈니스 영향도를 고려하여 마이그레이션 웨이브를 계획합니다. 일반적으로 비중요 시스템부터 시작하여 경험을 축적한 후 중요 시스템을 마이그레이션합니다.

4. **롤백 계획을 수립하십시오.** 각 웨이브별로 롤백 절차를 사전에 정의하고 테스트해야 합니다.

### 보안 모범 사례

- Discovery Agent가 수집하는 데이터는 전송 중 암호화됩니다. 추가로 저장 시 암호화도 적용됩니다.
- Migration Hub에 대한 IAM 권한을 마이그레이션 팀으로 제한하십시오.
- 마이그레이션 중 데이터 전송은 Direct Connect 또는 VPN을 통해 수행하십시오.
- 소스 서버의 자격 증명 정보가 마이그레이션 과정에서 노출되지 않도록 주의하십시오.

```bash
# Migration Hub 접근을 위한 IAM 정책 예시
aws iam create-policy \
  --policy-name "MigrationHubReadAccess" \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "mgh:ListMigrationTasks",
          "mgh:DescribeMigrationTask",
          "mgh:ListProgressUpdateStreams",
          "discovery:DescribeConfigurations",
          "discovery:ListConfigurations"
        ],
        "Resource": "*"
      }
    ]
  }'
```

### 비용 관련 고려사항

- Migration Hub 자체는 무료입니다.
- Application Discovery Service의 에이전트 기반 검색은 에이전트당 월별 요금이 발생합니다.
- MGN, DMS 등 실제 마이그레이션 도구는 각 서비스의 요금 체계에 따라 과금됩니다.
- 마이그레이션 기간 동안 온프레미스와 AWS 양쪽에서 리소스가 동시에 운영될 수 있으므로, 이중 비용을 예산에 반영해야 합니다.

## 관련 서비스 비교

### Migration Hub vs 개별 마이그레이션 도구

| 항목 | Migration Hub | 개별 도구 (MGN, DMS 등) |
|------|--------------|------------------------|
| 역할 | 전체 프로젝트 추적/관리 | 실제 마이그레이션 실행 |
| 범위 | 모든 마이그레이션 도구 통합 | 특정 워크로드 유형 |
| 비용 | 무료 | 서비스별 과금 |
| 디스커버리 | Application Discovery Service 통합 | 해당 없음 |
| 전략 권장 | Strategy Recommendations | 해당 없음 |

### AWS 마이그레이션 도구 비교

| 도구 | 용도 | 지원 워크로드 |
|------|------|-------------|
| Application Migration Service (MGN) | 서버 마이그레이션 (Rehost) | 물리/가상 서버 |
| Database Migration Service (DMS) | 데이터베이스 마이그레이션 | 관계형/NoSQL DB |
| DataSync | 데이터 전송 | 파일/객체 스토리지 |
| Transfer Family | 파일 전송 프로토콜 | SFTP/FTPS/FTP |
| Snow Family | 오프라인 대용량 전송 | 모든 데이터 |
| Migration Hub Refactor Spaces | 애플리케이션 현대화 | 마이크로서비스 전환 |

## 요약

AWS Migration Hub는 대규모 마이그레이션 프로젝트의 중앙 관제탑 역할을 하는 서비스입니다.

핵심 포인트를 정리하면 다음과 같습니다.

- **중앙 집중 추적**: 여러 마이그레이션 도구의 진행 상황을 하나의 대시보드에서 추적합니다.
- **디스커버리**: Application Discovery Service와 통합하여 온프레미스 인벤토리를 자동으로 수집하고 종속성을 매핑합니다.
- **전략 권장**: Strategy Recommendations로 애플리케이션별 최적의 마이그레이션 전략(7R)을 제안합니다.
- **Refactor Spaces**: Strangler Fig 패턴을 활용한 점진적 애플리케이션 현대화를 지원합니다.
- **무료 서비스**: Migration Hub 자체는 추가 비용 없이 사용할 수 있습니다.
- **통합 생태계**: AWS 마이그레이션 도구뿐 아니라 서드파티 도구와도 통합됩니다.

마이그레이션 프로젝트의 성공은 계획과 추적에 달려 있습니다. Migration Hub를 활용하면 복잡한 마이그레이션 프로젝트를 체계적으로 관리하고, 전체 진행 상황을 투명하게 파악할 수 있습니다.