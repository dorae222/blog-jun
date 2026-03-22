---
title: Pig
slug: pig
category: "data-engineering"
tags: ["big-data", "data-engineering", "hadoop", "hdfs", "mapreduce", "pig", "pig-latin", "wordcount"]
status: published
post_type: tutorial
quality_score: 9.0
created_at: "2026-03-02T01:08:09.284472+00:00"
---

# [Pig]

### WordCloud 실습 — jar파일 실행하기

- jar → WordCount class에서 실행 가능
    - jar은 자바 클래스를 묶어 저장한 파일입니다.

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
        
        // if mapper outputs are different, call setMapOutputKeyClass and setMapOutputValueClass
        job.setOutputKeyClass(Text.class);
        job.setOutputValueClass(LongWritable.class);
            
        // An InputFormat for plain text files. Files are broken into lines. Either linefeed or carriage-return are used to signal end of line.
        // Keys are the position in the file, and values are the line of text..        
        job.setInputFormatClass(TextInputFormat.class);
        job.setOutputFormatClass(TextOutputFormat.class);
            
        FileInputFormat.addInputPath(job, new Path(args[0]));
        FileOutputFormat.setOutputPath(job, new Path(args[1]));
            
        job.waitForCompletion(true);
     }
    }
    ```
    
- 윈도우 → 리눅스(txt, jar)
    
    ![](/media/posts/imported/dev/BD-General_Untitled_9.png)
    
    ![](/media/posts/imported/dev/BD-General_Untitled-1_8.png)
    
- 리눅스 → 하둡(txt)
    
    ![](/media/posts/imported/dev/BD-General_Untitled-2_8.png)
    
- 실행
    - `hadoop jar /Data/WordCount-1.0-SNAPSHOT.jar WordCount /tmp/data/READEME.txt /tmp/output`
        - `jar` : jar 파일 실행
        - `/Data/WordCount-1.0-SNAPSHOT.jar`: jar 파일 경로
        - `WordCount:` 실행할 클래스 이름
        - `/tmp/data/READEME.txt`  : 입력 데이터 경로
        - `/tmp/output` : 결과 저장 디렉토리
    
    ![](/media/posts/imported/dev/BD-General_Untitled-3_7.png)
    
    ![](/media/posts/imported/dev/BD-General_Untitled-4_6.png)
    
- 결과
    
    ![](/media/posts/imported/dev/BD-General_Untitled-5_6.png)
    

### Pig 기초 명령어

- Pig 접속, 나가기
    - 접속: `pig`
    - 나가기: `quit` , ctrl+z
    
    ![](/media/posts/imported/dev/BD-General_Untitled-6_6.png)
    
- 예제 데이터 생성
    - 1. 윈도우→리눅스→하둡 전송 과정
        
        ![](/media/posts/imported/dev/BD-General_Untitled-7_6.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-8_6.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-9_6.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-10_6.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-11_6.png)
        
    - 2. vi로 파일 생성
        
        ![](/media/posts/imported/dev/BD-General_Untitled-12_6.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-13_6.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-14_6.png)
        
- 변수 선언하기
    
    ![](/media/posts/imported/dev/BD-General_Untitled-15_6.png)
    
    ![](/media/posts/imported/dev/BD-General_Untitled-16_6.png)
    
- 튜플 자료구조
    - X = FOREACH A GENERATE name,$2;
        
        ![](/media/posts/imported/dev/BD-General_Untitled-17_5.png)
        
    - A = LOAD 'sample_tuple.txt' AS (t1:tuple(t1a:int,t1b:int,t1c:int),t2:tuple(t2a:int,t2b:int,t2c:int));
        
        ![](/media/posts/imported/dev/BD-General_Untitled-18_5.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-19_5.png)
        
    - X = FOREACH A GENERATE t1.t1a, t2.$0;
        
        ![](/media/posts/imported/dev/BD-General_Untitled-20_4.png)
        
- Bag 자료구조
    - `A = LOAD ‘sample_bag.txt’ as (f1:int, f2:int, f3:int);`
        
        ![](/media/posts/imported/dev/BD-General_Untitled-21_4.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-22_4.png)
        
    - `X = GROUP A BY f1;`
        
        ![](/media/posts/imported/dev/BD-General_Untitled-23_4.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-24_4.png)
        
- Map 자료구조
    - `A = LOAD ‘sample_map.txt’ AS (M:map []);`
        
        ![](/media/posts/imported/dev/BD-General_Untitled-25_4.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-26_3.png)
        
- 산술 연산자
    - `A = LOAD ‘sample_arithmetic.txt’ AS (f1:int, f2:int);`
        
        ![](/media/posts/imported/dev/BD-General_Untitled-27_3.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-28_3.png)
        
    - `X = FOREACH A GENERATE f1, f2, f1�;`
        
        ![](/media/posts/imported/dev/BD-General_Untitled-29_3.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-30_3.png)
        
    - `X = FOREACH GENERATE f1,f2, f1+f2, f1-f2, f1*f2, f1/f2;`
        
        ![](/media/posts/imported/dev/BD-General_Untitled-31_3.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-32_3.png)
        
- 불린 연산자
    - `X = FILTER A BY (f1==8) OR (NOT (f2+f3 > f1));`
        
        ![](/media/posts/imported/dev/BD-General_Untitled-33_3.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-34_3.png)
        
    - `X = FILTER A BY (f2 > 2) and f3 == 9;`
        
        ![](/media/posts/imported/dev/BD-General_Untitled-35_3.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-36_3.png)
        
- 형 변환(Cast) 연산자
    - `B = GROUP A BY f1;`
        
        ![](/media/posts/imported/dev/BD-General_Untitled-37_3.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-38_3.png)
        
    - `X = FOREACH B GENERATE group, (chararray)COUNT(A) AS total;`
        
        ![](/media/posts/imported/dev/BD-General_Untitled-39_3.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-40_2.png)
        
- 데이터 조건 지정(ASSERT)
    - `ASSERT A by a0 > 3, 'a0 should be greater than 3';` → 오류 발생
        
        ![](/media/posts/imported/dev/BD-General_Untitled-41_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-42_2.png)
        
- 직교 연산자(CROSS)
    - `X = CROSS A,B;`
        
        ![](/media/posts/imported/dev/BD-General_Untitled-43_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-44_2.png)
        
- Cube 연산
    - `cubedinp = CUBE salesinp BY CUBE(product,year);`
        
        ![](/media/posts/imported/dev/BD-General_Untitled-45_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-46_2.png)
        
- Rollup 연산
    - `rolledup = CUBE salesinp BY ROLLUP (region, state, city);`
        
        ![](/media/posts/imported/dev/BD-General_Untitled-47_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-48_2.png)
        
- Distinct 연산
    - `X = DISTINCT A;`
        
        ![](/media/posts/imported/dev/BD-General_Untitled-49_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-50_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-51_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-52_2.png)
        
- 복합 FOREACH ~ GENERATE
    - `X = FOREACH B {FA= FILTER A BY outlink == '[www.xyz.org](http://www.xyz.org/)’;DA = DISTINCT PA;GENERATE group, COUNT(DA);}`
        
        ![](/media/posts/imported/dev/BD-General_Untitled-53_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-54_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-55_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-56_2.png)
        
- COGROUP
    - `X = COGROUP A BY owner, B BY friend2;`
        
        ![](/media/posts/imported/dev/BD-General_Untitled-57_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-58_2.png)
        
- Join
    - Self Join
        
        ![](/media/posts/imported/dev/BD-General_Untitled-59_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-60_2.png)
        
    - Inner Join
        
        ![](/media/posts/imported/dev/BD-General_Untitled-61_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-62_2.png)
        
    - Outer Join
        
        ![](/media/posts/imported/dev/BD-General_Untitled-63_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-64_2.png)
        
    - Right Outer Join
        
        ![](/media/posts/imported/dev/BD-General_Untitled-65_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-66_2.png)
        
    - Full Outer Join
        
        ![](/media/posts/imported/dev/BD-General_Untitled-67_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-68_2.png)
        
- Limit
    - `X = LIMIT fullouterjoin 3;`
        
        ![](/media/posts/imported/dev/BD-General_Untitled-69_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-70_2.png)
        
- Order by
    
    ![](/media/posts/imported/dev/BD-General_Untitled-71_2.png)
    
    ![](/media/posts/imported/dev/BD-General_Untitled-72_2.png)
    
- rank
    - `B = rank A;`
        
        ![](/media/posts/imported/dev/BD-General_Untitled-73_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-74_2.png)
        
    - `C = rank A by f1 DESC, f2 ASC;`
        
        ![](/media/posts/imported/dev/BD-General_Untitled-75_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-76_2.png)
        
- SAMPLE
    - 현재 버전에서는 올림 처리 동작을 확인할 것
    
    ![](/media/posts/imported/dev/BD-General_Untitled-77_2.png)
    
    ![](/media/posts/imported/dev/BD-General_Untitled-78_2.png)
    
- Split
    
    ![](/media/posts/imported/dev/BD-General_Untitled-79_2.png)
    
    - `DUMP X;`
        
        ![](/media/posts/imported/dev/BD-General_Untitled-80_2.png)
        
    - `DUMP Y;`
        
        ![](/media/posts/imported/dev/BD-General_Untitled-81_2.png)
        
    - `DUMP Z;`
        
        ![](/media/posts/imported/dev/BD-General_Untitled-82_2.png)
        
- Store
    - Pig 실행 위치에 디렉토리가 생성됩니다.
    - A
        
        ![](/media/posts/imported/dev/BD-General_Untitled-83_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-84_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-85_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-86_2.png)
        
    - B → CONCAT(+형변환)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-87_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-88_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-89_2.png)
        
