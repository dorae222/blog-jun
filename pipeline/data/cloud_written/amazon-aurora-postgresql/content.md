## 개요

Amazon Aurora PostgreSQL은 PostgreSQL과 완전히 호환되면서 클라우드 네이티브 아키텍처의 이점을 제공하는 완전관리형 관계형 데이터베이스입니다. 표준 PostgreSQL 대비 최대 3배의 처리량을 제공하며, Aurora의 분산 스토리지 아키텍처를 기반으로 높은 가용성과 내구성을 보장합니다.

Aurora PostgreSQL은 기존 PostgreSQL 애플리케이션을 코드 변경 없이 마이그레이션할 수 있으며, PostgreSQL의 풍부한 확장 생태계를 그대로 활용할 수 있습니다. PostGIS(지리 정보), pgvector(벡터 검색), pg_cron(스케줄링) 등 다양한 확장을 지원합니다.

Aurora PostgreSQL만의 특별한 기능은 다음과 같습니다.

- **Babelfish for Aurora PostgreSQL**: SQL Server 애플리케이션을 최소한의 코드 변경으로 Aurora PostgreSQL에서 실행할 수 있게 합니다.
- **pgvector 확장**: 벡터 유사도 검색을 지원하여 AI/ML 애플리케이션의 임베딩 저장소로 활용할 수 있습니다.
- **Aurora 기계 학습 통합**: SageMaker, Comprehend 등 AWS ML 서비스와 SQL 쿼리를 통해 직접 통합됩니다.
- **Trusted Language Extensions (TLE)**: 안전한 환경에서 사용자 정의 확장을 생성할 수 있습니다.

현재 지원하는 PostgreSQL 버전은 12, 13, 14, 15, 16이며, AWS는 새로운 PostgreSQL 메이저 버전을 빠르게 지원하고 있습니다.

## 핵심 기능

### Aurora PostgreSQL 클러스터 구성

```bash
# Aurora PostgreSQL 클러스터 생성
aws rds create-db-cluster \
  --db-cluster-identifier my-aurora-pg-cluster \
  --engine aurora-postgresql \
  --engine-version 16.1 \
  --master-username postgres \
  --master-user-password MySecurePassword123! \
  --db-subnet-group-name my-db-subnet-group \
  --vpc-security-group-ids sg-0123456789abcdef0 \
  --storage-encrypted \
  --backup-retention-period 35 \
  --enable-cloudwatch-logs-exports '["postgresql"]' \
  --serverless-v2-scaling-configuration MinCapacity=0.5,MaxCapacity=64

# Writer 인스턴스 생성
aws rds create-db-instance \
  --db-instance-identifier aurora-pg-writer \
  --db-cluster-identifier my-aurora-pg-cluster \
  --engine aurora-postgresql \
  --db-instance-class db.r6g.xlarge \
  --enable-performance-insights \
  --performance-insights-retention-period 731

# Serverless v2 Reader 인스턴스 생성
aws rds create-db-instance \
  --db-instance-identifier aurora-pg-reader-sv2 \
  --db-cluster-identifier my-aurora-pg-cluster \
  --engine aurora-postgresql \
  --db-instance-class db.serverless
```

### Babelfish for Aurora PostgreSQL

Babelfish는 Aurora PostgreSQL에서 SQL Server의 T-SQL을 직접 실행할 수 있게 하는 기능입니다. SQL Server 애플리케이션을 최소한의 변경으로 Aurora PostgreSQL로 마이그레이션할 수 있습니다.

