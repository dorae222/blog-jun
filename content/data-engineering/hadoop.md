---
title: "[Hadoop]"
slug: hadoop
category: "data-engineering"
tags: ["centos", "data-transfer", "hadoop", "hadoop-commands", "hdfs", "hortonworks", "linux", "putty", "ssh"]
status: published
post_type: tutorial
quality_score: 9.0
created_at: "2026-03-02T01:08:09.273729+00:00"
---

### HORTONWORKS(CentOS+Hadoop+pig+$\alpha$) → GUI없는 이미지 파일

- 개념
    - HORTONWORKS라는 회사에서 CentOS 위에 Hadoop, Pig 등을 이미지화해서 배포함
    - 배포된 이미지에는 GUI가 없기 때문에 직접 커맨드창을 열 수 없음
    - 따라서 현재 사용하는 OS(Windows)에서 PuTTY 같은 SSH 클라이언트를 사용해 원격으로 CentOS에 접속함
- HORTONWORKS 설치
    
    ![](/media/posts/imported/dev/BD-General_Untitled_10.png)
    
    ![](/media/posts/imported/dev/BD-General_Untitled-1_9.png)
    
    ![](/media/posts/imported/dev/BD-General_Untitled-2_9.png)
    
    ![](/media/posts/imported/dev/BD-General_Untitled-3_8.png)
    
    ![](/media/posts/imported/dev/BD-General_Untitled-4_7.png)
    
    ![](/media/posts/imported/dev/BD-General_Untitled-5_7.png)
    
    ![](/media/posts/imported/dev/BD-General_Untitled-6_7.png)
    
    ![](/media/posts/imported/dev/BD-General_Untitled-7_7.png)
    
    ![](/media/posts/imported/dev/BD-General_Untitled-8_7.png)
    
    ![](/media/posts/imported/dev/BD-General_Untitled-9_7.png)
    
    - 서버가 켜진 상태
        
        ![](/media/posts/imported/dev/BD-General_Untitled-10_7.png)
        
- HORTONWORKS 접속
    - 윈도우에 PuTTY 다운로드
        
        [Download PuTTY - a free SSH and telnet client for Windows](https://putty.org/)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-11_7.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-12_7.png)
        
    - PuTTY 설정
        
        ![](/media/posts/imported/dev/BD-General_Untitled-13_7.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-14_7.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-15_7.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-16_7.png)
        
        - 첫 접속은 SSH 프로토콜을 통한 것이므로 서버의 호스트키를 확인하는 과정이 포함됨
            
            ![](/media/posts/imported/dev/BD-General_Untitled-17_6.png)
            
        - PuTTY의 자동 종료를 방지하려면 설정 수정 필요
            
            [putty 자동 종료 방지 설정 하기](https://jun7222.tistory.com/437)
        
    - 편한 접속 방법 선택하기
        1. PuTTY 실행
            
            ![](/media/posts/imported/dev/BD-General_Untitled-18_6.png)
            
        2. 웹 인터페이스로 `localhost:4200` 접속
            
            ![](/media/posts/imported/dev/BD-General_Untitled-19_6.png)
            
- 윈도우 → 리눅스 데이터 전달하기
    - 이전 방식처럼 Windows와 공유 폴더를 바로 연결할 수 없음
        - 공유 폴더 설정(예: NameNode만 실행)으로 보이는 것과 달리
        - 실제로는 리눅스와 하둡이 서로 다른 HDD(저장 경로)를 사용함
        - 따라서 파일을 하둡에 넣을 때는 하둡 명령어로 경로를 지정하여 전송해야 함
        - 즉, 리눅스의 경로와 하둡의 경로가 다름에 유의
        - 추가로 주의할 점: 리눅스 상에서 홈(root) 폴더와 실제 루트(root) 폴더 등 2개의 유사한 경로가 존재할 수 있으므로 **폴더명에 유의**
    - 리눅스에 데이터를 공유할 폴더 생성
        
        ![](/media/posts/imported/dev/BD-General_Untitled-20_5.png)
        
    - Windows(cmd)에서 전송할 파일 생성(stocks.csv)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-21_5.png)
        
    - Windows(cmd)에서 Hortonworks 리눅스로 파일 전송
        - `scp -P 포트번호 파일명.확장자 root@사용자명:/경로`
            - `root@사용자명:/경로` : 리눅스 상의 경로(하둡으로 옮길 파일이 위치할 경로)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-22_5.png)
        
    - 리눅스에서 데이터 복사 확인
        
        ![](/media/posts/imported/dev/BD-General_Untitled-23_5.png)
        
    - 하둡에서 사용할 폴더 생성
        
        ![](/media/posts/imported/dev/BD-General_Untitled-24_5.png)
        
    - 리눅스 → 하둡 전송
        - 데이터 전송 예시
        - `hadoop fs -D dfs.block.size=1048576 - put /Data/stocks.csv /tmp/data/stocks_1.csv`
            - `dfs.block.size` : 분산 파일 블록 크기 설정
            - `put 원래파일경로 보낼파일경로`
            
            ![](/media/posts/imported/dev/BD-General_Untitled-25_5.png)
            
        - 하둡에 데이터가 들어갔는지 확인
            
            ![](/media/posts/imported/dev/BD-General_Untitled-26_4.png)
            
            ![](/media/posts/imported/dev/BD-General_Untitled-27_4.png)
            

