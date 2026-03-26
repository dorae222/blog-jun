## 개요

데이터의 양(Volume)이 기하급수적으로 증가하고, 생성 속도(Velocity)가 빨라지며, 형태(Variety)가 다양해지면서 기존 RDBMS만으로는 데이터를 효과적으로 처리하기 어려운 시대가 되었습니다. 이 문제를 해결하기 위해 등장한 것이 **Hadoop 에코시스템**입니다.

Hadoop은 단일 기술이 아닙니다. Apache Software Foundation이 관리하는 오픈소스 프로젝트들의 집합체로, HDFS(분산 저장), MapReduce(분산 처리), YARN(리소스 관리)이라는 코어 위에 Hive, Pig, Sqoop, HBase, Flume, Spark 등 수십 가지 서브 프로젝트가 유기적으로 결합된 생태계입니다.

이 글에서는 빅데이터의 개념과 RDBMS의 한계부터 시작해서, Hadoop 에코시스템 각 컴포넌트의 역할과 관계를 정리합니다.

## 핵심 개념

### 빅데이터의 정의와 3V

빅데이터는 기존 데이터 관리 도구로는 저장, 처리, 분석이 어려운 대규모 데이터를 의미합니다. 일반적으로 3V로 특성을 정의합니다.

- Volume(양): TB에서 PB 이상의 데이터 규모
- Velocity(속도): 실시간 또는 준실시간으로 생성되는 데이터의 처리 속도
- Variety(다양성): 정형(structured), 반정형(semi-structured), 비정형(unstructured) 데이터의 혼합

최근에는 Veracity(정확성)와 Value(가치)를 추가하여 5V로 확장하기도 합니다.

### RDBMS의 한계와 Scale-Out의 필요성

전통적인 RDBMS는 빅데이터 환경에서 두 가지 근본적인 한계에 부딪힙니다.

첫째, 스키마 경직성 문제입니다. 비정형 데이터를 RDBMS의 정해진 스키마에 맞춰 변환하려면 긴 다운타임이 발생하고, 변환 과정 자체가 병목이 됩니다.

둘째, **Scale-Up의 물리적 한계**입니다. RDBMS는 본질적으로 단일 서버의 성능을 높이는 수직 확장에 의존하는데, 하드웨어 성능에는 물리적 상한이 있고 고성능 장비일수록 비용이 기하급수적으로 증가합니다.

Hadoop은 이와 반대로 **Scale-Out** 방식을 채택했습니다. 저가의 범용 서버(commodity hardware)를 수평적으로 추가함으로써 처리 능력을 선형에 가깝게 확장할 수 있습니다.

```text
Scale-Up:    [작은 서버] --> [큰 서버]
             비용 급증, 물리적 한계 존재

Scale-Out:   [서버1] [서버2] [서버3] ... [서버N]
             저비용 서버를 추가하여 선형 확장
```

### NoSQL의 등장

Hadoop의 디스크 기반 처리 과정에서 속도 이슈가 부각되면서 메모리 기반 처리 기술이 등장했고, 동시에 RDBMS의 한계를 극복하기 위한 비관계형 데이터베이스인 NoSQL이 본격적으로 발전했습니다. NoSQL은 네 가지 주요 데이터 모델로 분류됩니다.

| 데이터 모델 | 설명 | 대표 제품 |
|---|---|---|
| Key-Value | 키와 값의 단순한 쌍으로 저장 | Redis, DynamoDB |
| Column Family | 컬럼 단위로 데이터를 그룹화하여 저장 | HBase, Cassandra |
| Document | JSON/BSON 형태의 문서 단위로 저장 | MongoDB, CouchDB |
| Graph | 노드와 엣지로 관계를 표현 | Neo4j, Amazon Neptune |

### Hadoop 에코시스템 아키텍처

Hadoop 에코시스템은 코어 프로젝트와 서브 프로젝트의 계층 구조로 구성됩니다.

