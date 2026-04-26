<!-- infographic-hero -->
![AWS Application Discovery Service(ADS) 개요 및 활용: 마이그레이션을 위한 온프레미스 인프라 탐색 핵심 요약](figures/infographic.svg)

*Figure: AWS Application Discovery Service(ADS) 개요 및 활용: 마이그레이션을 위한 온프레미스 인프라 탐색 한 장 요약 인포그래픽*

## 개요

AWS Application Discovery Service(ADS)는 온프레미스 데이터센터의 IT 인프라 정보를 자동으로 수집하고 분석하여, AWS 클라우드 마이그레이션 계획을 수립하는 데 필요한 인사이트를 제공하는 서비스입니다.

클라우드 마이그레이션의 첫 번째 단계는 현재 인프라를 정확히 이해하는 것입니다. 기업의 데이터센터에는 수백에서 수천 대의 서버가 운영되고 있으며, 이들 간의 네트워크 통신 패턴, 종속성(dependency), 리소스 사용률 등을 파악하는 것은 매우 어렵고 시간이 많이 소요되는 작업입니다. 수동으로 스프레드시트를 만들어 관리하는 경우가 대부분이지만, 이 정보는 금방 구식이 되고 정확성을 보장하기 어렵습니다.

Application Discovery Service는 이 문제를 해결합니다. 에이전트 기반 또는 에이전트리스 방식으로 서버 정보를 자동 수집하고, 서버 간 네트워크 연결을 분석하여 애플리케이션 그룹을 식별합니다. 수집된 데이터는 AWS Migration Hub에서 중앙 집중적으로 관리되며, 마이그레이션 계획 수립, TCO(Total Cost of Ownership) 분석, 마이그레이션 우선순위 결정에 활용됩니다.

ADS는 AWS 마이그레이션 프레임워크의 "Discover" 단계에서 핵심적인 역할을 수행하며, Migration Hub, Application Migration Service(MGN), Database Migration Service(DMS) 등 AWS 마이그레이션 도구 생태계와 긴밀하게 통합됩니다.

## 핵심 기능

### 데이터 수집 방식

ADS는 두 가지 데이터 수집 방식을 제공합니다.

**1. 에이전트리스 수집 (Agentless Collector)**

VMware vCenter 환경에서 에이전트 설치 없이 VM 정보를 수집합니다. OVA(Open Virtual Appliance) 파일을 vCenter에 배포하여 동작합니다.

수집 정보:
- VM 구성 정보 (CPU, 메모리, 디스크, OS)
- 리소스 사용률 (CPU, 메모리, 디스크 I/O)
- VM 이름, IP 주소, MAC 주소
- 데이터 저장소 정보

제한 사항:
- VMware 환경에서만 동작합니다.
- 네트워크 연결(종속성) 정보는 수집하지 않습니다.
- 프로세스 정보는 수집하지 않습니다.

**2. 에이전트 기반 수집 (Discovery Agent)**

각 서버에 AWS Discovery Agent를 설치하여 상세한 정보를 수집합니다. Windows와 Linux를 모두 지원합니다.

수집 정보:
- 시스템 구성 (CPU, 메모리, 디스크, OS, 커널 버전)
- 리소스 사용률 (CPU, 메모리, 디스크, 네트워크)
- 실행 중인 프로세스 정보
- **네트워크 연결(TCP 연결) 정보** -- 종속성 분석에 핵심
- 시스템 성능 데이터 (시계열)

### Migration Hub 통합

수집된 모든 데이터는 AWS Migration Hub에 자동으로 전송됩니다. Migration Hub에서 다음 작업을 수행할 수 있습니다.

- 검색된 서버 목록 조회 및 필터링
- 애플리케이션 그룹 정의 (관련 서버들을 하나의 애플리케이션으로 묶기)
- 마이그레이션 전략 선택 (Rehost, Replatform, Refactor 등)
- 마이그레이션 진행 상태 추적

### Athena 통합

ADS가 수집한 원시 데이터를 Amazon Athena에서 SQL로 직접 쿼리할 수 있습니다. 이를 통해 커스텀 분석과 리포트 생성이 가능합니다.

## 아키텍처/동작 원리

### 에이전트리스 수집 아키텍처

1. Agentless Collector OVA를 VMware vCenter에 배포합니다.
2. Collector가 vCenter API를 통해 VM 정보를 수집합니다.
3. 수집된 데이터는 TLS로 암호화되어 ADS 서비스로 전송됩니다.
4. 데이터는 Migration Hub에서 조회할 수 있습니다.

```bash
# ADS 데이터 수집 시작 (에이전트리스)
aws discovery start-data-collection-by-agent-ids \
  --agent-ids agent-001 agent-002 agent-003

# 수집된 서버 목록 조회
aws discovery describe-agents \
  --query 'agentsInfo[*].{AgentId:agentId,HostName:hostName,Health:health,CollectionStatus:collectionStatus}' \
  --output table
```

### 에이전트 기반 수집 아키텍처

