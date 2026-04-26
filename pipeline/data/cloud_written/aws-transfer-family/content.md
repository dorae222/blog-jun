<!-- infographic-hero -->
![AWS Transfer Family 핵심 요약](figures/infographic.svg)

*Figure: AWS Transfer Family 한 장 요약 인포그래픽*

## 개요

AWS Transfer Family는 AWS 스토리지 서비스(Amazon S3, Amazon EFS)를 대상으로 파일 전송을 수행할 수 있는 완전 관리형 서비스입니다. SFTP(SSH File Transfer Protocol), FTPS(FTP over SSL), FTP(File Transfer Protocol), AS2(Applicability Statement 2) 프로토콜을 지원하여 기존 파일 전송 워크플로우를 변경 없이 클라우드로 마이그레이션할 수 있습니다.

기업 간 데이터 교환, 파트너사와의 파일 전송, 고객 데이터 수집 등 다양한 B2B 파일 전송 시나리오에서 활용됩니다. 기존에는 SFTP 서버를 직접 운영하며 보안 패치, 고가용성 구성, 스토리지 관리 등을 직접 수행해야 했지만, Transfer Family를 사용하면 이러한 인프라 관리 부담을 AWS에 위임할 수 있습니다.

Transfer Family의 주요 장점은 다음과 같습니다.

- **완전 관리형**: 서버 프로비저닝, 패치, 모니터링이 자동으로 처리됩니다.
- **고가용성**: 다중 가용 영역(Multi-AZ) 배포로 99.99% SLA를 제공합니다.
- **탄력적 확장**: 동시 연결 수와 데이터 전송량에 따라 자동으로 확장됩니다.
- **기존 워크플로우 호환**: 클라이언트 측 변경 없이 기존 SFTP/FTPS/FTP 클라이언트를 그대로 사용할 수 있습니다.
- **AWS 서비스 통합**: S3, EFS, CloudWatch, IAM, Secrets Manager, Lambda 등과 긴밀하게 통합됩니다.

## 핵심 기능

### 지원 프로토콜

| 프로토콜 | 포트 | 암호화 | 사용 사례 |
|---|---|---|---|
| SFTP | 22 | SSH 기반 암호화 | 가장 일반적, 보안이 중요한 파일 전송 |
| FTPS | 990 (implicit), 21 (explicit) | TLS/SSL 암호화 | 레거시 FTP 환경의 보안 업그레이드 |
| FTP | 21 | 없음 (VPC 내부 전용) | 내부 네트워크 파일 전송 |
| AS2 | 443 | S/MIME + TLS | EDI, 공급망, 의료 데이터 교환 |

FTP는 암호화를 지원하지 않으므로 VPC 내부 엔드포인트에서만 사용할 수 있습니다. 인터넷에 노출되는 파일 전송 서버에는 반드시 SFTP 또는 FTPS를 사용해야 합니다.

### 서버 생성 및 구성

```bash
# SFTP 서버 생성 (공개 인터넷 접근)
aws transfer create-server \
  --protocols SFTP \
  --endpoint-type PUBLIC \
  --identity-provider-type SERVICE_MANAGED \
  --logging-role "arn:aws:iam::123456789012:role/TransferLoggingRole" \
  --security-policy-name "TransferSecurityPolicy-2024-01" \
  --tags '[{"Key": "Environment", "Value": "Production"}, {"Key": "Project", "Value": "B2BFileExchange"}]'

# VPC 엔드포인트를 사용하는 SFTP 서버 (프라이빗 접근)
aws transfer create-server \
  --protocols SFTP FTPS \
  --endpoint-type VPC \
  --endpoint-details '{
    "SubnetIds": ["subnet-0a1b2c3d4e5f6a7b8", "subnet-0b2c3d4e5f6a7b8c9"],
    "VpcId": "vpc-0123456789abcdef0",
    "SecurityGroupIds": ["sg-0123456789abcdef0"]
  }' \
  --identity-provider-type API_GATEWAY \
  --identity-provider-details '{
    "Url": "https://abc123.execute-api.ap-northeast-2.amazonaws.com/prod",
    "InvocationRole": "arn:aws:iam::123456789012:role/TransferAPIGatewayRole"
  }' \
  --logging-role "arn:aws:iam::123456789012:role/TransferLoggingRole" \
  --security-policy-name "TransferSecurityPolicy-2024-01"
```