```text
+-------------------------------------------------------+
|                     Applications                      |
|            Hive / Pig / Mahout / Sqoop ...             |
+-------------------------------------------------------+
|                   Processing Layer                    |
|            MapReduce  |  Spark  |  Tez                |
+-------------------------------------------------------+
|                Resource Management                    |
|                       YARN                            |
+-------------------------------------------------------+
|                    Storage Layer                      |
|                       HDFS                            |
+-------------------------------------------------------+
|                   Infrastructure                      |
|              Commodity Hardware Cluster                |
+-------------------------------------------------------+
```

최하단의 범용 하드웨어 클러스터 위에 HDFS가 분산 저장 계층을 형성하고, YARN이 리소스를 관리하며, 그 위에서 MapReduce나 Spark 같은 처리 엔진이 동작합니다. 최상단에는 Hive, Pig, Sqoop 등 사용자 친화적인 애플리케이션 계층이 놓입니다.

### HDFS (Hadoop Distributed File System)

HDFS는 Hadoop의 분산 파일 시스템으로, 대용량 파일을 여러 서버에 나누어 저장합니다. 구성 요소는 다음과 같습니다.

- **NameNode** (Master): 메타데이터 관리, 파일 시스템 네임스페이스 유지
- **DataNode** (Slave): 실제 데이터 블록 저장
- **Secondary NameNode**: NameNode의 메타데이터 체크포인트 생성 (Standby NameNode와는 다른 역할이므로 주의가 필요합니다)

파일은 기본 128MB(Hadoop 2.x 이후) 크기의 블록으로 분할되어 저장되며, 기본 복제 계수(Replication Factor)는 3입니다. 한 블록이 3개의 서로 다른 DataNode에 복제되므로, 특정 노드가 장애를 일으켜도 데이터 유실 없이 서비스를 지속할 수 있습니다.

### MapReduce

MapReduce는 대용량 데이터를 병렬 처리하기 위한 프로그래밍 모델입니다. 이름 그대로 Map과 Reduce 두 단계로 구성됩니다.

1. **Map 단계**: 입력 데이터를 Key-Value 쌍으로 변환합니다.
2. **Shuffle & Sort**: 같은 Key를 가진 데이터를 모아서 정렬합니다.
3. **Reduce 단계**: 같은 Key를 가진 Value들을 집계합니다.

Map 단계에서 데이터가 분산 노드별로 독립적으로 처리되기 때문에 병렬성이 확보됩니다. 그러나 중간 결과를 디스크에 기록하는 구조 때문에 반복 연산이 잦은 작업(머신러닝 등)에서는 성능 저하가 발생합니다. 이 한계가 이후 Spark 등장의 직접적인 배경이 됩니다.

### YARN (Yet Another Resource Negotiator)

Hadoop 1.x에서는 MapReduce가 리소스 관리와 작업 실행을 모두 담당했습니다. 이로 인해 MapReduce 이외의 처리 프레임워크를 Hadoop 클러스터에서 실행할 수 없었습니다.

Hadoop 2.0에서 도입된 YARN은 리소스 관리를 별도 계층으로 분리한 것이 핵심입니다.

- **ResourceManager**: 클러스터 전체의 리소스 할당을 관리
- **NodeManager**: 각 노드의 리소스 사용을 모니터링
- **ApplicationMaster**: 개별 애플리케이션의 실행을 조율

YARN 덕분에 MapReduce 외에도 Spark, Tez, Flink 등 다양한 컴퓨팅 프레임워크가 동일한 Hadoop 클러스터 위에서 동작할 수 있게 되었습니다.

## 실전 코드

### HDFS 기본 명령어

HDFS는 Linux 파일 시스템 명령어와 유사한 CLI를 제공합니다.

