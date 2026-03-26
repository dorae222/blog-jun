## 개요

VPC Flow Logs는 Amazon VPC 내 네트워크 인터페이스에서 송수신되는 IP 트래픽에 대한 정보를 캡처할 수 있는 기능입니다. 캡처된 로그 데이터는 Amazon CloudWatch Logs, Amazon S3, Amazon Kinesis Data Firehose로 게시할 수 있습니다.

VPC Flow Logs를 사용하면 다음과 같은 질문에 답할 수 있습니다.

- 특정 보안 그룹 규칙에 의해 거부된 트래픽은 무엇인가?
- 인스턴스에 도달하는 트래픽의 출발지는 어디인가?
- 네트워크 인터페이스를 통해 송수신되는 트래픽 양은 얼마인가?

Flow Logs는 VPC, 서브넷, 또는 개별 네트워크 인터페이스(ENI) 수준에서 생성할 수 있으며, 이를 통해 세밀한 네트워크 모니터링이 가능합니다.

## 핵심 기능

### Flow Log 레코드 형식

VPC Flow Logs의 기본 레코드 형식은 다음과 같습니다.

```
<version> <account-id> <interface-id> <srcaddr> <dstaddr> <srcport> <dstport> <protocol> <packets> <bytes> <start> <end> <action> <log-status>
```

각 필드의 의미는 다음과 같습니다.

| 필드 | 설명 |
|------|------|
| version | Flow Log 버전 |
| account-id | AWS 계정 ID |
| interface-id | 네트워크 인터페이스 ID |
| srcaddr | 소스 IP 주소 |
| dstaddr | 대상 IP 주소 |
| srcport | 소스 포트 |
| dstport | 대상 포트 |
| protocol | IANA 프로토콜 번호 |
| packets | 캡처 윈도우 동안의 패킷 수 |
| bytes | 캡처 윈도우 동안의 바이트 수 |
| start | 캡처 윈도우 시작 시간 (Unix 타임스탬프) |
| end | 캡처 윈도우 종료 시간 |
| action | ACCEPT 또는 REJECT |
| log-status | OK, NODATA, SKIPDATA |

### 사용자 정의 형식 (v3+)

Flow Logs 버전 3 이상에서는 사용자 정의 필드를 포함할 수 있습니다.

```
${version} ${account-id} ${interface-id} ${srcaddr} ${dstaddr} ${srcport} ${dstport} ${protocol} ${packets} ${bytes} ${start} ${end} ${action} ${log-status} ${vpc-id} ${subnet-id} ${instance-id} ${tcp-flags} ${type} ${pkt-srcaddr} ${pkt-dstaddr} ${region} ${az-id} ${sublocation-type} ${sublocation-id} ${pkt-src-aws-service} ${pkt-dst-aws-service} ${flow-direction} ${traffic-path}
```

특히 `traffic-path` 필드는 트래픽이 어떤 경로를 통해 전달되었는지 파악하는 데 매우 유용합니다.

| traffic-path 값 | 의미 |
|-----------------|------|
| 1 | 같은 VPC 내 리소스를 통과 |
| 2 | Internet Gateway 또는 Gateway VPC Endpoint를 통과 |
| 3 | Virtual Private Gateway를 통과 |
| 4 | 리전 내 VPC Peering을 통과 |
| 5 | 리전 간 VPC Peering을 통과 |
| 6 | Local Gateway를 통과 |
| 7 | Gateway VPC Endpoint를 통과 |
| 8 | Internet Gateway를 통과 |

### 캡처 윈도우

Flow Logs는 약 10분의 집계 간격(aggregation interval)을 가집니다. 이는 트래픽 발생 후 로그가 게시되기까지 최대 10분이 소요될 수 있음을 의미합니다. 다만 1분 간격으로 설정할 수도 있습니다.

```bash
# 1분 집계 간격으로 Flow Log 생성
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids vpc-0a1b2c3d4e5f6g7h8 \
  --traffic-type ALL \
  --log-destination-type s3 \
  --log-destination arn:aws:s3:::my-flow-logs-bucket \
  --max-aggregation-interval 60
```

### Flow Logs가 캡처하지 않는 트래픽