### 엔드포인트 유형

Transfer Family는 세 가지 엔드포인트 유형을 제공합니다.

1. **PUBLIC**: 인터넷에서 직접 접근 가능. DNS 이름이 자동 할당됩니다(`s-xxxxx.server.transfer.ap-northeast-2.amazonaws.com`). 커스텀 도메인도 설정 가능합니다.

2. **VPC**: VPC 내부에 엔드포인트를 생성합니다. VPN이나 Direct Connect를 통한 프라이빗 접근에 적합합니다. Elastic IP를 연결하면 인터넷에서도 접근 가능하며, 이 경우 고정 IP 주소를 파트너에게 제공할 수 있습니다.

3. **VPC_ENDPOINT** (레거시): 이전 버전의 VPC 엔드포인트 방식으로, 신규 생성 시에는 VPC 유형을 사용하는 것이 권장됩니다.

```bash
# VPC 엔드포인트에 Elastic IP 연결 (고정 IP)
aws transfer update-server \
  --server-id "s-0123456789abcdef0" \
  --endpoint-details '{
    "AddressAllocationIds": ["eipalloc-0123456789abcdef0", "eipalloc-0abcdef0123456789"]
  }'

# 커스텀 도메인 설정 (Route 53)
aws route53 change-resource-record-sets \
  --hosted-zone-id Z0123456789 \
  --change-batch '{
    "Changes": [
      {
        "Action": "UPSERT",
        "ResourceRecordSet": {
          "Name": "sftp.example.com",
          "Type": "CNAME",
          "TTL": 300,
          "ResourceRecords": [
            {"Value": "s-0123456789abcdef0.server.transfer.ap-northeast-2.amazonaws.com"}
          ]
        }
      }
    ]
  }'
```

### 사용자 인증 방식

Transfer Family는 세 가지 인증 방식을 지원합니다.

#### 1. Service Managed (서비스 관리형)

SSH 공개 키 기반 인증입니다. 가장 간단한 설정 방식이며, 각 사용자의 공개 키를 Transfer Family에 직접 등록합니다.

```bash
# SFTP 사용자 생성 (서비스 관리형)
aws transfer create-user \
  --server-id "s-0123456789abcdef0" \
  --user-name "partner-company-a" \
  --role "arn:aws:iam::123456789012:role/TransferS3AccessRole" \
  --home-directory-type LOGICAL \
  --home-directory-mappings '[
    {
      "Entry": "/incoming",
      "Target": "/my-transfer-bucket/partner-a/incoming"
    },
    {
      "Entry": "/outgoing",
      "Target": "/my-transfer-bucket/partner-a/outgoing"
    }
  ]' \
  --ssh-public-key-body "ssh-rsa AAAAB3NzaC1yc2EAAAA... partner-a-key" \
  --tags '[{"Key": "Partner", "Value": "CompanyA"}]'

# 사용자에게 추가 SSH 키 등록
aws transfer import-ssh-public-key \
  --server-id "s-0123456789abcdef0" \
  --user-name "partner-company-a" \
  --ssh-public-key-body "ssh-rsa AAAAB3NzaC1yc2EAAAA... partner-a-key-2"
```

#### 2. API Gateway (커스텀 인증)

API Gateway + Lambda를 사용하여 커스텀 인증 로직을 구현합니다. Active Directory, LDAP, 데이터베이스 등 기존 인증 시스템과 통합할 수 있습니다.

