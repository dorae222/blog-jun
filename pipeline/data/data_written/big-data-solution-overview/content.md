# 빅데이터 솔루션 총정리: Hadoop 에코시스템 컴포넌트와 아키텍처

## 개요

데이터의 규모가 테라바이트를 넘어 페타바이트 단위에 도달하면, 단일 서버에서 동작하는 전통적인 RDBMS만으로는 저장과 처리 모두 한계에 부딪힙니다. 이 문제를 해결하기 위해 등장한 것이 Hadoop을 중심으로 한 빅데이터 솔루션 스택입니다.

Hadoop은 대용량 데이터를 낮은 비용으로 빠르게 분석할 수 있게 해 주는 오픈소스 소프트웨어 프레임워크입니다. 하지만 Hadoop이라는 이름 하나로 모든 것을 설명하기에는 범위가 너무 넓습니다. 실제 빅데이터 파이프라인을 구축하려면 데이터 저장, 분산 처리, 데이터 전송, 분석 쿼리, NoSQL 저장소 등 여러 컴포넌트를 조합해야 합니다.

이 글에서는 Hadoop 에코시스템을 구성하는 주요 솔루션들의 역할과 관계를 정리하고, 각 도구가 해결하는 문제가 무엇인지 실전 코드와 함께 살펴보겠습니다.

## 핵심 개념

### Hadoop 에코시스템의 구조

Hadoop 에코시스템은 크게 코어 프로젝트와 서브 프로젝트로 나뉩니다.

코어 프로젝트는 분산 파일 시스템인 HDFS와 분산 처리 모델인 MapReduce로 구성됩니다. 이 두 가지가 Hadoop의 근간이며, 나머지 모든 서브 프로젝트들은 이 코어 위에서 데이터 마이닝, 수집, 분석 등 다양한 작업을 수행하는 도구들입니다.

전체 구조를 계층별로 정리하면 다음과 같습니다.

```text
+----------------------------------------------------------+
|                    응용 계층 (Applications)                |
|         Hive (SQL)  |  Pig (Script)  |  Sqoop (전송)      |
+----------------------------------------------------------+
|                    처리 계층 (Processing)                  |
|         MapReduce   |   Spark   |   Tez                  |
+----------------------------------------------------------+
|                  리소스 관리 (Resource Mgmt)               |
|                        YARN                              |
+----------------------------------------------------------+
|                    저장 계층 (Storage)                     |
|              HDFS          |        HBase                |
+----------------------------------------------------------+
|                     인프라 (Infrastructure)                |
|               범용 하드웨어 클러스터                        |
+----------------------------------------------------------+
```

각 계층의 컴포넌트는 독립적으로 교체하거나 확장할 수 있습니다. 예를 들어 처리 계층에서 MapReduce 대신 Spark를 사용하거나, 저장 계층에서 HDFS 대신 클라우드 스토리지를 사용하는 것이 가능합니다.

### HDFS: 분산 파일 시스템

HDFS(Hadoop Distributed File System)는 Hadoop의 분산 파일 시스템입니다. 파일 시스템이란 보조 저장장치에 파일을 어떻게 저장할지 결정하는 체계를 말합니다. 운영체제마다 파일 시스템이 다른데, 윈도우는 NTFS를, 리눅스는 ext 계열을 사용하는 것이 대표적인 예입니다.

HDFS가 분산인 이유는 단순합니다. 매우 큰 파일 하나를 단일 디스크에 저장하면 읽기 속도가 디스크 하나의 대역폭에 묶이지만, 여러 디스크에 나누어 저장하면 병렬로 읽을 수 있기 때문입니다. 9초 걸리는 읽기 작업도 3개 디스크에 분산하면 3초에 끝낼 수 있습니다.

HDFS는 Master-Slave 구조로 동작합니다.

- NameNode(Master): 파일이 어떤 블록으로 나뉘어 어느 DataNode에 저장되어 있는지 메타데이터를 관리합니다.
- DataNode(Slave): 실제 데이터 블록을 저장하고, NameNode의 지시에 따라 블록을 복제하거나 삭제합니다.

파일은 기본 128MB 단위의 블록으로 분할되며, 각 블록은 기본적으로 3개의 복제본이 서로 다른 노드에 저장됩니다.

