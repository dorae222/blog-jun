## 개요

AWS Backup은 AWS 서비스 전반에 걸쳐 데이터 백업을 중앙에서 관리하고 자동화할 수 있는 완전 관리형 백업 서비스입니다. 개별 서비스마다 별도의 백업 스크립트나 도구를 관리하는 대신, 단일 콘솔에서 통합된 백업 정책을 정의하고 적용할 수 있습니다.

기존에는 각 AWS 서비스(EBS 스냅샷, RDS 자동 백업, DynamoDB 백업 등)마다 별도의 백업 메커니즘을 관리해야 했습니다. 이는 운영 복잡성을 높이고, 백업 정책의 일관성을 유지하기 어렵게 만들었습니다. AWS Backup은 이러한 문제를 해결하기 위해 2019년에 출시되었습니다.

AWS Backup이 지원하는 주요 서비스는 다음과 같습니다.

- **컴퓨팅**: Amazon EC2 (AMI 포함), AWS CloudFormation 스택
- **스토리지**: Amazon S3, Amazon EBS, Amazon EFS, Amazon FSx (전 제품군)
- **데이터베이스**: Amazon RDS (전 엔진), Amazon Aurora, Amazon DynamoDB, Amazon Neptune, Amazon DocumentDB, Amazon Redshift
- **하이브리드**: AWS Storage Gateway (Volume Gateway)
- **기타**: Amazon Timestream, AWS VMware Cloud on AWS

## 핵심 기능

### 백업 계획(Backup Plan)

백업 계획은 AWS Backup의 핵심 구성 요소로, 백업 빈도, 보존 기간, 전환 규칙 등을 정의합니다. 하나의 백업 계획에 여러 규칙을 포함시킬 수 있으며, 태그 기반으로 리소스를 자동 할당할 수 있습니다.

```bash
# 백업 계획 생성
aws backup create-backup-plan \
  --backup-plan '{
    "BackupPlanName": "ProductionDailyBackup",
    "Rules": [
      {
        "RuleName": "DailyBackup",
        "TargetBackupVaultName": "production-vault",
        "ScheduleExpression": "cron(0 3 * * ? *)",
        "StartWindowMinutes": 60,
        "CompletionWindowMinutes": 180,
        "Lifecycle": {
          "MoveToColdStorageAfterDays": 30,
          "DeleteAfterDays": 365
        },
        "CopyActions": [
          {
            "DestinationBackupVaultArn": "arn:aws:backup:us-west-2:123456789012:backup-vault:dr-vault",
            "Lifecycle": {
              "DeleteAfterDays": 365
            }
          }
        ]
      },
      {
        "RuleName": "WeeklyBackup",
        "TargetBackupVaultName": "production-vault",
        "ScheduleExpression": "cron(0 5 ? * SUN *)",
        "StartWindowMinutes": 120,
        "CompletionWindowMinutes": 360,
        "Lifecycle": {
          "MoveToColdStorageAfterDays": 90,
          "DeleteAfterDays": 2555
        }
      },
      {
        "RuleName": "MonthlyBackup",
        "TargetBackupVaultName": "production-vault",
        "ScheduleExpression": "cron(0 6 1 * ? *)",
        "StartWindowMinutes": 120,
        "CompletionWindowMinutes": 720,
        "Lifecycle": {
          "MoveToColdStorageAfterDays": 90,
          "DeleteAfterDays": 2555
        }
      }
    ],
    "AdvancedBackupSettings": [
      {
        "ResourceType": "EC2",
        "BackupOptions": {
          "WindowsVSS": "enabled"
        }
      }
    ]
  }'
```

위 예시에서 일별, 주별, 월별 백업 규칙을 단일 계획에 정의했습니다. 각 규칙에는 시작 윈도우(백업이 시작되어야 하는 최대 대기 시간)와 완료 윈도우(백업이 완료되어야 하는 최대 시간)를 지정합니다. EC2 인스턴스에 대해서는 Windows VSS(Volume Shadow Copy Service) 옵션을 활성화하여 애플리케이션 일관성 있는 백업을 수행합니다.

