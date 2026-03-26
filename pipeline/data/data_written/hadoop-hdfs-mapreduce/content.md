## 개요

Apache Hadoop은 대용량 데이터를 여러 서버에 나누어 저장하고, 병렬로 처리하기 위한 오픈소스 프레임워크입니다. 구글이 2003년에 발표한 GFS(Google File System) 논문과 2004년의 MapReduce 논문을 기반으로 Yahoo!에서 개발했고, 현재는 Apache 재단에서 관리하고 있습니다.

Hadoop을 처음 접했을 때 가장 헷갈렸던 부분은 "파일 시스템"과 "처리 엔진"이 별개의 계층이라는 점이었습니다. HDFS는 데이터를 저장하는 역할이고, MapReduce는 그 데이터를 처리하는 역할입니다. 이 두 가지가 Hadoop의 핵심 구성 요소이며, 이 글에서는 각각의 아키텍처와 실제 CLI 사용법, 그리고 완전분산모드 구성까지 정리합니다.

---

## 핵심 개념

### HDFS(Hadoop Distributed File System) 아키텍처

HDFS는 대용량 파일을 블록 단위(기본 128MB)로 나누어 여러 데이터 노드에 분산 저장하는 파일 시스템입니다. 클러스터는 하나의 NameNode(마스터)와 다수의 DataNode(슬레이브)로 구성됩니다.

각 구성 요소의 역할은 다음과 같습니다.

- NameNode: 파일 시스템의 메타데이터(파일명, 블록 위치, 디렉토리 구조 등)를 메모리에 유지하며 클라이언트 요청을 처리합니다. 전체 클러스터에서 단 하나만 존재하는 마스터 노드입니다.
- Secondary NameNode: NameNode의 메타데이터를 주기적으로 체크포인트로 저장합니다. 이름 때문에 NameNode의 백업 노드로 오해하기 쉬운데, 실시간 장애 복구용이 아닙니다. 처음엔 이해가 안 됐는데, 실제로는 edits 로그와 fsimage를 병합하는 역할에 가깝습니다.
- DataNode: 실제 블록 데이터를 디스크에 저장하며, NameNode에 블록 리포트(heartbeat)를 주기적으로 전송합니다.

HDFS는 기본적으로 각 블록을 3개의 노드에 복제(replication factor = 3)하여 노드 장애 시 데이터 손실을 방지합니다. 하나의 DataNode가 죽더라도 다른 두 곳에 동일한 블록이 있으므로 서비스 중단 없이 데이터에 접근할 수 있습니다.

리눅스의 로컬 파일 시스템과 HDFS는 별도의 경로 체계를 사용한다는 점을 꼭 기억해야 합니다. 직접 돌려보니 리눅스의 `/Data` 경로에 파일을 두었다고 해서 Hadoop에서 바로 접근할 수 있는 것이 아니었습니다. 반드시 `hadoop fs -put` 같은 명령어로 HDFS에 명시적으로 올려야 합니다.

### MapReduce 프로그래밍 모델

MapReduce는 대용량 데이터를 병렬로 처리하기 위한 프로그래밍 모델입니다. 처리 과정은 세 단계로 나뉩니다.

1. Map 단계: 입력 데이터를 읽어 Key-Value 쌍으로 변환합니다. 예를 들어 웹 로그에서 URL별 접속 횟수를 세려면, 각 로그 라인에서 URL을 Key로, 1을 Value로 출력합니다.
2. Shuffle & Sort 단계: 같은 Key를 가진 데이터를 모아서 하나의 Reducer로 전달합니다. 이 과정은 프레임워크가 자동으로 처리합니다.
3. Reduce 단계: 같은 Key에 속하는 Value들을 집계하여 최종 결과를 출력합니다. 위의 예시라면 URL별로 모인 1들을 합산하여 총 접속 횟수를 계산합니다.

MapReduce는 각 단계에서 디스크 I/O를 거치기 때문에, 반복적인 연산이 필요한 머신러닝 알고리즘 같은 작업에서는 성능이 떨어집니다. 이 한계를 극복하기 위해 중간 결과를 메모리에 유지하는 In-memory 기반의 Apache Spark가 등장했습니다.

### YARN(Yet Another Resource Negotiator)

Hadoop 1.x에서는 MapReduce가 자원 관리와 작업 실행을 모두 담당했지만, Hadoop 2.x부터는 YARN이 자원 관리를 전담하게 되었습니다. 이 분리 덕분에 MapReduce뿐 아니라 Spark, Tez, Flink 같은 다양한 처리 엔진을 HDFS 위에서 동시에 실행할 수 있게 되었습니다.