```bash
# HDFS 기본 명령어
hadoop fs -mkdir /user/data/logs             # 디렉토리 생성
hadoop fs -put access.log /user/data/logs/    # 로컬 파일을 HDFS로 업로드
hadoop fs -ls /user/data/logs/               # 디렉토리 목록 확인
hadoop fs -cat /user/data/logs/access.log    # 파일 내용 출력
hadoop fs -get /user/data/logs/access.log ./ # HDFS 파일을 로컬로 다운로드
hadoop fs -rm /user/data/logs/access.log     # 파일 삭제
```

### MapReduce: 분산 처리 모델

MapReduce는 HDFS에 저장된 대용량 데이터를 병렬로 처리하기 위한 프로그래밍 모델이자 라이브러리입니다. Java 기반으로 작성되며, 이름 그대로 Map 단계와 Reduce 단계로 구성됩니다.

- Map 단계: 입력 데이터를 읽어 Key-Value 쌍으로 변환합니다.
- Shuffle 단계: 같은 Key를 가진 데이터를 모아서 정렬합니다.
- Reduce 단계: 같은 Key에 대한 Value들을 집계하여 최종 결과를 생성합니다.

MapReduce는 분산 파일 시스템에 명령을 내리기 위한 핵심 수단이지만, Java로 직접 작성해야 한다는 점이 진입 장벽으로 작용했습니다. 이 문제를 해결하기 위해 Pig와 Hive가 등장했습니다.

### DBMS와 Hadoop 사이의 다리: Sqoop

실제 기업 환경에서는 기존 RDBMS에 축적된 데이터를 Hadoop으로 옮기거나, Hadoop에서 분석한 결과를 다시 RDBMS로 내보내야 하는 경우가 빈번합니다. Sqoop(SQL-to-Hadoop)은 이 문제를 해결합니다.

Sqoop은 MySQL, Oracle 같은 RDBMS와 HDFS, Hive, HBase 같은 Hadoop 저장소 사이에서 대용량 데이터를 신속하게 전송할 수 있는 방법을 제공합니다. 내부적으로 MapReduce 작업을 생성하여 병렬 전송을 수행하므로, 단순한 JDBC 덤프보다 훨씬 빠릅니다.

### MapReduce를 쉽게 쓰는 두 가지 방법: Pig와 Hive

Hadoop은 내부적으로 MapReduce를 수행하지만, MapReduce를 직접 다루려면 Java를 사용해야 합니다. SQL이나 스크립트에 익숙한 개발자에게는 진입 장벽이 높았고, 이를 해소하기 위해 두 가지 접근 방식이 등장했습니다.

Pig는 데이터 흐름을 명시적으로 표현하는 Pig Latin이라는 스크립트 언어를 제공합니다. Pig Latin으로 작성한 프로그램은 논리적 실행 계획으로 변환되고, 최종적으로 MapReduce 실행 계획으로 변환됩니다. 내장 옵티마이저가 여러 실행 방법 중 가장 효율적인 경로를 자동으로 선택해 줍니다.

Hive는 SQL 구문 형식으로 MapReduce를 실행할 수 있게 해주는 데이터 웨어하우스 프레임워크입니다. SQL에 익숙한 분석가가 별도의 프로그래밍 없이 대용량 데이터를 쿼리할 수 있다는 점이 가장 큰 장점입니다.

두 도구의 핵심적인 차이를 정리하면 다음과 같습니다.

| 구분 | Pig | Hive |
|------|-----|------|
| 언어 | Pig Latin (절차적 스크립트) | HiveQL (선언적, SQL 유사) |
| 주 사용자 | 데이터 엔지니어, ETL 개발자 | 데이터 분석가, BI 담당자 |
| JOIN 성능 | 우수 | 상대적으로 약함 |
| 최적화 | 내장 옵티마이저 | Cost-Based Optimizer |
| 적합한 작업 | ETL 파이프라인, 데이터 흐름 처리 | 대화형 분석, 데이터 웨어하우징 |

Pig의 장점은 옵티마이저를 통한 실행 최적화입니다. 여러 실행 경로 중 반복 작업을 줄이고 CPU 사용량이 적은 방법을 자동으로 선택합니다. 반면 잘못 작성하면 반복 작업이 많아지고 CPU를 과도하게 사용할 수 있다는 점은 주의해야 합니다.

Hive는 SQL 사용자에게 친숙하다는 점이 강력한 장점이지만, JOIN 연산이 취약한 편입니다. 여러 테이블을 JOIN해서 사용해야 하는 경우에는 Pig가 성능 면에서 유리한 경우가 있습니다.

