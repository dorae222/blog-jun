<!-- infographic-hero -->
![Amazon EMR 핵심 요약](figures/infographic.svg)

*Figure: Amazon EMR 한 장 요약 인포그래픽*

# Amazon EMR (Elastic MapReduce) 개요

## 개요

Amazon EMR(Elastic MapReduce)은 Apache Spark, Hive, Presto, Trino, Flink, HBase, Hudi, Iceberg 등 빅데이터 프레임워크를 AWS에서 손쉽게 실행할 수 있는 관리형 클러스터 플랫폼입니다. 2009년 출시된 이래 AWS의 가장 오래된 분석 서비스 중 하나이며, 페타바이트 규모의 데이터를 처리하는 수많은 기업에서 사용되고 있습니다.

EMR이 등장하기 전, Hadoop 클러스터를 직접 운영하려면 다음과 같은 작업이 필요했습니다.

- 수십~수백 대의 서버 프로비저닝
- HDFS, YARN, Spark, Hive 등 컴포넌트 설치 및 버전 관리
- 클러스터 매니저 구성, 모니터링, 로그 수집
- 노드 장애 대응, 데이터 리밸런싱
- 보안 설정 (Kerberos, 암호화)

EMR은 이 모든 작업을 추상화하여 콘솔 클릭 또는 API 호출 한 번으로 수십~수천 대의 빅데이터 클러스터를 분 단위로 배포할 수 있게 합니다. 작업이 끝나면 클러스터를 종료하여 비용을 절약할 수 있고, S3에 데이터를 저장하면 클러스터 수명과 데이터 수명을 분리할 수 있습니다.

EMR의 핵심 가치는 다음과 같습니다.

- **빠른 배포**: 분 단위 클러스터 생성
- **유연한 확장**: 수동 또는 자동으로 노드 추가/제거
- **비용 효율**: Spot 인스턴스, 트랜시언트 클러스터(Transient Cluster)로 비용 절감
- **다양한 프레임워크**: 30여 개의 오픈소스 빅데이터 도구
- **AWS 통합**: S3, Glue Data Catalog, Lake Formation, IAM 등

---

## 핵심 기능

### 1. 3가지 배포 모드

EMR은 워크로드 특성에 따라 세 가지 배포 모드를 제공합니다.

| 배포 모드 | 출시 | 특징 | 적합 워크로드 |
|----------|------|------|--------------|
| EMR on EC2 | 2009 | 전통적 클러스터. 노드별 EC2 직접 사용 | 장시간 실행, 모든 EMR 프레임워크 |
| EMR on EKS | 2020 | Kubernetes 기반 Spark 실행 | 컨테이너 표준화, Spark 위주 |
| EMR Serverless | 2022 | 인프라 관리 없는 서버리스 | 간헐적 작업, 빠른 시작 |

**EMR on EC2**

가장 전통적인 방식으로 모든 EMR 기능을 지원합니다. Master, Core, Task 노드 구조를 명시적으로 관리합니다.

```bash
# EMR on EC2 클러스터 생성 (Spark + Hive)
aws emr create-cluster \
  --name "data-pipeline-cluster" \
  --release-label emr-7.0.0 \
  --applications Name=Spark Name=Hive Name=Hadoop \
  --instance-groups \
    InstanceGroupType=MASTER,InstanceType=m6g.xlarge,InstanceCount=1 \
    InstanceGroupType=CORE,InstanceType=r6g.2xlarge,InstanceCount=3 \
    InstanceGroupType=TASK,InstanceType=r6g.2xlarge,InstanceCount=5 \
  --ec2-attributes KeyName=my-key,SubnetId=subnet-0123456789abcdef0 \
  --use-default-roles \
  --log-uri s3://my-emr-logs/ \
  --region ap-northeast-2
```

**EMR on EKS**

Kubernetes 클러스터 위에서 Spark 작업을 실행합니다. 다른 컨테이너 워크로드와 인프라를 공유할 수 있어 비용 효율적입니다.

```bash
# Virtual Cluster 생성 (EKS 네임스페이스에 매핑)
aws emr-containers create-virtual-cluster \
  --name spark-virtual-cluster \
  --container-provider '{
    "id": "my-eks-cluster",
    "type": "EKS",
    "info": {"eksInfo": {"namespace": "spark"}}
  }'

# Spark Job 실행
aws emr-containers start-job-run \
  --virtual-cluster-id abc123def456 \
  --name spark-pi-job \
  --execution-role-arn arn:aws:iam::123456789012:role/EMRContainersJobExecutionRole \
  --release-label emr-7.0.0-latest \
  --job-driver '{
    "sparkSubmitJobDriver": {
      "entryPoint": "s3://my-bucket/scripts/pi.py",
      "sparkSubmitParameters": "--conf spark.executor.instances=2"
    }
  }'
```