YARN의 구성 요소는 다음과 같습니다.

- ResourceManager: 클러스터 전체의 자원(CPU, 메모리)을 관리하는 마스터 프로세스입니다. 어떤 노드에 얼마만큼의 자원을 할당할지 결정합니다.
- NodeManager: 각 DataNode에서 실행되며, 해당 노드의 자원 상태를 ResourceManager에 보고하고, 할당받은 컨테이너를 실행합니다.
- ApplicationMaster: 개별 애플리케이션(MapReduce 작업 등)마다 하나씩 생성되어, ResourceManager에게 필요한 자원을 요청하고 작업의 생애주기를 관리합니다.
- Container: YARN이 자원을 할당하는 단위입니다. CPU 코어 수와 메모리 크기가 지정된 격리된 실행 환경으로, 하나의 Map 태스크나 Reduce 태스크가 하나의 Container에서 실행됩니다.

```bash
# YARN 클러스터 상태 확인
yarn node -list

# 실행 중인 애플리케이션 확인
yarn application -list

# 특정 애플리케이션의 로그 확인
yarn logs -applicationId application_1234567890_0001
```

YARN의 도입은 Hadoop 생태계의 확장성을 크게 높인 변화입니다. 하나의 HDFS 클러스터 위에서 배치 처리(MapReduce), 대화형 쿼리(Tez + Hive), 실시간 스트리밍(Spark Streaming) 등 다양한 워크로드를 동시에 실행할 수 있게 되었기 때문입니다.

### HDFS 고가용성(HA)

Hadoop 1.x의 가장 큰 약점은 NameNode가 단일 장애 지점(Single Point of Failure)이라는 것이었습니다. NameNode가 죽으면 전체 클러스터가 멈추는 구조였기 때문입니다.

Hadoop 2.x부터는 NameNode HA가 도입되어, Active NameNode와 Standby NameNode 두 대를 운영합니다. Active가 장애를 일으키면 Standby가 자동으로 승격되어 서비스를 이어받습니다. 두 NameNode 간의 메타데이터 동기화에는 JournalNode(보통 3대)를 사용하며, 자동 장애 감지와 전환은 ZooKeeper가 담당합니다.

```xml
<!-- hdfs-site.xml: HA 구성 예시 -->
<configuration>
  <property>
    <name>dfs.nameservices</name>
    <value>mycluster</value>
  </property>
  <property>
    <name>dfs.ha.namenodes.mycluster</name>
    <value>nn1,nn2</value>
  </property>
  <property>
    <name>dfs.namenode.rpc-address.mycluster.nn1</name>
    <value>namenode1:8020</value>
  </property>
  <property>
    <name>dfs.namenode.rpc-address.mycluster.nn2</name>
    <value>namenode2:8020</value>
  </property>
</configuration>
```

운영 환경에서 HA 없이 Hadoop을 구성하는 것은 사실상 없다고 봐야 합니다. NameNode 장애가 곧 전체 데이터 접근 불가를 의미하기 때문입니다.

---

## 실전 코드

### 환경 구성: Hortonworks 접속

HORTONWORKS는 CentOS 위에 Hadoop, Pig 등을 미리 설치해서 이미지로 배포한 가상머신입니다. GUI가 없기 때문에 Windows에서는 PuTTY 같은 SSH 클라이언트를 통해 원격 접속해야 합니다.

접속 방법은 두 가지입니다.

- PuTTY 실행 후 SSH로 직접 접속
- 웹 브라우저에서 `localhost:4200` 접속 (Hortonworks Shell-in-a-Box)

### 데이터 전송: Windows에서 HDFS까지

데이터를 Hadoop에 넣기까지는 두 단계를 거칩니다. 먼저 Windows에서 리눅스로 파일을 보내고, 그다음 리눅스에서 HDFS로 올립니다.

```bash
# 1단계: Windows(cmd)에서 리눅스로 파일 전송
scp -P 2222 stocks.csv root@localhost:/Data

# 리눅스에서 전송된 파일 확인
cd /Data
ls
```

```bash
# 2단계: HDFS에 폴더 생성 후 파일 업로드
hadoop fs -mkdir -p /tmp/data
hadoop fs -D dfs.block.size=1048576 -put /Data/stocks.csv /tmp/data/stocks_1.csv

# HDFS에 파일이 올라갔는지 확인
hadoop fs -ls /tmp/data/
```