다음 트래픽은 Flow Logs에 기록되지 않습니다.

- Amazon DNS 서버로의 트래픽 (자체 DNS 서버 트래픽은 기록됨)
- Amazon Windows 라이선스 활성화 트래픽
- 인스턴스 메타데이터 (169.254.169.254) 트래픽
- Amazon Time Sync Service (169.254.169.123) 트래픽
- DHCP 트래픽
- 기본 VPC 라우터의 예약 IP 주소 트래픽
- Endpoint Network Interface와 Network Load Balancer Network Interface 간 트래픽

## 아키텍처/동작 원리

### Flow Logs 게시 대상

Flow Logs 데이터는 세 가지 대상으로 게시할 수 있습니다.

**1. Amazon CloudWatch Logs**

CloudWatch Logs로 게시하면 CloudWatch Logs Insights를 사용하여 실시간에 가까운 쿼리 분석이 가능합니다. 또한 CloudWatch 경보를 설정하여 이상 트래픽을 감지할 수 있습니다.

```bash
# CloudWatch Logs로 Flow Log 생성
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids vpc-0a1b2c3d4e5f6g7h8 \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-group-name /vpc/flow-logs \
  --deliver-logs-permission-arn arn:aws:iam::123456789012:role/FlowLogsRole
```

CloudWatch Logs에 게시하기 위해서는 IAM 역할이 필요합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams"
      ],
      "Resource": "*"
    }
  ]
}
```

**2. Amazon S3**

S3로 게시하면 대량의 로그를 비용 효율적으로 저장하고, Athena를 사용한 대규모 분석이 가능합니다.

```bash
# S3로 Flow Log 생성 (Parquet 형식)
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids vpc-0a1b2c3d4e5f6g7h8 \
  --traffic-type ALL \
  --log-destination-type s3 \
  --log-destination arn:aws:s3:::my-flow-logs-bucket/vpc-logs/ \
  --log-format '${version} ${account-id} ${interface-id} ${srcaddr} ${dstaddr} ${srcport} ${dstport} ${protocol} ${packets} ${bytes} ${start} ${end} ${action} ${log-status}' \
  --destination-options '{"FileFormat": "parquet", "HiveCompatiblePartitions": true, "PerHourPartition": true}'
```

S3에 저장되는 로그의 디렉터리 구조는 다음과 같습니다.

```
s3://my-flow-logs-bucket/vpc-logs/AWSLogs/{account-id}/vpcflowlogs/{region}/{year}/{month}/{day}/
```

Hive 호환 파티션을 활성화하면 다음과 같은 구조가 됩니다.

```
s3://my-flow-logs-bucket/vpc-logs/AWSLogs/aws-account-id=123456789012/aws-service=vpcflowlogs/aws-region=ap-northeast-2/year=2024/month=01/day=15/
```

**3. Amazon Kinesis Data Firehose**

Kinesis Data Firehose로 게시하면 실시간 스트리밍 분석이 가능하며, OpenSearch Service, Splunk 등 다양한 분석 도구로 데이터를 전달할 수 있습니다.

```bash
# Kinesis Data Firehose로 Flow Log 생성
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids vpc-0a1b2c3d4e5f6g7h8 \
  --traffic-type ALL \
  --log-destination-type kinesis-data-firehose \
  --log-destination arn:aws:firehose:ap-northeast-2:123456789012:deliverystream/vpc-flow-logs-stream
