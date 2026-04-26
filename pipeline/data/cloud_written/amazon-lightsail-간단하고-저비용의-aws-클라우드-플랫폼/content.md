<!-- infographic-hero -->
![Amazon Lightsail - 간단하고 저비용의 AWS 클라우드 플랫폼 완벽 가이드 핵심 요약](figures/infographic.svg)

*Figure: Amazon Lightsail - 간단하고 저비용의 AWS 클라우드 플랫폼 완벽 가이드 한 장 요약 인포그래픽*

## 개요

Amazon Lightsail은 AWS의 간소화된 클라우드 플랫폼으로, 소규모 프로젝트, 개인 블로그, 스타트업의 MVP, 개발/테스트 환경 등에 최적화된 서비스입니다. EC2, RDS, ALB, CloudFront 등 복잡한 AWS 서비스를 개별적으로 설정하는 대신, Lightsail은 이 모든 것을 통합된 하나의 인터페이스에서 예측 가능한 월정액 가격으로 제공합니다.

Lightsail의 핵심 가치는 **단순성**과 **비용 예측성**입니다. AWS를 처음 접하는 사용자도 몇 번의 클릭만으로 웹 서버, WordPress 블로그, Node.js 앱을 배포할 수 있으며, 월별 고정 비용으로 예산 관리가 용이합니다.

본 글에서는 Lightsail의 주요 기능을 심도 있게 살펴보고, 실전 활용 사례와 함께 프로젝트 성장에 따라 EC2로 마이그레이션하는 전략까지 다루겠습니다.

## 핵심 기능

### 1. Lightsail 인스턴스

Lightsail 인스턴스는 가상 프라이빗 서버(VPS)로, 고정된 월정액 가격에 컴퓨팅, 메모리, SSD 스토리지, 데이터 전송을 번들로 제공합니다.

```bash
# 사용 가능한 인스턴스 번들(플랜) 조회
aws lightsail get-bundles \
  --query 'bundles[?isActive==`true`].{BundleId: bundleId, Name: name, Price: price, CPU: cpuCount, RAM: ramSizeInGb, Disk: diskSizeInGb, Transfer: transferPerMonthInGb}' \
  --output table

# 사용 가능한 블루프린트(OS/앱) 조회
aws lightsail get-blueprints \
  --query 'blueprints[?isActive==`true`].{BlueprintId: blueprintId, Name: name, Type: type, Platform: platform}' \
  --output table
```

**인스턴스 플랜 예시 (2024년 기준):**

| 플랜 | vCPU | 메모리 | SSD | 전송량 | 월 가격(USD) |
|------|------|--------|-----|--------|-------------|
| nano | 1 | 512 MB | 20 GB | 1 TB | $3.50 |
| micro | 1 | 1 GB | 40 GB | 2 TB | $5.00 |
| small | 1 | 2 GB | 60 GB | 3 TB | $10.00 |
| medium | 2 | 4 GB | 80 GB | 4 TB | $20.00 |
| large | 2 | 8 GB | 160 GB | 5 TB | $40.00 |
| xlarge | 4 | 16 GB | 320 GB | 6 TB | $80.00 |
| 2xlarge | 8 | 32 GB | 640 GB | 7 TB | $160.00 |

```bash
# Lightsail 인스턴스 생성
aws lightsail create-instances \
  --instance-names "my-web-server" \
  --availability-zone ap-northeast-2a \
  --blueprint-id "amazon_linux_2023" \
  --bundle-id "medium_3_0" \
  --key-pair-name my-lightsail-key \
  --tags '[{"key": "Project", "value": "personal-blog"}]'

# WordPress 블루프린트로 인스턴스 생성
aws lightsail create-instances \
  --instance-names "my-wordpress" \
  --availability-zone ap-northeast-2a \
  --blueprint-id "wordpress" \
  --bundle-id "small_3_0" \
  --key-pair-name my-lightsail-key
```

### 2. 고정 IP (Static IP)

```bash
# 고정 IP 할당
aws lightsail allocate-static-ip \
  --static-ip-name "web-server-ip"

# 인스턴스에 고정 IP 연결
aws lightsail attach-static-ip \
  --static-ip-name "web-server-ip" \
  --instance-name "my-web-server"

# 고정 IP 상태 확인
aws lightsail get-static-ip \
  --static-ip-name "web-server-ip"
```

고정 IP는 인스턴스에 연결된 상태에서는 무료이며, 미사용 시에만 소액의 비용이 발생합니다.

### 3. Lightsail 관리형 데이터베이스