### 리소스 할당

백업 계획에 리소스를 할당하는 방법은 두 가지입니다.

1. **태그 기반 할당**: 특정 태그를 가진 모든 리소스를 자동으로 백업 대상에 포함
2. **리소스 ARN 직접 지정**: 개별 리소스를 명시적으로 지정

```bash
# 태그 기반 리소스 할당
aws backup create-backup-selection \
  --backup-plan-id "12345678-1234-1234-1234-123456789012" \
  --backup-selection '{
    "SelectionName": "ProductionResources",
    "IamRoleArn": "arn:aws:iam::123456789012:role/AWSBackupDefaultServiceRole",
    "ListOfTags": [
      {
        "ConditionType": "STRINGEQUALS",
        "ConditionKey": "Environment",
        "ConditionValue": "Production"
      }
    ],
    "NotResources": [
      "arn:aws:ec2:ap-northeast-2:123456789012:instance/i-0temp*"
    ]
  }'
```

태그 기반 할당은 새로 생성되는 리소스에도 자동으로 적용되므로, 인프라 변경에 따른 백업 누락을 방지할 수 있습니다.

### 백업 볼트(Backup Vault)

백업 볼트는 복구 지점(Recovery Point)을 저장하는 논리적 컨테이너입니다. AWS KMS 키로 암호화되며, 액세스 정책을 통해 세밀한 접근 제어가 가능합니다.

```bash
# 백업 볼트 생성
aws backup create-backup-vault \
  --backup-vault-name production-vault \
  --encryption-key-arn arn:aws:kms:ap-northeast-2:123456789012:key/12345-abcde

# 볼트 액세스 정책 설정 (특정 역할만 삭제 허용)
aws backup put-backup-vault-access-policy \
  --backup-vault-name production-vault \
  --policy '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "DenyDeleteByNonAdmin",
        "Effect": "Deny",
        "Principal": "*",
        "Action": [
          "backup:DeleteRecoveryPoint",
          "backup:UpdateRecoveryPointLifecycle",
          "backup:PurgeRecoveryPoint"
        ],
        "Resource": "*",
        "Condition": {
          "StringNotEquals": {
            "aws:PrincipalArn": "arn:aws:iam::123456789012:role/BackupAdminRole"
          }
        }
      }
    ]
  }'
```

### 볼트 잠금(Vault Lock)

Vault Lock은 WORM(Write Once Read Many) 보호를 백업 볼트에 적용합니다. 한번 잠금이 설정되면 루트 사용자를 포함하여 누구도 잠금 설정을 변경하거나 보호된 복구 지점을 삭제할 수 없습니다.

```bash
# 볼트 잠금 설정 (Compliance 모드)
aws backup put-backup-vault-lock-configuration \
  --backup-vault-name compliance-vault \
  --min-retention-days 365 \
  --max-retention-days 2555 \
  --changeable-for-days 3
```

`changeable-for-days`는 유예 기간으로, 이 기간이 지나면 잠금 설정을 변경할 수 없습니다. 규정 준수 요구사항(HIPAA, PCI-DSS, SOC 2 등)을 충족하기 위해 필수적인 기능입니다.

### 크로스 리전/크로스 계정 백업

AWS Backup은 재해 복구(DR)를 위해 크로스 리전 및 크로스 계정 백업을 지원합니다.

```bash
# AWS Organizations 수준에서 크로스 계정 백업 활성화
aws backup update-region-settings \
  --resource-type-opt-in-preference '{
    "Aurora": true,
    "DynamoDB": true,
    "EBS": true,
    "EC2": true,
    "EFS": true,
    "FSx": true,
    "RDS": true,
    "S3": true
  }'

# 크로스 계정 백업 설정 확인
aws backup describe-region-settings
```

AWS Organizations와 통합하면 조직 전체에 걸쳐 일관된 백업 정책을 적용할 수 있습니다. 관리 계정에서 백업 정책을 정의하고 OU(Organizational Unit) 단위로 배포합니다.

## 아키텍처/동작 원리

### AWS Backup의 동작 흐름