```python
import json
import boto3
import os

def lambda_handler(event, context):
    """
    Transfer Family 커스텀 인증 Lambda 핸들러.
    Secrets Manager에서 사용자 자격 증명을 조회합니다.
    """
    username = event.get('username', '')
    password = event.get('password', '')
    server_id = event.get('serverId', '')
    protocol = event.get('protocol', '')
    source_ip = event.get('sourceIp', '')

    print(f"인증 요청: user={username}, server={server_id}, "
          f"protocol={protocol}, source={source_ip}")

    # IP 화이트리스트 검증
    allowed_ips = os.environ.get('ALLOWED_IPS', '').split(',')
    if allowed_ips[0] and source_ip not in allowed_ips:
        print(f"IP 차단: {source_ip}")
        return {}

    # Secrets Manager에서 사용자 정보 조회
    secrets_client = boto3.client('secretsmanager')
    try:
        secret_response = secrets_client.get_secret_value(
            SecretId=f"transfer/{server_id}/{username}"
        )
        user_config = json.loads(secret_response['SecretString'])
    except secrets_client.exceptions.ResourceNotFoundException:
        print(f"사용자 미발견: {username}")
        return {}

    # 비밀번호 검증 (SFTP 키 인증 시 password는 빈 문자열)
    if password:
        if user_config.get('Password') != password:
            print(f"비밀번호 불일치: {username}")
            return {}

    # 인증 성공 시 사용자 설정 반환
    response = {
        'Role': user_config['Role'],
        'HomeDirectoryType': 'LOGICAL',
        'HomeDirectoryDetails': json.dumps(user_config['HomeDirectoryDetails']),
        'Policy': json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AllowListingOfUserFolder",
                    "Effect": "Allow",
                    "Action": "s3:ListBucket",
                    "Resource": "arn:aws:s3:::${transfer:HomeBucket}",
                    "Condition": {
                        "StringLike": {
                            "s3:prefix": [
                                "${transfer:HomeFolder}/*",
                                "${transfer:HomeFolder}"
                            ]
                        }
                    }
                },
                {
                    "Sid": "AllowReadWriteToUserFolder",
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:DeleteObject",
                        "s3:GetObjectVersion"
                    ],
                    "Resource": "arn:aws:s3:::${transfer:HomeBucket}/${transfer:HomeFolder}/*"
                }
            ]
        })
    }

    # SSH 키 인증인 경우 공개 키 반환
    if not password and 'PublicKeys' in user_config:
        response['PublicKeys'] = user_config['PublicKeys']

    print(f"인증 성공: {username}")
    return response
```

#### 3. AWS Directory Service

AWS Managed Microsoft AD 또는 AD Connector를 통해 Active Directory 인증을 직접 사용합니다. 비밀번호 기반 인증이 필요한 SFTP, FTPS 환경에 적합합니다.

```bash
# Directory Service 연동 서버 생성
aws transfer create-server \
  --protocols SFTP \
  --endpoint-type PUBLIC \
  --identity-provider-type AWS_DIRECTORY_SERVICE \
  --identity-provider-details '{
    "DirectoryId": "d-0123456789"
  }' \
  --logging-role "arn:aws:iam::123456789012:role/TransferLoggingRole"

# AD 사용자에 대한 Transfer Family 접근 권한 설정
aws transfer create-access \
  --server-id "s-0123456789abcdef0" \
  --external-id "S-1-5-21-1234567890-1234567890-1234567890-1001" \
  --role "arn:aws:iam::123456789012:role/TransferS3AccessRole" \
  --home-directory-type LOGICAL \
  --home-directory-mappings '[
    {"Entry": "/", "Target": "/transfer-bucket/ad-users/${transfer:UserName}"}
  ]'
```

### 관리형 워크플로우(Managed Workflows)

Transfer Family의 관리형 워크플로우를 사용하면 파일 업로드 후 자동으로 처리 작업을 실행할 수 있습니다. 파일 복사, 태깅, 커스텀 Lambda 처리, 삭제 등의 단계를 조합합니다.