```bash
# 디렉토리 생성
hadoop fs -mkdir -p /user/hive/warehouse

# 로컬 파일을 HDFS로 업로드
hadoop fs -put local_data.csv /user/hive/warehouse/

# HDFS 파일 목록 확인
hadoop fs -ls /user/hive/warehouse/

# HDFS 파일 내용 확인
hadoop fs -cat /user/hive/warehouse/local_data.csv | head -5

# HDFS 파일을 로컬로 다운로드
hadoop fs -get /user/hive/warehouse/local_data.csv ./downloaded.csv

# 파일 크기 및 복제 계수 확인
hadoop fs -stat "%r %b %n" /user/hive/warehouse/local_data.csv
```

### MapReduce: WordCount 구현

MapReduce의 전형적인 예제인 WordCount입니다. 텍스트 파일에서 각 단어의 출현 빈도를 계산합니다.

```java
public class WordCount {

    // Mapper: 텍스트를 단어별로 분리하여 (단어, 1) 쌍 생성
    public static class TokenizerMapper
            extends Mapper<LongWritable, Text, Text, LongWritable> {

        private final static LongWritable one = new LongWritable(1);
        private Text word = new Text();

        public void map(LongWritable key, Text value, Context context)
                throws IOException, InterruptedException {
            StringTokenizer tokenizer = new StringTokenizer(value.toString());
            while (tokenizer.hasMoreTokens()) {
                word.set(tokenizer.nextToken().toLowerCase());
                context.write(word, one);
            }
        }
    }

    // Reducer: 같은 단어의 개수를 합산
    public static class SumReducer
            extends Reducer<Text, LongWritable, Text, LongWritable> {

        public void reduce(Text key, Iterable<LongWritable> values, Context context)
                throws IOException, InterruptedException {
            long sum = 0;
            for (LongWritable val : values) {
                sum += val.get();
            }
            context.write(key, new LongWritable(sum));
        }
    }

    public static void main(String[] args) throws Exception {
        Configuration conf = new Configuration();
        Job job = Job.getInstance(conf, "word count");
        job.setJarByClass(WordCount.class);
        job.setMapperClass(TokenizerMapper.class);
        job.setReducerClass(SumReducer.class);
        job.setOutputKeyClass(Text.class);
        job.setOutputValueClass(LongWritable.class);
        FileInputFormat.addInputPath(job, new Path(args[0]));
        FileOutputFormat.setOutputPath(job, new Path(args[1]));
        System.exit(job.waitForCompletion(true) ? 0 : 1);
    }
}
```

이 코드를 컴파일 후 다음과 같이 실행합니다.

```bash
hadoop jar wordcount.jar WordCount /input/text_files /output/wordcount_result
```

### Hive: SQL로 빅데이터 분석

Hive는 HDFS 위에서 SQL 구문(HiveQL)으로 MapReduce를 실행할 수 있게 해주는 데이터 웨어하우스 도구입니다. SQL에 익숙한 분석가가 별도의 Java 코딩 없이 대용량 데이터를 쿼리할 수 있다는 점이 강점입니다.

```sql
-- 테이블 생성
CREATE TABLE IF NOT EXISTS access_logs (
    request_time  STRING,
    method        STRING,
    url           STRING,
    status_code   INT,
    response_time DOUBLE
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE;

-- HDFS 데이터 로드
LOAD DATA INPATH '/raw/access_logs/' INTO TABLE access_logs;

-- 상태 코드별 요청 수 집계
SELECT status_code, COUNT(*) AS request_count
FROM access_logs
WHERE request_time >= '2025-01-01'
GROUP BY status_code
ORDER BY request_count DESC;

-- 평균 응답 시간이 긴 URL 상위 10개
SELECT url, AVG(response_time) AS avg_response
FROM access_logs
GROUP BY url
ORDER BY avg_response DESC
LIMIT 10;
```

Hive는 내부적으로 HiveQL을 MapReduce(또는 Tez, Spark) 작업으로 변환하여 실행합니다. 대규모 배치 분석에 적합하지만, 실시간 조회에는 적합하지 않습니다.

### Pig: 데이터 흐름 중심의 처리

