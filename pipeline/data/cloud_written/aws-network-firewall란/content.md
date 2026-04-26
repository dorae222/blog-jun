<!-- infographic-hero -->
![AWS Network Firewall 완벽 가이드: 관리형 네트워크 방화벽 서비스 핵심 요약](figures/infographic.svg)

*Figure: AWS Network Firewall 완벽 가이드: 관리형 네트워크 방화벽 서비스 한 장 요약 인포그래픽*

## 개요

AWS Network Firewall은 Amazon VPC를 위한 관리형 네트워크 방화벽 서비스입니다. AWS Network Firewall을 사용하면 네트워크 트래픽을 세밀하게 제어하는 방화벽 규칙을 정의하고 적용할 수 있습니다.

Network Firewall은 단순한 포트/프로토콜 기반 필터링을 넘어, 상태 기반(Stateful) 패킷 검사, 도메인 필터링, 침입 탐지/방지(IDS/IPS) 기능을 제공합니다. 이는 기존의 보안 그룹(Security Group)과 네트워크 ACL(NACL)만으로는 충족할 수 없었던 고급 네트워크 보안 요구사항을 해결합니다.

### Network Firewall이 필요한 상황

- **아웃바운드 트래픽 도메인 필터링**: 특정 도메인으로만 아웃바운드 통신을 허용
- **IDS/IPS 기능**: Suricata 호환 규칙을 사용한 침입 탐지 및 방지
- **프로토콜 수준 검사**: HTTP, TLS, DNS 등 애플리케이션 프로토콜 수준 검사
- **중앙 집중 방화벽**: AWS Transit Gateway와 연계한 허브-스포크 아키텍처의 중앙 방화벽
- **규정 준수**: PCI DSS, HIPAA 등의 네트워크 보안 요구사항 충족

## 핵심 기능

### 방화벽 정책 구조

Network Firewall의 정책 구조는 계층적으로 구성됩니다.

```
Firewall Policy
  ├── Stateless Rule Groups (상태 비저장 규칙)
  │   ├── Rule Group 1 (Priority: 1)
  │   └── Rule Group 2 (Priority: 2)
  ├── Stateless Default Action
  │   └── Forward to Stateful Rules / Drop / Pass
  └── Stateful Rule Groups (상태 저장 규칙)
      ├── Rule Group A (Domain filtering)
      ├── Rule Group B (Suricata rules)
      └── Rule Group C (5-tuple rules)
```

### Stateless 규칙

상태 비저장 규칙은 각 패킷을 독립적으로 검사합니다. 요청 패킷과 응답 패킷을 별도로 처리해야 합니다.

```bash
# Stateless 규칙 그룹 생성
aws network-firewall create-rule-group \
  --rule-group-name my-stateless-rules \
  --type STATELESS \
  --capacity 100 \
  --rule-group '{
    "RulesSource": {
      "StatelessRulesAndCustomActions": {
        "StatelessRules": [
          {
            "RuleDefinition": {
              "MatchAttributes": {
                "Sources": [{"AddressDefinition": "0.0.0.0/0"}],
                "Destinations": [{"AddressDefinition": "10.0.0.0/16"}],
                "DestinationPorts": [{"FromPort": 443, "ToPort": 443}],
                "Protocols": [6]
              },
              "Actions": ["aws:forward_to_sfe"]
            },
            "Priority": 1
          },
          {
            "RuleDefinition": {
              "MatchAttributes": {
                "Sources": [{"AddressDefinition": "0.0.0.0/0"}],
                "Destinations": [{"AddressDefinition": "10.0.0.0/16"}],
                "DestinationPorts": [{"FromPort": 22, "ToPort": 22}],
                "Protocols": [6]
              },
              "Actions": ["aws:drop"]
            },
            "Priority": 2
          }
        ],
        "CustomActions": []
      }
    }
  }'
```

### Stateful 규칙

상태 저장 규칙은 연결 상태를 추적하므로, 요청에 대한 응답 트래픽은 자동으로 허용됩니다.

**5-Tuple 규칙**

