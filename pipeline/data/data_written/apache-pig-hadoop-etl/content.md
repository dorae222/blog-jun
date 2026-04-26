<!-- infographic-hero -->
![Apache Pig - Hadoop ETL with Pig Latin Guide 핵심 요약](figures/infographic.svg)

*Figure: Apache Pig - Hadoop ETL with Pig Latin Guide 한 장 요약 인포그래픽*

## 개요

Hadoop 생태계에서 대용량 데이터를 처리하려면 MapReduce 프로그래밍이 필수적입니다. 그러나 단순한 WordCount 하나를 구현하는 데도 Mapper, Reducer 클래스를 정의하고, 입출력 포맷을 설정하며, Job 설정을 작성해야 합니다. Java 코드가 수십 줄에 달하는 이 과정은 데이터 엔지니어에게 반복적이고 생산성을 떨어뜨리는 작업입니다.

Apache Pig는 이러한 문제를 해결하기 위해 Yahoo에서 개발한 고수준 데이터 흐름 플랫폼입니다. Pig Latin이라는 절차적 스크립팅 언어를 통해 복잡한 Java MapReduce 코드 없이도 대용량 데이터의 변환, 필터링, 집계, 조인 등 ETL 작업을 수행할 수 있습니다.

예를 들어, MapReduce로 작성하면 60줄이 넘는 WordCount 프로그램을 Pig Latin으로는 단 4줄로 표현할 수 있습니다. 이 글에서는 Pig의 핵심 개념과 자료구조, 관계형 연산자, 집계 함수, 문자열 처리까지 실전 코드를 중심으로 살펴보겠습니다.

### Pig Latin vs Hive 비교

Hadoop 위에서 데이터를 다루는 도구로는 Pig 외에도 Hive가 있습니다. 두 도구의 차이를 이해하면 상황에 맞는 선택이 가능합니다.

- Pig Latin은 데이터 흐름을 단계적으로 정의하는 절차적(procedural) 언어입니다. 비정형 데이터나 복잡한 변환 로직에 강점이 있습니다.
- Hive는 SQL과 유사한 선언적(declarative) 언어입니다. 구조화된 데이터의 분석과 임시 쿼리(ad-hoc query)에 적합합니다.
- Pig는 반복적인 ETL 파이프라인 구성에 유리하고, Hive는 데이터 분석가가 익숙한 SQL 문법으로 쿼리를 작성할 수 있다는 장점이 있습니다.

---

## 핵심 개념

### MapReduce의 한계와 Pig의 등장

먼저 MapReduce로 작성한 WordCount 코드를 살펴보겠습니다. 이 예제를 통해 Pig가 왜 필요한지 체감할 수 있습니다.

```java
import java.io.IOException;
import java.util.*;

import org.apache.hadoop.fs.Path;
import org.apache.hadoop.conf.*;
import org.apache.hadoop.io.*;
import org.apache.hadoop.mapreduce.*;
import org.apache.hadoop.mapreduce.lib.input.*;
import org.apache.hadoop.mapreduce.lib.output.*;

public class WordCount {

 public static class MyMapper extends Mapper<LongWritable, Text, Text, LongWritable> {
    private final static LongWritable one = new LongWritable(1);
    private Text word = new Text();

    public void map(LongWritable key, Text value, Context context) throws IOException, InterruptedException {
        String line = value.toString();
        StringTokenizer tokenizer = new StringTokenizer(line, "\t\r\n\f |,.()<>");
        while (tokenizer.hasMoreTokens()) {
            word.set(tokenizer.nextToken().toLowerCase());
            context.write(word, one);
        }
    }
 }

 public static class MyReducer extends Reducer<Text, LongWritable, Text, LongWritable> {
    private LongWritable sumWritable = new LongWritable();

    public void reduce(Text key, Iterable<LongWritable> values, Context context)
      throws IOException, InterruptedException {
        long sum = 0;
        for (LongWritable val : values) {
            sum += val.get();
        }
        sumWritable.set(sum);
        context.write(key, sumWritable);
    }
 }

 public static void main(String[] args) throws Exception {
    Configuration conf = new Configuration();
    Job job = new Job(conf, "WordCount");
    job.setJarByClass(WordCount.class);
    job.setMapperClass(MyMapper.class);
    job.setReducerClass(MyReducer.class);
    job.setOutputKeyClass(Text.class);
    job.setOutputValueClass(LongWritable.class);
    job.setInputFormatClass(TextInputFormat.class);
    job.setOutputFormatClass(TextOutputFormat.class);
    FileInputFormat.addInputPath(job, new Path(args[0]));
    FileOutputFormat.setOutputPath(job, new Path(args[1]));
    job.waitForCompletion(true);
 }
}
```