### NoSQL 저장소: HBase

HBase는 Hadoop의 HDFS 위에 만들어진 분산 컬럼 기반 NoSQL 데이터베이스입니다. Google의 Bigtable 논문에서 영감을 받아 설계되었으며, 수십억 행과 수백만 컬럼 규모의 테이블을 다룰 수 있습니다.

HDFS가 배치 처리에 최적화되어 있어 실시간 읽기/쓰기에는 부적합한 반면, HBase는 랜덤 액세스와 실시간 읽기/쓰기가 가능합니다. HDFS의 저장 능력과 실시간 접근성을 결합한 솔루션이라고 볼 수 있습니다.

### 차세대 처리 엔진: Spark

Apache Spark는 MapReduce의 디스크 I/O 병목을 극복한 인메모리 분산 처리 엔진입니다. MapReduce가 매 연산 단계마다 중간 결과를 디스크에 저장하는 것과 달리, Spark는 중간 결과를 메모리에 유지하여 반복적 연산에서 극적인 성능 향상을 제공합니다.

Spark가 제공하는 주요 기능은 다음과 같습니다.

- 고속 인메모리 처리
- MLlib을 통한 머신러닝 라이브러리
- GraphX를 통한 그래프 처리
- Spark SQL을 통한 SQL 형태의 인터페이스
- Structured Streaming을 통한 실시간 스트리밍 처리

## 실전 코드

각 컴포넌트의 실제 사용 방법을 코드로 살펴보겠습니다.

### Sqoop: RDBMS에서 Hadoop으로 데이터 가져오기

```bash
# MySQL의 orders 테이블을 HDFS로 Import
sqoop import \
    --connect jdbc:mysql://db-server:3306/ecommerce \
    --table orders \
    --username hadoop_user \
    --password-file /user/hadoop/.password \
    --target-dir /user/data/orders \
    --num-mappers 4 \
    --split-by order_id

# 증분 Import: 마지막 Import 이후 추가된 데이터만 가져오기
sqoop import \
    --connect jdbc:mysql://db-server:3306/ecommerce \
    --table orders \
    --username hadoop_user \
    --password-file /user/hadoop/.password \
    --target-dir /user/data/orders_incremental \
    --incremental append \
    --check-column order_id \
    --last-value 10000

# 분석 결과를 다시 MySQL로 Export
sqoop export \
    --connect jdbc:mysql://db-server:3306/ecommerce \
    --table daily_summary \
    --export-dir /user/data/analysis_output \
    --input-fields-terminated-by '\t'
```

### Pig Latin: ETL 데이터 처리

```pig
-- 웹 로그 분석 예시: 시간대별 접속 통계
raw_logs = LOAD '/user/data/logs/access.log'
    USING TextLoader() AS (line:chararray);

-- 로그 파싱: IP, 타임스탬프, 요청 URL 추출
parsed = FOREACH raw_logs GENERATE
    REGEX_EXTRACT(line, '^(\\S+)', 1) AS ip,
    REGEX_EXTRACT(line, '\\[(.*?)\\]', 1) AS timestamp,
    REGEX_EXTRACT(line, '"\\S+ (\\S+)', 1) AS url;

-- 시간대 추출 (HH 부분)
with_hour = FOREACH parsed GENERATE
    SUBSTRING(timestamp, 12, 14) AS hour,
    ip;

-- 시간대별 고유 접속자 수 집계
grouped = GROUP with_hour BY hour;
hourly_stats = FOREACH grouped {
    unique_ips = DISTINCT with_hour.ip;
    GENERATE group AS hour,
             COUNT(with_hour) AS total_requests,
             COUNT(unique_ips) AS unique_visitors;
};

sorted = ORDER hourly_stats BY hour ASC;
STORE sorted INTO '/user/data/output/hourly_stats';
```

### Hive: SQL 스타일의 빅데이터 분석

