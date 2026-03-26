## 개요

AWS Compute Optimizer는 머신러닝 알고리즘을 활용하여 AWS 리소스의 사용 패턴을 분석하고, 비용 절감과 성능 향상을 위한 최적의 리소스 구성을 추천하는 서비스입니다. 많은 조직이 클라우드 리소스를 과도하게 프로비저닝(Over-provisioning)하거나 부족하게 프로비저닝(Under-provisioning)하는 문제를 겪고 있으며, Compute Optimizer는 이러한 비효율성을 데이터 기반으로 해결합니다.

기존의 리소스 최적화는 운영팀이 CloudWatch 메트릭을 수동으로 분석하고, 경험에 기반하여 인스턴스 타입을 변경하는 방식이었습니다. 이 접근 방식은 시간이 많이 소요되고, 최적의 선택이 아닌 경우가 많았습니다. Compute Optimizer는 Amazon 자체의 머신러닝 기술을 활용하여 수십 가지 인스턴스 타입과 구성 중에서 워크로드에 가장 적합한 옵션을 자동으로 식별합니다.

Compute Optimizer가 지원하는 리소스 유형은 다음과 같습니다.

- Amazon EC2 인스턴스
- Amazon EC2 Auto Scaling 그룹
- Amazon EBS 볼륨
- AWS Lambda 함수
- Amazon ECS on Fargate 서비스
- 상용 소프트웨어 라이선스

이 서비스는 추가 비용 없이 사용할 수 있으며, Enhanced Infrastructure Metrics 기능을 활성화하면 최대 93일간의 메트릭 데이터를 기반으로 더 정확한 추천을 받을 수 있습니다.

## 핵심 기능

### 리소스 추천 (Resource Recommendations)

Compute Optimizer는 각 리소스에 대해 현재 구성, 추천 구성, 예상 비용 절감액, 성능 위험도를 제공합니다. 추천은 크게 세 가지 카테고리로 분류됩니다.

- **Over-provisioned**: 리소스가 과도하게 할당되어 비용 낭비가 발생하는 경우
- **Under-provisioned**: 리소스가 부족하여 성능 저하가 발생할 수 있는 경우
- **Optimized**: 현재 구성이 적절한 경우

```bash
# Compute Optimizer 활성화 (계정 수준)
aws compute-optimizer update-enrollment-status \
  --status Active \
  --include-member-accounts

# 등록 상태 확인
aws compute-optimizer get-enrollment-status
```

### EC2 인스턴스 추천

EC2 인스턴스에 대해 CPU 사용률, 메모리 사용률(CloudWatch 에이전트 필요), 네트워크 I/O, 디스크 I/O 등의 메트릭을 분석하여 최적의 인스턴스 타입을 추천합니다.

```bash
# EC2 인스턴스 추천 조회
aws compute-optimizer get-ec2-instance-recommendations \
  --instance-arns arn:aws:ec2:ap-northeast-2:123456789012:instance/i-0123456789abcdef0 \
  --region ap-northeast-2

# 모든 EC2 인스턴스 추천 내보내기
aws compute-optimizer export-ec2-instance-recommendations \
  --s3-destination-config '{
    "bucket": "my-optimizer-reports",
    "keyPrefix": "ec2-recommendations"
  }' \
  --file-format Csv \
  --include-member-accounts
```

추천 결과에는 다음 정보가 포함됩니다.

- 현재 인스턴스 타입 및 가격
- 최대 3개의 추천 인스턴스 타입
- 각 추천에 대한 예상 월간 비용
- 성능 위험 점수 (낮을수록 좋음)
- CPU, 메모리, 네트워크, 디스크 활용률 그래프

### EBS 볼륨 추천

EBS 볼륨의 IOPS, 처리량, 볼륨 크기를 분석하여 적절한 볼륨 타입(gp2, gp3, io1, io2, st1, sc1)을 추천합니다.

```bash
# EBS 볼륨 추천 조회
aws compute-optimizer get-ebs-volume-recommendations \
  --volume-arns arn:aws:ec2:ap-northeast-2:123456789012:volume/vol-0123456789abcdef0

# 모든 EBS 추천 내보내기
aws compute-optimizer export-ebs-volume-recommendations \
  --s3-destination-config '{
    "bucket": "my-optimizer-reports",
    "keyPrefix": "ebs-recommendations"
  }' \
  --file-format Csv
```