JAR 파일로 컴파일한 후 다음과 같이 실행합니다.

```bash
hadoop jar /Data/WordCount-1.0-SNAPSHOT.jar WordCount /tmp/data/README.txt /tmp/output
```

각 인자의 의미는 다음과 같습니다.

- `jar`: JAR 파일 실행 명령
- `/Data/WordCount-1.0-SNAPSHOT.jar`: JAR 파일 경로
- `WordCount`: 실행할 클래스 이름
- `/tmp/data/README.txt`: HDFS 상의 입력 데이터 경로
- `/tmp/output`: 결과가 저장될 HDFS 디렉토리

이처럼 간단한 단어 빈도 집계를 위해 Mapper 클래스, Reducer 클래스, 메인 메서드까지 상당한 분량의 코드가 필요합니다. Pig Latin을 사용하면 동일한 작업을 훨씬 간결하게 처리할 수 있습니다.

### Pig 실행 환경

Pig는 Grunt Shell이라는 대화형 인터페이스를 제공합니다.

```bash
# Pig 접속
pig

# Pig 종료
quit
```

Grunt Shell에서는 Pig Latin 명령을 한 줄씩 입력하며 데이터를 탐색하고 변환할 수 있습니다. 스크립트 파일(.pig)을 작성하여 일괄 실행하는 것도 가능합니다.

### 자료구조

Pig Latin에서 다루는 핵심 자료구조는 세 가지입니다.

Tuple은 순서가 있는 필드의 집합으로, 관계형 데이터베이스의 행(row)에 해당합니다. 소괄호로 표현됩니다.

```pig
-- 튜플 자료구조 로드
A = LOAD 'sample_tuple.txt' AS (t1:tuple(t1a:int,t1b:int,t1c:int), t2:tuple(t2a:int,t2b:int,t2c:int));

-- 특정 필드 접근: 이름 또는 위치($n) 사용
X = FOREACH A GENERATE t1.t1a, t2.$0;
```

Bag은 튜플의 집합입니다. 중괄호로 표현되며, GROUP 연산의 결과로 자주 생성됩니다.

```pig
-- Bag 자료구조
A = LOAD 'sample_bag.txt' AS (f1:int, f2:int, f3:int);
X = GROUP A BY f1;
DUMP X;
```

GROUP 연산을 수행하면 같은 키를 가진 튜플들이 하나의 Bag으로 묶입니다. 결과에는 group이라는 키 필드와 원본 릴레이션 이름의 Bag 필드가 생성됩니다.

Map은 키-값 쌍의 집합입니다. 대괄호로 표현됩니다.

```pig
-- Map 자료구조
A = LOAD 'sample_map.txt' AS (M:map []);
DUMP A;
```

---

## 실전 코드

### 데이터 로드와 기본 연산

Pig에서 데이터를 다루는 첫 단계는 LOAD 명령으로 파일을 읽어들이는 것입니다. AS 절을 통해 스키마를 정의할 수 있습니다.

```pig
-- 기본 데이터 로드 (스키마 지정)
A = LOAD 'sample.txt' AS (name:chararray, age:int, score:double);

-- FOREACH ~ GENERATE로 필드 선택
X = FOREACH A GENERATE name, $2;
DUMP X;
```

$0, $1, $2와 같은 위치 참조를 사용하면 필드 이름 대신 순서로 접근할 수 있습니다.

### 산술 연산자