**EMR Serverless**

인프라를 완전히 추상화하여 작업 실행에만 집중할 수 있습니다. Spark와 Hive를 지원하며, 사용한 vCPU/메모리 시간만큼만 과금됩니다.

```bash
# Application 생성
aws emr-serverless create-application \
  --name spark-app \
  --release-label emr-7.0.0 \
  --type SPARK \
  --initial-capacity '{
    "DRIVER": {"workerCount": 1, "workerConfiguration": {"cpu": "4 vCPU", "memory": "16 GB"}},
    "EXECUTOR": {"workerCount": 4, "workerConfiguration": {"cpu": "4 vCPU", "memory": "16 GB"}}
  }' \
  --maximum-capacity '{"cpu": "100 vCPU", "memory": "400 GB"}'

# Job 실행
aws emr-serverless start-job-run \
  --application-id 00f1abc23def \
  --execution-role-arn arn:aws:iam::123456789012:role/EMRServerlessJobRole \
  --job-driver '{
    "sparkSubmit": {
      "entryPoint": "s3://my-bucket/scripts/etl.py",
      "sparkSubmitParameters": "--conf spark.executor.cores=4"
    }
  }'
```

### 2. EMR on EC2 노드 역할

전통적 EMR 클러스터는 세 종류의 노드로 구성됩니다.

| 노드 타입 | 역할 | 개수 | 스토리지 |
|----------|------|------|---------|
| Master | YARN ResourceManager, HDFS NameNode, 클러스터 관리 | 1개 (EMR 5.23+ HA는 3개) | EBS |
| Core | 데이터 저장(HDFS DataNode) + 작업 실행 | 1개 이상 | EBS (HDFS) |
| Task | 작업 실행만 (HDFS 없음) | 0개 이상 | EBS (임시) |

Task 노드는 HDFS 데이터를 저장하지 않으므로 Spot 인스턴스로 운영하기에 가장 안전합니다. 인스턴스가 회수되어도 데이터 손실이 없습니다.

```bash
# Spot Task 노드 추가
aws emr modify-instance-groups \
  --cluster-id j-1ABCD2345EFGH \
  --instance-groups InstanceGroupId=ig-task1,InstanceCount=10
```

### 3. Instance Fleet vs Instance Group

EMR은 두 가지 노드 프로비저닝 방식을 제공합니다.

**Instance Group**

- 노드 타입별로 단일 인스턴스 타입 사용
- 단순하지만 유연성이 낮음

**Instance Fleet (권장)**

- 여러 인스턴스 타입을 가중치로 혼합 가능
- Spot 인스턴스 가용성에 따라 자동 선택
- AZ 가용성에 따라 자동 분산
- 가격 최적화에 유리

```bash
# Instance Fleet 기반 클러스터 (Spot 우선)
aws emr create-cluster \
  --name "fleet-cluster" \
  --release-label emr-7.0.0 \
  --applications Name=Spark \
  --instance-fleets '[
    {
      "Name": "Master",
      "InstanceFleetType": "MASTER",
      "TargetOnDemandCapacity": 1,
      "InstanceTypeConfigs": [{"InstanceType": "m6g.xlarge"}]
    },
    {
      "Name": "Core",
      "InstanceFleetType": "CORE",
      "TargetOnDemandCapacity": 2,
      "TargetSpotCapacity": 8,
      "InstanceTypeConfigs": [
        {"InstanceType": "r6g.2xlarge", "WeightedCapacity": 1},
        {"InstanceType": "r6g.4xlarge", "WeightedCapacity": 2},
        {"InstanceType": "r5.2xlarge", "WeightedCapacity": 1}
      ]
    }
  ]'
```

### 4. Storage 옵션

EMR은 여러 스토리지 백엔드를 지원합니다.