`dfs.block.size=1048576`은 블록 크기를 1MB로 지정하는 옵션입니다. 기본값은 128MB이지만, 테스트용 소규모 파일에서는 블록 분산을 확인하기 위해 작은 값을 사용하기도 합니다.

### HDFS 데이터 입/출력 명령어

```bash
# 파일 업로드 (로컬 -> HDFS)
hadoop fs -put /Data/data.txt /tmp/test/data.txt

# 파일 다운로드 (HDFS -> 로컬)
hadoop fs -get /tmp/test/data.txt /tmp/

# 파일 내용 출력
hadoop fs -cat /tmp/test/data.txt
hadoop fs -tail /tmp/test/data.txt

# HDFS 내부에서 파일 복사
hadoop fs -cp /tmp/test/data.txt /tmp/test/test1/data2.txt

# 한 폴더 내의 파일들을 하나로 합치기 (HDFS -> 로컬)
hadoop fs -getmerge /tmp/test/ merged.txt

# 0바이트 빈 파일 생성
hadoop fs -touchz /tmp/test/empty.txt

# 로컬 파일을 HDFS 파일에 이어붙이기
hadoop fs -appendToFile file1.txt file2.txt /tmp/test/test.txt
```

`put`과 `get`이 가장 자주 쓰는 명령어입니다. `getmerge`는 여러 파일을 하나로 합칠 때 유용한데, 결과가 로컬 파일 시스템에 저장된다는 점에 주의해야 합니다.

### 검색 및 권한 명령어

```bash
# 파일 이름 패턴으로 검색
hadoop fs -find / -name test* -print

# 디렉토리의 소유자와 그룹 정보 확인
hadoop fs -getfacl /tmp

# 권한 변경
hadoop fs -chmod 777 /tmp/test/data.txt

# 소유자 변경
hadoop fs -chown newowner /tmp/test/data.txt

# 그룹 변경
hadoop fs -chgrp newgroup /tmp/test/data.txt
```

HDFS의 권한 체계는 리눅스와 유사합니다. 기본적으로 루트(`/`) 경로에는 일반 사용자 권한으로 디렉토리를 생성할 수 없고, `/tmp` 같은 공용 경로 아래에서 작업해야 합니다.

### 클러스터 관리 명령어

```bash
# Hadoop 버전 확인
hadoop version

# 현재 클러스터의 노드 정보 확인
hadoop dfsadmin -report

# 파일/디렉토리 용량 확인 (-h 옵션으로 읽기 쉬운 단위 표시)
hadoop fs -du -h /tmp/

# 파일시스템 전체 공간 확인
hadoop fs -df /tmp/

# 파일 통계 확인
hadoop fs -stat "%F %u %g %b %y %n" /tmp/test/data.txt
# %F: 파일 타입, %u: 소유자, %g: 그룹, %b: 크기, %y: UTC 날짜, %n: 파일명

# 파일 길이 줄이기
hadoop fs -truncate 100 /tmp/test/data.txt

# 실행 중인 MapReduce 작업 목록 확인
hadoop job -list
```

`dfsadmin -report`는 클러스터 전체 상태를 한눈에 볼 수 있어서 문제 진단할 때 가장 먼저 실행하는 명령어입니다.

### 완전분산모드 구성

실제 운영 환경에서는 NameNode와 DataNode를 각각 별도의 서버에서 실행하는 완전분산모드(Fully Distributed Mode)로 구성합니다. 가상머신으로 실습할 때의 구성 순서는 다음과 같습니다.

1. 가상머신 생성: NameNode용 1대, DataNode용 N대를 동일한 스펙으로 생성합니다.
2. 네트워크 설정: 모든 노드가 동일한 네트워크 포트를 사용하도록 설정합니다. 노드 간 통신이 되어야 하므로 같은 네트워크 대역에 위치시킵니다.
3. OS 설치: Ubuntu 20.04 LTS 등을 각 노드에 설치합니다.
4. Hadoop 설치 및 설정: 각 노드에 Hadoop을 설치하고, `core-site.xml`, `hdfs-site.xml`, `mapred-site.xml`, `yarn-site.xml` 등의 설정 파일을 작성합니다.

주요 설정 파일의 예시입니다.

```xml
<!-- core-site.xml: NameNode의 주소 지정 -->
<configuration>
  <property>
    <name>fs.defaultFS</name>
    <value>hdfs://namenode-host:9000</value>
  </property>
</configuration>
```

