<!-- infographic-hero -->
![AWS OpsWorks 개요 및 활용 가이드 핵심 요약](figures/infographic.svg)

*Figure: AWS OpsWorks 개요 및 활용 가이드 한 장 요약 인포그래픽*

## 개요

AWS OpsWorks는 Chef와 Puppet을 사용하여 서버 인프라의 구성(Configuration)을 자동으로 관리하는 서비스입니다. 서버에 설치할 소프트웨어, 구성 파일, 서비스 상태 등을 코드로 정의하고 자동으로 적용할 수 있습니다.

서버가 수십 대에서 수백 대로 늘어나면, 각 서버의 구성을 수동으로 관리하는 것은 사실상 불가능합니다. OpsWorks는 인프라를 코드(Infrastructure as Code)로 관리함으로써, 서버 구성의 일관성을 보장하고 변경 사항을 추적할 수 있게 합니다.

### OpsWorks 제품 라인

OpsWorks는 세 가지 제품으로 구성되어 있습니다.

**AWS OpsWorks Stacks**
- AWS가 자체 개발한 애플리케이션 관리 서비스입니다.
- Chef Solo를 기반으로 동작하며, Stack/Layer/Instance 모델로 인프라를 구성합니다.
- 참고: 2024년 5월 26일부로 신규 고객 온보딩이 중단되었습니다. 기존 사용자는 계속 사용할 수 있지만, 새로운 프로젝트에는 AWS Systems Manager나 다른 대안을 권장합니다.

**AWS OpsWorks for Chef Automate**
- 완전 관리형 Chef Automate 서버를 제공합니다.
- Chef Infra, Chef InSpec, Chef Habitat 등 Chef의 전체 기능을 사용할 수 있습니다.
- 참고: 이 서비스도 2024년에 신규 고객 온보딩이 종료되었습니다.

**AWS OpsWorks for Puppet Enterprise**
- 완전 관리형 Puppet Enterprise 서버를 제공합니다.
- Puppet의 모듈, 매니페스트 등을 사용하여 인프라를 관리합니다.
- 참고: 이 서비스도 2024년에 신규 고객 온보딩이 종료되었습니다.

현재 AWS는 구성 관리를 위해 AWS Systems Manager를 권장하고 있습니다. 그러나 기존에 OpsWorks를 사용 중인 환경이 많고, Chef/Puppet 자체는 여전히 업계에서 널리 사용되므로, OpsWorks의 개념과 아키텍처를 이해하는 것은 여전히 가치가 있습니다.

## 핵심 기능

### 1. OpsWorks Stacks

OpsWorks Stacks는 Stack, Layer, Instance, App의 4계층 모델로 인프라를 구성합니다.

**Stack (스택)**
- 최상위 컨테이너로, 하나의 애플리케이션 환경을 나타냅니다.
- VPC, 리전, 기본 운영체제 등의 설정을 포함합니다.

**Layer (레이어)**
- 동일한 역할을 수행하는 인스턴스 그룹입니다.
- 내장 레이어: Web Server(Apache/Nginx), App Server(Rails/PHP/Node.js), DB(MySQL), Custom
- 각 레이어에 Chef 레시피(Recipe)를 할당합니다.

**Instance (인스턴스)**
- 실제 EC2 인스턴스입니다.
- 24/7 인스턴스, 시간 기반 인스턴스, 로드 기반 인스턴스를 지원합니다.

**App (앱)**
- 배포할 애플리케이션 코드를 정의합니다.
- Git, SVN, S3, HTTP 등에서 코드를 가져올 수 있습니다.

```bash
# OpsWorks 스택 생성
aws opsworks create-stack \
  --name "production-stack" \
  --region us-east-1 \
  --stack-region ap-northeast-2 \
  --service-role-arn "arn:aws:iam::123456789012:role/aws-opsworks-service-role" \
  --default-instance-profile-arn "arn:aws:iam::123456789012:instance-profile/aws-opsworks-ec2-role" \
  --default-os "Amazon Linux 2" \
  --configuration-manager '{"Name":"Chef","Version":"12"}' \
  --use-custom-cookbooks \
  --custom-cookbooks-source '{"Type":"git","Url":"https://github.com/org/cookbooks.git"}'

# 레이어 생성
aws opsworks create-layer \
  --stack-id "stack-abc123" \
  --type "custom" \
  --name "Web Server Layer" \
  --shortname "web" \
  --custom-recipes '{"Setup":["web::setup"],"Configure":["web::configure"],"Deploy":["web::deploy"],"Undeploy":["web::undeploy"],"Shutdown":["web::shutdown"]}' \
  --auto-assign-elastic-ips true \
  --auto-assign-public-ips true

# 인스턴스 생성
aws opsworks create-instance \
  --stack-id "stack-abc123" \
  --layer-ids "layer-web123" \
  --instance-type "t3.medium" \
  --hostname "web-01" \
  --auto-scaling-type "load"

# 인스턴스 시작
aws opsworks start-instance \
  --instance-id "instance-abc123"
```