AWS Backup의 백업 프로세스는 다음과 같은 흐름으로 동작합니다.

1. **스케줄 트리거**: 백업 계획에 정의된 cron 표현식에 따라 백업 작업이 시작됩니다.
2. **리소스 평가**: 백업 선택(Selection) 규칙에 따라 대상 리소스를 식별합니다.
3. **백업 수행**: 각 리소스 유형에 적합한 네이티브 백업 메커니즘을 호출합니다 (EBS 스냅샷, RDS 스냅샷 등).
4. **복구 지점 생성**: 백업 결과가 지정된 백업 볼트에 복구 지점으로 저장됩니다.
5. **복제 수행**: CopyAction이 정의되어 있으면 다른 리전/계정의 볼트로 복구 지점을 복제합니다.
6. **수명 주기 관리**: Lifecycle 규칙에 따라 복구 지점을 Cold Storage로 전환하거나 삭제합니다.

### 증분 백업

AWS Backup은 대부분의 리소스 유형에 대해 증분 백업을 수행합니다. 첫 번째 백업만 전체 백업(Full Backup)이고, 이후의 백업은 변경된 부분만 저장합니다. 이를 통해 백업 시간과 스토리지 비용을 크게 절감할 수 있습니다.

단, 복원 시에는 최신 복구 지점 하나만 지정하면 됩니다. 증분 백업의 체인을 수동으로 관리할 필요가 없으며, 각 복구 지점은 독립적으로 복원 가능합니다.

### 연속 백업(Continuous Backup)과 PITR

Amazon S3, Amazon RDS, Amazon Aurora에 대해서는 연속 백업을 지원합니다. 이를 통해 특정 시점 복원(Point-in-Time Recovery, PITR)이 가능합니다.

```bash
# S3 연속 백업이 포함된 백업 계획 생성
aws backup create-backup-plan \
  --backup-plan '{
    "BackupPlanName": "S3ContinuousBackup",
    "Rules": [
      {
        "RuleName": "ContinuousRule",
        "TargetBackupVaultName": "s3-backup-vault",
        "ScheduleExpression": "cron(0 0 * * ? *)",
        "Lifecycle": {
          "DeleteAfterDays": 35
        },
        "EnableContinuousBackup": true
      }
    ]
  }'
```

연속 백업을 활성화하면 최대 35일 이내의 임의 시점으로 데이터를 복원할 수 있습니다.

## 실전 활용

### 프로덕션 환경의 종합 백업 전략

실전에서는 GFS(Grandfather-Father-Son) 백업 전략을 적용하는 것이 일반적입니다.

```bash
# 1. 백업 볼트 생성 (프로덕션 + DR)
aws backup create-backup-vault \
  --backup-vault-name prod-primary-vault \
  --encryption-key-arn arn:aws:kms:ap-northeast-2:123456789012:key/primary-key-id \
  --region ap-northeast-2

aws backup create-backup-vault \
  --backup-vault-name prod-dr-vault \
  --encryption-key-arn arn:aws:kms:us-west-2:123456789012:key/dr-key-id \
  --region us-west-2

# 2. GFS 백업 계획 생성
aws backup create-backup-plan \
  --backup-plan '{
    "BackupPlanName": "ProductionGFS",
    "Rules": [
      {
        "RuleName": "HourlySnapshots",
        "TargetBackupVaultName": "prod-primary-vault",
        "ScheduleExpression": "cron(0 * * * ? *)",
        "StartWindowMinutes": 60,
        "CompletionWindowMinutes": 120,
        "Lifecycle": {
          "DeleteAfterDays": 1
        }
      },
      {
        "RuleName": "DailyBackup",
        "TargetBackupVaultName": "prod-primary-vault",
        "ScheduleExpression": "cron(0 18 * * ? *)",
        "StartWindowMinutes": 60,
        "CompletionWindowMinutes": 240,
        "Lifecycle": {
          "MoveToColdStorageAfterDays": 30,
          "DeleteAfterDays": 90
        },
        "CopyActions": [
          {
            "DestinationBackupVaultArn": "arn:aws:backup:us-west-2:123456789012:backup-vault:prod-dr-vault",
            "Lifecycle": {
              "DeleteAfterDays": 90
            }
          }
        ]
      },
      {
        "RuleName": "MonthlyArchive",
        "TargetBackupVaultName": "prod-primary-vault",
        "ScheduleExpression": "cron(0 20 1 * ? *)",
        "StartWindowMinutes": 120,
        "CompletionWindowMinutes": 720,
        "Lifecycle": {
          "MoveToColdStorageAfterDays": 30,
          "DeleteAfterDays": 2555
        }
      }
    ]
  }'

# 3. 태그 기반 리소스 할당
aws backup create-backup-selection \
  --backup-plan-id "<PLAN_ID>" \
  --backup-selection '{
    "SelectionName": "AllProductionResources",
    "IamRoleArn": "arn:aws:iam::123456789012:role/AWSBackupDefaultServiceRole",
    "ListOfTags": [
      {
        "ConditionType": "STRINGEQUALS",
        "ConditionKey": "Backup",
        "ConditionValue": "true"
      },
      {
        "ConditionType": "STRINGEQUALS",
        "ConditionKey": "Environment",
        "ConditionValue": "production"
      }
    ]
  }'
```