특히 gp2에서 gp3로의 마이그레이션 추천이 많이 발생합니다. gp3는 gp2 대비 동일 성능에서 약 20% 저렴하며, IOPS와 처리량을 독립적으로 설정할 수 있어 비용 효율성이 높습니다.

### Lambda 함수 추천

Lambda 함수의 메모리 할당량을 분석하여 최적의 메모리 크기를 추천합니다. 메모리가 과도하게 할당된 경우 비용 절감을, 부족한 경우 성능 향상을 제안합니다.

```bash
# Lambda 함수 추천 조회
aws compute-optimizer get-lambda-function-recommendations \
  --function-arns arn:aws:lambda:ap-northeast-2:123456789012:function:my-function

# Lambda 추천 내보내기
aws compute-optimizer export-lambda-function-recommendations \
  --s3-destination-config '{
    "bucket": "my-optimizer-reports",
    "keyPrefix": "lambda-recommendations"
  }' \
  --file-format Csv
```

### ECS on Fargate 추천

ECS Fargate 서비스의 CPU 및 메모리 사용 패턴을 분석하여 태스크 정의의 CPU/메모리 구성을 최적화합니다.

```bash
# ECS 서비스 추천 조회
aws compute-optimizer get-ecs-service-recommendations \
  --service-arns arn:aws:ecs:ap-northeast-2:123456789012:service/my-cluster/my-service
```

### Enhanced Infrastructure Metrics

기본적으로 Compute Optimizer는 최근 14일간의 CloudWatch 메트릭을 분석합니다. Enhanced Infrastructure Metrics를 활성화하면 분석 기간이 최대 93일로 확장되어 더 정확한 추천을 받을 수 있습니다.

```bash
# Enhanced Infrastructure Metrics 활성화
aws compute-optimizer put-recommendation-preferences \
  --resource-type Ec2Instance \
  --scope '{
    "name": "AccountId",
    "value": "123456789012"
  }' \
  --enhanced-infrastructure-metrics Active

# 추천 선호도 확인
aws compute-optimizer get-recommendation-preferences \
  --resource-type Ec2Instance
```

이 기능은 유료이며, 분석 대상 리소스당 월별 소액의 비용이 발생합니다.

## 아키텍처/동작 원리

### 데이터 수집

Compute Optimizer는 CloudWatch에서 수집된 리소스 메트릭을 입력 데이터로 사용합니다. EC2 인스턴스의 경우 CPU 사용률, 네트워크 I/O, 디스크 I/O 메트릭을 자동으로 수집하며, CloudWatch 에이전트를 설치하면 메모리 사용률 데이터도 함께 분석에 활용됩니다.

### 머신러닝 분석

Amazon이 내부적으로 개발한 머신러닝 모델이 수집된 메트릭 데이터를 분석합니다. 단순 평균이 아닌 시계열 패턴, 피크 사용량, 주기적 패턴 등을 종합적으로 고려합니다. 이 모델은 수십만 개의 AWS 계정에서 학습된 데이터를 기반으로 지속적으로 개선됩니다.

### 추천 생성

분석 결과를 바탕으로 각 리소스에 대해 최대 3개의 추천 옵션을 생성합니다. 각 옵션에는 예상 비용, 성능 위험도, 워크로드 적합성 점수가 포함됩니다. 추천은 비용 절감 우선, 성능 우선 등 사용자의 선호도에 따라 필터링할 수 있습니다.

### 추천 갱신 주기

추천은 일반적으로 24~48시간마다 갱신됩니다. 리소스의 사용 패턴이 변경되면 추천도 자동으로 업데이트됩니다. 새로운 인스턴스 타입이 출시되면 해당 타입도 추천 후보에 포함됩니다.

## 실전 활용

### 조직 전체 비용 최적화 프로젝트

대규모 조직에서 Compute Optimizer를 활용한 비용 최적화 프로젝트를 진행하는 일반적인 절차입니다.

