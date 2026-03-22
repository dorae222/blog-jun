---
title: "[Spark]"
slug: spark
category: "data-engineering"
tags: ["big-data", "dataframe", "hadoop", "mllib", "pyspark", "rdd", "spark", "spark-cluster", "spark-standalone"]
status: published
post_type: tutorial
quality_score: 8.0
created_at: "2026-03-02T01:08:09.338709+00:00"
---

# [Spark]

---

---

## Spark 이론 및 설치

### Spark 이론

- Apache Spark
    - Spark는 기존 MapReduce 기반 클러스터 컴퓨팅의 한계를 보완하기 위해 등장한 프레임워크입니다.
    - MapReduce
        - MapReduce는 디스크로부터 데이터를 읽어 Map 단계에서 관련된 데이터를 키-값 형태로 묶고, Reduce 단계에서 중복을 제거하거나 원하는 형태로 가공한 뒤 다시 디스크에 저장하는 방식입니다.
    - 그러나 파일 기반의 디스크 I/O는 성능이 낮았고, 메모리 기반 연산을 통해 처리 성능을 높이기 위해 Spark가 개발되었습니다.

    ---

    - Apache Spark는 오픈소스 범용 분산 클러스터 컴퓨팅 프레임워크로, Fault Tolerance와 Data Parallelism을 바탕으로 클러스터를 프로그래밍할 수 있게 해줍니다.
    - Spark는 RDD, DataFrame, Dataset의 3가지 API를 제공하며, 이들로 인메모리 연산을 수행합니다.
    - 디스크 기반의 Hadoop보다 최대 수십 배(통상적으로는 약 100배라고 언급됨) 성능 향상이 가능합니다.

        ![](/media/posts/imported/dev/BD-General_Untitled_3.png)

    ---

    - Spark는 클러스터를 관리하는 Cluster Manager와 데이터를 분산 저장하는 Distributed Storage System이 필요합니다.
    - Cluster Manager
        - Spark Standalone(기본), Hadoop YARN, Apache Mesos
    - Distributed Storage System
        - HDFS, MapR-FS, Cassandra, OpenStack Swift, Amazon S3, Kudu, custom solution 등
        - 가장 널리 사용되는 스토리지는 Hadoop(HDFS)입니다. zlib, bzip2 같은 압축 알고리즘을 지원하고 Spark 노드에서 구동 가능하기 때문입니다.

    ---

    - Cluster Manager

        ![](/media/posts/imported/dev/BD-General_Untitled-1_3.png)

        - Standalone
            - Spark에 포함된 기본 리소스 매니저
        - YARN (Hadoop)
            - Hadoop에 포함된 리소스 매니저
        - Mesos
            - 원래 Hadoop MapReduce 위에서 동작하는 매니저였으나, 현재는 사용이 권장되지 않습니다.
        - Kubernetes
            - 가상화된 분산 컨테이너 환경에서 동작하는 매니저

### Spark Standalone Cluster