```bash
# 5-Tuple Stateful 규칙 그룹 생성
aws network-firewall create-rule-group \
  --rule-group-name my-stateful-5tuple \
  --type STATEFUL \
  --capacity 100 \
  --rule-group '{
    "RulesSource": {
      "StatefulRules": [
        {
          "Action": "PASS",
          "Header": {
            "Protocol": "TCP",
            "Source": "10.0.0.0/16",
            "SourcePort": "ANY",
            "Direction": "FORWARD",
            "Destination": "ANY",
            "DestinationPort": "443"
          },
          "RuleOptions": [{"Keyword": "sid", "Settings": ["1"]}]
        },
        {
          "Action": "DROP",
          "Header": {
            "Protocol": "TCP",
            "Source": "ANY",
            "SourcePort": "ANY",
            "Direction": "ANY",
            "Destination": "ANY",
            "DestinationPort": "ANY"
          },
          "RuleOptions": [{"Keyword": "sid", "Settings": ["2"]}]
        }
      ]
    },
    "StatefulRuleOptions": {
      "RuleOrder": "STRICT_ORDER"
    }
  }'
```

**도메인 필터링 규칙**

아웃바운드 트래픽을 특정 도메인으로만 제한하는 가장 일반적인 사용 사례입니다.

```bash
# 도메인 허용 목록 규칙 그룹 생성
aws network-firewall create-rule-group \
  --rule-group-name allowed-domains \
  --type STATEFUL \
  --capacity 100 \
  --rule-group '{
    "RulesSource": {
      "RulesSourceList": {
        "Targets": [
          ".amazonaws.com",
          ".aws.amazon.com",
          "github.com",
          ".docker.io",
          ".docker.com"
        ],
        "TargetTypes": ["HTTP_HOST", "TLS_SNI"],
        "GeneratedRulesType": "ALLOWLIST"
      }
    }
  }'
```

**Suricata 호환 규칙**

Network Firewall은 Suricata IDS/IPS 엔진과 호환되는 규칙을 지원합니다.

```bash
# Suricata 규칙 파일을 사용한 규칙 그룹 생성
aws network-firewall create-rule-group \
  --rule-group-name suricata-ips-rules \
  --type STATEFUL \
  --capacity 200 \
  --rules 'alert tcp any any -> any 80 (msg:"SQL Injection attempt"; content:"SELECT"; nocase; content:"FROM"; nocase; distance:0; sid:1000001; rev:1;)
alert tcp any any -> any 80 (msg:"XSS attempt"; content:"<script"; nocase; sid:1000002; rev:1;)
alert tcp any any -> any any (msg:"Potential C2 communication"; flow:to_server,established; content:"|00 00 00 00|"; depth:4; sid:1000003; rev:1;)
drop tcp any any -> any 445 (msg:"Block SMB"; sid:1000004; rev:1;)
drop tcp any any -> any 3389 (msg:"Block RDP from external"; sid:1000005; rev:1;)'
```

### 방화벽 정책 생성

```bash
# 방화벽 정책 생성
aws network-firewall create-firewall-policy \
  --firewall-policy-name my-firewall-policy \
  --firewall-policy '{
    "StatelessDefaultActions": ["aws:forward_to_sfe"],
    "StatelessFragmentDefaultActions": ["aws:forward_to_sfe"],
    "StatelessRuleGroupReferences": [
      {
        "ResourceArn": "arn:aws:network-firewall:ap-northeast-2:123456789012:stateless-rulegroup/my-stateless-rules",
        "Priority": 1
      }
    ],
    "StatefulRuleGroupReferences": [
      {
        "ResourceArn": "arn:aws:network-firewall:ap-northeast-2:123456789012:stateful-rulegroup/allowed-domains"
      },
      {
        "ResourceArn": "arn:aws:network-firewall:ap-northeast-2:123456789012:stateful-rulegroup/suricata-ips-rules"
      }
    ],
    "StatefulEngineOptions": {
      "RuleOrder": "STRICT_ORDER"
    }
  }'
```

## 아키텍처/동작 원리

### 방화벽 배포 아키텍처

Network Firewall을 배포하면 각 가용 영역에 방화벽 엔드포인트(GWLB Endpoint)가 생성됩니다. 트래픽이 이 엔드포인트를 통과하도록 라우팅 테이블을 구성해야 합니다.