| 스토리지 | 위치 | 특징 | 적합 사례 |
|---------|------|------|----------|
| HDFS | 로컬 EBS | 가장 빠름. 클러스터 종료 시 데이터 소실 | 임시 셔플, 중간 데이터 |
| EMRFS | S3 백엔드 | 영구 저장. 클러스터와 데이터 수명 분리 | 입력/출력 데이터, 데이터 레이크 |
| Local FS | 인스턴스 스토어 | 매우 빠른 임시 디스크 | Spark Shuffle 캐시 |
| DynamoDB | DynamoDB | 메타데이터 저장 (HBase, EMRFS Consistent View) | 트랜잭션 메타데이터 |

EMRFS는 S3를 HDFS처럼 사용할 수 있게 해주는 EMR 전용 파일 시스템입니다. S3에 데이터를 저장하면 클러스터를 종료해도 데이터가 유지되며, 다른 EMR 클러스터에서 즉시 접근할 수 있습니다.

```python
# Spark에서 S3 직접 읽기/쓰기 (EMRFS)
df = spark.read.parquet("s3://my-data-lake/raw/events/")
df.filter("event_type = 'purchase'") \
  .write.partitionBy("date") \
  .parquet("s3://my-data-lake/curated/purchases/")
```

### 5. Auto Scaling

EMR은 두 가지 자동 확장 옵션을 제공합니다.

**Managed Scaling (2019+, 권장)**

- AWS가 메트릭과 워크로드 기반으로 자동 확장
- 최소/최대 노드 수만 지정
- 가장 단순하고 효과적

```bash
# Managed Scaling 활성화
aws emr put-managed-scaling-policy \
  --cluster-id j-1ABCD2345EFGH \
  --managed-scaling-policy '{
    "ComputeLimits": {
      "UnitType": "Instances",
      "MinimumCapacityUnits": 2,
      "MaximumCapacityUnits": 50,
      "MaximumCoreCapacityUnits": 10,
      "MaximumOnDemandCapacityUnits": 5
    }
  }'
```

**Custom Auto Scaling Policy**

CloudWatch 메트릭(YARN Memory, Container Pending 등) 기반으로 사용자 정의 스케일링 규칙을 작성할 수 있습니다. Managed Scaling으로 처리되지 않는 특수한 패턴에만 사용을 권장합니다.

### 6. EMR Studio

EMR Studio는 데이터 사이언티스트를 위한 통합 IDE입니다.

- Jupyter Notebook과 JupyterLab 기반
- Git 통합
- 여러 EMR 클러스터에 연결 가능
- IAM Identity Center 또는 IAM 인증
- Workspace를 S3에 자동 백업

EMR Studio Notebook은 Sparkmagic을 통해 PySpark, Spark SQL, Scala를 실행하며, 결과를 인터랙티브하게 시각화할 수 있습니다.

---

## 아키텍처

### EMR on EC2 클러스터 구조

```
[Client / Boto3 / EMR Studio]
            |
            v
    [Step Submission]
            |
            v
+-----------+-----------+
|     Master Node       |
|  - YARN ResourceMgr   |
|  - HDFS NameNode      |
|  - Hive Metastore     |
+-----------+-----------+
            |
            +----+----+----+
            |    |    |
            v    v    v
        [Core] [Core] [Core]
        - HDFS DataNode
        - YARN NodeMgr
        - Spark Executor
            |
            +----+----+----+
                 v    v    v
              [Task][Task][Task]
              - YARN NodeMgr
              - Spark Executor
                 |
                 v
              [S3 / EMRFS]
```

YARN(Yet Another Resource Negotiator)이 클러스터 리소스를 중앙에서 관리하며, Spark/Hive/Flink 등 모든 프레임워크가 YARN 위에서 실행됩니다.

### EMR on EKS 아키텍처

```
[Spark Job Submission via emr-containers API]
            |
            v
[EMR on EKS Control Plane]
            |
            v
[EKS Cluster - 사용자 소유]
       |
       +-- [Namespace: spark]
            |
            +-- [Spark Driver Pod]
                |
                +-- [Spark Executor Pod x N]
            |
            +-- [Volcano / YuniKorn (옵션) - 스케줄러]
```

EMR on EKS는 Spark Driver/Executor를 Pod으로 실행하므로, Kubernetes의 격리 모델과 자원 관리 기능을 그대로 활용할 수 있습니다. 다른 워크로드와 동일 EKS 클러스터를 공유하면서도 namespace 단위로 격리됩니다.

### EMR Serverless 아키텍처