Pig는 MapReduce를 추상화한 **Pig Latin**이라는 스크립트 언어를 제공합니다. 데이터의 흐름(flow)을 절차적으로 표현할 수 있으며, 내장 옵티마이저가 실행 계획을 자동으로 최적화합니다.

```pig
-- 로그 파일 로드
raw_logs = LOAD '/raw/access_logs/' USING PigStorage('\t')
           AS (request_time:chararray, method:chararray,
               url:chararray, status_code:int, response_time:double);

-- 에러 로그만 필터링
error_logs = FILTER raw_logs BY status_code >= 400;

-- URL별 에러 횟수 집계
grouped = GROUP error_logs BY url;
error_counts = FOREACH grouped GENERATE
                 group AS url,
                 COUNT(error_logs) AS error_count;

-- 에러가 많은 순서로 정렬
sorted = ORDER error_counts BY error_count DESC;
top_errors = LIMIT sorted 20;
DUMP top_errors;
```

Pig와 Hive의 차이를 정리하면 다음과 같습니다.

| 항목 | Pig | Hive |
|---|---|---|
| 언어 | Pig Latin (절차적) | HiveQL (선언적, SQL 유사) |
| 주 사용자 | 데이터 엔지니어 | 분석가, 데이터 사이언티스트 |
| JOIN 성능 | 상대적으로 우수 | 상대적으로 약함 |
| 적합한 작업 | ETL, 복잡한 데이터 변환 | 대화형 분석, 집계 쿼리 |

### Sqoop: RDBMS-Hadoop 간 데이터 전송

Sqoop(SQL-to-Hadoop)은 RDBMS와 HDFS 간 대용량 데이터를 효율적으로 전송하기 위한 도구입니다. 내부적으로 MapReduce 작업을 생성하여 병렬로 데이터를 전송합니다.

```bash
# MySQL -> HDFS Import (4개 Mapper로 병렬 전송)
sqoop import \
    --connect jdbc:mysql://db-server:3306/production \
    --table orders \
    --username etl_user \
    --password-file /user/etl/.password \
    --target-dir /data/warehouse/orders \
    --num-mappers 4 \
    --incremental lastmodified \
    --check-column updated_at \
    --last-value '2025-01-01'

# HDFS -> MySQL Export
sqoop export \
    --connect jdbc:mysql://db-server:3306/analytics \
    --table daily_summary \
    --export-dir /data/results/daily_summary \
    --input-fields-terminated-by ','
```

`--incremental` 옵션을 사용하면 전체 데이터를 매번 가져올 필요 없이 변경된 데이터만 증분 임포트할 수 있습니다.

## 활용 사례

### 전통 RDBMS와 Hadoop의 비교

어떤 상황에서 Hadoop을 도입해야 하는지 판단하기 위해, 전통 RDBMS와의 차이를 명확히 이해할 필요가 있습니다.

| 항목 | 전통 RDBMS | Hadoop 에코시스템 |
|---|---|---|
| 데이터 규모 | GB ~ TB | TB ~ PB |
| 확장 방식 | Scale-Up (수직) | Scale-Out (수평) |
| 데이터 구조 | 정형 데이터 | 정형 + 반정형 + 비정형 |
| 처리 방식 | 실시간 트랜잭션 | 배치 처리 중심 |
| 스키마 전략 | Schema-on-Write | Schema-on-Read |
| 비용 | 고비용 상용 라이선스 | 오픈소스 + 범용 하드웨어 |
| 일관성 | ACID 보장 | Eventual Consistency |

핵심적인 차이는 **Schema-on-Write vs Schema-on-Read**입니다. RDBMS는 데이터를 저장할 때(Write) 스키마를 강제하지만, Hadoop은 데이터를 읽을 때(Read) 스키마를 적용합니다. 이 덕분에 Hadoop은 원시 데이터를 그대로 저장한 뒤, 분석 시점에 필요한 형태로 해석할 수 있습니다.

### 실무에서의 에코시스템 조합

실제 데이터 파이프라인에서는 여러 컴포넌트를 조합하여 사용합니다. 전형적인 배치 분석 파이프라인의 예시를 보겠습니다.