```pig
A = LOAD 'sample_arithmetic.txt' AS (f1:int, f2:int);

-- 사칙연산과 나머지 연산
X = FOREACH A GENERATE f1, f2, f1+f2, f1-f2, f1*f2, f1/f2, f1%f2;
DUMP X;
```

### 불린 연산자와 필터링

FILTER 명령은 조건에 맞는 튜플만 추출합니다. AND, OR, NOT 연산자를 조합하여 복합 조건을 구성할 수 있습니다.

```pig
A = LOAD 'sample.txt' AS (f1:int, f2:int, f3:int);

-- OR, NOT 조합
X = FILTER A BY (f1==8) OR (NOT (f2+f3 > f1));
DUMP X;

-- AND 조합
Y = FILTER A BY (f2 > 2) AND f3 == 9;
DUMP Y;
```

### 형 변환(Cast) 연산자

집계 결과의 타입을 변환할 때 형 변환 연산자를 사용합니다.

```pig
B = GROUP A BY f1;
X = FOREACH B GENERATE group, (chararray)COUNT(A) AS total;
DUMP X;
```

COUNT 함수의 반환값은 long 타입인데, 이를 chararray(문자열)로 변환하여 출력 포맷을 맞출 수 있습니다.

### 데이터 조건 검증(ASSERT)

데이터 품질을 검증할 때 ASSERT를 사용합니다. 조건을 만족하지 않는 데이터가 있으면 오류가 발생합니다.

```pig
ASSERT A BY a0 > 3, 'a0 should be greater than 3';
```

### 관계형 연산자

Pig Latin은 SQL의 주요 관계형 연산을 지원합니다.

DISTINCT는 중복 튜플을 제거합니다.

```pig
X = DISTINCT A;
DUMP X;
```

CROSS는 두 릴레이션의 직교 곱(Cartesian Product)을 생성합니다.

```pig
X = CROSS A, B;
DUMP X;
```

### Join 연산

Pig는 다양한 종류의 조인을 지원합니다.

```pig
-- Inner Join: 양쪽 모두에 존재하는 키만 매칭
C = JOIN A BY id, B BY id;

-- Left Outer Join: 왼쪽 릴레이션의 모든 레코드 유지
C = JOIN A BY id LEFT OUTER, B BY id;

-- Right Outer Join: 오른쪽 릴레이션의 모든 레코드 유지
C = JOIN A BY id RIGHT OUTER, B BY id;

-- Full Outer Join: 양쪽 모든 레코드 유지
C = JOIN A BY id FULL OUTER, B BY id;
```

Self Join도 가능합니다. 같은 릴레이션을 별도의 별칭으로 로드한 뒤 조인하면 됩니다.

### COGROUP

COGROUP은 여러 릴레이션을 키 기준으로 그룹화하되, 각 릴레이션의 데이터를 별도의 Bag으로 유지합니다. JOIN과 달리 데이터가 병합되지 않으므로 원본 구조를 보존한 채 분석할 수 있습니다.

```pig
X = COGROUP A BY owner, B BY friend2;
DUMP X;
```

### 복합 FOREACH ~ GENERATE

중첩된 블록 안에서 FILTER, DISTINCT 등을 수행한 후 결과를 생성하는 패턴입니다. 그룹화된 데이터에서 세부적인 변환이 필요할 때 유용합니다.

```pig
X = FOREACH B {
    FA = FILTER A BY outlink == 'www.xyz.org';
    DA = DISTINCT FA;
    GENERATE group, COUNT(DA);
}
DUMP X;
```

### Cube와 Rollup

OLAP 스타일의 다차원 집계를 수행할 수 있습니다.

```pig
-- CUBE: 모든 차원 조합의 집계
cubedinp = CUBE salesinp BY CUBE(product, year);

-- ROLLUP: 계층적 집계 (region > state > city)
rolledup = CUBE salesinp BY ROLLUP(region, state, city);
```

CUBE는 지정된 차원의 모든 조합에 대해 집계를 수행하고, ROLLUP은 왼쪽에서 오른쪽으로 계층적으로 집계합니다.