- 가상환경에서 Spark를 다운로드하고 폴더를 구성합니다.

    ![](/media/posts/imported/dev/BD-General_Untitled-2_3.png)

    [Downloads | Apache Spark](https://spark.apache.org/downloads.html)

    ![](/media/posts/imported/dev/BD-General_Untitled-3_2.png)

    ![](/media/posts/imported/dev/BD-General_Untitled-4_2.png)

    ![](/media/posts/imported/dev/BD-General_Untitled-5_2.png)

    ![](/media/posts/imported/dev/BD-General_Untitled-6_2.png)

- Spark, PySpark 환경 변수 설정

    ![](/media/posts/imported/dev/BD-General_Untitled-7_2.png)

    - 저장 및 적용

        ![](/media/posts/imported/dev/BD-General_Untitled-8_2.png)

- Spark 파일을 데이터 노드들에게 전송(네임노드에서 수행)
    - 노드 1~3까지 전송

    ![](/media/posts/imported/dev/BD-General_Untitled-9_2.png)

- Workers로 동작할 노드 설정(네임노드에서 수행)

    ![](/media/posts/imported/dev/BD-General_Untitled-10_2.png)

- Master 데몬 실행 및 JPS 확인(네임노드에서 수행)

```python
cd ~/bigdata/spark/sbin && ./start-master.sh --host 192.168.56.101
```

    ![](/media/posts/imported/dev/BD-General_Untitled-11_2.png)

- Workers 데몬 실행(데이터 노드 1,2,3)

```python
cd ~/bigdata/spark/sbin && ./start-slave.sh spark://192.168.56.101:7077
```

    ![](/media/posts/imported/dev/BD-General_Untitled-12_2.png)

- Workers 연결 확인
    - 브라우저에서 http://192.168.56.101:8080/ 접속
    - 정상 연결 확인

        ![](/media/posts/imported/dev/BD-General_Untitled-13_2.png)

- PySpark 쉘 실행 및 동작 확인

```python
cd ~/bigdata/spark/bin && ./pyspark --master spark://192.168.56.101:7077
```

    - 브라우저에서 http://192.168.56.101:8080/ 재접속

        ![](/media/posts/imported/dev/BD-General_Untitled-14_2.png)

    - pyspark 종료 시

        ![](/media/posts/imported/dev/BD-General_Untitled-15_2.png)

        ![](/media/posts/imported/dev/BD-General_Untitled-16_2.png)

- 데이터 입력 및 병렬화 수행 후 동작 확인
    - 데이터 입력

        ```python
        cd ~/bigdata/spark/bin && ./spark-shell --master spark://192.168.56.101:7077
        ```

        ![](/media/posts/imported/dev/BD-General_Untitled-17_2.png)

    - 병렬화

        ```python
        val rdd = spark.sparkContext.parallelize(dataSeq)
        ```

        ![](/media/posts/imported/dev/BD-General_Untitled-18_2.png)

    - 동작 확인

        ![](/media/posts/imported/dev/BD-General_Untitled-19_2.png)

        ![](/media/posts/imported/dev/BD-General_Untitled-20.png)

        ![](/media/posts/imported/dev/BD-General_Untitled-21.png)

        ![](/media/posts/imported/dev/BD-General_Untitled-22.png)

        - 항목의 첫 번째와 두 번째 컬럼은 Executor ID와 Address로 표시됩니다.
        - Executor ID가 Driver이고 Address가 hadoopname:포트번호로 되어 있다면, 해당 항목은 SparkShell을 통해 생성된 Driver를 의미합니다.
        - 나머지 0, 1, 2는 Task 단위로 분할되어 병렬/분산으로 작업을 실행하는 Worker들입니다.

- Spark 동작 과정 이해

    ![](/media/posts/imported/dev/BD-General_Untitled-23.png)

    - Part1. 본 실습에서는 Yarn, Mesos, Kubernetes 등을 사용하지 않고 Standalone 설치 과정을 통해 Standalone Cluster를 구성하여 Spark 내에서 직접 리소스를 관리합니다.
    - 앞서 본 Executor ID가 0인 노드는 DriverProgram의 SparkContext를 생성합니다.
    - Executor ID가 0, 1, 2인 나머지 노드들은 Worker Node이며 각 Task로 분할되어 데이터를 처리합니다.

---

## 데이터 처리 방법

### PySpark RDD → 요즘은 거의 사용하지 않음

- 개념

    ![](/media/posts/imported/dev/BD-General_Untitled-24.png)

    - Spark의 데이터 구조
        - Spark에서의 데이터 구조는 RDD(Resilient Distributed Dataset), DataFrame, Dataset으로 구분됩니다.
    - Spark RDD
        - RDD는 Resilient Distributed Dataset의 약어로, 내결함성(Fault Tolerance)을 갖는 변경 불가능한 분산 컬렉션입니다.
        - Python에서 리스트 형태인 데이터를 RDD로 변환하면 분할된 데이터셋으로 나뉘며, 이들 분할을 파티션이라고 부릅니다.

    ---

    - Spark DataFrame(스파크 2.x 이후)

        ![](/media/posts/imported/dev/BD-General_Untitled-25.png)

        - RDD는 스키마(데이터 구조)가 없기 때문에 구조화된 데이터를 처리하려면 행과 열의 테이블 형태가 더 편리합니다.
        - DataFrame으로 스키마를 정의하면 Spark SQL 등을 통해 손쉽게 데이터를 처리·조작할 수 있습니다.
        - CSV, TXT, JSON 등 다양한 포맷을 읽을 수 있어 Spark에서 가장 널리 쓰이는 자료구조입니다.

    ---

    - Spark Dataset

        ![](/media/posts/imported/dev/BD-General_Untitled-26.png)

        - DataFrame은 Dataset[Row] 형태의 untyped API로 볼 수 있습니다.
        - Dataset은 typed API를 제공하여 컴파일 시점에 타입 검사를 할 수 있어 런타임 오류를 줄여줍니다.
        - Dataset은 JVM 객체 기반으로 동작하므로 주로 Scala Spark에서 지원되며 PySpark에서는 지원되지 않습니다.

    ---

    - PySpark
        - PySpark는 Python에서 Spark API를 사용하는 인터페이스입니다.
            - Scala에 대한 이해가 충분하다면 Scala 기반 Spark를 사용하는 것이 성능 및 JVM 호환성 측면에서 유리합니다.
            - 그러나 Python은 데이터 처리 생태계(Numpy, Pandas, scikit-learn, SciPy 등)가 풍부하므로 PySpark를 선호하는 경우가 많습니다.
        - Spark-Shell과 마찬가지로 PySpark-Shell을 통해 대화형 프로그래밍이 가능합니다.
        - RDD, SQL, DataFrame, Streaming, MLlib 등 대부분의 Spark 기능을 사용할 수 있습니다.
        - Spark(Scala) vs PySpark
            - 성능: Scala 기반 Spark가 내부적으로 JVM 객체를 직접 활용하므로 성능 우위가 있는 편입니다.
            - 활용성: PySpark는 Python 생태계의 풍부한 라이브러리를 활용할 수 있어 개발 생산성이 높습니다.

- 실습
    - RDD 생성

        ![](/media/posts/imported/dev/BD-General_Untitled-27.png)

        - parallelize() 함수로 RDD를 생성합니다.
            - 예제에서는 data 변수에 리스트 형태로 튜플을 저장한 뒤 RDD로 생성하고 출력합니다.
            - 일반적인 print는 생성된 RDD 객체에 대한 설명을 출력하므로, 실제 데이터를 확인하려면 collect() 함수를 사용합니다.
            - 파이썬 반복문으로 출력할 수도 있지만 정수형 데이터를 바로 출력할 경우 문자열로 변환이 필요할 수 있습니다.

        ![](/media/posts/imported/dev/BD-General_Untitled-28.png)

        - parallelize()에 리스트를 넣어 RDD를 생성합니다. 출력 방식은 동일합니다.
    - count

        ![](/media/posts/imported/dev/BD-General_Untitled-29.png)

        - count() 함수는 RDD에 포함된 요소의 개수를 반환합니다.
    - countByValue()

        ![](/media/posts/imported/dev/BD-General_Untitled-30.png)

        - countByValue() 함수는 각 요소의 발생 횟수를 딕셔너리 형태로 반환합니다.
            - 예: 값 1이 1개, 2가 2개 등
    - first

        ![](/media/posts/imported/dev/BD-General_Untitled-31.png)

        - first() 함수는 RDD의 첫 번째 요소를 반환합니다.
    - top, min, max

        ![](/media/posts/imported/dev/BD-General_Untitled-32.png)

        - top(): RDD에서 지정한 개수만큼 큰 값들을 반환합니다.
        - min(): 최소값을 반환합니다.
        - max(): 최대값을 반환합니다.
    - map vs flatMap

        ![](/media/posts/imported/dev/BD-General_Untitled-33.png)

        - map(): 각 요소에 함수를 적용한 결과를 그대로 반환합니다.
        - flatMap(): 각 요소에 함수를 적용한 뒤 결과를 평탄화(flat)하여 반환합니다.
    - reduceByKey

        ![](/media/posts/imported/dev/BD-General_Untitled-34.png)

        - reduceByKey(): (key, value) 형태의 데이터에서 key를 기준으로 연산(예: 합계)을 수행합니다.

### PySpark - DataFrame, SQL

- DataFrame → CSV, JSON, TXT 등 다양한 포맷 지원

    ![](/media/posts/imported/dev/BD-General_Untitled-35.png)

    - columns 변수에 컬럼명을 리스트로 준비합니다.
    - data 변수에 튜플 형태의 데이터 리스트를 준비합니다.
    - toDF(), createDataFrame() 함수로 DataFrame을 생성할 수 있습니다.
    - toDF()에 columns 리스트를 인자로 넘기면 컬럼명을 지정할 수 있습니다.
    - DataFrame의 스키마 구조는 printSchema()로 확인합니다.

    ![](/media/posts/imported/dev/BD-General_Untitled-36.png)

    - StructType을 이용해 스키마를 별도로 정의한 뒤 createDataFrame()의 인자로 전달하여 DataFrame을 생성할 수 있습니다.
    - df.show(truncate=False)
        - 기본적으로 긴 Row 값은 ...으로 생략되어 표시됩니다. truncate=False를 사용하면 생략 없이 모두 출력합니다.
- DataFrame to Pandas
    - 설치

        ![](/media/posts/imported/dev/BD-General_Untitled-37.png)

        ![](/media/posts/imported/dev/BD-General_Untitled-38.png)

        ![](/media/posts/imported/dev/BD-General_Untitled-39.png)

    - 실습

### PySpark - Datasources, Built-In Functions

---

## 머신러닝

### PySpark - MLlib

## 

### PySpark - Streaming