### 복원 테스트 자동화

백업이 실제로 복원 가능한지 정기적으로 검증하는 것이 중요합니다. AWS Backup의 복원 테스트 프레임워크를 활용할 수 있습니다.

```bash
# 복원 테스트 계획 생성
aws backup create-restore-testing-plan \
  --restore-testing-plan '{
    "RestoreTestingPlanName": "WeeklyRestoreTest",
    "ScheduleExpression": "cron(0 8 ? * MON *)",
    "StartWindowHours": 2,
    "RecoveryPointSelection": {
      "Algorithm": "LATEST_WITHIN_WINDOW",
      "RecoveryPointTypes": ["CONTINUOUS", "SNAPSHOT"],
      "IncludeVaults": ["prod-primary-vault"],
      "SelectionWindowDays": 7
    }
  }'

# 복원 테스트 대상 리소스 지정
aws backup create-restore-testing-selection \
  --restore-testing-plan-name "WeeklyRestoreTest" \
  --restore-testing-selection '{
    "RestoreTestingSelectionName": "RDSRestoreTest",
    "ProtectedResourceType": "RDS",
    "IamRoleArn": "arn:aws:iam::123456789012:role/AWSBackupRestoreTestRole",
    "ProtectedResourceConditions": {
      "StringEquals": [
        {
          "Key": "aws:ResourceTag/CriticalDB",
          "Value": "true"
        }
      ]
    },
    "RestoreMetadataOverrides": {
      "DBInstanceClass": "db.t3.medium"
    },
    "ValidationWindowHours": 2
  }'
```

### 온디맨드 백업 및 복원

```bash
# 특정 리소스의 온디맨드 백업
aws backup start-backup-job \
  --backup-vault-name production-vault \
  --resource-arn arn:aws:rds:ap-northeast-2:123456789012:db:my-production-db \
  --iam-role-arn arn:aws:iam::123456789012:role/AWSBackupDefaultServiceRole \
  --lifecycle DeleteAfterDays=30

# 백업 작업 상태 확인
aws backup describe-backup-job \
  --backup-job-id "<BACKUP_JOB_ID>"

# 복구 지점 목록 조회
aws backup list-recovery-points-by-backup-vault \
  --backup-vault-name production-vault \
  --by-resource-type RDS

# RDS 복원 실행
aws backup start-restore-job \
  --recovery-point-arn "arn:aws:backup:ap-northeast-2:123456789012:recovery-point:12345678" \
  --iam-role-arn arn:aws:iam::123456789012:role/AWSBackupDefaultServiceRole \
  --metadata '{
    "DBInstanceIdentifier": "restored-production-db",
    "DBInstanceClass": "db.r6g.xlarge",
    "MultiAZ": "true"
  }'
```

### CloudWatch 모니터링 연동