```bash
# 관리형 워크플로우 생성
aws transfer create-workflow \
  --description "파트너 파일 수신 후 검증 및 처리 워크플로우" \
  --steps '[
    {
      "Type": "COPY",
      "CopyStepDetails": {
        "Name": "CopyToProcessing",
        "DestinationFileLocation": {
          "S3FileLocation": {
            "Bucket": "my-processing-bucket",
            "Key": "incoming/${transfer.username}/"
          }
        },
        "OverwriteExisting": "TRUE"
      }
    },
    {
      "Type": "CUSTOM",
      "CustomStepDetails": {
        "Name": "ValidateFile",
        "Target": "arn:aws:lambda:ap-northeast-2:123456789012:function:validate-transfer-file",
        "TimeoutSeconds": 300
      }
    },
    {
      "Type": "TAG",
      "TagStepDetails": {
        "Name": "TagProcessed",
        "Tags": [
          {"Key": "Status", "Value": "Validated"},
          {"Key": "ProcessedAt", "Value": "${transfer.timestamp}"}
        ]
      }
    },
    {
      "Type": "DELETE",
      "DeleteStepDetails": {
        "Name": "CleanupOriginal"
      }
    }
  ]' \
  --on-exception-steps '[
    {
      "Type": "COPY",
      "CopyStepDetails": {
        "Name": "MoveToErrorBucket",
        "DestinationFileLocation": {
          "S3FileLocation": {
            "Bucket": "my-error-bucket",
            "Key": "failed/${transfer.username}/"
          }
        },
        "OverwriteExisting": "TRUE"
      }
    },
    {
      "Type": "CUSTOM",
      "CustomStepDetails": {
        "Name": "SendErrorNotification",
        "Target": "arn:aws:lambda:ap-northeast-2:123456789012:function:notify-transfer-error",
        "TimeoutSeconds": 60
      }
    }
  ]'

# 서버에 워크플로우 연결
aws transfer update-server \
  --server-id "s-0123456789abcdef0" \
  --workflow-details '{
    "OnUpload": [
      {
        "WorkflowId": "w-0123456789abcdef0",
        "ExecutionRole": "arn:aws:iam::123456789012:role/TransferWorkflowRole"
      }
    ],
    "OnPartialUpload": [
      {
        "WorkflowId": "w-0abcdef0123456789",
        "ExecutionRole": "arn:aws:iam::123456789012:role/TransferWorkflowRole"
      }
    ]
  }'
```

### AS2 프로토콜 (B2B 전송)

AS2(Applicability Statement 2)는 EDI(Electronic Data Interchange) 데이터를 안전하게 전송하기 위한 프로토콜로, 공급망 관리, 의료 데이터 교환, 금융 거래에서 널리 사용됩니다.

```bash
# AS2 프로파일 생성 (로컬)
aws transfer create-profile \
  --as2-id "MYCOMPANY-AS2-ID" \
  --profile-type LOCAL \
  --certificate-ids '["cert-0123456789abcdef0"]'

# AS2 파트너 프로파일 생성
aws transfer create-profile \
  --as2-id "PARTNER-AS2-ID" \
  --profile-type PARTNER \
  --certificate-ids '["cert-0abcdef0123456789"]'

# AS2 협약(Agreement) 생성
aws transfer create-agreement \
  --server-id "s-0123456789abcdef0" \
  --local-profile-id "p-local123" \
  --partner-profile-id "p-partner456" \
  --base-directory "/as2-bucket/incoming" \
  --access-role "arn:aws:iam::123456789012:role/TransferAS2Role" \
  --description "파트너사 EDI 데이터 수신 협약"

# AS2 커넥터 생성 (파트너에게 전송)
aws transfer create-connector \
  --url "https://partner-as2-endpoint.example.com" \
  --as2-config '{
    "LocalProfileId": "p-local123",
    "PartnerProfileId": "p-partner456",
    "MessageSubject": "EDI-Transfer",
    "Compression": "ZLIB",
    "EncryptionAlgorithm": "AES256_CBC",
    "SigningAlgorithm": "SHA256",
    "MdnSigningAlgorithm": "SHA256",
    "MdnResponse": "SYNC"
  }' \
  --access-role "arn:aws:iam::123456789012:role/TransferConnectorRole" \
  --logging-role "arn:aws:iam::123456789012:role/TransferLoggingRole"
```