### 2. OpsWorks 라이프사이클 이벤트

OpsWorks Stacks는 다섯 가지 라이프사이클 이벤트를 통해 Chef 레시피를 실행합니다.

| 이벤트 | 발생 시점 | 용도 |
|--------|----------|------|
| Setup | 인스턴스 부팅 완료 후 | 초기 소프트웨어 설치 및 구성 |
| Configure | 인스턴스 추가/삭제/상태 변경 시 | 전체 인스턴스의 구성 업데이트 |
| Deploy | 앱 배포 명령 실행 시 | 애플리케이션 코드 배포 |
| Undeploy | 앱 제거 명령 실행 시 | 애플리케이션 정리 |
| Shutdown | 인스턴스 종료 전 | 정리 작업 수행 |

```bash
# 수동으로 Chef 레시피 실행 (Execute Recipes)
aws opsworks create-deployment \
  --stack-id "stack-abc123" \
  --command '{"Name":"execute_recipes","Args":{"recipes":["nginx::restart","app::configure"]}}' \
  --instance-ids "instance-abc123" "instance-def456"

# 앱 배포
aws opsworks create-deployment \
  --stack-id "stack-abc123" \
  --app-id "app-abc123" \
  --command '{"Name":"deploy"}' \
  --comment "Release v2.1.0"

# 배포 상태 확인
aws opsworks describe-deployments \
  --deployment-ids "deployment-abc123" \
  --query 'Deployments[*].{Id:DeploymentId,Status:Status,Command:Command.Name,CreatedAt:CreatedAt}' \
  --output table
```

### 3. OpsWorks for Chef Automate

Chef Automate 서버를 완전 관리형으로 제공합니다. Chef Automate는 Chef Infra(구성 관리), Chef InSpec(규정 준수 검사), Chef Habitat(애플리케이션 자동화)를 통합한 플랫폼입니다.

```bash
# Chef Automate 서버 생성
aws opsworks-cm create-server \
  --server-name "chef-automate-prod" \
  --engine "ChefAutomate" \
  --engine-model "Single" \
  --engine-version "2" \
  --instance-profile-arn "arn:aws:iam::123456789012:instance-profile/aws-opsworks-cm-ec2-role" \
  --instance-type "m5.large" \
  --service-role-arn "arn:aws:iam::123456789012:role/aws-opsworks-cm-service-role" \
  --subnet-ids "subnet-abc123" \
  --preferred-backup-window "03:00" \
  --preferred-maintenance-window "Mon:08:00" \
  --region ap-northeast-2

# 서버 상태 확인
aws opsworks-cm describe-servers \
  --query 'Servers[*].{Name:ServerName,Status:Status,Endpoint:Endpoint,Engine:Engine}' \
  --output table \
  --region ap-northeast-2

# 노드(관리 대상 서버) 목록 조회
aws opsworks-cm describe-node-association-status \
  --server-name "chef-automate-prod" \
  --node-association-status-token "token-abc123" \
  --region ap-northeast-2
```

### 4. OpsWorks for Puppet Enterprise

Puppet Enterprise 서버를 완전 관리형으로 제공합니다.

```bash
# Puppet Enterprise 서버 생성
aws opsworks-cm create-server \
  --server-name "puppet-enterprise-prod" \
  --engine "Puppet" \
  --engine-model "Monolithic" \
  --engine-version "2019" \
  --instance-profile-arn "arn:aws:iam::123456789012:instance-profile/aws-opsworks-cm-ec2-role" \
  --instance-type "m5.xlarge" \
  --service-role-arn "arn:aws:iam::123456789012:role/aws-opsworks-cm-service-role" \
  --subnet-ids "subnet-abc123" \
  --region ap-northeast-2

# 서버 백업 생성
aws opsworks-cm create-backup \
  --server-name "puppet-enterprise-prod" \
  --description "Pre-upgrade backup" \
  --region ap-northeast-2

# 백업 목록 조회
aws opsworks-cm describe-backups \
  --server-name "puppet-enterprise-prod" \
  --query 'Backups[*].{BackupId:BackupId,Status:Status,CreatedAt:CreatedAt,Description:Description}' \
  --output table \
  --region ap-northeast-2
```