### 정렬, 제한, 샘플링

```pig
-- ORDER BY: 정렬
B = ORDER A BY f1 ASC, f2 DESC;

-- RANK: 순위 부여
B = RANK A;
C = RANK A BY f1 DESC, f2 ASC;

-- LIMIT: 상위 N개 추출
X = LIMIT A 3;

-- SAMPLE: 무작위 샘플링 (10%)
S = SAMPLE A 0.1;
```

### 분할, 합집합, 저장

```pig
-- SPLIT: 조건에 따라 데이터 분할
SPLIT A INTO X IF f1 > 5, Y IF f1 <= 5, Z IF f1 == 5;

-- UNION: 릴레이션 합치기
C = UNION A, B;

-- STORE: 결과 저장 (디렉토리로 저장됨)
STORE A INTO 'output_dir' USING PigStorage(',');
```

STORE의 결과는 파일이 아니라 디렉토리로 저장됩니다. 내부적으로 part-m-00000, part-r-00000 형태의 파일들로 분산 저장됩니다.

### 집계 함수

```pig
-- 전체 그룹에 대한 집계
B = GROUP A ALL;
X = FOREACH B GENERATE AVG(A.score), MAX(A.score), COUNT(A);
DUMP X;
```

AVG, MAX, MIN, COUNT, SUM 등 일반적인 집계 함수를 사용할 수 있습니다.

### 문자열 함수

```pig
-- 대소문자 변환, 공백 제거
X = FOREACH A GENERATE UPPER(name), LOWER(name), TRIM(name);

-- 부분 문자열 추출
X = FOREACH A GENERATE SUBSTRING(name, 0, 3);

-- 문자열 치환
X = FOREACH A GENERATE REPLACE(name, 'old', 'new');

-- ENDSWITH, STARTSWITH 필터링
X = FILTER A BY ENDSWITH(name, 'son');
Y = FILTER A BY STARTSWITH(name, 'Jo');
```

### 기타 유용한 함수

BagToString은 Bag의 내용을 하나의 문자열로 변환합니다.

```pig
B = GROUP A BY f1;
X = FOREACH B GENERATE group, BagToString(A, ',');
DUMP X;
```

TOKENIZE는 문자열을 토큰 단위로 분리하여 Bag으로 반환합니다. WordCount 구현에 핵심적으로 사용됩니다.

```pig
A = LOAD 'input.txt' AS (line:chararray);
B = FOREACH A GENERATE TOKENIZE(line) AS words;
C = FOREACH B GENERATE FLATTEN(words) AS word;
D = GROUP C BY word;
E = FOREACH D GENERATE group, COUNT(C);
STORE E INTO 'wordcount_output';
```

위 코드는 MapReduce로 60줄 이상 작성해야 했던 WordCount를 6줄로 구현한 것입니다.

TextLoader는 각 행을 하나의 텍스트 필드로 로드할 때 사용합니다.

```pig
A = LOAD 'input.txt' USING TextLoader() AS (line:chararray);
DUMP A;
```

ToMap은 키-값 쌍을 Map 자료구조로 변환합니다.

```pig
X = FOREACH A GENERATE ToMap(key, value);
DUMP X;
```

Top은 각 그룹에서 상위 N개의 튜플을 추출합니다.

```pig
B = GROUP A ALL;
X = FOREACH B GENERATE TOP(3, 1, A);
DUMP X;
```

IN 연산자는 값이 특정 집합에 포함되는지 확인합니다.

```pig
X = FILTER A BY f1 IN (1, 3, 5, 7);
DUMP X;
```

### 데이터 분석 실전 예제

탭으로 구분된 직원 데이터를 로드하여 부서별 그룹화까지 수행하는 종합 예제입니다.

```pig
-- 데이터 로드 (탭 구분)
emp = LOAD '/tmp/pigdemo.txt' USING PigStorage('\t') AS (name:chararray, dept:chararray);

-- 조건 필터링
filtered = FILTER emp BY dept == 'Engineering';

-- 그룹화
emp_group = GROUP emp BY dept;

-- 저장
STORE emp_group INTO 'emp_group.txt';
```

