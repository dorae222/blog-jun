---
title: "[What is Big Data?]"
slug: "what-is-big-data"
category: "data-engineering"
tags: ["big-data", "data-engineering", "distributed-systems", "hadoop", "hdfs", "mapreduce", "nosql", "rdbms", "spark"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:09.398339+00:00"
---

# [What is Big Data?]

- Hadoop이란?
    - Mapreduce → 병렬 처리를 할 수 있는 프로그래밍 모델 및 라이브러리
        - 분산 파일 시스템(HDFS)에 명령을 내려 대용량 데이터를 처리하기 위해 사용
        - JAVA 기반
    - HDFS → 분산 파일 시스템
        - 파일 시스템이란
            - 보조 저장장치에 파일을 어떻게 저장할 것인지에 대한 규칙
            - 운영체제가 결정 → 운영체제마다 다름
                - 윈도우: NTFS?, 리눅스: exf
        - 분산을 하는 이유
            - 너무 큰 파일들을 여러 저장장치에 분산 저장하기 위함
            - 여러 하드디스크에 데이터를 분산해 저장
            - 예: 9 = 3 + 3 + 3 → 3초
- NO-SQL, Spark 탄생 배경
    - 하둡에서 하드디스크 기반 처리를 할 때 속도 이슈가 발생
    - 이를 해결하기 위해 메모리 기반 처리가 등장
    - NO-SQL

        [[DB] NoSQL이란?, NoSQL 특징, NoSQL 종류, NoSQL 장점](https://code-lab1.tistory.com/53)

        - key,value
        - Column
        - Graph
        - **Document**
    - Spark
        - 고속 메모리 처리
        - 머신러닝 라이브러리 포함
        - 시각화 라이브러리
        - SQL 형태의 인터페이스 제공
- 데이터베이스 관리 시스템의 응용
    - 메인 메모리 데이터베이스, 분산 데이터베이스, 멀티미디어 데이터베이스, 공간 데이터베이스, 비정형 데이터베이스
    - 메인 메모리 데이터베이스
        - 데이터베이스의 일부 또는 전부를 메인 메모리에 상주시켜 운영하는 데이터베이스
    - 분산 데이터베이스
        - 물리적으로 여러 데이터베이스 시스템을 네트워크로 연결해 사용자가 논리적으로 하나의 데이터베이스 시스템처럼
        사용하는 데이터베이스
    - 멀티미디어 데이터베이스
        - 숫자나 문자 데이터뿐 아니라 영상, 음향, 애니메이션 등 멀티미디어 데이터를 효과적으로 저장하고 처리하는 데이터베이스
    - 공간 데이터베이스
        - 공간에 존재하는 점, 선, 폴리곤 등을 포함하는 객체 데이터를 저장하고 검색하는 데 최적화된 데이터베이스
    - 비정형 데이터베이스
        - 빅데이터 처리를 위해 전통적인 관계형 데이터베이스와 다르게 설계된 비관계형(non-relational) 데이터베이스 → NoSQL
        - 빅데이터의 3가지 특성(3V)을 고려
            - 데이터량(Volume), 속도(Velocity), 다양성(Variety)
        - 대표적인 NoSQL 데이터 모델
            - 컬럼(Column), 도큐먼트(Document), 키 값(Key-Value), 그래프(Graph)
- RDBMS의 한계
    - 스키마 문제: RDB의 스키마에 맞춰 데이터를 변경해서 넣으려면 긴 다운타임이 발생할 수 있음
    - 스케일업의 한계
        - 스케일업: 기존 서버를 더 높은 사양으로 업그레이드하는 것

            ![](/media/posts/imported/dev/BD-General_Untitled_5.png)

        - 스케일아웃: 장비를 추가하여 확장

            ![](/media/posts/imported/dev/BD-General_Untitled-1_5.png)

            ![](/media/posts/imported/dev/BD-General_Untitled-2_5.png)

- NO-SQL 데이터 모델
    
    ![](/media/posts/imported/dev/BD-General_Untitled-3_4.png)
    
    - 네임노드, 세컨더리 네임노드
    - 데이터노드 / 마스터 노드 / 슬레이브 노드