1. 각 서버에 Discovery Agent를 설치합니다.
2. Agent가 서버의 시스템 정보, 프로세스 정보, 네트워크 연결 정보를 수집합니다.
3. 수집된 데이터는 TLS로 암호화되어 ADS 서비스로 전송됩니다.
4. ADS는 네트워크 연결 데이터를 분석하여 서버 간 종속성 맵을 생성합니다.

```bash
# Discovery Agent 설치 (Linux)
# 1. 에이전트 다운로드
curl -o ./aws-discovery-agent.tar.gz \
  https://s3-us-west-2.amazonaws.com/aws-discovery-agent.us-west-2/linux/latest/aws-discovery-agent.tar.gz

# 2. 설치 실행
sudo bash install -r ap-northeast-2 -k <ACCESS_KEY_ID> -s <SECRET_ACCESS_KEY>
```

```bash
# Discovery Agent 상태 확인
aws discovery describe-agents \
  --filters '[{"name": "hostName", "values": ["web-server-01"], "condition": "EQUALS"}]'
```

### 데이터 수집 및 분석 프로세스

```bash
# 검색된 서버 목록 조회
aws discovery list-configurations \
  --configuration-type SERVER \
  --max-results 25

# 특정 서버의 상세 정보 조회
aws discovery describe-configurations \
  --configuration-ids d-server-01234567890abcdef
```

```bash
# 서버 간 네트워크 연결(종속성) 조회
aws discovery list-configurations \
  --configuration-type CONNECTION \
  --filters '[{"name": "sourceServerId", "values": ["d-server-01234567890abcdef"], "condition": "EQUALS"}]'
```

### 데이터 내보내기 및 분석

```bash
# 수집 데이터 내보내기 (S3로)
aws discovery start-export-task \
  --export-data-format CSV

# 내보내기 상태 확인
aws discovery describe-export-tasks \
  --export-ids export-01234567890abcdef
```

내보내기된 CSV 파일은 다음 카테고리로 구분됩니다.

- `servers.csv`: 서버 구성 정보
- `processes.csv`: 실행 중인 프로세스
- `connections.csv`: 네트워크 연결 정보
- `performance.csv`: 성능 메트릭

## 실전 활용

### 사례 1: 마이그레이션 평가 (Migration Assessment)

대규모 마이그레이션 프로젝트에서 ADS를 활용한 전형적인 워크플로우입니다.

```bash
# 1단계: 모든 에이전트 상태 확인
aws discovery describe-agents \
  --query 'agentsInfo[?health==`HEALTHY`].{Host:hostName,Agent:agentId}' \
  --output table

# 2단계: 데이터 수집이 충분히 진행된 후 태그 기반 그룹핑
aws discovery create-tags \
  --configuration-ids d-server-01234567890abcdef d-server-0fedcba987654321 \
  --tags '[{"key": "Application", "value": "E-Commerce-Frontend"}]'

# 3단계: 태그로 서버 필터링
aws discovery list-configurations \
  --configuration-type SERVER \
  --filters '[{"name": "tag.Application", "values": ["E-Commerce-Frontend"], "condition": "EQUALS"}]'
```

### 사례 2: 종속성 매핑

에이전트 기반 수집을 통해 서버 간 네트워크 종속성을 파악할 수 있습니다. 이 정보는 마이그레이션 순서와 애플리케이션 그룹을 결정하는 데 핵심적입니다.

```python
import boto3
import json

def analyze_server_dependencies(server_id: str):
    """특정 서버의 네트워크 종속성을 분석합니다."""
    client = boto3.client('discovery')
    
    # 해당 서버에서 나가는 연결 조회
    outbound = client.list_configurations(
        configurationType='CONNECTION',
        filters=[{
            'name': 'sourceServerId',
            'values': [server_id],
            'condition': 'EQUALS'
        }]
    )
    
    # 해당 서버로 들어오는 연결 조회
    inbound = client.list_configurations(
        configurationType='CONNECTION',
        filters=[{
            'name': 'destinationServerId',
            'values': [server_id],
            'condition': 'EQUALS'
        }]
    )
    
    return {
        'server_id': server_id,
        'outbound_connections': outbound['configurations'],
        'inbound_connections': inbound['configurations'],
        'outbound_count': len(outbound['configurations']),
        'inbound_count': len(inbound['configurations'])
    }
```

### 사례 3: Athena를 활용한 커스텀 분석

```bash
# Athena 데이터 탐색 활성화
aws discovery start-continuous-export

# 탐색 상태 확인
aws discovery describe-continuous-exports
```

Athena에서 실행할 수 있는 분석 쿼리 예시입니다.