```bash
# MySQL 데이터베이스 생성
aws lightsail create-relational-database \
  --relational-database-name "app-database" \
  --availability-zone ap-northeast-2a \
  --relational-database-blueprint-id "mysql_8_0" \
  --relational-database-bundle-id "medium_2_0" \
  --master-database-name "appdb" \
  --master-username "admin" \
  --master-user-password "SecurePassword123!" \
  --preferred-backup-window "03:00-04:00" \
  --preferred-maintenance-window "sun:05:00-sun:06:00" \
  --tags '[{"key": "Environment", "value": "production"}]'

# PostgreSQL 데이터베이스 생성
aws lightsail create-relational-database \
  --relational-database-name "analytics-db" \
  --availability-zone ap-northeast-2a \
  --relational-database-blueprint-id "postgres_16" \
  --relational-database-bundle-id "small_2_0" \
  --master-database-name "analytics" \
  --master-username "admin" \
  --master-user-password "SecurePassword456!"

# 데이터베이스 상태 확인
aws lightsail get-relational-database \
  --relational-database-name "app-database" \
  --query '{Name: name, Engine: engine, State: state, Endpoint: masterEndpoint}'
```

### 4. 컨테이너 서비스

Lightsail은 간단한 컨테이너 배포도 지원합니다.

```bash
# 컨테이너 서비스 생성
aws lightsail create-container-service \
  --service-name "my-app-container" \
  --power medium \
  --scale 2 \
  --tags '[{"key": "App", "value": "web"}]'

# 컨테이너 이미지 푸시
aws lightsail push-container-image \
  --service-name "my-app-container" \
  --label "my-app" \
  --image myapp:latest

# 컨테이너 배포
aws lightsail create-container-service-deployment \
  --service-name "my-app-container" \
  --containers '{
    "my-app": {
      "image": ":my-app-container.my-app.1",
      "ports": {"8080": "HTTP"},
      "environment": {
        "NODE_ENV": "production"
      }
    }
  }' \
  --public-endpoint '{
    "containerName": "my-app",
    "containerPort": 8080,
    "healthCheck": {
      "path": "/health",
      "intervalSeconds": 30
    }
  }'
```

### 5. CDN (Content Delivery Network)

```bash
# CDN 배포 생성
aws lightsail create-distribution \
  --distribution-name "blog-cdn" \
  --origin '{"name": "my-web-server", "regionName": "ap-northeast-2", "protocolPolicy": "https-only"}' \
  --default-cache-behavior '{"behavior": "cache"}' \
  --cache-behaviors '[{
    "path": "/api/*",
    "behavior": "dont-cache"
  }]' \
  --bundle-id "medium_bundle" \
  --tags '[{"key": "Purpose", "value": "blog-acceleration"}]'

# CDN 상태 확인
aws lightsail get-distributions \
  --query 'distributions[*].{Name: name, Status: status, DomainName: domainName, Origin: origin.name}'
```

### 6. 로드 밸런서

```bash
# 로드 밸런서 생성
aws lightsail create-load-balancer \
  --load-balancer-name "web-lb" \
  --instance-port 80 \
  --health-check-path "/health" \
  --tags '[{"key": "Service", "value": "web"}]'

# 인스턴스 연결
aws lightsail attach-instances-to-load-balancer \
  --load-balancer-name "web-lb" \
  --instance-names "web-server-1" "web-server-2"

# SSL/TLS 인증서 생성 및 연결
aws lightsail create-load-balancer-tls-certificate \
  --load-balancer-name "web-lb" \
  --certificate-name "my-cert" \
  --certificate-domain-name "example.com" \
  --certificate-alternative-names "www.example.com"
```

## 아키텍처/동작 원리

### Lightsail과 AWS 인프라의 관계

```
[Amazon Lightsail 콘솔/API]
         |
         v
[Lightsail 관리 레이어]
  ├── 간소화된 인터페이스
  ├── 번들 기반 가격 정책
  └── 자동화된 인프라 설정
         |
         v
[AWS 기반 인프라]
  ├── EC2 (인스턴스)
  ├── EBS (블록 스토리지)
  ├── VPC (네트워킹)
  ├── RDS (관리형 DB)
  ├── CloudFront (CDN)
  └── ELB (로드 밸런서)
```

Lightsail 인스턴스는 내부적으로 EC2 위에서 동작합니다. 하지만 Lightsail은 복잡한 VPC, 보안 그룹, IAM 설정을 추상화하여 사용자에게 단순한 인터페이스를 제공합니다.

### VPC Peering

Lightsail은 자체 VPC에서 동작하지만, VPC Peering을 통해 기본 AWS VPC의 리소스와 통신할 수 있습니다.

```bash
# VPC Peering 활성화
aws lightsail peer-vpc

# VPC Peering 상태 확인
aws lightsail is-vpc-peered
```

이를 통해 Lightsail 인스턴스에서 같은 리전의 RDS, ElastiCache, EC2 등에 프라이빗 네트워크로 접근할 수 있습니다.