```

### Athena를 활용한 Flow Logs 분석

S3에 저장된 Flow Logs를 Athena로 분석하는 것은 가장 비용 효율적이고 강력한 방법입니다.

```sql
-- Athena 테이블 생성 (Parquet 형식)
CREATE EXTERNAL TABLE IF NOT EXISTS vpc_flow_logs (
  version int,
  account_id string,
  interface_id string,
  srcaddr string,
  dstaddr string,
  srcport int,
  dstport int,
  protocol bigint,
  packets bigint,
  bytes bigint,
  start bigint,
  `end` bigint,
  action string,
  log_status string
)
PARTITIONED BY (
  `date` date
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
STORED AS INPUTFORMAT 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat'
OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION 's3://my-flow-logs-bucket/vpc-logs/AWSLogs/123456789012/vpcflowlogs/ap-northeast-2/'
TBLPROPERTIES ('has_encrypted_data'='false');
```

유용한 분석 쿼리 예시는 다음과 같습니다.

```sql
-- 가장 많이 거부된 IP 상위 10개
SELECT srcaddr, COUNT(*) as reject_count
FROM vpc_flow_logs
WHERE action = 'REJECT'
  AND date >= current_date - interval '7' day
GROUP BY srcaddr
ORDER BY reject_count DESC
LIMIT 10;

-- 시간대별 트래픽 볼륨
SELECT 
  date_format(from_unixtime(start), '%Y-%m-%d %H:00') as hour,
  SUM(bytes) / 1073741824 as total_gb,
  SUM(packets) as total_packets
FROM vpc_flow_logs
WHERE date >= current_date - interval '1' day
GROUP BY date_format(from_unixtime(start), '%Y-%m-%d %H:00')
ORDER BY hour;

-- 특정 포트에 대한 접근 시도
SELECT srcaddr, dstaddr, dstport, action, COUNT(*) as attempts
FROM vpc_flow_logs
WHERE dstport IN (22, 3389, 3306, 5432)
  AND date >= current_date - interval '1' day
GROUP BY srcaddr, dstaddr, dstport, action
ORDER BY attempts DESC
LIMIT 20;
```

## 실전 활용

### 보안 모니터링 파이프라인 구축

실무에서 VPC Flow Logs를 활용한 보안 모니터링 파이프라인을 구축하는 방법을 살펴보겠습니다.

**Step 1: Flow Logs 활성화**

```bash
# 모든 VPC에 대해 Flow Logs 활성화 (스크립트)
for vpc_id in $(aws ec2 describe-vpcs --query 'Vpcs[].VpcId' --output text); do
  echo "Enabling flow logs for $vpc_id"
  aws ec2 create-flow-logs \
    --resource-type VPC \
    --resource-ids $vpc_id \
    --traffic-type ALL \
    --log-destination-type s3 \
    --log-destination arn:aws:s3:::my-flow-logs-bucket/all-vpcs/ \
    --max-aggregation-interval 60 \
    --tag-specifications 'ResourceType=vpc-flow-log,Tags=[{Key=Environment,Value=Production}]'
done
```

**Step 2: CloudWatch 경보 설정**

CloudWatch Logs에 게시된 Flow Logs를 기반으로 메트릭 필터를 생성하고 경보를 설정합니다.

```bash
# SSH 거부 트래픽에 대한 메트릭 필터 생성
aws logs put-metric-filter \
  --log-group-name /vpc/flow-logs \
  --filter-name SSHRejectCount \
  --filter-pattern '[version, account_id, interface_id, srcaddr, dstaddr, srcport, dstport="22", protocol, packets, bytes, start, end, action="REJECT", log_status]' \
  --metric-transformations \
    metricName=SSHRejectCount,metricNamespace=VPCFlowLogs,metricValue=1

# 경보 생성 (5분 내 100건 이상 SSH 거부 시)
aws cloudwatch put-metric-alarm \
  --alarm-name "HighSSHRejects" \
  --metric-name SSHRejectCount \
  --namespace VPCFlowLogs \
  --statistic Sum \
  --period 300 \
  --threshold 100 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:ap-northeast-2:123456789012:security-alerts
```

**Step 3: Lambda를 활용한 자동 대응**

의심스러운 IP를 자동으로 NACL에 추가하는 Lambda 함수를 구현할 수 있습니다.

```python
import boto3
import json
import os

def lambda_handler(event, context):
    ec2 = boto3.client('ec2')
    
    # CloudWatch Logs에서 전달된 이벤트 파싱
    suspicious_ip = event['detail']['srcaddr']
    nacl_id = os.environ['NACL_ID']
    
    # 현재 NACL 규칙 확인
    response = ec2.describe_network-acls(
        NetworkAclIds=[nacl_id]
    )
    
    # 가장 낮은 사용 가능한 규칙 번호 찾기
    existing_rules = [entry['RuleNumber'] 
                      for entry in response['NetworkAcls'][0]['Entries']
                      if not entry['Egress']]
    rule_number = max(existing_rules) + 1 if existing_rules else 1
    
    # 차단 규칙 추가
    ec2.create_network_acl_entry(
        NetworkAclId=nacl_id,
        RuleNumber=rule_number,
        Protocol='-1',
        RuleAction='deny',
        Egress=False,
        CidrBlock=f'{suspicious_ip}/32'
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps(f'Blocked IP: {suspicious_ip}')
    }
```

### 네트워크 트러블슈팅

Flow Logs를 활용하여 네트워크 연결 문제를 진단하는 방법입니다.

```bash
# 특정 ENI의 Flow Logs 확인
aws logs filter-log-events \
  --log-group-name /vpc/flow-logs \
  --filter-pattern '{$.interface_id = "eni-0a1b2c3d4e5f6g7h8"}' \
  --start-time $(date -d '1 hour ago' +%s000) \
  --limit 50

# 특정 IP 간 통신 확인
aws logs filter-log-events \
  --log-group-name /vpc/flow-logs \
  --filter-pattern '[version, account_id, interface_id, srcaddr="10.0.1.100", dstaddr="10.0.2.200", srcport, dstport, protocol, packets, bytes, start, end, action, log_status]' \
  --start-time $(date -d '1 hour ago' +%s000)
```

### VPC Flow Logs와 VPC Traffic Mirroring 비교

| 특성 | VPC Flow Logs | VPC Traffic Mirroring |
|------|--------------|----------------------|
| 캡처 수준 | 메타데이터 (헤더 정보) | 전체 패킷 (페이로드 포함) |
| 비용 | 상대적으로 저렴 | 상대적으로 비쌈 |
| 성능 영향 | 거의 없음 | 약간 있음 |
| 분석 도구 | Athena, CloudWatch | Suricata, Zeek 등 |
| 주요 용도 | 네트워크 모니터링, 감사 | 심층 패킷 검사, 위협 탐지 |

## 모범 사례/보안

### 비용 최적화

VPC Flow Logs는 데이터 양에 따라 비용이 발생합니다. 다음은 비용을 최적화하는 방법입니다.

1. **필요한 트래픽만 캡처**: ACCEPT만 또는 REJECT만 캡처하도록 설정합니다.

```bash
# REJECT 트래픽만 캡처 (보안 모니터링 목적)
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids vpc-0a1b2c3d4e5f6g7h8 \
  --traffic-type REJECT \
  --log-destination-type s3 \
  --log-destination arn:aws:s3:::my-flow-logs-bucket
```

2. **Parquet 형식 사용**: Parquet 형식은 텍스트 대비 약 60-80% 저장 공간을 절약합니다.

3. **S3 수명 주기 정책 설정**: 오래된 로그를 Glacier로 이동하거나 삭제합니다.

```bash
# S3 수명 주기 정책 설정
aws s3api put-bucket-lifecycle-configuration \
  --bucket my-flow-logs-bucket \
  --lifecycle-configuration '{
    "Rules": [
      {
        "ID": "FlowLogsLifecycle",
        "Status": "Enabled",
        "Filter": {"Prefix": "vpc-logs/"},
        "Transitions": [
          {"Days": 30, "StorageClass": "STANDARD_IA"},
          {"Days": 90, "StorageClass": "GLACIER"}
        ],
        "Expiration": {"Days": 365}
      }
    ]
  }'