### 하둡명령

### 블록 관련 명령

### Hortonworks HDP 3.0.1 설정

- `cat /etc/passwd`
    
    ![](/media/posts/imported/dev/BD-General_Untitled-28_4.png)
    
- `cat /etc/group`
    
    ![](/media/posts/imported/dev/BD-General_Untitled-29_4.png)
    
- 참고
    
    groupadd: group 추가
    
    groupadd 그룹명
    
    cat /etc/group
    
    groupmod: 그룹 변경
    
    groupmod -n [변경후 그룹명] [변경전 그룹명]
    
    groupdel: 그룹 삭제
    
    groupdel [그룹명]
    
    ---
    
    useradd: user 추가
    
    useradd [user명]
    
    useradd -g [그룹명] [user명]
    
    passwd [user명]: 비밀번호 설정
    
    usermod: 그룹 변경
    
    usermod -G [그룹명] [user명]
    
    userdel: 사용자 삭제
    
    userdel [user명]: 사용자 계정 삭제
    
    users: 사용자 확인
    
    cat /etc/passwd
    

### 디렉토리 관련 명령

### 데이터 입/출력 관련 명령 `hadoop fs - ~`

- `hadoop fs - ~`
    - HDFS(Hadoop Distributed File System)에 대한 명령어 집합
- 빈 폴더는 바로 생성할 수 없음(권한 문제) → tmp 아래에 생성 예정 (`mkdir` 사용)
    - 기본적으로 루트(`hadoop /`) 상에는 권한이 없음을 확인할 수 있음
    - 따라서 tmp 폴더 등 권한이 있는 경로 아래에 파일을 생성함
    
    ![](/media/posts/imported/dev/BD-General_Untitled-30_4.png)
    
- 데이터 전송(data.txt) - `put`
    - Windows → 리눅스
        - 공유 폴더 이동
        - `scp -P 2222 data.txt root@localhost:/Data`
        - `2222` - 포트번호
        - `data.txt` - 전송할 파일
        - `root@localhost:/Data` - 리눅스 상의 경로
        
        ![](/media/posts/imported/dev/BD-General_Untitled-31_4.png)
        
    - 리눅스에서 확인
        - `/Data`에 파일을 전송했으므로
        - `cd /Data`
        - `ls`
        
        ![](/media/posts/imported/dev/BD-General_Untitled-32_4.png)
        
    - 리눅스 → 하둡
        - 빈 폴더 생성
        - 파일 전달
        - 확인
        
        ![](/media/posts/imported/dev/BD-General_Untitled-33_4.png)
        
- 다른 폴더로 파일 복사 - `copy`
    - `hadoop fs -cp /tmp/test/data.txt /tmp/test/test1/data2.txt`
    
    ![](/media/posts/imported/dev/BD-General_Untitled-34_4.png)
    
- 내용 출력 - `cat`, `tail`
    - `hadoop fs -cat /tmp/test/data.txt`
    
    ![](/media/posts/imported/dev/BD-General_Untitled-35_4.png)
    
    - `hadoop fs -tail /tmp/test/data.txt`
    
    ![](/media/posts/imported/dev/BD-General_Untitled-36_4.png)
    