- UNION
    
    ![](/media/posts/imported/dev/BD-General_Untitled-90_2.png)
    
    ![](/media/posts/imported/dev/BD-General_Untitled-91_2.png)
    
- AVG
    
    ![](/media/posts/imported/dev/BD-General_Untitled-92_2.png)
    
    ![](/media/posts/imported/dev/BD-General_Untitled-93_2.png)
    
- BagToString
    
    ![](/media/posts/imported/dev/BD-General_Untitled-94_2.png)
    
    ![](/media/posts/imported/dev/BD-General_Untitled-95_2.png)
    
- Max
    
    ![](/media/posts/imported/dev/BD-General_Untitled-96_2.png)
    
    ![](/media/posts/imported/dev/BD-General_Untitled-97_2.png)
    
- Size
    
    ![](/media/posts/imported/dev/BD-General_Untitled-98_2.png)
    
    ![](/media/posts/imported/dev/BD-General_Untitled-99_2.png)
    
- Substract
    - 1
        
        ![](/media/posts/imported/dev/BD-General_Untitled-100_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-101_2.png)
        
    - 2
        
        ![](/media/posts/imported/dev/BD-General_Untitled-102_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-103_2.png)
        
    - 3
        
        ![](/media/posts/imported/dev/BD-General_Untitled-104_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-105_2.png)
        