```bash
# Babelfish 활성화된 클러스터 생성
aws rds create-db-cluster \
  --db-cluster-identifier babelfish-cluster \
  --engine aurora-postgresql \
  --engine-version 16.1 \
  --master-username postgres \
  --master-user-password MySecurePassword123! \
  --db-subnet-group-name my-db-subnet-group \
  --enable-babelfish

# Babelfish 파라미터 설정
aws rds create-db-cluster-parameter-group \
  --db-cluster-parameter-group-name babelfish-params \
  --db-parameter-group-family aurora-postgresql16 \
  --description "Babelfish enabled parameters"

aws rds modify-db-cluster-parameter-group \
  --db-cluster-parameter-group-name babelfish-params \
  --parameters '[
    {"ParameterName": "rds.babelfish_status", "ParameterValue": "on", "ApplyMethod": "pending-reboot"},
    {"ParameterName": "babelfishpg_tsql.migration_mode", "ParameterValue": "multi-db", "ApplyMethod": "pending-reboot"}
  ]'
```

Babelfish가 활성화되면 TDS(Tabular Data Stream) 프로토콜 포트(기본 1433)로 SQL Server 클라이언트에서 직접 연결할 수 있습니다.

### pgvector 확장 - 벡터 검색

pgvector는 PostgreSQL에서 벡터 유사도 검색을 지원하는 확장입니다. AI/ML 애플리케이션에서 임베딩 벡터를 저장하고 검색하는 데 활용됩니다.

```bash
# pgvector 확장이 지원되는지 확인
aws rds describe-db-engine-versions \
  --engine aurora-postgresql \
  --engine-version 16.1 \
  --query 'DBEngineVersions[0].SupportedFeatureNames'
```

pgvector 사용 예제 (SQL):

```python
import psycopg2

def setup_pgvector(conn_string):
    """pgvector 확장을 설정하고 벡터 테이블을 생성합니다."""
    conn = psycopg2.connect(conn_string)
    cur = conn.cursor()
    
    # pgvector 확장 활성화
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    
    # 벡터 테이블 생성 (OpenAI text-embedding-3-small: 1536차원)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            embedding vector(1536),
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)
    
    # HNSW 인덱스 생성 (코사인 유사도)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS documents_embedding_idx
        ON documents
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    """)
    
    conn.commit()
    cur.close()
    conn.close()

def search_similar(conn_string, query_embedding, limit=10):
    """벡터 유사도 검색을 수행합니다."""
    conn = psycopg2.connect(conn_string)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, title, content,
               1 - (embedding <=> %s::vector) AS similarity
        FROM documents
        ORDER BY embedding <=> %s::vector
        LIMIT %s;
    """, (query_embedding, query_embedding, limit))
    
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results
```

### Aurora 기계 학습 통합

SQL 쿼리 내에서 SageMaker 엔드포인트나 Comprehend를 직접 호출할 수 있습니다.

```bash
# ML 통합을 위한 IAM 역할 연결
aws rds add-role-to-db-cluster \
  --db-cluster-identifier my-aurora-pg-cluster \
  --role-arn arn:aws:iam::123456789012:role/AuroraMLRole \
  --feature-name SageMaker

aws rds add-role-to-db-cluster \
  --db-cluster-identifier my-aurora-pg-cluster \
  --role-arn arn:aws:iam::123456789012:role/AuroraComprehendRole \
  --feature-name Comprehend
```

### 논리적 복제 (Logical Replication)

Aurora PostgreSQL은 PostgreSQL의 논리적 복제를 지원하여, 다른 PostgreSQL 인스턴스나 외부 시스템으로 실시간 데이터 복제가 가능합니다.

```bash
# 논리적 복제 활성화를 위한 파라미터 설정
aws rds modify-db-cluster-parameter-group \
  --db-cluster-parameter-group-name my-aurora-pg-params \
  --parameters '[
    {"ParameterName": "rds.logical_replication", "ParameterValue": "1", "ApplyMethod": "pending-reboot"},
    {"ParameterName": "max_replication_slots", "ParameterValue": "10", "ApplyMethod": "pending-reboot"},
    {"ParameterName": "max_wal_senders", "ParameterValue": "10", "ApplyMethod": "pending-reboot"}
  ]'
```

### RDS Proxy 연동

RDS Proxy를 사용하여 데이터베이스 연결 풀링과 장애 조치 시간을 개선합니다.