## 아키텍처/동작 원리

### 내부 아키텍처

Transfer Family 서버는 내부적으로 다음과 같은 구성 요소로 동작합니다.

1. **프로토콜 엔드포인트**: SFTP/FTPS/FTP/AS2 프로토콜 요청을 수신하는 관리형 엔드포인트입니다. Multi-AZ로 배포되어 고가용성을 보장합니다.

2. **인증 계층**: 사용자 인증 요청을 Service Managed, API Gateway, 또는 Directory Service로 라우팅합니다. 인증 결과에 따라 IAM 역할, 홈 디렉터리, 세션 정책이 결정됩니다.

3. **스토리지 백엔드**: 인증된 파일 작업을 S3 또는 EFS API 호출로 변환합니다. 파일 읽기는 GetObject, 쓰기는 PutObject, 목록 조회는 ListObjectsV2로 매핑됩니다.

4. **워크플로우 엔진**: 파일 업로드 이벤트를 감지하고 정의된 워크플로우 단계를 순차적으로 실행합니다.

### Logical Home Directory 매핑

Logical Home Directory는 사용자에게 가상 디렉터리 구조를 제공합니다. 여러 S3 버킷이나 경로를 하나의 논리적 디렉터리 구조로 조합할 수 있어, 사용자가 실제 S3 구조를 알 필요가 없습니다.

```bash
# 복수 버킷을 매핑하는 사용자 생성
aws transfer create-user \
  --server-id "s-0123456789abcdef0" \
  --user-name "data-team" \
  --role "arn:aws:iam::123456789012:role/TransferMultiBucketRole" \
  --home-directory-type LOGICAL \
  --home-directory-mappings '[
    {"Entry": "/raw-data", "Target": "/datalake-raw-bucket/team-data"},
    {"Entry": "/processed", "Target": "/datalake-processed-bucket/team-data"},
    {"Entry": "/shared", "Target": "/shared-assets-bucket/common"},
    {"Entry": "/reports", "Target": "/reports-bucket/data-team/output"}
  ]'
```

### EFS 백엔드

S3 외에 Amazon EFS를 스토리지 백엔드로 사용할 수 있습니다. EFS를 사용하면 POSIX 파일 시스템 의미론(파일 잠금, 디렉터리 작업 등)을 완전히 지원하며, EC2 인스턴스에서 동일한 파일 시스템에 동시에 접근할 수 있습니다.

```bash
# EFS 백엔드 사용자 생성
aws transfer create-user \
  --server-id "s-0123456789abcdef0" \
  --user-name "app-uploader" \
  --role "arn:aws:iam::123456789012:role/TransferEFSAccessRole" \
  --home-directory-type PATH \
  --home-directory "/fs-0123456789abcdef0/uploads/app-data" \
  --posix-profile '{
    "Uid": 1001,
    "Gid": 1001,
    "SecondaryGids": [1002, 1003]
  }'
```

## 실전 활용

### B2B 파일 교환 플랫폼 구축

여러 파트너사와 안전하게 파일을 교환하는 플랫폼을 구축하는 종합 예제입니다.