```bash
# 1. Organizations 전체에 Compute Optimizer 활성화
aws compute-optimizer update-enrollment-status \
  --status Active \
  --include-member-accounts

# 2. 모든 계정의 EC2 추천을 S3로 내보내기
aws compute-optimizer export-ec2-instance-recommendations \
  --s3-destination-config '{
    "bucket": "org-optimizer-reports",
    "keyPrefix": "ec2/monthly-review"
  }' \
  --file-format Csv \
  --include-member-accounts \
  --filters '[{"name": "Finding", "values": ["OVER_PROVISIONED"]}]'

# 3. EBS 추천도 함께 내보내기
aws compute-optimizer export-ebs-volume-recommendations \
  --s3-destination-config '{
    "bucket": "org-optimizer-reports",
    "keyPrefix": "ebs/monthly-review"
  }' \
  --file-format Csv \
  --include-member-accounts \
  --filters '[{"name": "Finding", "values": ["NotOptimized"]}]'
```

### Athena를 활용한 추천 분석

S3로 내보낸 추천 데이터를 Athena로 분석하여 비용 절감 잠재량을 산출할 수 있습니다.

```bash
# Athena 테이블 생성을 위한 쿼리 실행
aws athena start-query-execution \
  --query-string "
    CREATE EXTERNAL TABLE IF NOT EXISTS optimizer_ec2_recommendations (
      accountId STRING,
      instanceArn STRING,
      instanceName STRING,
      finding STRING,
      currentInstanceType STRING,
      recommendationOptions ARRAY<STRUCT<
        instanceType: STRING,
        estimatedMonthlySavings: DOUBLE,
        performanceRisk: DOUBLE
      >>
    )
    ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
    LOCATION 's3://org-optimizer-reports/ec2/monthly-review/'
  " \
  --result-configuration OutputLocation=s3://org-optimizer-reports/athena-results/ \
  --work-group primary
```

### 자동화된 추천 적용 (주의 필요)

Systems Manager Automation과 연계하여 추천을 반자동으로 적용할 수 있습니다. 다만, 프로덕션 환경에서는 반드시 검토 단계를 거치는 것을 권장합니다.

```python
import boto3

def get_savings_summary(region='ap-northeast-2'):
    """Compute Optimizer 추천을 기반으로 비용 절감 요약을 생성합니다."""
    client = boto3.client('compute-optimizer', region_name=region)
    
    # EC2 추천 조회
    response = client.get_ec2_instance_recommendations(
        filters=[{
            'name': 'Finding',
            'values': ['OVER_PROVISIONED']
        }]
    )
    
    total_monthly_savings = 0
    recommendations = []
    
    for rec in response.get('instanceRecommendations', []):
        instance_id = rec['instanceArn'].split('/')[-1]
        current_type = rec['currentInstanceType']
        
        if rec.get('recommendationOptions'):
            best_option = rec['recommendationOptions'][0]
            savings = best_option.get('estimatedMonthlySavings', {}).get('value', 0)
            total_monthly_savings += savings
            
            recommendations.append({
                'instance_id': instance_id,
                'current_type': current_type,
                'recommended_type': best_option['instanceType'],
                'monthly_savings': savings,
                'performance_risk': best_option.get('performanceRisk', 0)
            })
    
    return {
        'total_monthly_savings': total_monthly_savings,
        'recommendation_count': len(recommendations),
        'recommendations': sorted(recommendations, key=lambda x: x['monthly_savings'], reverse=True)
    }
```

### Graviton 프로세서 마이그레이션

Compute Optimizer는 ARM 기반 Graviton 인스턴스로의 마이그레이션도 추천합니다. Graviton 인스턴스는 x86 대비 최대 40% 더 나은 가성비를 제공합니다.

```bash
# Graviton 추천이 포함된 EC2 추천 조회
aws compute-optimizer get-ec2-instance-recommendations \
  --recommendation-preferences '{
    "cpuVendorArchitectures": ["AWS_ARM64", "CURRENT"]
  }'
```

## 모범 사례/보안

### 데이터 수집 최적화

1. **CloudWatch 에이전트 설치**: EC2 인스턴스에 CloudWatch 에이전트를 설치하여 메모리 사용률 데이터를 수집합니다. 메모리 데이터가 없으면 추천 정확도가 떨어집니다.