```
                Internet
                   |
          +--------+--------+
          |  Internet GW    |
          +--------+--------+
                   |
          [IGW Route Table]
          10.0.0.0/16 -> local
          10.0.1.0/24 -> fw-endpoint-a
          10.0.2.0/24 -> fw-endpoint-c
                   |
     +-------------+-------------+
     |                           |
+----+----+               +------+----+
| FW      |               | FW       |
| Subnet  |               | Subnet   |
| (AZ-a)  |               | (AZ-c)   |
| fw-ep-a |               | fw-ep-c  |
+----+----+               +-----+----+
     |                          |
[FW Subnet RT]          [FW Subnet RT]
0.0.0.0/0 -> IGW       0.0.0.0/0 -> IGW
     |                          |
+----+----+               +-----+----+
| Public  |               | Public   |
| Subnet  |               | Subnet   |
| (AZ-a)  |               | (AZ-c)   |
+----+----+               +-----+----+
     |                          |
[Public Subnet RT]       [Public Subnet RT]
0.0.0.0/0 -> fw-ep-a    0.0.0.0/0 -> fw-ep-c
```

### 방화벽 생성 및 라우팅 설정

```bash
# 1. 방화벽 생성
aws network-firewall create-firewall \
  --firewall-name my-network-firewall \
  --firewall-policy-arn arn:aws:network-firewall:ap-northeast-2:123456789012:firewall-policy/my-firewall-policy \
  --vpc-id vpc-0a1b2c3d4e5f6g7h8 \
  --subnet-mappings SubnetId=subnet-fw-a SubnetId=subnet-fw-c \
  --tags Key=Environment,Value=Production

# 2. 방화벽 엔드포인트 확인
aws network-firewall describe-firewall \
  --firewall-name my-network-firewall \
  --query 'FirewallStatus.SyncStates' \
  --output json

# 3. 라우팅 테이블에 방화벽 엔드포인트 경로 추가
# Public Subnet Route Table
aws ec2 create-route \
  --route-table-id rtb-public-a \
  --destination-cidr-block 0.0.0.0/0 \
  --vpc-endpoint-id vpce-fw-endpoint-a

# IGW Route Table (Ingress Routing)
aws ec2 create-route \
  --route-table-id rtb-igw \
  --destination-cidr-block 10.0.1.0/24 \
  --vpc-endpoint-id vpce-fw-endpoint-a
```

### Transit Gateway 통합 (허브-스포크 아키텍처)

중앙 집중식 방화벽 아키텍처를 구현하려면 Transit Gateway와 Network Firewall을 결합합니다.

```bash
# Inspection VPC에 Transit Gateway 연결
aws ec2 create-transit-gateway-vpc-attachment \
  --transit-gateway-id tgw-0a1b2c3d4e5f6g7h8 \
  --vpc-id vpc-inspection \
  --subnet-ids subnet-tgw-a subnet-tgw-c \
  --options ApplianceModeSupport=enable
```

`ApplianceModeSupport=enable`은 매우 중요합니다. 이 옵션이 없으면 요청 트래픽과 응답 트래픽이 서로 다른 AZ의 방화벽 엔드포인트를 통과할 수 있어 비대칭 라우팅 문제가 발생합니다.

## 실전 활용

### 로깅 설정

Network Firewall은 세 가지 로그 유형을 지원합니다.

- **Alert Log**: 규칙에 매칭된 트래픽 로그
- **Flow Log**: 상태 저장 엔진의 네트워크 흐름 로그
- **TLS Log**: TLS 검사 관련 로그

```bash
# 로깅 설정 (CloudWatch + S3)
aws network-firewall update-logging-configuration \
  --firewall-name my-network-firewall \
  --logging-configuration '{
    "LogDestinationConfigs": [
      {
        "LogType": "ALERT",
        "LogDestinationType": "CloudWatchLogs",
        "LogDestination": {
          "logGroup": "/aws/network-firewall/alerts"
        }
      },
      {
        "LogType": "FLOW",
        "LogDestinationType": "S3",
        "LogDestination": {
          "bucketName": "my-firewall-logs",
          "prefix": "flow-logs"
        }
      }
    ]
  }'
```