```

4. **서브넷 수준 캡처**: VPC 전체 대신 필요한 서브넷만 모니터링합니다.

### 보안 모범 사례

1. **모든 프로덕션 VPC에 Flow Logs 활성화**: AWS Security Hub와 AWS Config를 통해 Flow Logs 미활성 VPC를 탐지합니다.

2. **로그 무결성 보장**: S3 버킷에 Object Lock을 활성화하여 로그 변조를 방지합니다.

```bash
# S3 버킷에 Object Lock 활성화
aws s3api put-object-lock-configuration \
  --bucket my-flow-logs-bucket \
  --object-lock-configuration '{
    "ObjectLockEnabled": "Enabled",
    "Rule": {
      "DefaultRetention": {
        "Mode": "GOVERNANCE",
        "Days": 90
      }
    }
  }'
```

3. **크로스 계정 로그 집중화**: AWS Organizations 환경에서는 중앙 로깅 계정으로 Flow Logs를 집중화합니다.

4. **암호화 적용**: S3에 저장되는 Flow Logs에 KMS 암호화를 적용합니다.

```bash
# KMS 암호화가 적용된 Flow Log 생성
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids vpc-0a1b2c3d4e5f6g7h8 \
  --traffic-type ALL \
  --log-destination-type s3 \
  --log-destination arn:aws:s3:::my-flow-logs-bucket \
  --destination-options '{"FileFormat": "parquet", "HiveCompatiblePartitions": true, "PerHourPartition": true}' \
  --tag-specifications 'ResourceType=vpc-flow-log,Tags=[{Key=Name,Value=Production-FlowLogs}]'