## 아키텍처/동작 원리

### OpsWorks Stacks 아키텍처

```
AWS OpsWorks Service
    │
    ▼
┌──────────────────────────────────────┐
│           Stack (Production)          │
│                                      │
│  ┌─────────────────────────────────┐ │
│  │ Web Layer (Nginx)               │ │
│  │  ┌──────┐ ┌──────┐ ┌──────┐   │ │
│  │  │web-01│ │web-02│ │web-03│   │ │
│  │  └──────┘ └──────┘ └──────┘   │ │
│  │  Chef Recipes: nginx::setup    │ │
│  └─────────────────────────────────┘ │
│                                      │
│  ┌─────────────────────────────────┐ │
│  │ App Layer (Rails)               │ │
│  │  ┌──────┐ ┌──────┐             │ │
│  │  │app-01│ │app-02│             │ │
│  │  └──────┘ └──────┘             │ │
│  │  Chef Recipes: rails::setup    │ │
│  └─────────────────────────────────┘ │
│                                      │
│  ┌─────────────────────────────────┐ │
│  │ DB Layer (MySQL)                │ │
│  │  ┌──────┐                      │ │
│  │  │db-01 │                      │ │
│  │  └──────┘                      │ │
│  │  Chef Recipes: mysql::setup    │ │
│  └─────────────────────────────────┘ │
│                                      │
│  App: my-rails-app (Git repo)       │
│  Custom Cookbooks: GitHub repo      │
└──────────────────────────────────────┘
```

### Chef 레시피 동작 원리

Chef는 "원하는 상태(Desired State)"를 코드로 선언하고, 시스템을 해당 상태로 수렴(Converge)시킵니다.

```bash
# Chef 레시피 예시 (Ruby DSL) - web::setup
# cookbooks/web/recipes/setup.rb

# Nginx 패키지 설치
package 'nginx' do
  action :install
end

# Nginx 설정 파일 배포
template '/etc/nginx/nginx.conf' do
  source 'nginx.conf.erb'
  owner 'root'
  group 'root'
  mode '0644'
  variables(
    worker_processes: node['cpu']['total'],
    worker_connections: 1024
  )
  notifies :restart, 'service[nginx]'
end

# Nginx 서비스 활성화 및 시작
service 'nginx' do
  action [:enable, :start]
  supports restart: true, reload: true, status: true
end

# 로그 디렉토리 생성
directory '/var/log/nginx/app' do
  owner 'www-data'
  group 'www-data'
  mode '0755'
  recursive true
end
```

### OpsWorks Stacks 자동 스케일링

OpsWorks Stacks는 두 가지 자동 스케일링 방식을 제공합니다.

**시간 기반 스케일링**
- 정해진 시간에 인스턴스를 자동으로 시작/종료합니다.
- 예: 업무 시간(9시-18시)에만 개발 서버를 운영합니다.

**로드 기반 스케일링**
- CPU, 메모리, 로드 평균 등의 메트릭에 따라 인스턴스를 자동으로 추가/제거합니다.
- CloudWatch 메트릭과 연동됩니다.

```bash
# 로드 기반 자동 스케일링 설정
aws opsworks set-load-based-auto-scaling \
  --layer-id "layer-web123" \
  --enable \
  --up-scaling '{"InstanceCount":2,"ThresholdsWaitTime":3,"CpuThreshold":70,"MemoryThreshold":80,"LoadThreshold":5}' \
  --down-scaling '{"InstanceCount":1,"ThresholdsWaitTime":10,"CpuThreshold":30,"MemoryThreshold":40,"LoadThreshold":2}'

# 시간 기반 자동 스케일링 설정
aws opsworks set-time-based-auto-scaling \
  --instance-id "instance-abc123" \
  --auto-scaling-schedule '{"Monday":{"9":"on","18":"off"},"Tuesday":{"9":"on","18":"off"},"Wednesday":{"9":"on","18":"off"},"Thursday":{"9":"on","18":"off"},"Friday":{"9":"on","18":"off"}}'
```