```sql
-- 외부 테이블 생성: HDFS 경로의 로그 데이터를 테이블로 매핑
CREATE EXTERNAL TABLE IF NOT EXISTS web_logs (
    ip STRING,
    request_time STRING,
    method STRING,
    url STRING,
    status INT,
    size BIGINT
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE
LOCATION '/user/data/logs/parsed/';

-- 일별 HTTP 상태 코드 분포 분석
SELECT
    SUBSTR(request_time, 1, 10) AS log_date,
    status,
    COUNT(*) AS request_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (
        PARTITION BY SUBSTR(request_time, 1, 10)
    ), 2) AS percentage
FROM web_logs
WHERE request_time >= '2025-01-01'
GROUP BY SUBSTR(request_time, 1, 10), status
ORDER BY log_date, status;

-- 파티셔닝된 테이블 생성: 날짜별로 분할하여 쿼리 성능 향상
CREATE TABLE web_logs_partitioned (
    ip STRING,
    method STRING,
    url STRING,
    status INT,
    size BIGINT
)
PARTITIONED BY (log_date STRING)
STORED AS ORC;

-- 동적 파티션 삽입
SET hive.exec.dynamic.partition = true;
SET hive.exec.dynamic.partition.mode = nonstrict;

INSERT OVERWRITE TABLE web_logs_partitioned PARTITION (log_date)
SELECT ip, method, url, status, size,
       SUBSTR(request_time, 1, 10) AS log_date
FROM web_logs;
```

### Spark (PySpark): 인메모리 분산 처리

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, desc, hour, to_timestamp

spark = SparkSession.builder \
    .appName("WebLogAnalysis") \
    .getOrCreate()

# HDFS에서 로그 데이터 읽기
df = spark.read.csv(
    "/user/data/logs/access_parsed.csv",
    header=True,
    inferSchema=True
)

# 타임스탬프 변환 및 시간대 추출
df_with_hour = df.withColumn(
    "request_hour",
    hour(to_timestamp(col("request_time"), "yyyy-MM-dd HH:mm:ss"))
)

# 시간대별 요청 수 집계
hourly_stats = df_with_hour \
    .groupBy("request_hour") \
    .agg(count("*").alias("request_count")) \
    .orderBy("request_hour")

hourly_stats.show(24)

# 상위 10개 URL 분석
top_urls = df \
    .groupBy("url") \
    .agg(count("*").alias("hit_count")) \
    .orderBy(desc("hit_count")) \
    .limit(10)

top_urls.show(truncate=False)

# 결과를 Parquet 포맷으로 저장
hourly_stats.write.parquet(
    "/user/data/output/hourly_stats",
    mode="overwrite"
)
```

### MapReduce (Java): Word Count

MapReduce의 기본 동작을 이해하기 위한 고전적인 예제입니다.

```java
import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;

import java.io.IOException;
import java.util.StringTokenizer;