```
[Job Submission]
       |
       v
[EMR Serverless Application]
       | (사전 워밍된 워커 풀 - Pre-warmed)
       v
[Spark Driver (자동 프로비저닝)]
       |
       +-- [Executor x N (자동 확장)]
              |
              v
          [S3 데이터]
```

EMR Serverless는 사전 워밍된 워커 풀을 유지하여 콜드 스타트를 1분 이내로 단축합니다. `initialCapacity`로 사전 할당량을 지정하면 더 빠른 시작이 가능합니다.

---

## 실전 사용

### 1. Step Functions로 ETL 파이프라인 구성

```json
{
  "StartAt": "RunSparkJob",
  "States": {
    "RunSparkJob": {
      "Type": "Task",
      "Resource": "arn:aws:states:::elasticmapreduce:addStep.sync",
      "Parameters": {
        "ClusterId.$": "$.ClusterId",
        "Step": {
          "Name": "Daily ETL",
          "ActionOnFailure": "CONTINUE",
          "HadoopJarStep": {
            "Jar": "command-runner.jar",
            "Args": [
              "spark-submit", "--deploy-mode", "cluster",
              "s3://my-bucket/etl.py", "--date", "2026-04-25"
            ]
          }
        }
      },
      "End": true
    }
  }
}
```

### 2. Glue Data Catalog 통합

EMR Hive Metastore를 AWS Glue Data Catalog로 대체하면 EMR 클러스터, Athena, Redshift Spectrum, Glue ETL 모두가 동일한 메타데이터를 공유할 수 있습니다.

```json
{
  "Classification": "spark-hive-site",
  "Properties": {
    "hive.metastore.client.factory.class": "com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory"
  }
}
```

위 설정을 EMR 클러스터 생성 시 Configuration으로 전달하면 Glue Catalog를 자동 사용합니다.

### 3. Trino로 Federated Query

Trino(구 PrestoSQL)는 여러 데이터 소스를 SQL로 조회할 수 있는 엔진입니다.

```sql
-- S3의 Parquet과 RDS PostgreSQL을 조인
SELECT
  s.user_id,
  s.event_count,
  u.email,
  u.signup_date
FROM hive.events.user_events s
JOIN postgres.public.users u
  ON s.user_id = u.id
WHERE s.event_date = DATE '2026-04-25';
```

### 4. Spot 비용 최적화

Task 노드를 Spot으로 운영하면 최대 90% 비용 절감이 가능합니다. Instance Fleet과 함께 사용하면 가용성도 개선됩니다.

- Master 노드: 항상 OnDemand
- Core 노드: HDFS 데이터 손실 위험을 감안하여 OnDemand 또는 Spot Mix
- Task 노드: 100% Spot 가능

### 5. Graviton 활용

EMR 7.0+ 는 Graviton 인스턴스(c7g, m7g, r7g)를 완전 지원합니다. x86 대비 최대 30% 가격 대비 성능 개선이 가능합니다.

---

## 가격/한도

### 가격 구성

EMR 비용은 두 가지로 구성됩니다.

1. **EC2 인스턴스 비용**: 일반 EC2 가격 (Spot/RI 적용 가능)
2. **EMR 추가 요금**: 인스턴스당 시간당 $0.026~$0.27

| 인스턴스 클래스 | EMR 추가 요금/시간 |
|---------------|-------------------|
| m6g.xlarge | $0.048 |
| r6g.2xlarge | $0.126 |
| m6g.16xlarge | $0.27 |

**EMR Serverless 가격**

- vCPU 시간당 $0.052624
- 메모리 GB 시간당 $0.0057785
- Storage(추가 셔플 스토리지): GB 시간당 $0.000111

**EMR on EKS 가격**

- 기본 EKS 클러스터 비용 (시간당 $0.10)
- EMR on EKS 추가: vCPU 시간당 $0.01012, 메모리 GB 시간당 $0.00111125

### 주요 한도

| 항목 | 한도 |
|------|------|
| 계정/리전당 활성 클러스터 수 | 25 (요청 시 증가 가능) |
| 클러스터당 노드 수 | 수천 대 (실용적 한도) |
| 클러스터당 동시 Step 수 | 256 |
| 인스턴스 타입 종류 (Fleet) | 30 (Master 5개, Core/Task 30개) |

---

## Best Practice

### 1. Transient Cluster 사용

작업 시작 시 클러스터를 생성하고 작업 완료 시 자동 종료하는 패턴을 사용합니다. 비용을 80% 이상 절감할 수 있습니다.