## 실전 활용

### Chef 쿡북을 활용한 웹 서버 구성

Chef 쿡북으로 완전한 웹 서버 환경을 구성하는 예시입니다.

```yaml
# cookbooks/web/metadata.rb 내용 (YAML 형식으로 설명)
name: web
version: 1.0.0
depends:
  - nginx: "~> 12.0"
  - ssl_certificate: "~> 2.0"

# cookbooks/web/attributes/default.rb
default['web']['document_root'] = '/var/www/app'
default['web']['server_name'] = 'app.example.com'
default['web']['ssl_enabled'] = true
```

```bash
# 쿡북 업데이트 후 모든 인스턴스에 적용
aws opsworks create-deployment \
  --stack-id "stack-abc123" \
  --command '{"Name":"update_custom_cookbooks"}'

# 이후 Setup 레시피 재실행
aws opsworks create-deployment \
  --stack-id "stack-abc123" \
  --command '{"Name":"setup"}'

# 특정 레이어의 인스턴스에만 배포
aws opsworks create-deployment \
  --stack-id "stack-abc123" \
  --layer-ids "layer-web123" \
  --command '{"Name":"deploy"}' \
  --app-id "app-abc123"
```

### 모니터링 및 로그 관리

```bash
# 스택의 모든 인스턴스 상태 확인
aws opsworks describe-instances \
  --stack-id "stack-abc123" \
  --query 'Instances[*].{Hostname:Hostname,Status:Status,InstanceType:InstanceType,PublicIp:PublicIp,Layer:LayerIds[0]}' \
  --output table

# 배포 이력 조회
aws opsworks describe-deployments \
  --stack-id "stack-abc123" \
  --query 'Deployments[*].{Id:DeploymentId,Status:Status,Command:Command.Name,CreatedAt:CreatedAt,Duration:Duration}' \
  --output table

# CloudWatch 로그 그룹에서 OpsWorks 로그 조회
aws logs get-log-events \
  --log-group-name "/aws/opsworks/stack-abc123" \
  --log-stream-name "instance-abc123/chef-log" \
  --limit 50 \
  --region ap-northeast-2
```

### OpsWorks에서 Systems Manager로 마이그레이션

OpsWorks Stacks의 신규 온보딩이 중단되었으므로, 기존 OpsWorks 환경을 AWS Systems Manager로 마이그레이션하는 것이 권장됩니다.

```bash
# 1. OpsWorks 인스턴스 목록 추출
aws opsworks describe-instances \
  --stack-id "stack-abc123" \
  --query 'Instances[*].{InstanceId:Ec2InstanceId,Hostname:Hostname,LayerId:LayerIds[0]}' \
  --output json > opsworks-instances.json

# 2. SSM Agent가 설치되어 있는지 확인
aws ssm describe-instance-information \
  --query 'InstanceInformationList[*].{InstanceId:InstanceId,PingStatus:PingStatus,AgentVersion:AgentVersion}' \
  --output table

# 3. Systems Manager State Manager로 구성 관리 전환
aws ssm create-association \
  --name "AWS-ApplyChefRecipes" \
  --targets '[{"Key":"tag:Environment","Values":["production"]}]' \
  --parameters '{"sourceType":["s3"],"sourceInfo":["{\"path\":\"https://s3.amazonaws.com/my-bucket/cookbooks.tar.gz\"}"],"runList":["recipe[web::setup]"],"chefClientVersion":["18"],"compliance":[""]}' \
  --schedule-expression "rate(30 minutes)"
```

## 모범 사례/보안

### 구성 관리 모범 사례

1. **쿡북/매니페스트를 버전 관리하십시오.** Chef 쿡북이나 Puppet 매니페스트는 반드시 Git 등의 버전 관리 시스템에서 관리해야 합니다. OpsWorks는 Git 리포지토리에서 쿡북을 직접 가져올 수 있습니다.

2. **환경별 스택을 분리하십시오.** 개발, 스테이징, 프로덕션 환경을 별도의 스택으로 구성하여 격리해야 합니다.

3. **커스텀 JSON을 활용하십시오.** 환경별 설정 차이는 OpsWorks의 Custom JSON 기능을 통해 관리합니다.

```json
{
  "app": {
    "environment": "production",
    "database": {
      "host": "db.example.com",
      "port": 3306,
      "name": "app_production"
    },
    "cache": {
      "host": "cache.example.com",
      "port": 6379
    }
  }
}
```