1. **수집**: Flume으로 웹 서버 로그를 실시간 수집하여 HDFS에 적재
2. **전송**: Sqoop으로 MySQL의 사용자 테이블을 HDFS로 임포트
3. **가공**: Pig로 로그 데이터를 파싱하고 정제하는 ETL 작업 수행
4. **분석**: Hive로 정제된 데이터에 대해 SQL 기반 집계 분석
5. **서빙**: 분석 결과를 Sqoop으로 다시 RDBMS에 내보내거나, HBase에 저장하여 실시간 조회 제공

이 구조에서 HDFS가 중앙 저장소 역할을 하고, YARN이 각 처리 엔진의 리소스를 통합 관리합니다.

### 현대 데이터 플랫폼에서의 위치

클라우드 네이티브 시대에 접어들면서 Hadoop 에코시스템의 각 컴포넌트는 클라우드 서비스로 대체되거나 진화하고 있습니다.

- HDFS는 Amazon S3, Google Cloud Storage 등 오브젝트 스토리지로 대체되는 추세입니다.
- 순수 MapReduce의 사용은 급감하고, Spark와 Flink가 주류 처리 엔진이 되었습니다.
- YARN의 역할을 Kubernetes가 대신하는 사례가 늘고 있습니다.
- Hive는 여전히 메타스토어로서 활발히 사용되지만, 대화형 분석은 Trino(구 PrestoSQL)나 DuckDB 쪽으로 이동하고 있습니다.
- Sqoop은 AWS Glue, Airbyte 같은 클라우드 ETL 도구로 대체되고 있습니다.

그러나 Hadoop이 확립한 분산 저장-처리 패러다임 자체는 현대 데이터 엔지니어링의 근간으로 남아 있습니다. S3 + Spark + Hive Metastore로 구성되는 데이터 레이크 아키텍처도, Delta Lake나 Apache Iceberg 같은 차세대 테이블 포맷도, 모두 Hadoop이 제시한 패러다임의 연장선에 있습니다.

## 정리

Hadoop 에코시스템의 핵심 구성 요소를 다시 한번 정리합니다.

| 컴포넌트 | 역할 | 핵심 포인트 |
|---|---|---|
| HDFS | 분산 파일 시스템 | 128MB 블록 단위, 3중 복제 |
| MapReduce | 분산 처리 모델 | Map-Shuffle-Reduce, 디스크 기반 |
| YARN | 리소스 관리 | Hadoop 2.0부터 도입, 멀티 엔진 지원 |
| Hive | SQL 기반 분석 | HiveQL -> MapReduce/Tez/Spark 변환 |
| Pig | 데이터 흐름 처리 | Pig Latin, ETL에 적합 |
| Sqoop | RDBMS 연동 | Import/Export, 증분 전송 지원 |
| HBase | NoSQL DB | 실시간 읽기/쓰기, Column Family 모델 |
| Flume | 로그 수집 | 실시간 스트리밍 수집 |

Hadoop 에코시스템을 이해하는 것은 레거시 기술을 공부하는 것이 아닙니다. 현대 데이터 플랫폼의 설계 원리를 이해하는 것입니다. 클라우드 환경에서 Spark를 사용하든, Kubernetes 위에서 Flink를 운영하든, 그 기저에는 Hadoop이 정립한 분산 저장과 분산 처리의 원칙이 깔려 있습니다.

다음 글에서는 Hadoop의 디스크 I/O 한계를 극복한 인메모리 분산 처리 엔진인 Apache Spark를 다룹니다.

---

참고 자료:
- [Apache Hadoop 공식 문서](https://hadoop.apache.org/docs/current/)
- [Hadoop: The Definitive Guide (Tom White)](https://www.oreilly.com/library/view/hadoop-the-definitive/9781491901687/)
- [하둡 에코시스템(Hadoop-Ecosystem)이란](https://butter-shower.tistory.com/73)