```

## 관련 서비스 비교

### VPC Flow Logs vs AWS CloudTrail

| 항목 | VPC Flow Logs | AWS CloudTrail |
|------|--------------|----------------|
| 대상 | 네트워크 트래픽 메타데이터 | AWS API 호출 |
| 수준 | 패킷 레벨 (IP, 포트, 프로토콜) | API 레벨 (누가, 무엇을, 언제) |
| 주요 용도 | 네트워크 모니터링/보안 | 거버넌스/컴플라이언스/감사 |
| 비용 모델 | 데이터 볼륨 기반 | 이벤트 수 기반 |

### VPC Flow Logs vs AWS GuardDuty

GuardDuty는 내부적으로 VPC Flow Logs 데이터를 분석하지만, 별도로 Flow Logs를 활성화할 필요가 없습니다. GuardDuty는 독립적인 데이터 소스를 사용합니다.

| 항목 | VPC Flow Logs | AWS GuardDuty |
|------|--------------|---------------|
| 데이터 | 원시 네트워크 로그 | 위협 인텔리전스 기반 분석 결과 |
| 분석 | 직접 쿼리/분석 필요 | 자동 위협 탐지 |
| 비용 | 로그 볼륨 기반 | 분석된 데이터 볼륨 기반 |
| 활용 | 커스텀 분석, 감사 | 즉시 사용 가능한 보안 탐지 |

### 게시 대상별 비교

| 항목 | CloudWatch Logs | Amazon S3 | Kinesis Data Firehose |
|------|----------------|-----------|----------------------|
| 실시간성 | 준실시간 | 배치 (5~10분) | 실시간 |
| 비용 | 높음 | 낮음 | 중간 |
| 분석 도구 | CloudWatch Insights | Athena | OpenSearch, Splunk |
| 보존 기간 | 설정 가능 | 무제한 | 대상에 따라 다름 |
| 알람 설정 | 용이 | 별도 설정 필요 | 별도 설정 필요 |
| 추천 용도 | 실시간 모니터링 | 장기 보관/분석 | 실시간 분석/SIEM 연동 |

## 요약

VPC Flow Logs는 AWS 네트워크 보안 모니터링의 핵심 도구입니다. 주요 포인트를 정리하면 다음과 같습니다.

1. **VPC, 서브넷, ENI 수준**에서 트래픽 메타데이터를 캡처합니다.
2. **CloudWatch Logs, S3, Kinesis Data Firehose** 세 가지 대상으로 게시할 수 있습니다.
3. **Athena와 결합**하면 대규모 네트워크 트래픽을 비용 효율적으로 분석할 수 있습니다.
4. **Parquet 형식과 파티셔닝**을 활용하면 저장 비용과 쿼리 성능을 최적화할 수 있습니다.
5. **보안 모니터링 파이프라인**을 구축하여 이상 트래픽 자동 탐지 및 대응이 가능합니다.
6. 프로덕션 환경에서는 **모든 VPC에 Flow Logs를 활성화**하는 것이 보안 모범 사례입니다.
7. **비용 최적화**를 위해 필요한 트래픽 유형만 캡처하고, 수명 주기 정책을 적용하는 것이 중요합니다.

VPC Flow Logs는 단독으로도 강력하지만, GuardDuty, Security Hub, Detective 등 다른 AWS 보안 서비스와 결합하면 더욱 포괄적인 네트워크 보안 체계를 구축할 수 있습니다.