```bash
# RDS Proxy 생성
aws rds create-db-proxy \
  --db-proxy-name aurora-pg-proxy \
  --engine-family POSTGRESQL \
  --auth '[{
    "AuthScheme": "SECRETS",
    "SecretArn": "arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:aurora-pg-credentials",
    "IAMAuth": "DISABLED"
  }]' \
  --role-arn arn:aws:iam::123456789012:role/RDSProxyRole \
  --vpc-subnet-ids subnet-01 subnet-02 subnet-03 \
  --vpc-security-group-ids sg-0123456789abcdef0 \
  --require-tls

# 프록시를 Aurora 클러스터에 연결
aws rds register-db-proxy-targets \
  --db-proxy-name aurora-pg-proxy \
  --db-cluster-identifiers my-aurora-pg-cluster
```

## 아키텍처/동작 원리

### Aurora PostgreSQL 스토리지 엔진

Aurora PostgreSQL은 PostgreSQL의 기본 스토리지 엔진 대신 Aurora 분산 스토리지를 사용합니다. PostgreSQL의 WAL(Write-Ahead Log)이 Aurora 스토리지 노드로 전송되고, 스토리지 노드가 비동기적으로 데이터 페이지를 재구성합니다.

이 설계의 장점은 다음과 같습니다.

1. **네트워크 I/O 감소**: 전체 데이터 페이지가 아닌 WAL 레코드만 전송합니다.
2. **VACUUM 효율성 향상**: Aurora 스토리지가 가비지 컬렉션을 보조하여 VACUUM 부하를 줄입니다.
3. **빠른 크래시 복구**: WAL 재생(Replay) 없이 스토리지에서 직접 최신 데이터를 읽을 수 있습니다.

### PostgreSQL 확장 아키텍처

Aurora PostgreSQL에서 사용 가능한 주요 확장 목록은 다음과 같습니다.

- **PostGIS**: 지리 공간 데이터 처리
- **pgvector**: 벡터 유사도 검색
- **pg_stat_statements**: 쿼리 성능 통계
- **pg_cron**: 데이터베이스 내 작업 스케줄링
- **pg_hint_plan**: 쿼리 실행 계획 힌트
- **hstore**: 키-값 쌍 저장
- **citext**: 대소문자 구분 없는 텍스트
- **uuid-ossp**: UUID 생성

### VACUUM 관리

PostgreSQL의 MVCC(Multi-Version Concurrency Control) 특성상, VACUUM은 매우 중요한 유지보수 작업입니다. Aurora PostgreSQL은 자동 VACUUM을 기본으로 활성화하고 있으며, 대규모 테이블에 대한 VACUUM 성능도 개선되어 있습니다.

## 실전 활용

### RAG (Retrieval-Augmented Generation) 시스템 구축

pgvector를 활용하여 RAG 시스템의 벡터 스토어를 구축하는 실전 예제입니다.

