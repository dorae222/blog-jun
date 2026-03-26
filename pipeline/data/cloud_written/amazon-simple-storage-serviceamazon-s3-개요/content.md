## 개요

Amazon Simple Storage Service(Amazon S3)는 AWS에서 제공하는 객체 스토리지 서비스로, 업계에서 가장 널리 사용되는 클라우드 스토리지 솔루션입니다. 2006년 AWS의 초기 서비스 중 하나로 출시된 이후, S3는 99.999999999%(11 9's)의 내구성을 보장하며 사실상 무제한에 가까운 확장성을 제공합니다.

S3는 단순한 파일 저장소를 넘어 정적 웹사이트 호스팅, 데이터 레이크 구축, 백업 및 아카이빙, 빅데이터 분석의 기반 스토리지 등 다양한 용도로 활용됩니다. AWS 서비스 생태계의 중심축 역할을 하며, Lambda, CloudFront, Athena, EMR 등 수많은 서비스와 긴밀하게 통합됩니다.

S3의 핵심 구성 요소는 다음과 같습니다.

- **버킷(Bucket)**: 객체를 저장하는 컨테이너로, 전 세계적으로 고유한 이름을 가져야 합니다. 리전 단위로 생성되며, 하나의 AWS 계정당 기본 100개까지 생성 가능합니다.
- **객체(Object)**: S3에 저장되는 데이터의 기본 단위입니다. 최대 5TB까지의 파일을 저장할 수 있으며, 각 객체는 키(Key), 값(Value), 메타데이터, 버전 ID 등으로 구성됩니다.
- **키(Key)**: 버킷 내에서 객체를 고유하게 식별하는 전체 경로입니다. 예를 들어 `images/2024/photo.jpg`와 같은 형태입니다.

## 핵심 기능

### 스토리지 클래스

S3는 데이터 접근 빈도와 비용 요구사항에 따라 다양한 스토리지 클래스를 제공합니다.

| 스토리지 클래스 | 용도 | 가용 영역 | 최소 보관 기간 | 검색 비용 |
|---|---|---|---|---|
| S3 Standard | 자주 접근하는 데이터 | 3개 이상 | 없음 | 없음 |
| S3 Intelligent-Tiering | 접근 패턴이 변하는 데이터 | 3개 이상 | 없음 | 없음 |
| S3 Standard-IA | 비빈번 접근, 즉시 필요 | 3개 이상 | 30일 | 있음 |
| S3 One Zone-IA | 비빈번 접근, 재생성 가능 | 1개 | 30일 | 있음 |
| S3 Glacier Instant Retrieval | 분기별 1회 접근, 즉시 검색 | 3개 이상 | 90일 | 있음 |
| S3 Glacier Flexible Retrieval | 연 1-2회 접근, 분 단위 검색 | 3개 이상 | 90일 | 있음 |
| S3 Glacier Deep Archive | 장기 보관, 연 1회 미만 접근 | 3개 이상 | 180일 | 있음 |

S3 Intelligent-Tiering은 머신러닝을 활용하여 객체의 접근 패턴을 분석하고 자동으로 가장 비용 효율적인 계층으로 이동시킵니다. 모니터링 및 자동화 비용(객체당 월 $0.0025/1,000개)만 추가로 발생하며, 검색 비용은 없습니다.

### 버전 관리(Versioning)

버전 관리를 활성화하면 동일한 키에 대해 여러 버전의 객체를 유지할 수 있습니다. 실수로 삭제하거나 덮어쓴 데이터를 복구할 수 있어 데이터 보호에 필수적인 기능입니다.

```bash
# 버킷 버전 관리 활성화
aws s3api put-bucket-versioning \
  --bucket my-production-bucket \
  --versioning-configuration Status=Enabled

# 버전 관리 상태 확인
aws s3api get-bucket-versioning \
  --bucket my-production-bucket

# 특정 객체의 모든 버전 조회
aws s3api list-object-versions \
  --bucket my-production-bucket \
  --prefix config/app-settings.json
```

버전 관리가 활성화된 상태에서 객체를 삭제하면 실제로 삭제되지 않고 "삭제 마커(Delete Marker)"가 추가됩니다. 이전 버전을 지정하여 복원할 수 있습니다.

### 수명 주기 정책(Lifecycle Policy)

수명 주기 규칙을 설정하면 객체를 자동으로 다른 스토리지 클래스로 전환하거나 삭제할 수 있습니다. 비용 최적화의 핵심 도구입니다.

```json
{
  "Rules": [
    {
      "ID": "LogRetentionPolicy",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "logs/"
      },
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "STANDARD_IA"
        },
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        }
      ],
      "Expiration": {
        "Days": 365
      },
      "NoncurrentVersionTransitions": [
        {
          "NoncurrentDays": 30,
          "StorageClass": "GLACIER"
        }
      ],
      "NoncurrentVersionExpiration": {
        "NoncurrentDays": 90
      }
    }
  ]
}
```

```bash
# 수명 주기 정책 적용
aws s3api put-bucket-lifecycle-configuration \
  --bucket my-production-bucket \
  --lifecycle-configuration file://lifecycle-policy.json

# 현재 수명 주기 정책 확인
aws s3api get-bucket-lifecycle-configuration \
  --bucket my-production-bucket
```

### 복제(Replication)

S3 복제는 버킷 간에 객체를 자동으로 복사하는 기능으로, 두 가지 유형이 있습니다.

- **교차 리전 복제(CRR, Cross-Region Replication)**: 서로 다른 AWS 리전의 버킷 간 복제. 지리적 이중화, 지연 시간 단축, 규정 준수 요구사항 충족에 활용됩니다.
- **동일 리전 복제(SRR, Same-Region Replication)**: 같은 리전 내 버킷 간 복제. 로그 집계, 프로덕션과 테스트 환경 간 데이터 동기화에 활용됩니다.

복제를 설정하려면 원본 버킷과 대상 버킷 모두 버전 관리가 활성화되어 있어야 합니다.

```bash
# 복제 설정 적용
aws s3api put-bucket-replication \
  --bucket my-source-bucket \
  --replication-configuration '{
    "Role": "arn:aws:iam::123456789012:role/S3ReplicationRole",
    "Rules": [
      {
        "ID": "CrossRegionReplication",
        "Status": "Enabled",
        "Priority": 1,
        "Filter": {},
        "Destination": {
          "Bucket": "arn:aws:s3:::my-destination-bucket",
          "StorageClass": "STANDARD_IA"
        },
        "DeleteMarkerReplication": {
          "Status": "Enabled"
        }
      }
    ]
  }'
```

### S3 이벤트 알림

S3 버킷에서 발생하는 이벤트(객체 생성, 삭제 등)를 SNS, SQS, Lambda, EventBridge로 전달할 수 있습니다. 이를 통해 이벤트 기반 아키텍처를 구축할 수 있습니다.

```bash
# 이벤트 알림 설정 (Lambda 트리거)
aws s3api put-bucket-notification-configuration \
  --bucket my-upload-bucket \
  --notification-configuration '{
    "LambdaFunctionConfigurations": [
      {
        "Id": "ImageProcessingTrigger",
        "LambdaFunctionArn": "arn:aws:lambda:ap-northeast-2:123456789012:function:image-processor",
        "Events": ["s3:ObjectCreated:*"],
        "Filter": {
          "Key": {
            "FilterRules": [
              {"Name": "prefix", "Value": "uploads/"},
              {"Name": "suffix", "Value": ".jpg"}
            ]
          }
        }
      }
    ]
  }'
```

## 아키텍처/동작 원리

### 데이터 일관성 모델

2020년 12월부터 S3는 모든 작업에 대해 **강력한 읽기 후 쓰기 일관성(Strong Read-After-Write Consistency)**을 제공합니다. 이는 PUT 또는 DELETE 요청이 성공한 직후, 후속 GET 요청이 최신 데이터를 반환한다는 것을 의미합니다. 이전의 최종 일관성(Eventual Consistency) 모델에서 크게 개선된 부분입니다.

### 멀티파트 업로드

대용량 파일(100MB 이상 권장, 5GB 이상 필수)은 멀티파트 업로드를 사용해야 합니다. 파일을 여러 파트로 분할하여 병렬로 업로드하고, 모든 파트가 업로드되면 하나의 객체로 조합합니다.

```bash
# 멀티파트 업로드 시작
aws s3api create-multipart-upload \
  --bucket my-bucket \
  --key large-dataset/data.tar.gz \
  --storage-class STANDARD_IA

# aws s3 cp는 자동으로 멀티파트 업로드를 처리합니다
# multipart_threshold와 multipart_chunksize 설정
aws configure set default.s3.multipart_threshold 64MB
aws configure set default.s3.multipart_chunksize 16MB

# 대용량 파일 업로드 (자동 멀티파트)
aws s3 cp large-file.tar.gz s3://my-bucket/backups/ \
  --storage-class STANDARD_IA
```

### S3 Transfer Acceleration

Transfer Acceleration은 Amazon CloudFront의 글로벌 엣지 로케이션을 활용하여 S3 버킷으로의 장거리 파일 전송 속도를 높입니다. 클라이언트와 S3 버킷 사이에 최적화된 네트워크 경로를 사용합니다.

```bash
# Transfer Acceleration 활성화
aws s3api put-bucket-accelerate-configuration \
  --bucket my-global-bucket \
  --accelerate-configuration Status=Enabled

# Transfer Acceleration 엔드포인트 사용
aws s3 cp large-file.zip \
  s3://my-global-bucket/uploads/ \
  --endpoint-url https://s3-accelerate.amazonaws.com
```

### S3 Select와 데이터 쿼리

S3 Select를 사용하면 전체 객체를 다운로드하지 않고 SQL 표현식으로 필요한 데이터만 추출할 수 있습니다. CSV, JSON, Parquet 형식을 지원하며, 데이터 전송량과 처리 시간을 크게 줄일 수 있습니다.

```bash
# S3 Select로 CSV 파일에서 특정 조건의 데이터 추출
aws s3api select-object-content \
  --bucket my-data-bucket \
  --key sales/2024-report.csv \
  --expression "SELECT s.product, s.revenue FROM s3object s WHERE s.revenue > '10000'" \
  --expression-type SQL \
  --input-serialization '{"CSV": {"FileHeaderInfo": "USE", "FieldDelimiter": ","}}' \
  --output-serialization '{"CSV": {}}' \
  output.csv
```

### 내부 아키텍처 이해

S3는 내부적으로 데이터를 여러 가용 영역(AZ)에 걸쳐 자동으로 복제합니다. Standard 클래스의 경우 최소 3개 AZ에 데이터를 분산 저장하여 99.999999999%의 내구성을 달성합니다. 객체의 키를 기반으로 파티셔닝이 이루어지며, 접두사(prefix)별로 초당 5,500 GET 요청과 3,500 PUT/COPY/POST/DELETE 요청을 처리할 수 있습니다.

## 실전 활용

### 정적 웹사이트 호스팅

S3를 사용하여 정적 웹사이트를 호스팅할 수 있습니다. React, Vue 등 SPA(Single Page Application)의 빌드 결과물을 배포하는 데 널리 사용됩니다.

```bash
# 정적 웹사이트 호스팅 설정
aws s3 website s3://my-website-bucket/ \
  --index-document index.html \
  --error-document error.html

# 빌드 결과물 업로드
aws s3 sync ./build s3://my-website-bucket/ \
  --delete \
  --cache-control "public, max-age=31536000" \
  --exclude "index.html" \
  --exclude "service-worker.js"

# index.html은 캐시를 짧게 설정
aws s3 cp ./build/index.html s3://my-website-bucket/ \
  --cache-control "public, max-age=0, must-revalidate"
```

### 데이터 레이크 구축

S3는 데이터 레이크의 중앙 저장소로 가장 많이 사용됩니다. 구조화된 데이터와 비구조화된 데이터를 모두 저장하고, Athena, Redshift Spectrum, EMR 등으로 분석할 수 있습니다.

```bash
# 데이터 레이크용 버킷 생성 및 구성
aws s3 mb s3://my-datalake-raw-ap-northeast-2 --region ap-northeast-2
aws s3 mb s3://my-datalake-processed-ap-northeast-2 --region ap-northeast-2
aws s3 mb s3://my-datalake-curated-ap-northeast-2 --region ap-northeast-2

# 서버 액세스 로깅 활성화
aws s3api put-bucket-logging \
  --bucket my-datalake-raw-ap-northeast-2 \
  --bucket-logging-status '{
    "LoggingEnabled": {
      "TargetBucket": "my-datalake-logs",
      "TargetPrefix": "raw-bucket-logs/"
    }
  }'
```

### 백업 자동화 (Python boto3)

```python
import boto3
from datetime import datetime
import os
import gzip

def backup_database_to_s3(db_dump_path, bucket_name, prefix="db-backups"):
    """데이터베이스 덤프 파일을 압축하여 S3에 업로드합니다."""
    s3_client = boto3.client('s3')
    timestamp = datetime.now().strftime('%Y/%m/%d/%H%M%S')
    filename = os.path.basename(db_dump_path)

    # gzip 압축
    compressed_path = f"{db_dump_path}.gz"
    with open(db_dump_path, 'rb') as f_in:
        with gzip.open(compressed_path, 'wb') as f_out:
            f_out.writelines(f_in)

    s3_key = f"{prefix}/{timestamp}/{filename}.gz"

    # 멀티파트 업로드 설정과 함께 업로드
    from boto3.s3.transfer import TransferConfig
    config = TransferConfig(
        multipart_threshold=64 * 1024 * 1024,  # 64MB
        multipart_chunksize=16 * 1024 * 1024,   # 16MB
        max_concurrency=10
    )

    s3_client.upload_file(
        compressed_path,
        bucket_name,
        s3_key,
        Config=config,
        ExtraArgs={
            'StorageClass': 'STANDARD_IA',
            'ServerSideEncryption': 'aws:kms',
            'Metadata': {
                'backup-source': 'production-db',
                'backup-timestamp': timestamp
            }
        }
    )

    # 압축 파일 정리
    os.remove(compressed_path)
    print(f"백업 완료: s3://{bucket_name}/{s3_key}")
    return s3_key
```

### 사전 서명 URL (Presigned URL)

사전 서명 URL을 사용하면 S3 자격 증명 없이도 제한된 시간 동안 객체에 접근할 수 있습니다. 파일 다운로드 링크 공유나 클라이언트에서의 직접 업로드에 활용됩니다.

```bash
# 다운로드용 사전 서명 URL 생성 (1시간 유효)
aws s3 presign s3://my-bucket/reports/monthly-report.pdf \
  --expires-in 3600

# 업로드용 사전 서명 URL 생성
aws s3api put-object \
  --bucket my-upload-bucket \
  --key uploads/user-file.pdf \
  --content-type application/pdf
```

```python
import boto3

def generate_presigned_upload_url(bucket, key, expiration=3600):
    """클라이언트가 직접 S3에 업로드할 수 있는 사전 서명 URL을 생성합니다."""
    s3_client = boto3.client('s3', region_name='ap-northeast-2')

    presigned_url = s3_client.generate_presigned_url(
        'put_object',
        Params={
            'Bucket': bucket,
            'Key': key,
            'ContentType': 'application/octet-stream'
        },
        ExpiresIn=expiration
    )
    return presigned_url
```

## 모범 사례/보안

### 버킷 정책과 접근 제어

S3 보안은 여러 계층으로 구성됩니다. IAM 정책, 버킷 정책, ACL, S3 Block Public Access 설정을 조합하여 세밀한 접근 제어가 가능합니다.

```bash
# 퍼블릭 접근 차단 (계정 수준)
aws s3control put-public-access-block \
  --account-id 123456789012 \
  --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

# 버킷 수준 퍼블릭 접근 차단
aws s3api put-public-access-block \
  --bucket my-private-bucket \
  --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
```

최소 권한 원칙을 적용한 버킷 정책 예시입니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowSpecificRoleAccess",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:role/DataProcessingRole"
      },
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::my-data-bucket/processed/*"
    },
    {
      "Sid": "DenyUnencryptedUploads",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::my-data-bucket/*",
      "Condition": {
        "StringNotEquals": {
          "s3:x-amz-server-side-encryption": "aws:kms"
        }
      }
    },
    {
      "Sid": "EnforceSSLOnly",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::my-data-bucket",
        "arn:aws:s3:::my-data-bucket/*"
      ],
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "false"
        }
      }
    }
  ]
}
```

### 서버 측 암호화

S3는 세 가지 서버 측 암호화 옵션을 제공합니다.

- **SSE-S3**: Amazon에서 관리하는 키로 암호화. 추가 비용 없음.
- **SSE-KMS**: AWS KMS 키로 암호화. 키 사용 감사 로그 제공. KMS 요청 비용 발생.
- **SSE-C**: 고객이 제공하는 키로 암호화. 키 관리 책임은 고객에게 있음.

```bash
# 기본 암호화 설정 (SSE-KMS)
aws s3api put-bucket-encryption \
  --bucket my-secure-bucket \
  --server-side-encryption-configuration '{
    "Rules": [
      {
        "ApplyServerSideEncryptionByDefault": {
          "SSEAlgorithm": "aws:kms",
          "KMSMasterKeyID": "arn:aws:kms:ap-northeast-2:123456789012:key/12345-abcde"
        },
        "BucketKeyEnabled": true
      }
    ]
  }'
```

`BucketKeyEnabled: true`를 설정하면 S3 버킷 키를 사용하여 KMS 요청 비용을 최대 99%까지 절감할 수 있습니다.

### S3 Object Lock

S3 Object Lock은 WORM(Write Once Read Many) 모델을 적용하여 지정된 보존 기간 동안 객체의 삭제 또는 덮어쓰기를 방지합니다. 규정 준수(Compliance) 모드와 거버넌스(Governance) 모드를 지원합니다.

```bash
# Object Lock이 활성화된 버킷 생성
aws s3api create-bucket \
  --bucket my-compliance-bucket \
  --region ap-northeast-2 \
  --create-bucket-configuration LocationConstraint=ap-northeast-2 \
  --object-lock-enabled-for-bucket

# 기본 보존 정책 설정 (Compliance 모드, 365일)
aws s3api put-object-lock-configuration \
  --bucket my-compliance-bucket \
  --object-lock-configuration '{
    "ObjectLockEnabled": "Enabled",
    "Rule": {
      "DefaultRetention": {
        "Mode": "COMPLIANCE",
        "Days": 365
      }
    }
  }'
```

### 비용 최적화 체크리스트

1. **S3 Storage Lens**를 활용하여 스토리지 사용 패턴을 분석합니다.
2. **수명 주기 정책**을 설정하여 접근 빈도가 낮아진 데이터를 자동으로 저렴한 클래스로 이동합니다.
3. **S3 Intelligent-Tiering**을 접근 패턴이 불규칙한 데이터에 적용합니다.
4. **불완전한 멀티파트 업로드**를 정리하는 수명 주기 규칙을 추가합니다.
5. **S3 Analytics**를 활성화하여 IA 전환 시점을 데이터 기반으로 결정합니다.

```bash
# 불완전한 멀티파트 업로드 정리 규칙
aws s3api put-bucket-lifecycle-configuration \
  --bucket my-bucket \
  --lifecycle-configuration '{
    "Rules": [
      {
        "ID": "CleanupIncompleteUploads",
        "Status": "Enabled",
        "Filter": {},
        "AbortIncompleteMultipartUpload": {
          "DaysAfterInitiation": 7
        }
      }
    ]
  }'
```

## 관련 서비스 비교

| 특성 | Amazon S3 | Amazon EBS | Amazon EFS | Amazon FSx |
|---|---|---|---|---|
| 유형 | 객체 스토리지 | 블록 스토리지 | 파일 스토리지 (NFS) | 파일 스토리지 (다양) |
| 접근 방식 | HTTP/HTTPS API | EC2 인스턴스 연결 | 다수 인스턴스 마운트 | 다수 인스턴스 마운트 |
| 최대 크기 | 무제한 | 64TB (볼륨당) | 무제한 | 수백 PB |
| 지연 시간 | ms~sec | sub-ms | ms | sub-ms~ms |
| 내구성 | 99.999999999% | 99.8~99.999% | 99.999999999% | 99.999999999% |
| 주요 용도 | 백업, 정적 콘텐츠, 데이터 레이크 | 데이터베이스, 부팅 볼륨 | 공유 파일 시스템, CMS | HPC, ML, Windows 워크로드 |
| 비용 | 가장 저렴 (GB당) | 중간 | 중간~높음 | 높음 |

S3와 직접 비교되는 서비스로 Google Cloud Storage와 Azure Blob Storage가 있습니다.

- **Google Cloud Storage**: S3와 유사한 객체 스토리지. Nearline, Coldline, Archive 클래스 제공. S3 호환 API를 지원하여 마이그레이션이 용이합니다.
- **Azure Blob Storage**: Hot, Cool, Cold, Archive 계층 제공. Azure 생태계와의 통합이 강점입니다.
- **MinIO**: S3 호환 오픈소스 객체 스토리지. 온프레미스 또는 하이브리드 환경에서 S3 API 호환이 필요할 때 사용됩니다.

## 요약

Amazon S3는 AWS 클라우드 인프라의 핵심 스토리지 서비스로, 무한에 가까운 확장성, 11 9's 내구성, 다양한 스토리지 클래스를 통한 비용 최적화를 제공합니다. 단순한 파일 저장소를 넘어 데이터 레이크, 정적 웹 호스팅, 백업/아카이빙, 이벤트 기반 아키텍처의 기반으로 활용됩니다.

핵심 포인트를 정리하면 다음과 같습니다.

- **스토리지 클래스 선택**: 데이터 접근 패턴에 맞는 스토리지 클래스를 선택하고, 수명 주기 정책으로 자동 전환을 설정합니다.
- **보안**: Block Public Access를 기본으로 활성화하고, 버킷 정책으로 최소 권한 원칙을 적용하며, 서버 측 암호화(SSE-KMS)를 적용합니다.
- **버전 관리**: 중요 데이터가 저장된 버킷에는 반드시 버전 관리를 활성화합니다.
- **성능 최적화**: 접두사를 분산하여 요청을 병렬화하고, 대용량 파일은 멀티파트 업로드를 사용합니다.
- **비용 관리**: S3 Storage Lens와 Analytics로 사용 패턴을 모니터링하고, Intelligent-Tiering과 수명 주기 정책으로 비용을 최적화합니다.

S3는 거의 모든 AWS 워크로드의 기반이 되므로, 스토리지 클래스별 특성, 보안 설정, 비용 최적화 전략을 충분히 이해하고 활용하는 것이 중요합니다.