```python
import boto3
import json
from datetime import datetime, timedelta

def check_backup_compliance(days=1):
    """지난 N일간의 백업 작업 상태를 점검합니다."""
    backup_client = boto3.client('backup', region_name='ap-northeast-2')
    cloudwatch = boto3.client('cloudwatch', region_name='ap-northeast-2')
    sns = boto3.client('sns', region_name='ap-northeast-2')

    start_date = datetime.now() - timedelta(days=days)

    # 실패한 백업 작업 조회
    failed_jobs = backup_client.list_backup_jobs(
        ByState='FAILED',
        ByCreatedAfter=start_date
    )

    failed_count = len(failed_jobs.get('BackupJobs', []))

    # 커스텀 메트릭 발행
    cloudwatch.put_metric_data(
        Namespace='CustomBackupMonitoring',
        MetricData=[
            {
                'MetricName': 'FailedBackupJobs',
                'Value': failed_count,
                'Unit': 'Count',
                'Timestamp': datetime.now()
            }
        ]
    )

    if failed_count > 0:
        job_details = []
        for job in failed_jobs['BackupJobs']:
            job_details.append({
                'ResourceArn': job.get('ResourceArn'),
                'Status': job.get('State'),
                'Message': job.get('StatusMessage', 'N/A')
            })

        sns.publish(
            TopicArn='arn:aws:sns:ap-northeast-2:123456789012:backup-alerts',
            Subject=f'[경고] {failed_count}건의 백업 실패 감지',
            Message=json.dumps(job_details, indent=2, default=str)
        )

    return failed_count
```

## 모범 사례/보안

### 백업 보안 강화

1. **전용 KMS 키 사용**: 백업 볼트에 전용 CMK(Customer Managed Key)를 할당하여 암호화합니다.
2. **볼트 액세스 정책**: 최소 권한 원칙으로 복구 지점에 대한 접근을 제한합니다.
3. **볼트 잠금**: 규정 준수가 필요한 환경에서는 Vault Lock을 활성화합니다.
4. **크로스 계정 백업**: 별도의 보안 계정에 백업을 복제하여 랜섬웨어 공격으로부터 보호합니다.

### IAM 정책 분리

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowBackupOperations",
      "Effect": "Allow",
      "Action": [
        "backup:StartBackupJob",
        "backup:DescribeBackupJob",
        "backup:ListBackupJobs",
        "backup:ListRecoveryPointsByBackupVault"
      ],
      "Resource": "*"
    },
    {
      "Sid": "DenyDeleteOperations",
      "Effect": "Deny",
      "Action": [
        "backup:DeleteRecoveryPoint",
        "backup:DeleteBackupVault",
        "backup:DeleteBackupPlan"
      ],
      "Resource": "*"
    }
  ]
}
```

### 태그 전략

효과적인 백업 관리를 위해 일관된 태그 전략을 수립합니다.

```bash
# 리소스에 백업 관련 태그 부여
aws ec2 create-tags \
  --resources i-0123456789abcdef0 \
  --tags \
    Key=Backup,Value=true \
    Key=BackupPlan,Value=ProductionGFS \
    Key=Environment,Value=production \
    Key=DataClassification,Value=confidential \
    Key=RetentionRequired,Value=7years