```python
import boto3
import psycopg2
import json
from typing import List

class AuroraVectorStore:
    """Aurora PostgreSQL + pgvector 기반 벡터 스토어"""
    
    def __init__(self, conn_string: str):
        self.conn_string = conn_string
        self._initialize()
    
    def _initialize(self):
        conn = psycopg2.connect(self.conn_string)
        cur = conn.cursor()
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS rag_documents (
                id SERIAL PRIMARY KEY,
                source TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding vector(1536),
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(source, chunk_index)
            );
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS rag_embedding_idx
            ON rag_documents USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 128);
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS rag_metadata_idx
            ON rag_documents USING gin (metadata);
        """)
        conn.commit()
        cur.close()
        conn.close()
    
    def upsert_documents(self, documents: List[dict]):
        conn = psycopg2.connect(self.conn_string)
        cur = conn.cursor()
        for doc in documents:
            cur.execute("""
                INSERT INTO rag_documents (source, chunk_index, content, embedding, metadata)
                VALUES (%s, %s, %s, %s::vector, %s::jsonb)
                ON CONFLICT (source, chunk_index)
                DO UPDATE SET content = EXCLUDED.content,
                             embedding = EXCLUDED.embedding,
                             metadata = EXCLUDED.metadata;
            """, (doc['source'], doc['chunk_index'], doc['content'],
                  doc['embedding'], json.dumps(doc.get('metadata', {}))))
        conn.commit()
        cur.close()
        conn.close()
    
    def search(self, query_embedding, limit=5, metadata_filter=None):
        conn = psycopg2.connect(self.conn_string)
        cur = conn.cursor()
        
        if metadata_filter:
            cur.execute("""
                SELECT id, source, content, metadata,
                       1 - (embedding <=> %s::vector) AS similarity
                FROM rag_documents
                WHERE metadata @> %s::jsonb
                ORDER BY embedding <=> %s::vector
                LIMIT %s;
            """, (query_embedding, json.dumps(metadata_filter),
                  query_embedding, limit))
        else:
            cur.execute("""
                SELECT id, source, content, metadata,
                       1 - (embedding <=> %s::vector) AS similarity
                FROM rag_documents
                ORDER BY embedding <=> %s::vector
                LIMIT %s;
            """, (query_embedding, query_embedding, limit))
        
        results = cur.fetchall()
        cur.close()
        conn.close()
        return results
```

### DMS를 활용한 마이그레이션

기존 PostgreSQL에서 Aurora PostgreSQL로 마이그레이션하는 과정입니다.

```bash
# DMS 복제 인스턴스 생성
aws dms create-replication-instance \
  --replication-instance-identifier pg-to-aurora-migration \
  --replication-instance-class dms.r5.xlarge \
  --allocated-storage 100

# 소스 엔드포인트 (기존 PostgreSQL)
aws dms create-endpoint \
  --endpoint-identifier source-pg \
  --endpoint-type source \
  --engine-name postgres \
  --server-name source-db.example.com \
  --port 5432 \
  --username postgres \
  --password SourcePassword123! \
  --database-name mydb

# 대상 엔드포인트 (Aurora PostgreSQL)
aws dms create-endpoint \
  --endpoint-identifier target-aurora-pg \
  --endpoint-type target \
  --engine-name aurora-postgresql \
  --server-name my-aurora-pg-cluster.cluster-abc123.ap-northeast-2.rds.amazonaws.com \
  --port 5432 \
  --username postgres \
  --password TargetPassword123! \
  --database-name mydb

# 마이그레이션 태스크 생성 (전체 로드 + CDC)
aws dms create-replication-task \
  --replication-task-identifier full-load-and-cdc \
  --source-endpoint-arn arn:aws:dms:ap-northeast-2:123456789012:endpoint:source-pg \
  --target-endpoint-arn arn:aws:dms:ap-northeast-2:123456789012:endpoint:target-aurora-pg \
  --replication-instance-arn arn:aws:dms:ap-northeast-2:123456789012:rep:pg-to-aurora-migration \
  --migration-type full-load-and-cdc \
  --table-mappings file://table-mappings.json
```

### Performance Insights 활용

```bash
# Performance Insights 데이터 조회
aws pi get-resource-metrics \
  --service-type RDS \
  --identifier db-ABCDEFGHIJKLMNOP \
  --metric-queries '[{
    "Metric": "db.load.avg",
    "GroupBy": {"Group": "db.wait_event"}
  }]' \
  --start-time 2026-03-22T00:00:00Z \
  --end-time 2026-03-23T00:00:00Z \
  --period-in-seconds 3600
```

## 모범 사례/보안

### PostgreSQL 특화 보안

1. **Row Level Security (RLS)**: 테이블의 행 수준 접근 제어를 구현하여 멀티 테넌트 보안을 강화합니다.
2. **SSL 필수 연결**: `rds.force_ssl` 파라미터를 활성화하여 암호화되지 않은 연결을 차단합니다.
3. **pgAudit 확장**: PostgreSQL Audit 확장을 활용하여 상세한 감사 로그를 기록합니다.