- IN
    
    ![](/media/posts/imported/dev/BD-General_Untitled-106_2.png)
    
    ![](/media/posts/imported/dev/BD-General_Untitled-107_2.png)
    
- Tokenize
    - 1
        
        ![](/media/posts/imported/dev/BD-General_Untitled-108_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-109.png)
        
    - 2
        
        ![](/media/posts/imported/dev/BD-General_Untitled-110.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-111.png)
        
    - 3
        
        ![](/media/posts/imported/dev/BD-General_Untitled-112.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-113.png)
        
- TextLoader()
    - 1
        
        ![](/media/posts/imported/dev/BD-General_Untitled-114.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-115.png)
        
    - 2
        
        ![](/media/posts/imported/dev/BD-General_Untitled-116.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-117.png)
        
- Top
    
    ![](/media/posts/imported/dev/BD-General_Untitled-118.png)
    
    ![](/media/posts/imported/dev/BD-General_Untitled-119.png)
    
- ToMap
    
    ![](/media/posts/imported/dev/BD-General_Untitled-120.png)
    
    ![](/media/posts/imported/dev/BD-General_Untitled-121.png)
    
- Endswith
    
    ![](/media/posts/imported/dev/BD-General_Untitled-122.png)
    
    ![](/media/posts/imported/dev/BD-General_Untitled-123.png)
    
- Startswith
    
    ![](/media/posts/imported/dev/BD-General_Untitled-124.png)
    
    ![](/media/posts/imported/dev/BD-General_Untitled-125.png)
    
- Substring
    
    ![](/media/posts/imported/dev/BD-General_Untitled-126.png)

[... content truncated for processing ...]
