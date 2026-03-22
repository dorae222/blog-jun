---
title: Big Data Solution
slug: "big-data-solution"
category: "data-engineering"
tags: ["big-data", "hadoop", "hbase", "hdfs", "hive", "mapreduce", "pig", "spark", "sqoop"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:09.391591+00:00"
---

# Big Data Solution

- **Hadoop Ecosystem**
    - 에코시스템 및 참고 사이트
        
        
        ![](/media/posts/imported/dev/BD-General_Untitled.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-1.png)
        
        [하둡 에코시스템(Hadoop-Ecosystem)이란](https://butter-shower.tistory.com/73)
        
    
    ---
    
    - Hadoop
        - 대용량 데이터를 낮은 비용으로 빠르게 분석할 수 있게 해 주는 소프트웨어
        - 하둡 코어 프로젝트: HDFS(분산 데이터 저장), MapReduce(분산 처리)
        - 하둡 서브 프로젝트: 데이터 마이닝, 수집, 분석 등 다양한 작업을 수행하는 하위 프로젝트들
        - **MapReduce** → 병렬 처리를 지원하는 모델 및 라이브러리
            - 분산 파일 시스템에 명령을 내리기 위해 사용
            - JAVA 기반
        - **HDFS** → 분산 파일 시스템
            - 파일 시스템이란
                - 보조 저장장치에 파일을 어떻게 저장할지 결정하는 것
                - 운영체제가 결정 → 운영체제마다 파일 시스템이 다름
                    - 예: 윈도우: NTFS, 리눅스: ext 계열 등
            - 분산의 이유
                - 매우 큰 파일을 여러 디스크에 분산 저장하기 위해
                - 예시: 9 = 3 + 3 + 3 → 병렬 처리로 3초에 끝낼 수 있음
    - DBMS ↔ HADOOP
        - Sqoop
            - Sqoop은 일반적으로 사용하는 **RDBMS**(MySQL, Oracle)와 **HDFS**(Hive, HBase) 간 데이터를 전송하기 위한 툴
            - HDFS, RDBMS, DW, NoSQL 등 **다양한 저장소로 대용량 데이터를 신속하게 전송**할 수 있는 방법을 제공
    - MapReduce
        - Pig와 Hive를 사용하는 이유
            - 하둡은 내부적으로 MapReduce를 수행함
                - 이 MapReduce를 직접 다루려면 JAVA를 사용해야 하는데, 다른 진영에서는 사용하기 어렵게 느껴짐
                - 그래서 더 간편한 PIG 언어가 등장함
                - 추가로 SQL 스타일의 쿼리로 MapReduce를 실행하는 HIVE가 등장함
        - Pig
            - Pig의 특징
                - 스크립트: 데이터 흐름을 명시적으로 보여 주는 코드 작성 방식
                    - 여러 작업을 모아 하나의 세트로 구성하는 것이 스크립트의 역할
                - 이해하기 쉽고 유지보수가 쉬움
                - 시스템이 코드 실행을 자동으로 최적화(옵티마이저)하므로 사용자는 효율성을 신경 쓰지 않고 로직에 집중할 수 있음
                - Pig Latin으로 작성한 데이터 처리 프로그램은 논리적 실행 계획으로 변환되고, 최종적으로 MapReduce 실행 계획으로 변환됨
            - **Pig의 장점: 옵티마이저를 통해 실행을 최적화함.**
                - 예를 들어 작업을 실행할 때 방법 A, B, C, D가 있을 경우, 반복 작업을 덜 하고 CPU 사용량이 적은 C안이 가장 효율적이라면 옵티마이저가 이를 선택하도록 돕는다.
            - **Pig의 단점: 잘못 작성하면 반복 작업이 많아지고 CPU를 많이 사용할 수 있음.**
        - Pig와 Hive의 차이
            - 이미지로 코드 차이 보기
                
                ![](/media/posts/imported/dev/BD-General_Untitled-2.png)
                
            - 위 이미지를 보면 알 수 있듯이, 기존 Pig Latin 언어는 SQL 사용자 입장에서는 개발 언어처럼 느껴져 사용이 어려웠음
            - 이에 따라 SQL 구문 형식으로 MapReduce를 실행할 수 있는 Hive가 만들어짐
        - Hive
            - **하둡 잡을 실행하는 DW 프레임워크**
            - SQL 구문을 이용해 MapReduce를 수행함
            - Hive의 약점은 JOIN 연산이 취약하다는 점
            - 여러 테이블을 JOIN해서 사용할 경우 Pig가 성능 면에서 더 유리한 경우가 있음
    - RDBMS & NoSQL → 진행 예정
        - HBase
            - NoSQL DB
            - 하둡의 HDFS 위에 만들어진 **분산 컬럼 기반 DB**
        - MongoDB
    - 웹 서버 구축 및 로그 → 진행 예정
        - Flume
    - 대규모 데이터 처리용 통합 분석 엔진 → 진행 예정
        - Spark
            - 고속 메모리 처리
            - 머신러닝 라이브러리
            - 시각화 라이브러리
            - SQL 형태의 인터페이스 제공


- **Each Components of Hadoop EcoSystem**
    
    What is Big Data?(%5BBig%20Data%20Solution%5D/%5BWhat%20is%20Big%20Data%20%5D%20ca7c26d6d5184ef4a0f893528a99ef92.md)
    
    ---
    
    Setting(%5BBig%20Data%20Solution%5D/%5BSetting%5D%2001b65bddffba4b9591ab31ff406a6dd7.md)
    
    Hadoop(%5BBig%20Data%20Solution%5D/%5BHadoop%5D%2081e413ea5d474ad6b2599e81d88516ea.md)
    
    ---
    
    SQOOP(%5BBig%20Data%20Solution%5D/%5BSQOOP%5D%20f8e7cd5397144f7fa38f33c9a7bed067.md)
    
    Pig(%5BBig%20Data%20Solution%5D/%5BPig%5D%200a44e2ccea1341f7bf1ee8dcbe153826.md)
    
    HIVE(%5BBig%20Data%20Solution%5D/%5BHIVE%5D%206999f8988dbf479b8c6ebe45302b9915.md)
    
    ---
    
    Spark(%5BBig%20Data%20Solution%5D/%5BSpark%5D%204e4d11f0fe80440898194570cc38fa0d.md)
    
    Error


빅데이터 수집 및 시각화(%5BBig%20Data%20Solution%5D/[빅데이터 수집 및 시각화] 327dede2828e49078cc19da132652fce.md)

하둡완전분산모드(%5BBig%20Data%20Solution%5D/[하둡완전분산모드] ba16e78affe2495f9deac22a6eedc029.md)