---

## 활용 사례

### 로그 분석 파이프라인

Pig는 웹 서버 로그 분석에 널리 사용되었습니다. 비정형 로그 데이터를 파싱하고, 필터링한 후, 통계를 집계하는 과정을 절차적으로 기술할 수 있기 때문입니다.

```pig
-- 웹 로그 분석 예제
logs = LOAD '/data/access.log' USING TextLoader() AS (line:chararray);
parsed = FOREACH logs GENERATE
    REGEX_EXTRACT(line, '(\\S+) - - \\[(.+?)\\]', 1) AS ip,
    REGEX_EXTRACT(line, '"(GET|POST) (.+?) HTTP', 2) AS url;
filtered = FILTER parsed BY url IS NOT NULL;
url_group = GROUP filtered BY url;
url_count = FOREACH url_group GENERATE group AS url, COUNT(filtered) AS cnt;
sorted = ORDER url_count BY cnt DESC;
top_urls = LIMIT sorted 20;
STORE top_urls INTO '/output/top_urls';
```

### 대규모 데이터 전처리

머신러닝 모델 학습 전 데이터를 정제하는 전처리 파이프라인에서도 Pig가 활용됩니다. 결측치 제거, 타입 변환, 피처 추출 등을 스크립트 한 벌로 정의할 수 있습니다.

### Yahoo와 대규모 조직에서의 활용

Pig는 Yahoo에서 내부 데이터 처리 작업의 상당 부분을 담당했습니다. 검색 인덱싱, 광고 클릭 데이터 분석, 사용자 행동 로그 집계 등 다양한 ETL 파이프라인이 Pig Latin으로 작성되었습니다.

### 현재의 위치

현재 Apache Pig는 Apache Spark, Apache Flink 등 차세대 분산 처리 프레임워크에 자리를 내주는 추세입니다. 2017년 이후 Apache Pig의 주요 릴리스가 사실상 중단되었고, 2024년에는 Apache Attic으로 이동했습니다. 하지만 기존 Hadoop 클러스터 기반의 레거시 파이프라인에서는 여전히 운영되고 있으며, Pig Latin의 데이터 흐름 중심 사고방식은 이후 등장한 Spark의 DataFrame API나 Beam의 파이프라인 모델에도 영향을 주었습니다.

---

## 정리

Apache Pig는 Hadoop MapReduce의 복잡성을 추상화하여 데이터 엔지니어가 ETL 로직에 집중할 수 있게 해주었던 도구입니다. 이 글에서 다룬 내용을 정리하면 다음과 같습니다.

첫째, Pig Latin은 절차적 데이터 흐름 언어로, MapReduce의 Map/Reduce 패러다임을 LOAD, FILTER, GROUP, FOREACH, STORE 같은 직관적인 명령어로 대체합니다. 수십 줄의 Java 코드가 몇 줄의 Pig Latin 스크립트로 줄어드는 것이 가장 큰 장점입니다.

둘째, Pig의 자료구조는 Tuple(행), Bag(튜플의 집합), Map(키-값 쌍)의 세 가지로 구성됩니다. GROUP 연산의 결과가 Bag으로 반환되는 점을 이해하면 복합 FOREACH 패턴까지 자연스럽게 연결됩니다.

셋째, 관계형 연산자로 JOIN, COGROUP, CROSS, DISTINCT, SPLIT, UNION을 지원하며, CUBE와 ROLLUP을 통해 다차원 집계도 가능합니다.

넷째, AVG, COUNT, MAX, TOKENIZE, SUBSTRING, BagToString 등 풍부한 내장 함수를 제공합니다.

Pig 자체는 현재 활발히 개발되는 프로젝트는 아니지만, Pig Latin이 보여준 데이터 흐름 중심의 파이프라인 설계 패턴은 Spark, Beam, dbt 등 현대 데이터 도구의 근간을 이루고 있습니다. Hadoop 생태계를 이해하고 레거시 시스템을 운영하는 데이터 엔지니어에게는 여전히 알아둘 가치가 있는 기술입니다.