```bash
aws emr create-cluster \
  --name "transient-job" \
  --auto-terminate \
  --steps Type=Spark,Name="ETL",ActionOnFailure=TERMINATE_CLUSTER,Args=[s3://my-bucket/etl.py]
```

### 2. S3를 데이터 레이크로

HDFS 대신 S3(EMRFS)를 기본 스토리지로 사용합니다.

- 클러스터와 데이터의 수명을 분리
- 다른 서비스(Athena, Redshift Spectrum, Glue)에서도 동일 데이터 접근
- S3 Intelligent-Tiering으로 비용 자동 최적화

### 3. Glue Data Catalog 통합

Hive Metastore를 Glue Data Catalog로 통합하여 메타데이터 단일 소스(Single Source of Truth)를 유지합니다.

### 4. EMR Serverless 우선 검토

다음 조건에 해당하면 EMR Serverless를 우선 검토합니다.

- 작업이 간헐적이거나 예측 불가능한 패턴
- 클러스터 운영 부담을 줄이고 싶음
- Spark 또는 Hive만 사용
- 빠른 시작 시간이 중요

장시간 실행되는 클러스터, HBase, Presto/Trino 사용 시에는 EMR on EC2가 적합합니다.

### 5. 모니터링과 로깅

- 모든 클러스터 로그는 S3로 자동 전송 설정
- CloudWatch Container Insights 활성화
- Spark UI는 Persistent Application UI로 접근 (클러스터 종료 후에도 조회 가능)

### 6. Auto Termination

Idle Timeout을 설정하여 작업이 없으면 자동 종료되도록 구성합니다.

```bash
aws emr put-auto-termination-policy \
  --cluster-id j-1ABCD2345EFGH \
  --auto-termination-policy '{"IdleTimeout": 3600}'
```

---

## 관련 서비스 비교

| 항목 | Amazon EMR | AWS Glue | Amazon Athena |
|------|-----------|----------|---------------|
| 유형 | 관리형 빅데이터 클러스터 | 서버리스 ETL | 서버리스 SQL 쿼리 |
| 프레임워크 | Spark, Hive, Presto, Flink, HBase 등 30+ | Spark (Glue ETL), Python | Trino |
| 운영 부담 | EC2 모드는 클러스터 관리, Serverless는 무관리 | 완전 무관리 | 완전 무관리 |
| 시작 시간 | EC2 5~10분, Serverless 1분 미만 | 1분 미만 | 즉시 |
| 가격 모델 | 인스턴스 시간 + EMR 요금 | DPU 시간 ($0.44/DPU-hour) | 스캔 데이터 TB ($5/TB) |
| 적합 사례 | 대규모 ETL, ML 학습, 인터랙티브 분석, OLAP | 정형 ETL, 카탈로그 관리 | Ad-hoc SQL 분석 |

**EMR vs Glue 선택 기준**

- **Glue가 적합한 경우**: 간단한 ETL, AWS 네이티브 서비스만 사용, 운영 부담 최소화 우선
- **EMR이 적합한 경우**: ML 학습 (PySpark MLlib, XGBoost), 다양한 프레임워크 (Hive, Trino, HBase, Flink), 커스텀 라이브러리 의존성, 장시간 실행 클러스터, 비용 최적화 (Spot)

---

## 관련 서비스

| 서비스 | 통합 |
|--------|------|
| Amazon S3 | EMRFS 기본 스토리지 |
| AWS Glue Data Catalog | Hive Metastore 대체 |
| AWS Step Functions | ETL 워크플로우 오케스트레이션 |
| Amazon MWAA (Managed Airflow) | 복잡한 DAG 기반 파이프라인 |
| AWS Lake Formation | 세분화된 데이터 권한 관리 |
| Amazon Athena | EMR이 처리한 S3 데이터를 SQL로 조회 |
| Amazon Redshift | EMR 출력을 데이터 웨어하우스로 적재 |
| Amazon SageMaker | EMR Spark Cluster를 ML 학습에 활용 |

---

## 관련 문서

- [[amazon-rds|Amazon RDS]] - EMR이 RDS를 데이터 소스로 사용 (Sqoop, JDBC)
- [[aws-iam-identity-and-access-management-개요|AWS IAM]] - EMR 클러스터의 EC2/Service Role 관리
- [[aws-kms-key-management-service-개요|AWS KMS]] - EMR 데이터 암호화 (전송/저장)