```bash
# 1. SFTP 서버 생성 (VPC 엔드포인트 + 고정 IP)
SERVER_ID=$(aws transfer create-server \
  --protocols SFTP \
  --endpoint-type VPC \
  --endpoint-details '{
    "SubnetIds": ["subnet-az1", "subnet-az2"],
    "VpcId": "vpc-main",
    "SecurityGroupIds": ["sg-sftp"],
    "AddressAllocationIds": ["eipalloc-az1", "eipalloc-az2"]
  }' \
  --identity-provider-type API_GATEWAY \
  --identity-provider-details '{
    "Url": "https://api-id.execute-api.ap-northeast-2.amazonaws.com/prod",
    "InvocationRole": "arn:aws:iam::123456789012:role/TransferAPIRole"
  }' \
  --logging-role "arn:aws:iam::123456789012:role/TransferLoggingRole" \
  --security-policy-name "TransferSecurityPolicy-2024-01" \
  --workflow-details '{
    "OnUpload": [{
      "WorkflowId": "w-file-processing",
      "ExecutionRole": "arn:aws:iam::123456789012:role/WorkflowRole"
    }]
  }' \
  --query 'ServerId' --output text)

echo "서버 생성 완료: ${SERVER_ID}"

# 2. 보안 그룹 규칙 설정 (파트너 IP만 허용)
aws ec2 authorize-security-group-ingress \
  --group-id sg-sftp \
  --protocol tcp \
  --port 22 \
  --cidr 203.0.113.0/24  # 파트너 A IP 대역

aws ec2 authorize-security-group-ingress \
  --group-id sg-sftp \
  --protocol tcp \
  --port 22 \
  --cidr 198.51.100.0/24  # 파트너 B IP 대역
```

### 파일 전송 후 자동 처리 파이프라인

```python
import boto3
import json
import csv
import io

def validate_transfer_file(event, context):
    """
    Transfer Family 워크플로우에서 호출되는 파일 검증 Lambda.
    업로드된 파일의 형식과 내용을 검증합니다.
    """
    s3 = boto3.client('s3')
    transfer = boto3.client('transfer')

    # 워크플로우 이벤트에서 파일 정보 추출
    file_location = event['fileLocation']
    bucket = file_location['bucket']
    key = file_location['key']
    execution_id = event['executionId']
    workflow_id = event['workflowId']
    token = event['token']

    print(f"파일 검증 시작: s3://{bucket}/{key}")

    try:
        # 파일 메타데이터 확인
        head = s3.head_object(Bucket=bucket, Key=key)
        file_size = head['ContentLength']

        # 파일 크기 검증 (100MB 이하)
        max_size = 100 * 1024 * 1024
        if file_size > max_size:
            raise ValueError(f"파일 크기 초과: {file_size} > {max_size}")

        # CSV 파일인 경우 헤더 검증
        if key.endswith('.csv'):
            response = s3.get_object(
                Bucket=bucket,
                Key=key,
                Range='bytes=0-10240'  # 처음 10KB만 읽기
            )
            content = response['Body'].read().decode('utf-8')
            reader = csv.reader(io.StringIO(content))
            headers = next(reader)

            required_headers = ['id', 'date', 'amount']
            missing = [h for h in required_headers if h not in headers]
            if missing:
                raise ValueError(f"필수 컬럼 누락: {missing}")

        # 검증 성공
        transfer.send_workflow_step_state(
            WorkflowId=workflow_id,
            ExecutionId=execution_id,
            Token=token,
            Status='SUCCESS'
        )
        print(f"파일 검증 성공: {key}")

    except Exception as e:
        print(f"파일 검증 실패: {key}, 오류: {str(e)}")
        transfer.send_workflow_step_state(
            WorkflowId=workflow_id,
            ExecutionId=execution_id,
            Token=token,
            Status='FAILURE'
        )
```

### 모니터링 및 알림 설정

