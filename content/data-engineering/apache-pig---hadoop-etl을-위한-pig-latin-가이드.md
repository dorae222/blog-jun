---
title: "Apache Pig - Hadoop ETL을 위한 Pig Latin 가이드"
slug: "apache-pig---hadoop-etl을-위한-pig-latin-가이드"
category: "data-engineering"
tags: ["bigdata", "data-processing", "etl", "hadoop", "hdfs", "mapreduce", "pig", "pig-latin"]
status: published
post_type: tutorial
quality_score: 7.5
created_at: "2026-03-02T01:08:46.850786+00:00"
---

# Apache Pig - Hadoop ETL을 위한 Pig Latin 가이드

## Pig란?

Apache Pig는 Hadoop MapReduce 위에서 동작하는 고수준 데이터 흐름 언어 및 실행 환경이다. **Pig Latin**이라는 절차적(procedural) 스크립팅 언어를 사용하여, 복잡한 Java MapReduce 코드 없이도 대용량 데이터 변환과 ETL 작업을 수행할 수 있다.

### Pig Latin vs Hive 비교

- **Pig Latin**: 데이터 흐름을 단계적으로 정의하는 절차적 언어. 비정형 데이터나 복잡한 변환 로직에 강하다.
- **Hive**: SQL과 유사한 선언적 언어. 구조화된 데이터 분석과 임시 쿼리(ad-hoc query)에 적합하다.
- Pig는 반복적인 ETL 파이프라인 구성에 유리하며, Hive는 분석 쿼리에 더 직관적이다.

---

## WordCount 실습 - MapReduce JAR 실행

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

JAR 실행:

```bash
hadoop jar /Data/WordCount-1.0-SNAPSHOT.jar WordCount /tmp/data/README.txt /tmp/output
```

---

## Pig 기초 명령어

### 데이터 로드 및 기본 연산자

```pig
-- 기본 데이터 로드
A = LOAD 'sample.txt' AS (name:chararray, age:int, score:double);

-- 투플 자료구조
A = LOAD 'sample_tuple.txt' AS (t1:tuple(t1a:int,t1b:int,t1c:int), t2:tuple(t2a:int,t2b:int,t2c:int));
X = FOREACH A GENERATE t1.t1a, t2.$0;

-- Bag 자료구조
A = LOAD 'sample_bag.txt' as (f1:int, f2:int, f3:int);
X = GROUP A BY f1;

-- 산술 연산
A = LOAD 'sample_arithmetic.txt' AS (f1:int, f2:int);
X = FOREACH A GENERATE f1, f2, f1+f2, f1-f2, f1*f2, f1/f2, f1%f2;

-- 불린 연산자
X = FILTER A BY (f1==8) OR (NOT (f2+f3 > f1));

-- 형 변환
B = GROUP A BY f1;
X = FOREACH B GENERATE group, (chararray)COUNT(A) AS total;
```

### 관계형 연산자

```pig
-- Inner Join
C = JOIN A BY id, B BY id;

-- Left Outer Join
C = JOIN A BY id LEFT OUTER, B BY id;

-- 중복 제거
X = DISTINCT A;

-- 복합 FOREACH
X = FOREACH B {
    FA = FILTER A BY outlink == 'www.xyz.org';
    DA = DISTINCT FA;
    GENERATE group, COUNT(DA);
}

-- COGROUP (여러 릴레이션을 키 기준으로 묶기)
X = COGROUP A BY owner, B BY friend2;
```

### 정렬 및 기타

```pig
-- 정렬
B = ORDER A BY f1 ASC, f2 DESC;

-- 상위 N개
X = LIMIT A 3;

-- 샘플링
S = SAMPLE A 0.1;

-- 분할
SPLIT A INTO X IF f1 > 5, Y IF f1 <= 5;

-- 저장
STORE A INTO 'output_dir' USING PigStorage(',');

-- UNION
C = UNION A, B;
```

### 집계 및 문자열 함수

```pig
-- AVG, MAX, COUNT
B = GROUP A ALL;
X = FOREACH B GENERATE AVG(A.score), MAX(A.score), COUNT(A);

-- 문자열 조작
X = FOREACH A GENERATE UPPER(name), LOWER(name), TRIM(name);
X = FOREACH A GENERATE SUBSTRING(name, 0, 3);
X = FOREACH A GENERATE REPLACE(name, 'old', 'new');
```

---

## 데이터 분석 예제

```pig
-- 데이터 로드 (탭 구분)
emp = LOAD '/tmp/pigdemo.txt' USING PigStorage('\t') AS (name:chararray, dept:chararray);

-- 조건 필터링
filtered = FILTER emp BY dept == 'Engineering';

-- 그룹화
emp_group = GROUP emp BY dept;

-- 저장 (디렉토리로 저장됨)
STORE emp_group INTO 'emp_group.txt';
```

> Pig의 STORE 결과는 파일이 아니라 디렉토리로 저장된다. 내부적으로 part-m-00000, part-r-00000 형태의 파일들로 분산 저장된다.