```xml
<!-- hdfs-site.xml: 복제 계수 및 저장 경로 설정 -->
<configuration>
  <property>
    <name>dfs.replication</name>
    <value>3</value>
  </property>
  <property>
    <name>dfs.namenode.name.dir</name>
    <value>file:///hadoop/hdfs/namenode</value>
  </property>
  <property>
    <name>dfs.datanode.data.dir</name>
    <value>file:///hadoop/hdfs/datanode</value>
  </property>
</configuration>
```

```xml
<!-- mapred-site.xml: MapReduce 실행 프레임워크 지정 -->
<configuration>
  <property>
    <name>mapreduce.framework.name</name>
    <value>yarn</value>
  </property>
</configuration>
```

노드 간 SSH 비밀번호 없이 접속할 수 있도록 키 기반 인증을 설정하는 것도 빠뜨리면 안 됩니다. NameNode에서 DataNode를 원격으로 제어해야 하기 때문입니다.

### 리눅스 사용자/그룹 관리 (Hadoop 환경 준비)

Hadoop 클러스터에서는 각 서비스가 특정 사용자로 실행되기 때문에 사용자와 그룹 관리가 중요합니다.

```bash
# 그룹 관리
groupadd hadoop             # 그룹 추가
groupmod -n newname oldname # 그룹명 변경
groupdel groupname          # 그룹 삭제
cat /etc/group              # 그룹 목록 확인

# 사용자 관리
useradd -g hadoop hduser    # hadoop 그룹에 사용자 추가
passwd hduser               # 비밀번호 설정
usermod -G hadoop hduser    # 기존 사용자의 그룹 변경
userdel hduser              # 사용자 삭제
cat /etc/passwd             # 사용자 목록 확인
```

---

## 활용 사례

Hadoop은 다음과 같은 상황에서 많이 사용됩니다.

- 로그 분석: 수십억 건의 웹 서버 로그를 한꺼번에 처리하여 사용자 행동 패턴을 분석합니다. 단일 서버로는 처리할 수 없는 규모의 로그도 MapReduce로 병렬 처리하면 수 시간 내에 결과를 얻을 수 있습니다.
- ETL 파이프라인: 다양한 소스(RDB, API, 파일 등)에서 데이터를 HDFS에 수집하고, Hive나 Pig 같은 도구로 변환/정제하여 분석 가능한 형태로 만듭니다.
- 배치 처리: 하루 단위 또는 시간 단위로 대량 데이터를 집계하는 배치 잡을 실행합니다. 실시간 처리가 아닌, 정해진 주기로 대량의 데이터를 일괄 처리하는 데 적합합니다.
- 데이터 레이크: 정형 데이터(CSV, 테이블)와 비정형 데이터(이미지, 로그, JSON)를 원본 그대로 HDFS에 저장해두고, 필요할 때 꺼내 처리합니다. 저장 비용이 저렴한 범용 하드웨어를 사용할 수 있다는 것이 장점입니다.

다만 Hadoop은 소규모 데이터 처리, 실시간 쿼리, 반복 연산에는 적합하지 않습니다. 이런 경우에는 Apache Spark, Apache Flink, 또는 전통적인 RDBMS가 더 나은 선택입니다.

---

## 정리

Hadoop의 핵심은 두 가지로 요약됩니다.

- HDFS: 대용량 파일을 블록 단위로 분산 저장하는 파일 시스템. NameNode가 메타데이터를, DataNode가 실제 데이터를 관리합니다. 복제를 통해 장애 내성(fault tolerance)을 확보합니다.
- MapReduce: Map(변환) -> Shuffle(분류) -> Reduce(집계) 세 단계로 데이터를 병렬 처리하는 프로그래밍 모델입니다. 디스크 I/O 기반이라 반복 연산에는 약하지만, 대규모 배치 처리에는 여전히 유효합니다.

실습 환경으로는 Hortonworks HDP나 Ubuntu에 직접 완전분산모드를 구성하는 방법이 있습니다. Hortonworks는 설치가 간편하지만 커스터마이징에 한계가 있고, 직접 구성하면 각 설정 파일(`core-site.xml`, `hdfs-site.xml`, `mapred-site.xml`)의 역할을 하나씩 이해할 수 있어서 학습 효과가 더 큽니다.

Hadoop 자체는 이제 레거시 기술로 분류되는 경우도 있지만, HDFS는 아직도 많은 빅데이터 스택의 저장 계층으로 사용되고 있고, MapReduce의 개념은 Spark를 비롯한 후속 프레임워크들의 기반이 됩니다. 분산 처리의 기본기를 다지는 데 Hadoop만큼 좋은 출발점은 없다고 생각합니다.