public class WordCount {

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

위 코드를 보면, 단순한 단어 빈도 집계에도 상당한 양의 보일러플레이트 코드가 필요합니다. 이것이 바로 Pig와 Hive가 등장한 이유입니다.

## 활용 사례

### 사례 1: 이커머스 데이터 파이프라인

대규모 이커머스 서비스에서 주문 데이터를 분석하는 파이프라인은 Hadoop 에코시스템의 여러 컴포넌트를 조합하여 구축합니다.

```text
[MySQL: 주문 DB]   -- Sqoop Import -->   [HDFS: 원본 데이터]
                                              |
                                    Pig (ETL: 정제/변환)
                                              |
                                    [HDFS: 정제된 데이터]
                                              |
                                    Hive (분석 쿼리 실행)
                                              |
                                    [HDFS: 분석 결과]
                                              |
                   [MySQL: 리포트 DB]  <-- Sqoop Export
```

운영 DB(MySQL)의 주문 데이터를 Sqoop으로 HDFS에 가져온 뒤, Pig로 ETL 작업(데이터 정제, 포맷 변환, 이상치 제거)을 수행합니다. 정제된 데이터에 대해 Hive로 매출 분석, 사용자 행동 패턴 분석 등을 실행하고, 최종 결과를 다시 Sqoop으로 리포트 DB에 적재합니다.

### 사례 2: 실시간 로그 분석

웹 서비스의 서버 로그를 실시간으로 수집하고 분석하는 아키텍처에서는 배치 처리와 실시간 처리를 함께 구성합니다.

- Flume이 각 웹 서버에서 로그를 실시간으로 수집하여 HDFS에 적재합니다.
- Spark Streaming이 실시간으로 들어오는 로그를 분석하여 이상 징후(비정상적인 트래픽 급증, 특정 에러 코드 반복 등)를 감지합니다.
- 축적된 로그 데이터에 대해서는 Hive로 일간/주간/월간 리포트를 배치로 생성합니다.
- 빈번하게 조회되는 분석 결과는 HBase에 저장하여 대시보드에서 실시간으로 조회할 수 있게 합니다.

### 사례 3: 솔루션 선택 기준

실무에서 어떤 도구를 선택할지 판단할 때, 데이터의 특성과 처리 요구사항에 따라 기준이 달라집니다.

| 요구사항 | 적합한 도구 | 이유 |
|----------|-------------|------|
| RDBMS 데이터를 HDFS로 이관 | Sqoop | 병렬 전송, 증분 Import 지원 |
| 복잡한 ETL 파이프라인 | Pig | 절차적 데이터 흐름, JOIN 성능 우수 |
| SQL 기반 대화형 분석 | Hive | SQL 호환, 기존 BI 도구 연동 용이 |
| 반복적 머신러닝 연산 | Spark | 인메모리 처리, MLlib 내장 |
| 실시간 읽기/쓰기 | HBase | 랜덤 액세스, 저지연 응답 |
| 대규모 로그 수집 | Flume | 안정적 스트리밍 수집, HDFS 직접 적재 |

### 현대적 환경에서의 변화

클라우드 환경이 보편화되면서 Hadoop 에코시스템의 각 컴포넌트는 클라우드 네이티브 서비스로 대체되는 추세입니다.

- HDFS의 역할을 Amazon S3, Google Cloud Storage가 대신합니다.
- MapReduce 대신 Spark와 Apache Flink가 처리 엔진의 주류가 되었습니다.
- Sqoop 대신 AWS Glue, Airbyte, Fivetran 같은 관리형 ETL 서비스가 사용됩니다.
- Hive 대신 Trino(구 PrestoSQL), Amazon Athena 같은 서버리스 쿼리 엔진이 등장했습니다.

그러나 이러한 클라우드 서비스들도 Hadoop이 확립한 분산 저장-처리 패러다임 위에서 동작합니다. HDFS의 블록 분산 저장 원리, MapReduce의 Map-Shuffle-Reduce 처리 패턴, Hive Metastore의 스키마 관리 방식은 현대 데이터 플랫폼에서도 그대로 계승되고 있습니다. Hadoop 에코시스템을 이해하는 것은 곧 현대 데이터 엔지니어링의 설계 원리를 이해하는 것과 같습니다.

## 정리

Hadoop 에코시스템은 빅데이터 처리를 위한 종합적인 솔루션 스택입니다. 각 컴포넌트의 역할을 다시 한번 정리하겠습니다.

- HDFS는 대용량 파일을 여러 서버에 분산 저장하는 파일 시스템입니다.
- MapReduce는 분산 저장된 데이터를 병렬로 처리하는 프로그래밍 모델이며, Java 기반으로 동작합니다.
- Sqoop은 기존 RDBMS와 Hadoop 저장소 사이에서 대용량 데이터를 전송하는 브릿지 역할을 합니다.
- Pig는 Pig Latin 스크립트를 통해 MapReduce를 보다 쉽게 작성할 수 있게 해주며, 내장 옵티마이저로 실행을 최적화합니다.
- Hive는 SQL 구문으로 MapReduce를 실행할 수 있게 해주는 데이터 웨어하우스 프레임워크입니다.
- HBase는 HDFS 위에 구축된 분산 컬럼 기반 NoSQL DB로, 실시간 읽기/쓰기가 필요한 경우에 사용합니다.
- Spark는 인메모리 처리를 통해 MapReduce의 디스크 I/O 한계를 극복한 차세대 분산 처리 엔진입니다.

이 컴포넌트들은 단독으로 사용되기보다는 파이프라인 안에서 유기적으로 조합됩니다. 데이터의 수집, 저장, 처리, 분석, 서빙이라는 각 단계에서 가장 적합한 도구를 선택하고 연결하는 것이 빅데이터 솔루션 설계의 핵심입니다.

---

참고 자료:
- [Apache Hadoop 공식 문서](https://hadoop.apache.org/docs/current/)
- [하둡 에코시스템(Hadoop-Ecosystem)이란](https://butter-shower.tistory.com/73)
- [Hadoop: The Definitive Guide (Tom White, O'Reilly)](https://www.oreilly.com/library/view/hadoop-the-definitive/9781491901687/)