```bash
# SSL 필수 연결 및 pgAudit 활성화
aws rds modify-db-cluster-parameter-group \
  --db-cluster-parameter-group-name my-aurora-pg-params \
  --parameters '[
    {"ParameterName": "rds.force_ssl", "ParameterValue": "1", "ApplyMethod": "immediate"},
    {"ParameterName": "shared_preload_libraries", "ParameterValue": "pgaudit,pg_stat_statements", "ApplyMethod": "pending-reboot"},
    {"ParameterName": "pgaudit.log", "ParameterValue": "ddl,role", "ApplyMethod": "immediate"}
  ]'
```

### 성능 최적화

1. **pg_stat_statements 활용**: 느린 쿼리를 식별하고 최적화합니다.
2. **적절한 인덱스 전략**: B-tree, GiST, GIN, BRIN 등 워크로드에 맞는 인덱스 유형을 선택합니다.
3. **파티셔닝**: 대규모 테이블에 선언적 파티셔닝을 적용하여 쿼리 성능을 개선합니다.
4. **연결 관리**: RDS Proxy 또는 PgBouncer를 활용하여 연결 풀링을 구성합니다.

### VACUUM 관리

1. `autovacuum_vacuum_scale_factor`를 대규모 테이블에 맞게 조정합니다.
2. `autovacuum_vacuum_cost_delay`를 낮추어 VACUUM 처리 속도를 높입니다.
3. Transaction ID Wraparound를 방지하기 위해 VACUUM 상태를 지속적으로 모니터링합니다.

## 관련 서비스 비교

### Aurora PostgreSQL vs RDS PostgreSQL

| 항목 | Aurora PostgreSQL | RDS PostgreSQL |
|------|------------------|----------------|
| 스토리지 | 공유 분산 (최대 128TB) | EBS (최대 64TB) |
| 복제본 | 최대 15개, 20ms 이하 지연 | 최대 5개, 초 단위 지연 |
| 장애 조치 | 30초 이내 | 60-120초 |
| 비용 | 약 20% 높음 | 기본 |
| Babelfish | 지원 | 미지원 |
| 글로벌 DB | 지원 | 미지원 |
| Serverless | 지원 (v2) | 미지원 |

### Aurora PostgreSQL vs Aurora MySQL

| 항목 | Aurora PostgreSQL | Aurora MySQL |
|------|------------------|---------------|
| SQL 표준 호환 | 높음 | 중간 |
| JSONB 지원 | 네이티브 | JSON (제한적) |
| 확장 생태계 | PostGIS, pgvector 등 풍부 | 제한적 |
| Babelfish | 지원 (SQL Server 호환) | 미지원 |
| 파티셔닝 | 선언적 파티셔닝 | 범위/해시/리스트 파티셔닝 |
| 동시성 | MVCC (진정한 MVCC) | MVCC (InnoDB) |

## 요약

Amazon Aurora PostgreSQL은 PostgreSQL의 풍부한 기능과 확장 생태계를 클라우드 네이티브 아키텍처의 성능과 가용성으로 제공하는 완전관리형 데이터베이스입니다.

Babelfish를 통한 SQL Server 마이그레이션, pgvector를 활용한 AI/ML 벡터 검색, 논리적 복제를 통한 유연한 데이터 파이프라인 구축 등 PostgreSQL 생태계의 강점을 그대로 활용할 수 있습니다. Serverless v2와 Global Database를 통해 자동 스케일링과 글로벌 배포도 지원합니다.

프로덕션 환경에서는 RDS Proxy를 통한 연결 관리, pgAudit을 통한 감사 로깅, SSL 필수 연결, 적절한 VACUUM 관리를 반드시 구성해야 합니다. DMS를 활용하면 기존 PostgreSQL에서 최소한의 다운타임으로 마이그레이션할 수 있습니다.