4. **데이터백(Data Bags)으로 민감 정보를 관리하십시오.** 비밀번호, API 키 등은 암호화된 데이터백을 사용하여 관리합니다.

### 보안 모범 사례

- OpsWorks 서비스 역할과 인스턴스 프로필에 최소 권한 원칙을 적용하십시오.
- Chef Automate/Puppet Enterprise 서버에 대한 네트워크 접근을 VPC 내부로 제한하십시오.
- 쿡북 리포지토리에 SSH 키 기반 인증을 사용하십시오.
- OpsWorks 이벤트를 CloudTrail로 감사하십시오.
- 정기적으로 서버 백업을 수행하십시오.

```bash
# Chef Automate 서버 백업 스케줄 확인
aws opsworks-cm describe-servers \
  --server-name "chef-automate-prod" \
  --query 'Servers[0].{BackupWindow:PreferredBackupWindow,MaintenanceWindow:PreferredMaintenanceWindow}' \
  --output json \
  --region ap-northeast-2
```

### 마이그레이션 권장 사항

OpsWorks의 서비스 종료가 진행 중이므로 다음과 같은 마이그레이션을 고려하십시오.

- **OpsWorks Stacks -> AWS Systems Manager**: State Manager, Run Command, Automation 문서를 활용합니다.
- **OpsWorks for Chef Automate -> 자체 관리형 Chef 또는 Systems Manager**: EC2에 Chef 서버를 직접 구축하거나, Systems Manager로 전환합니다.
- **OpsWorks for Puppet Enterprise -> 자체 관리형 Puppet 또는 Systems Manager**: EC2에 Puppet 서버를 직접 구축하거나, Systems Manager로 전환합니다.

## 관련 서비스 비교

### OpsWorks vs Systems Manager vs CloudFormation

| 항목 | OpsWorks | Systems Manager | CloudFormation |
|------|----------|----------------|----------------|
| 목적 | 서버 구성 관리 | 운영 자동화 | 인프라 프로비저닝 |
| 도구 | Chef/Puppet | SSM Documents/Run Command | JSON/YAML 템플릿 |
| 범위 | OS 내부 구성 | OS 내부 + AWS 리소스 | AWS 리소스 |
| 에이전트 | Chef/Puppet Agent | SSM Agent | 해당 없음 |
| 현재 상태 | 신규 온보딩 종료 | 활발히 개발 중 | 활발히 개발 중 |
| 학습 곡선 | Chef/Puppet 지식 필요 | AWS 네이티브 | AWS 네이티브 |

### Chef vs Puppet vs Ansible

| 항목 | Chef | Puppet | Ansible |
|------|------|--------|--------|
| 언어 | Ruby DSL | Puppet DSL | YAML |
| 아키텍처 | Client-Server | Client-Server | Agentless |
| 실행 방식 | Pull | Pull | Push |
| 학습 곡선 | 높음 | 중간 | 낮음 |
| AWS 통합 | OpsWorks for Chef | OpsWorks for Puppet | Systems Manager |

## 요약

AWS OpsWorks는 Chef와 Puppet을 활용한 서버 구성 관리 서비스입니다.

핵심 포인트를 정리하면 다음과 같습니다.

- **세 가지 제품**: OpsWorks Stacks(자체 관리), OpsWorks for Chef Automate, OpsWorks for Puppet Enterprise를 제공합니다.
- **Stack/Layer/Instance 모델**: OpsWorks Stacks는 직관적인 계층 구조로 인프라를 관리합니다.
- **라이프사이클 이벤트**: Setup, Configure, Deploy, Undeploy, Shutdown의 다섯 가지 이벤트로 Chef 레시피를 실행합니다.
- **자동 스케일링**: 시간 기반 및 로드 기반 자동 스케일링을 제공합니다.
- **서비스 전환**: 신규 온보딩이 종료되었으므로, AWS Systems Manager로의 전환을 계획해야 합니다.
- **IaC 원칙**: 서버 구성을 코드로 관리하는 Infrastructure as Code 원칙은 어떤 도구를 사용하든 핵심적인 개념입니다.

OpsWorks의 기존 사용자는 Systems Manager로의 마이그레이션을 계획하되, Chef/Puppet의 구성 관리 개념 자체는 클라우드 운영에서 여전히 중요한 역량입니다.