```bash
# 서버 상태 확인
aws transfer describe-server \
  --server-id "s-0123456789abcdef0" \
  --query '{State: State, Protocols: Protocols, EndpointType: EndpointType, UserCount: UserCount}'

# 사용자 세션 목록 조회
aws transfer list-executions \
  --workflow-id "w-0123456789abcdef0" \
  --max-results 20

# CloudWatch 메트릭으로 전송량 모니터링
aws cloudwatch get-metric-statistics \
  --namespace "AWS/Transfer" \
  --metric-name "BytesIn" \
  --dimensions Name=ServerId,Value=s-0123456789abcdef0 \
  --start-time "$(date -u -v-24H +%Y-%m-%dT%H:%M:%S)" \
  --end-time "$(date -u +%Y-%m-%dT%H:%M:%S)" \
  --period 3600 \
  --statistics Sum

# 파일 전송 실패 알람
aws cloudwatch put-metric-alarm \
  --alarm-name "Transfer-FileUploadFailures" \
  --namespace "AWS/Transfer" \
  --metric-name "FilesIn" \
  --dimensions Name=ServerId,Value=s-0123456789abcdef0 \
  --statistic Sum \
  --period 3600 \
  --threshold 0 \
  --comparison-operator LessThanOrEqualToThreshold \
  --evaluation-periods 6 \
  --alarm-actions "arn:aws:sns:ap-northeast-2:123456789012:transfer-alerts" \
  --alarm-description "6시간 동안 파일 수신이 없으면 알람"

# 워크플로우 실패 알람
aws cloudwatch put-metric-alarm \
  --alarm-name "Transfer-WorkflowFailures" \
  --namespace "AWS/Transfer" \
  --metric-name "OnUploadWorkflowFailed" \
  --dimensions Name=ServerId,Value=s-0123456789abcdef0 Name=WorkflowId,Value=w-0123456789abcdef0 \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --alarm-actions "arn:aws:sns:ap-northeast-2:123456789012:transfer-alerts"
```

## 모범 사례/보안

### 보안 정책 선택

Transfer Family는 여러 보안 정책을 제공하며, 지원하는 암호화 알고리즘과 프로토콜 버전이 다릅니다.

```bash
# 사용 가능한 보안 정책 목록 조회
aws transfer describe-security-policy \
  --security-policy-name "TransferSecurityPolicy-2024-01"
```

프로덕션 환경에서는 `TransferSecurityPolicy-2024-01` 이상을 사용하는 것이 권장됩니다. 이 정책은 취약한 암호화 알고리즘(SHA1, DES 등)을 비활성화하고 최신 보안 표준을 적용합니다.

### 세션 정책 (Scope-Down Policy)

사용자별로 S3 접근 범위를 제한하는 세션 정책을 적용합니다. IAM 역할의 권한을 더 좁은 범위로 제한할 수 있습니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowListingOfUserFolder",
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::${transfer:HomeBucket}",
      "Condition": {
        "StringLike": {
          "s3:prefix": [
            "${transfer:HomeFolder}/*",
            "${transfer:HomeFolder}"
          ]
        }
      }
    },
    {
      "Sid": "AllowReadWriteToUserFolder",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:GetObjectVersion"
      ],
      "Resource": "arn:aws:s3:::${transfer:HomeBucket}/${transfer:HomeFolder}/*"
    },
    {
      "Sid": "DenyDeletion",
      "Effect": "Deny",
      "Action": "s3:DeleteObject",
      "Resource": "*"
    }
  ]
}
```

### 운영 모범 사례

1. **VPC 엔드포인트 사용**: 프로덕션 환경에서는 PUBLIC 대신 VPC 엔드포인트를 사용하여 네트워크 보안을 강화합니다.
2. **IP 화이트리스트**: Security Group과 NACL로 허용된 IP만 접근할 수 있도록 제한합니다.
3. **CloudTrail 통합**: API 호출 감사를 위해 CloudTrail을 활성화합니다.
4. **CloudWatch Logs**: 상세 로깅을 활성화하여 모든 파일 전송 활동을 기록합니다.
5. **정기적 키 로테이션**: SSH 키와 인증서를 정기적으로 교체합니다.
6. **비용 관리**: 엔드포인트 시간당 요금($0.30/hour)과 데이터 전송량($0.04/GB)을 모니터링합니다.

```bash
# CloudTrail에서 Transfer Family 이벤트 조회
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventSource,AttributeValue=transfer.amazonaws.com \
  --start-time "$(date -u -v-24H +%Y-%m-%dT%H:%M:%S)" \
  --max-results 20
