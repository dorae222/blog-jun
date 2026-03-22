---
title: Hadoop 분산 파일 시스템과 MapReduce
slug: "hadoop-분산-파일-시스템과-mapreduce"
category: "data-engineering"
tags: ["bigdata", "datanode", "distributed-filesystem", "hadoop", "hdfs", "hortonworks", "mapreduce", "namenode"]
status: published
post_type: tutorial
quality_score: 7.5
created_at: "2026-03-02T01:08:46.837116+00:00"
---

# Hadoop 분산 파일 시스템과 MapReduce

## Hadoop 개요

Apache Hadoop은 대용량 데이터를 분산 저장하고 처리하기 위한 오픈소스 프레임워크다. 구글의 GFS(Google File System)와 MapReduce 논문을 기반으로 Yahoo!에서 개발하였으며, 현재 Apache 재단에서 관리한다. Hadoop의 핵심 구성 요소는 HDFS(분산 파일 시스템)와 MapReduce(분산 처리 엔진) 두 가지다.

### HDFS(Hadoop Distributed File System) 아키텍처

HDFS는 대용량 파일을 블록(기본 128MB) 단위로 나누어 여러 데이터 노드에 분산 저장한다. 클러스터는 하나의 **NameNode(마스터)**와 다수의 **DataNode(슬레이브)**로 구성된다.

- **NameNode**: 파일 시스템의 메타데이터(파일명, 블록 위치 등)를 메모리에 유지하며 클라이언트 요청을 처리한다.
- **Secondary NameNode**: NameNode의 메타데이터를 주기적으로 체크포인트로 저장한다. 실시간 장애 복구용이 아님에 주의한다.
- **DataNode**: 실제 블록 데이터를 디스크에 저장하며, NameNode에 블록 리포트를 주기적으로 전송한다.

HDFS는 기본적으로 각 블록을 3개의 노드에 복제(replication factor=3)하여 노드 장애 시 데이터 손실을 방지한다.

### MapReduce 개념

MapReduce는 대용량 데이터를 병렬로 처리하기 위한 프로그래밍 모델이다.

1. **Map 단계**: 입력 데이터를 읽어 Key-Value 쌍으로 변환한다.
2. **Shuffle & Sort**: 같은 Key를 가진 데이터를 하나의 Reducer로 모은다.
3. **Reduce 단계**: 같은 Key에 속하는 Value들을 집계하여 최종 결과를 출력한다.

MapReduce는 Disk I/O 기반이기 때문에 반복적인 알고리즘(머신러닝 등)에는 성능이 낮아, 이 한계를 극복하고자 In-memory 기반의 Apache Spark가 등장하였다.

---

## HORTONWORKS(CentOS + Hadoop) 설치 및 접속

HORTONWORKS는 CentOS 위에 Hadoop, Pig 등을 이미지화하여 배포한 가상머신 이미지다. GUI가 없으므로 Windows에서 PuTTY를 통해 원격 접속하여 사용한다.

- 접속 방법 1: PuTTY 파일 실행
- 접속 방법 2: `localhost:4200` 브라우저 접속

### 윈도우 → 리눅스 데이터 전달

```bash
# 윈도우 → 리눅스
scp -P 2222 data.txt root@localhost:/Data

# 리눅스 → Hadoop HDFS
hadoop fs -D dfs.block.size=1048576 -put /Data/stocks.csv /tmp/data/stocks_1.csv
```

---

## Hadoop 명령어

### 데이터 입/출력 명령

```bash
# 파일 업로드 (로컬 → HDFS)
hadoop fs -put /Data/data.txt /tmp/test/data.txt

# 파일 다운로드 (HDFS → 로컬)
hadoop fs -get /tmp/test/data.txt /tmp/

# 파일 내용 출력
hadoop fs -cat /tmp/test/data.txt
hadoop fs -tail /tmp/test/data.txt

# 파일 복사
hadoop fs -cp /tmp/test/data.txt /tmp/test/test1/data2.txt

# 폴더 내 파일 합치기
hadoop fs -getmerge /tmp/test/ merged.txt

# 빈 파일 생성
hadoop fs -touchz /tmp/test/empty.txt

# 로컬 파일을 HDFS에 이어붙이기
hadoop fs -appendToFile file1.txt file2.txt /tmp/test/test.txt
```

### 검색 및 권한 명령

```bash
# 특정 이름 패턴으로 파일 검색
hadoop fs -find / -name test* -print

# 권한 변경
hadoop fs -chmod 777 /파일경로

# 소유자 변경
hadoop fs -chown 소유자 /파일경로
```

### 기타 명령

```bash
# Hadoop 버전 확인
hadoop version

# 노드 정보 확인
hadoop dfsadmin -report

# 파일 용량 확인
hadoop fs -du -h /tmp/

# 파일시스템 공간 확인
hadoop fs -df /tmp/

# MapReduce 작업 목록 확인
hadoop job -list
```

---

## Hadoop 활용 사례

- **로그 분석**: 수십억 건의 웹 서버 로그를 일괄 처리하여 사용자 행동 분석
- **ETL 파이프라인**: 다양한 소스의 데이터를 HDFS에 수집하고 Hive/Pig로 변환
- **배치 처리**: 하루 단위로 대량 데이터를 집계하는 배치 잡 실행
- **데이터 레이크**: 정형/비정형 데이터를 원본 그대로 HDFS에 저장하고 필요 시 처리