### 스냅샷 및 백업

```bash
# 인스턴스 스냅샷 생성
aws lightsail create-instance-snapshot \
  --instance-name "my-web-server" \
  --instance-snapshot-name "web-server-backup-20240115"

# 자동 스냅샷 활성화
aws lightsail enable-add-on \
  --resource-name "my-web-server" \
  --add-on-request '{"addOnType": "AutoSnapshot", "autoSnapshotAddOnRequest": {"snapshotTimeOfDay": "02:00"}}'

# 스냅샷에서 인스턴스 복원
aws lightsail create-instances-from-snapshot \
  --instance-names "restored-web-server" \
  --availability-zone ap-northeast-2a \
  --instance-snapshot-name "web-server-backup-20240115" \
  --bundle-id "medium_3_0"

# 스냅샷 목록 조회
aws lightsail get-instance-snapshots \
  --query 'instanceSnapshots[*].{Name: name, State: state, CreatedAt: createdAt, SizeInGb: sizeInGb}' \
  --output table
```

## 실전 활용

### 사례 1: WordPress 블로그 운영

```bash
# 1. WordPress 인스턴스 생성
aws lightsail create-instances \
  --instance-names "blog-wordpress" \
  --availability-zone ap-northeast-2a \
  --blueprint-id "wordpress" \
  --bundle-id "small_3_0" \
  --key-pair-name my-key

# 2. 고정 IP 할당
aws lightsail allocate-static-ip --static-ip-name "blog-ip"
aws lightsail attach-static-ip \
  --static-ip-name "blog-ip" \
  --instance-name "blog-wordpress"

# 3. DNS 설정
aws lightsail create-domain \
  --domain-name "myblog.com"

aws lightsail create-domain-entry \
  --domain-name "myblog.com" \
  --domain-entry '{"name": "myblog.com", "type": "A", "target": "<static-ip>"}'

# 4. HTTPS 인증서 생성
aws lightsail create-certificate \
  --certificate-name "blog-cert" \
  --domain-name "myblog.com" \
  --subject-alternative-names "www.myblog.com"

# 5. CDN 배포
aws lightsail create-distribution \
  --distribution-name "blog-cdn" \
  --origin '{"name": "blog-wordpress", "regionName": "ap-northeast-2", "protocolPolicy": "https-only"}' \
  --default-cache-behavior '{"behavior": "cache"}' \
  --cache-behaviors '[{"path": "/wp-admin/*", "behavior": "dont-cache"}, {"path": "/wp-login.php", "behavior": "dont-cache"}]' \
  --bundle-id "small_bundle" \
  --certificate-name "blog-cert"
```

### 사례 2: Node.js 애플리케이션 배포

```bash
# Node.js 블루프린트 인스턴스 생성
aws lightsail create-instances \
  --instance-names "nodejs-app" \
  --availability-zone ap-northeast-2a \
  --blueprint-id "nodejs" \
  --bundle-id "medium_3_0" \
  --key-pair-name my-key \
  --user-data '#!/bin/bash
cd /home/bitnami
git clone https://github.com/myuser/myapp.git
cd myapp
npm install --production
pm2 start ecosystem.config.js --env production'
```

### 사례 3: 방화벽 설정

```bash
# 인스턴스 방화벽 규칙 추가
aws lightsail put-instance-public-ports \
  --instance-name "my-web-server" \
  --port-infos '[
    {"fromPort": 80, "toPort": 80, "protocol": "tcp"},
    {"fromPort": 443, "toPort": 443, "protocol": "tcp"},
    {"fromPort": 22, "toPort": 22, "protocol": "tcp", "cidrs": ["203.0.113.0/24"]}
  ]'

# 현재 방화벽 규칙 조회
aws lightsail get-instance-port-states \
  --instance-name "my-web-server"
```

### 사례 4: EC2로 마이그레이션

프로젝트가 성장하여 Lightsail의 한계를 넘어서면 EC2로 마이그레이션할 수 있습니다.

```bash
# 1. Lightsail 스냅샷 생성
aws lightsail create-instance-snapshot \
  --instance-name "my-web-server" \
  --instance-snapshot-name "migration-snapshot"

# 2. 스냅샷을 EC2 AMI로 내보내기
aws lightsail export-snapshot \
  --source-snapshot-name "migration-snapshot"

# 3. 내보내기 상태 확인
aws lightsail get-export-snapshot-records \
  --query 'exportSnapshotRecords[*].{Name: name, State: state, DestinationInfo: destinationInfo}'

# 4. 내보내진 AMI로 EC2 인스턴스 시작
# (export 완료 후 EC2 콘솔에서 AMI 확인 가능)
aws ec2 run-instances \
  --image-id ami-exported123 \
  --instance-type t3.medium \
  --key-name my-ec2-key \
  --subnet-id subnet-abc123 \
  --security-group-ids sg-abc123
```