2. **충분한 데이터 수집 기간**: 최소 14일, 이상적으로는 Enhanced Infrastructure Metrics를 활성화하여 93일간의 데이터를 기반으로 추천을 받습니다.

3. **주기적인 검토**: 워크로드 패턴은 시간이 지남에 따라 변하므로, 최소 월 1회 추천을 검토합니다.

### 보안 고려사항

1. **IAM 권한 관리**: Compute Optimizer 접근 권한을 FinOps 팀이나 인프라 팀에만 부여합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "compute-optimizer:Get*",
        "compute-optimizer:Describe*",
        "compute-optimizer:Export*"
      ],
      "Resource": "*"
    }
  ]
}
```

2. **S3 버킷 암호화**: 추천 데이터를 내보내는 S3 버킷에 서버 측 암호화를 활성화합니다.
3. **교차 계정 접근 제한**: Organizations를 통해 중앙 계정에서만 전체 추천을 조회할 수 있도록 제한합니다.

### 추천 적용 시 주의사항

1. 프로덕션 인스턴스 타입 변경 전 반드시 스테이징 환경에서 테스트합니다.
2. Auto Scaling 그룹의 경우 Launch Template을 업데이트하고 인스턴스 새로 고침을 활용합니다.
3. 라이선스 기반 소프트웨어가 설치된 인스턴스의 경우 라이선스 호환성을 확인합니다.

## 관련 서비스 비교

### Compute Optimizer vs AWS Cost Explorer 추천

| 항목 | Compute Optimizer | Cost Explorer 추천 |
|------|-------------------|--------------------|
| 분석 방법 | 머신러닝 기반 | 규칙 기반 |
| 지원 리소스 | EC2, EBS, Lambda, ECS, ASG | EC2, RI, Savings Plans |
| 메트릭 분석 | CPU, 메모리, 네트워크, 디스크 | CPU 사용률 중심 |
| 추천 수 | 리소스당 최대 3개 | 리소스당 1개 |
| 성능 위험도 | 제공 | 미제공 |
| 비용 | 기본 무료 (Enhanced 유료) | Cost Explorer 활성화 시 무료 |

### Compute Optimizer vs Trusted Advisor

Trusted Advisor는 비용, 성능, 보안, 내결함성, 서비스 한도 전반에 걸친 광범위한 검사를 제공합니다. Compute Optimizer는 컴퓨팅 리소스 최적화에 특화되어 있어, 더 정교한 인스턴스 타입 추천을 제공합니다. 두 서비스를 함께 사용하는 것이 가장 효과적입니다.

### Compute Optimizer vs 타사 솔루션

Datadog, Spot.io, CloudHealth 등의 타사 솔루션도 리소스 최적화 기능을 제공합니다. 다만 Compute Optimizer는 AWS 네이티브 서비스로 추가 에이전트 설치 없이 사용할 수 있고, AWS의 내부 가격 데이터와 인스턴스 성능 데이터를 직접 활용하므로 추천 정확도가 높습니다.

## 요약

AWS Compute Optimizer는 머신러닝 기반으로 AWS 리소스의 사용 패턴을 분석하여 비용 절감과 성능 향상을 동시에 달성할 수 있는 추천을 제공하는 서비스입니다. EC2 인스턴스, EBS 볼륨, Lambda 함수, ECS Fargate 서비스, Auto Scaling 그룹 등 다양한 리소스 유형을 지원합니다.

기본 기능은 무료로 제공되며, Enhanced Infrastructure Metrics를 활성화하면 최대 93일간의 데이터를 기반으로 더 정확한 추천을 받을 수 있습니다. Organizations 전체에 활성화하여 중앙에서 비용 최적화 현황을 파악하고, S3로 내보낸 데이터를 Athena로 분석하면 조직 전체의 비용 절감 잠재량을 체계적으로 관리할 수 있습니다.

Compute Optimizer 도입 시에는 CloudWatch 에이전트를 설치하여 메모리 메트릭을 수집하고, 충분한 데이터 수집 기간을 확보한 후 추천을 검토하는 것이 중요합니다. 프로덕션 환경에 추천을 적용할 때는 반드시 사전 테스트를 거치고, 롤백 계획을 수립해야 합니다.