- HDFS에 있는 data.txt 파일을 로컬의 tmp 디렉토리로 복사 - `get`
    
    ![](/media/posts/imported/dev/BD-General_Untitled-37_4.png)
    
    - 현재 결과 출력이 일부 잘려 보일 수 있음
- 한 폴더 내의 파일 합치기 - `getmerge`
    - `hadoop fs –germerge /tmp/test/ merged.txt`
        - test 폴더 내의 파일들을 merged.txt로 합치기
            
            ![](/media/posts/imported/dev/BD-General_Untitled-38_4.png)
            
    - `cat merged.txt`로 내용 출력
- 0바이트 크기의 빈 파일 생성 - `touchz`
    
    ![](/media/posts/imported/dev/BD-General_Untitled-39_4.png)
    
- 리눅스 로컬에서 file1.txt, file2.txt 생성 후 내용 삽입 (vi 사용)
    
    ![](/media/posts/imported/dev/BD-General_Untitled-40_3.png)
    
    ![](/media/posts/imported/dev/BD-General_Untitled-41_3.png)
    
- HDFS에 리눅스 로컬 파일 이어쓰기 - `appendToFile`
    - 로컬 파일을 하둡으로 옮기는 방식은 `put`과 동일한 원리
        
        ![](/media/posts/imported/dev/BD-General_Untitled-42_3.png)
        
    - `cat`을 통해 file2.txt를 test.txt에 이어쓰기 가능
- checksum
- count: 현재 디렉토리의 디렉토리 수, 파일 수, 전체 파일의 용량 확인

### 검색 관련 명령 `hadoop fs - ~`

- `find`
    - `hadoop fs -find / -name test* -print`
    - test로 시작하는 모든 경로 검색
    
    ![](/media/posts/imported/dev/BD-General_Untitled-43_3.png)
    
- `getfacl`
    - `hadoop fs -getfacl /tmp`
    - 해당 디렉토리의 경로와 소유자, 그룹명을 확인할 수 있음
    
    ![](/media/posts/imported/dev/BD-General_Untitled-44_3.png)
    

### 권한 관련 명령 `hadoop fs - ~`

- `chmod`
    - `hadoop fs -chmod 777 /파일경로`
    - 읽기/쓰기 권한 등을 변경
    
    ![](/media/posts/imported/dev/BD-General_Untitled-45_3.png)
    
- `chown`
- `chgrp`

### 기타 명령 `hadoop ~`

- 하둡 버전 확인: `hadoop version`
    
    ![](/media/posts/imported/dev/BD-General_Untitled-46_3.png)
    
- 현재 사용 중인 노드 정보 확인: `hadoop dfsadim -report`
    
    ![](/media/posts/imported/dev/BD-General_Untitled-47_3.png)
    
- 파일 길이를 지정한 크기로 줄이기: `hadoop fs -truncate 길이 /파일`
    
    ![](/media/posts/imported/dev/BD-General_Untitled-48_3.png)
    
- 파일 통계 확인: `hadoop fs -stat “type:기호” /파일`
    
    ![](/media/posts/imported/dev/BD-General_Untitled-49_3.png)
    
    - %F : 파일의 타입
    - %u : 파일의 소유자
    - %g : 파일의 그룹명
    - %b : 파일의 크기
    - %y : UTC 날짜 (yyyy—MM-dd HH:mm:ss)
    - %n : 파일명
- 현재 디렉토리 내 파일 용량 확인: `hadoop fs -du /tmp/`
    
    ![](/media/posts/imported/dev/BD-General_Untitled-50_3.png)
    
    - `-h` 옵션을 주면 읽기 쉬운 단위로 표시됨
- 파일시스템의 경로, 총 크기, 사용 가능 공간, 사용률 확인: `hadoop fs -df /tmp/`
    
    ![](/media/posts/imported/dev/BD-General_Untitled-51_3.png)
    
- MapReduce 작업 관련 정보 확인: `hadoop job -list`
    
    ![](/media/posts/imported/dev/BD-General_Untitled-52_3.png)
    
    - `list` 옵션은 현재 실행 중 또는 실행된 MapReduce 작업 목록을 보여줌. 예시에서는 총 작업 수(Total jobs)가 0으로 표시되어 있음