```

### 비용 최적화

- **Cold Storage 전환**: 장기 보관 복구 지점은 Cold Storage로 전환하여 비용을 절감합니다. Cold Storage는 Warm Storage 대비 약 75% 저렴합니다.
- **보존 기간 최적화**: 규정 요구사항과 비즈니스 요구를 분석하여 적절한 보존 기간을 설정합니다.
- **리소스 유형별 전략**: 모든 리소스에 동일한 백업 빈도를 적용하지 말고, 중요도에 따라 차등 적용합니다.

## 관련 서비스 비교

| 특성 | AWS Backup | 네이티브 백업 (EBS Snapshot 등) | AWS Elastic Disaster Recovery |
|---|---|---|---|
| 관리 방식 | 중앙 집중식 | 서비스별 개별 관리 | 중앙 집중식 DR |
| 지원 서비스 | 20개 이상 | 개별 서비스 | EC2, 온프레미스 서버 |
| 크로스 리전 복제 | 지원 | 서비스별 상이 | 지원 |
| 크로스 계정 복제 | 지원 | 제한적 | 미지원 |
| PITR | S3, RDS, Aurora | RDS, Aurora | RPO 초 단위 |
| 볼트 잠금 | 지원 (WORM) | 미지원 | 해당 없음 |
| 복원 테스트 | 자동화 프레임워크 제공 | 수동 | 드릴 기능 제공 |
| 규정 준수 보고 | Backup Audit Manager | 수동 구성 필요 | 제한적 |
| 비용 | 백업 스토리지 + 복원 비용 | 서비스별 스냅샷 비용 | 복제 인스턴스 비용 |
| 적합한 상황 | 통합 백업 관리, 규정 준수 | 단일 서비스 단순 백업 | 실시간 DR, 낮은 RPO/RTO |

AWS Backup Audit Manager는 백업 활동에 대한 감사 보고서를 자동으로 생성합니다. 백업 빈도, 보존 기간, 암호화 상태 등이 조직의 정책에 부합하는지 지속적으로 모니터링할 수 있습니다.

```bash
# 감사 프레임워크 생성
aws backup create-framework \
  --framework-name "ComplianceFramework" \
  --framework-controls '[
    {
      "ControlName": "BACKUP_RESOURCES_PROTECTED_BY_BACKUP_PLAN",
      "ControlInputParameters": [
        {"ParameterName": "resourceType", "ParameterValue": "RDS"}
      ]
    },
    {
      "ControlName": "BACKUP_RECOVERY_POINT_ENCRYPTED",
      "ControlInputParameters": []
    },
    {
      "ControlName": "BACKUP_RECOVERY_POINT_MINIMUM_RETENTION_CHECK",
      "ControlInputParameters": [
        {"ParameterName": "requiredRetentionDays", "ParameterValue": "30"}
      ]
    },
    {
      "ControlName": "BACKUP_PLAN_MIN_FREQUENCY_AND_MIN_RETENTION_CHECK",
      "ControlInputParameters": [
        {"ParameterName": "requiredFrequencyUnit", "ParameterValue": "hours"},
        {"ParameterName": "requiredFrequencyValue", "ParameterValue": "24"},
        {"ParameterName": "requiredRetentionDays", "ParameterValue": "35"}
      ]
    }
  ]'
```

## 요약

AWS Backup은 AWS 환경에서 백업 관리를 간소화하고 자동화하는 핵심 서비스입니다. 개별 서비스의 네이티브 백업 기능을 직접 관리하는 것에 비해, 중앙 집중식 정책 관리, 크로스 리전/크로스 계정 복제, 규정 준수 감사 등 엔터프라이즈 수준의 기능을 제공합니다.

핵심 포인트를 정리하면 다음과 같습니다.

- **백업 계획**: GFS 전략을 적용하여 일별/주별/월별 백업을 체계적으로 관리합니다. 태그 기반 리소스 할당으로 새 리소스에도 자동으로 백업 정책을 적용합니다.
- **데이터 보호**: 볼트 잠금(WORM)으로 복구 지점의 무단 삭제를 방지하고, 크로스 계정 백업으로 랜섬웨어 공격에 대비합니다.
- **연속 백업**: S3, RDS, Aurora에 대해 PITR을 활성화하여 임의 시점으로의 복원을 지원합니다.
- **규정 준수**: Backup Audit Manager를 통해 백업 정책 준수 여부를 지속적으로 모니터링하고 보고합니다.
- **복원 검증**: 정기적인 복원 테스트를 자동화하여 백업의 실제 복원 가능성을 검증합니다.
- **비용 최적화**: Cold Storage 전환, 적절한 보존 기간 설정, 리소스 중요도에 따른 차등 백업 전략으로 비용을 관리합니다.

백업은 설정만으로 끝나지 않습니다. 정기적인 복원 테스트, 모니터링 알림 설정, 그리고 규정 준수 감사를 통해 백업 체계의 실효성을 지속적으로 검증하는 것이 중요합니다.