```

## 관련 서비스 비교

| 특성 | AWS Transfer Family | Amazon S3 직접 접근 | AWS Storage Gateway | 자체 SFTP 서버 |
|---|---|---|---|---|
| 프로토콜 | SFTP, FTPS, FTP, AS2 | HTTP/HTTPS (S3 API) | NFS, SMB, iSCSI | 자유 선택 |
| 관리 수준 | 완전 관리형 | 관리 불필요 | 반관리형 (VM 운영) | 직접 관리 |
| 인증 | SSH Key, Password, AD | IAM, Presigned URL | NFS/SMB 인증 | 자체 구현 |
| 고가용성 | Multi-AZ 기본 제공 | 기본 제공 | 단일 VM | 직접 구성 |
| 커스텀 워크플로우 | 관리형 워크플로우 | S3 이벤트 + Lambda | 제한적 | 직접 구현 |
| B2B 적합성 | 매우 높음 (AS2 지원) | 낮음 | 중간 | 높음 |
| 비용 | 시간당 + 전송량 | 요청당 + 스토리지 | 시간당 + 스토리지 | 인프라 + 운영비 |
| 적합한 상황 | 파트너 파일 교환, 레거시 통합 | API 기반 통합 | 하이브리드 스토리지 | 완전한 커스터마이징 |

**Transfer Family vs 자체 SFTP 서버**:
- 파트너 수가 10개 미만이고 간단한 파일 교환만 필요하면 Transfer Family가 비용 대비 효율적입니다.
- 복잡한 커스터마이징이나 특수 프로토콜이 필요하면 자체 서버가 적합합니다.
- Transfer Family의 시간당 요금($0.30)을 고려하면 월 약 $216의 기본 비용이 발생합니다. EC2 기반 SFTP 서버와 비교하여 운영 비용 절감 효과를 평가해야 합니다.

## 요약

AWS Transfer Family는 기존 파일 전송 프로토콜(SFTP, FTPS, FTP, AS2)을 지원하는 완전 관리형 서비스로, B2B 파일 교환과 레거시 시스템 통합에 최적화되어 있습니다. AWS S3 및 EFS와의 긴밀한 통합을 통해 클라우드 네이티브 스토리지의 이점을 활용하면서도 기존 클라이언트와의 호환성을 유지합니다.

핵심 포인트를 정리하면 다음과 같습니다.

- **프로토콜 선택**: 보안이 중요하면 SFTP, EDI/공급망 연동이면 AS2, 레거시 호환이 필요하면 FTPS를 선택합니다. FTP는 VPC 내부에서만 사용합니다.
- **인증 방식**: 소규모 환경은 Service Managed, 기존 인증 시스템 연동은 API Gateway, Windows AD 환경은 Directory Service를 선택합니다.
- **관리형 워크플로우**: 파일 업로드 후 검증, 변환, 알림 등의 처리를 자동화하여 운영 효율성을 높입니다.
- **보안**: VPC 엔드포인트, IP 화이트리스트, 세션 정책(Scope-Down Policy), 최신 보안 정책을 적용합니다.
- **AS2 프로토콜**: B2B EDI 데이터 교환에서 S/MIME 암호화와 MDN(Message Disposition Notification)을 통한 신뢰성 있는 전송을 지원합니다.
- **비용 고려**: 시간당 엔드포인트 비용과 데이터 전송량 비용을 모니터링하고, 사용 패턴에 따라 자체 서버와의 비용 비교를 수행합니다.

Transfer Family는 파일 전송 인프라의 관리 부담을 크게 줄여주지만, 비용과 커스터마이징의 제약을 고려하여 적합한 사용 사례를 선별하는 것이 중요합니다.