```sql
-- OS별 서버 수 집계
SELECT os_name, os_version, COUNT(*) as server_count
FROM application_discovery_service_database.os_info_agent
GROUP BY os_name, os_version
ORDER BY server_count DESC;

-- CPU/메모리 사용률이 높은 서버 식별
SELECT server_id, host_name,
       AVG(cpu_usage_pct) as avg_cpu,
       AVG(ram_usage_pct) as avg_memory
FROM application_discovery_service_database.sys_performance_agent
GROUP BY server_id, host_name
HAVING AVG(cpu_usage_pct) > 80 OR AVG(ram_usage_pct) > 80
ORDER BY avg_cpu DESC;
```

## 모범 사례/보안

### 보안 모범 사례

1. **최소 권한 원칙**: Discovery Agent에 부여하는 IAM 자격 증명은 ADS 관련 권한만 포함해야 합니다.
2. **데이터 암호화**: 전송 중(TLS) 및 저장 중 데이터가 암호화됩니다.
3. **네트워크 보안**: Agent와 ADS 서비스 간 통신에 필요한 아웃바운드 포트(443)만 허용합니다.
4. **자격 증명 관리**: Agent 설치 시 사용하는 IAM 자격 증명을 정기적으로 교체합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "discovery:ListConfigurations",
        "discovery:DescribeConfigurations",
        "discovery:DescribeAgents",
        "discovery:DescribeExportTasks",
        "discovery:StartExportTask"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "discovery:StartDataCollectionByAgentIds",
        "discovery:StopDataCollectionByAgentIds"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "ap-northeast-2"
        }
      }
    }
  ]
}
```

### 운영 모범 사례

1. **충분한 수집 기간**: 최소 2~4주간 데이터를 수집하여 워크로드 패턴을 정확히 파악합니다.
2. **에이전트 기반 우선**: 네트워크 종속성 정보가 필수적이므로, 가능하면 에이전트 기반 수집을 사용합니다.
3. **태그 활용**: 서버에 태그(Application, Environment, Team 등)를 부여하여 체계적으로 관리합니다.
4. **정기적 데이터 내보내기**: 수집된 데이터를 정기적으로 S3로 내보내어 백업하고 커스텀 분석에 활용합니다.
5. **Migration Hub 통합**: 수집된 데이터를 Migration Hub에서 중앙 관리하여 마이그레이션 계획을 수립합니다.

```bash
# 에이전트 상태 모니터링 알람 설정
aws cloudwatch put-metric-alarm \
  --alarm-name "unhealthy-discovery-agents" \
  --metric-name UnhealthyAgentCount \
  --namespace AWS/ApplicationDiscoveryService \
  --statistic Maximum \
  --period 3600 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:ap-northeast-2:123456789012:ops-alerts
```

## 관련 서비스 비교

| 항목 | Application Discovery Service | Migration Evaluator | CloudEndure (MGN) |
|------|------------------------------|--------------------|-----------------|
| 주요 목적 | 인프라 검색 및 종속성 매핑 | TCO/비용 분석 | 실제 마이그레이션 실행 |
| 수집 방식 | 에이전트/에이전트리스 | 에이전트 기반 | 에이전트 기반 |
| 네트워크 종속성 | 에이전트 방식에서 지원 | 미지원 | 미지원 |
| TCO 분석 | 제한적 | 상세 분석 | 미지원 |
| Migration Hub 통합 | 자동 통합 | 통합 | 자동 통합 |
| 비용 | 무료 | 무료 | 무료 (EC2 비용 별도) |
| 마이그레이션 단계 | Discover | Assess | Migrate |

AWS 마이그레이션 프레임워크에서 각 서비스의 역할은 명확하게 구분됩니다.

1. **ADS**: 현재 인프라를 탐색하고 종속성을 매핑합니다 (Discover).
2. **Migration Evaluator**: 마이그레이션 비용을 분석하고 비즈니스 케이스를 수립합니다 (Assess).
3. **MGN**: 실제 서버 마이그레이션을 수행합니다 (Migrate).

## 요약

AWS Application Discovery Service는 클라우드 마이그레이션의 첫 단계인 인프라 탐색을 자동화하는 서비스입니다. 핵심 포인트를 정리하면 다음과 같습니다.

- **자동화된 인프라 탐색**: 수동 스프레드시트 관리 대신, 자동으로 서버 정보와 종속성을 수집합니다.
- **두 가지 수집 방식**: 에이전트리스(VMware 환경)와 에이전트 기반(모든 환경)을 상황에 맞게 선택합니다.
- **네트워크 종속성 매핑**: 에이전트 기반 수집으로 서버 간 TCP 연결을 분석하여 애플리케이션 그룹을 식별합니다.
- **Migration Hub 통합**: 수집된 데이터를 중앙에서 관리하고 마이그레이션 진행 상태를 추적합니다.
- **Athena 통합**: SQL 쿼리를 통한 커스텀 분석이 가능합니다.
- **무료 서비스**: ADS 자체는 무료이며, 데이터 저장(S3, Athena)에 대한 비용만 발생합니다.

대규모 마이그레이션 프로젝트에서 ADS를 활용한 체계적인 인프라 탐색은 마이그레이션 리스크를 줄이고 계획의 정확도를 높이는 핵심 단계입니다.