### TLS 검사 (TLS Inspection)

Network Firewall은 TLS 트래픽을 복호화하여 검사할 수 있습니다. 이를 위해 ACM에서 인증서를 사용합니다.

```bash
# TLS 검사 설정이 포함된 방화벽 정책 업데이트
aws network-firewall update-firewall-policy \
  --firewall-policy-name my-firewall-policy \
  --firewall-policy '{
    "StatelessDefaultActions": ["aws:forward_to_sfe"],
    "StatelessFragmentDefaultActions": ["aws:forward_to_sfe"],
    "StatefulRuleGroupReferences": [
      {
        "ResourceArn": "arn:aws:network-firewall:ap-northeast-2:123456789012:stateful-rulegroup/suricata-ips-rules"
      }
    ],
    "TLSInspectionConfigurationArn": "arn:aws:network-firewall:ap-northeast-2:123456789012:tls-inspection-configuration/my-tls-config",
    "StatefulEngineOptions": {
      "RuleOrder": "STRICT_ORDER"
    }
  }'
```

### 관리형 규칙 그룹 활용

AWS는 사전 정의된 관리형 규칙 그룹을 제공합니다.

```bash
# 사용 가능한 관리형 규칙 그룹 목록
aws network-firewall list-rule-groups \
  --scope MANAGED \
  --query 'RuleGroups[*].{Name:Name,Arn:Arn}' \
  --output table
```

## 모범 사례/보안

### 규칙 설계 원칙

1. **최소 권한 원칙**: 기본적으로 모든 트래픽을 차단하고, 필요한 트래픽만 명시적으로 허용합니다.
2. **STRICT_ORDER 사용**: 규칙 평가 순서를 명확히 하여 예측 가능한 동작을 보장합니다.
3. **도메인 기반 필터링**: IP 기반보다 도메인 기반 필터링을 우선 사용합니다.
4. **로깅 활성화**: 모든 로그 유형을 활성화하여 가시성을 확보합니다.
5. **규칙 용량 계획**: 규칙 그룹의 용량은 생성 후 변경할 수 없으므로 여유 있게 설정합니다.

### 성능 최적화

- Stateless 규칙으로 처리할 수 있는 트래픽은 Stateless에서 처리하여 성능을 향상시킵니다.
- 자주 매칭되는 규칙의 우선순위를 높여 처리 속도를 개선합니다.
- 불필요한 규칙은 정기적으로 정리합니다.

## 관련 서비스 비교

| 항목 | Network Firewall | Security Group | NACL | WAF |
|------|-----------------|----------------|------|-----|
| 계층 | L3-L7 | L3-L4 | L3-L4 | L7 |
| 상태 | Stateful + Stateless | Stateful | Stateless | Stateful |
| 범위 | 서브넷/VPC | ENI | 서브넷 | ALB/CloudFront/API GW |
| IDS/IPS | 지원 | 미지원 | 미지원 | 부분 지원 |
| 도메인 필터링 | 지원 | 미지원 | 미지원 | 미지원 |
| TLS 검사 | 지원 | 미지원 | 미지원 | 미지원 |
| 비용 | 높음 | 무료 | 무료 | 중간 |

## 요약

AWS Network Firewall은 VPC를 위한 엔터프라이즈급 관리형 방화벽 서비스입니다.

1. **Stateless와 Stateful 규칙**을 조합하여 세밀한 트래픽 제어가 가능합니다.
2. **도메인 기반 필터링**으로 아웃바운드 트래픽을 허용된 도메인으로만 제한할 수 있습니다.
3. **Suricata 호환 규칙**을 지원하여 기존 IDS/IPS 규칙을 재활용할 수 있습니다.
4. **Transit Gateway와 통합**하여 중앙 집중식 방화벽 아키텍처를 구현할 수 있습니다.
5. **TLS 검사 기능**으로 암호화된 트래픽도 검사할 수 있습니다.
6. 보안 그룹, NACL과 함께 사용하여 **심층 방어(Defense in Depth)** 전략을 구현할 수 있습니다.
7. 비용이 높으므로 **규정 준수 요구사항**이 있거나 **고급 네트워크 보안**이 필요한 환경에 적합합니다.