## 모범 사례/보안

### 1. 적절한 플랜 선택

- 처음에는 작은 플랜으로 시작하고, 필요에 따라 스냅샷을 통해 상위 플랜으로 업그레이드합니다.
- 데이터 전송량을 모니터링하여 초과 비용이 발생하지 않도록 합니다.
- 전송량 초과 시 GB당 추가 비용이 발생하므로 CDN 활용을 권장합니다.

### 2. 보안 강화

- SSH 접근을 특정 IP 범위로 제한합니다.
- 기본 비밀번호를 즉시 변경합니다 (특히 WordPress, LAMP 블루프린트).
- 자동 스냅샷을 활성화하여 정기적 백업을 수행합니다.
- 불필요한 포트를 방화벽에서 차단합니다.

### 3. 비용 관리

```bash
# 월별 비용 추정 확인
aws lightsail get-cost-estimate \
  --resource-name "my-web-server" \
  --start-time 2024-01-01 \
  --end-time 2024-01-31

# 알람 설정 (데이터 전송량 모니터링)
aws lightsail put-alarm \
  --alarm-name "transfer-alarm" \
  --metric-name NetworkOut \
  --monitored-resource-name "my-web-server" \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --threshold 3000000000 \
  --evaluation-periods 1 \
  --datapoints-to-alarm 1 \
  --treat-missing-data "notBreaching" \
  --contact-protocols '["Email"]' \
  --notification-triggers '["OK", "ALARM"]'
```

### 4. EC2 마이그레이션 시점 판단

다음 상황에서는 EC2로의 마이그레이션을 고려합니다.
- Auto Scaling이 필요한 경우
- GPU 인스턴스가 필요한 경우
- 세밀한 VPC/네트워크 구성이 필요한 경우
- Lightsail 최대 플랜(8 vCPU, 32 GB)을 초과하는 리소스가 필요한 경우
- 다른 AWS 서비스와의 깊은 통합이 필요한 경우

## 관련 서비스 비교

| 항목 | Lightsail | EC2 | App Runner | DigitalOcean |
|------|----------|-----|-----------|-------------|
| 복잡도 | 매우 낮음 | 높음 | 낮음 | 낮음 |
| 가격 모델 | 월정액 번들 | 사용량 기반 | 사용량 기반 | 월정액 |
| 최소 비용 | $3.50/월 | ~$4/월 (t4g.nano) | $5/월 | $4/월 |
| 최대 스케일 | 8 vCPU, 32 GB | 무제한 | 자동 확장 | 제한적 |
| Auto Scaling | 미지원 | 지원 | 자동 지원 | 미지원 |
| AWS 서비스 연동 | 제한적 (VPC Peering) | 완전 통합 | 완전 통합 | N/A |
| 관리형 DB | 지원 | RDS 별도 | 미지원 | 지원 |
| CDN 내장 | 지원 | CloudFront 별도 | 미지원 | 별도 |
| 적합한 대상 | 초보자, 소규모 | 중대규모, 전문가 | 웹앱/API | 소규모, 독립 |

## 요약

Amazon Lightsail은 AWS의 강력한 인프라를 단순하고 예측 가능한 비용으로 사용할 수 있는 서비스입니다. 핵심 내용을 정리하면 다음과 같습니다.

- **올인원 번들**: 컴퓨팅, 스토리지, 네트워크 전송량을 월정액으로 제공합니다. 최소 $3.50/월부터 시작합니다.
- **블루프린트**: WordPress, Node.js, LAMP, Django 등 사전 구성된 애플리케이션 스택을 즉시 배포할 수 있습니다.
- **관리형 서비스**: 데이터베이스, 로드 밸런서, CDN, 컨테이너 서비스를 간소화된 인터페이스로 관리합니다.
- **자동 백업**: 자동 스냅샷으로 정기적인 백업을 수행하고, 스냅샷에서 즉시 복원할 수 있습니다.
- **VPC Peering**: 기본 AWS VPC와 연결하여 RDS, ElastiCache 등 다른 AWS 서비스에 접근할 수 있습니다.
- **EC2 마이그레이션**: 프로젝트 성장 시 스냅샷 내보내기를 통해 EC2로 자연스럽게 이전할 수 있습니다.
- **적합한 대상**: AWS 입문자, 소규모 웹사이트, 블로그, 개발 환경, 스타트업 MVP에 최적입니다.

Lightsail은 복잡한 클라우드 인프라에 대한 진입 장벽을 낮추면서도, 필요시 AWS 전체 생태계로 확장할 수 있는 유연한 출발점을 제공합니다.