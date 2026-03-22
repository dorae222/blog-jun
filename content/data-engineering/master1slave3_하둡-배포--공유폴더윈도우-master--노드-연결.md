---
title: "Master1→Slave3_하둡 배포 / 공유폴더(윈도우-Master) / 노드 연결"
slug: "master1slave3_하둡-배포--공유폴더윈도우-master--노드-연결"
category: "data-engineering"
tags: ["hadoop", "hadoop-3.2.2", "hdfs", "networking", "openjdk", "ssh", "ubuntu", "virtualbox"]
status: published
post_type: tutorial
quality_score: 9.0
created_at: "2026-03-02T01:08:09.309841+00:00"
---

# [Setting]

### Master1→Slave3_하둡 배포 / 공유폴더(윈도우-Master) / 노드 연결

- CASE 1 (네임노드1 + 데이터노드3 | 네임노드 → 데이터노드 하둡 배포)
    - 기존 VirtualBox 삭제
        
        ![](/media/posts/imported/dev/BD-General_Untitled_4.png)
        
    - VirtualBox 다운로드
        
        [Hortonworks Data Platform (HDP) on Sandbox](https://www.cloudera.com/downloads/hortonworks-sandbox/hdp.html)
        
        [Index of /releases/20.04.2](http://old-releases.ubuntu.com/releases/20.04.2/)
        
        [Sandbox Docs - HDP 3.0.1](https://www.cloudera.com/tutorials/hortonworks-sandbox-guide/1.html)
        
        - 오라클 VM 열기
            
            ![](/media/posts/imported/dev/BD-General_Untitled-1_4.png)
            
            ![](/media/posts/imported/dev/BD-General_Untitled-2_4.png)
            
    - 네트워크 생성
        
        ![](/media/posts/imported/dev/BD-General_Untitled-3_3.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-4_3.png)
        
        - 추가된 NatNetwork를 더블클릭하여 그림과 같이 네트워크 CIDR 항목에 192.168.56.0/24 네트워크 주소 대역으로 구성하고, DHCP 지원 선택
            
            ![](/media/posts/imported/dev/BD-General_Untitled-5_3.png)
            
            ![](/media/posts/imported/dev/BD-General_Untitled-6_3.png)
            
    - 새로만들기 (모든 노드)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-7_3.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-8_3.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-9_3.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-10_3.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-11_3.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-12_3.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-13_3.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-14_3.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-15_3.png)
        
    - 네트워크 설정 (모든 노드)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-16_3.png)
        
    - 우분투 이미지 파일 설치(반복작업)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-17_3.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-18_3.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-19_3.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-20_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-21_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-22_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-23_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-24_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-25_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-26_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-27_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-28_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-29_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-30_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-31_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-32_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-33_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-34_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-35_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-36_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-37_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-38_2.png)
        
    - 다시 실행시 디스크가 비어있는데, 실행하면 됨
        
        ![](/media/posts/imported/dev/BD-General_Untitled-39_2.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-40.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-41.png)
        
    - 네트워크 설정(현재 가상화된 IP를 받은 것을 한 번 더 가상화를 진행 중)
        - 4개 서버 모두 동일하게 진행
            - Address 주소만 주의하기!
        - DNS: 도메인 네임 서비스 → IP를 도메인으로 바꿔줄 때 사용
        - Gateway: 현재 4대의 서버가 연결됐는데, 이것들도 결국 하나의 게이트를 통해 입출력
        
        ![](/media/posts/imported/dev/BD-General_Untitled-42.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-43.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-44.png)
        
        - Addresses
            - `192.168.56.101~104`
            - `24`
            - `192.169.56.1`
            - `162.126.63.1`
        - 껐다가 켜서 연결하여 네트워크 재접속
        
        ![](/media/posts/imported/dev/BD-General_Untitled-45.png)
        
    - 서버 간 통신 확인
        - `sudo apt install net-tools`
            
            ![](/media/posts/imported/dev/BD-General_Untitled-46.png)
            
            - cache lock 발생 경우
            
            [우분투 Waiting for cache lock: Could not get lock /var/lib/dpkg/lock-frontend 오류](https://writingdeveloper.blog/323)
            
        - `ifconfig`
            
            ![](/media/posts/imported/dev/BD-General_Untitled-47.png)
            
        - ping을 통해 서버간 테스트
            - `ping 다른 서버 주소 or DNS`
                
                ![](/media/posts/imported/dev/BD-General_Untitled-48.png)
                
                ![](/media/posts/imported/dev/BD-General_Untitled-49.png)
                
    - 공유 폴더 설정(Name 노드만 실행)
        - 네임노드와 데이터노드에 하둡을 설치하거나 데이터를 넣을 때,
        - 네임노드에서만 설치하고, 이 설정 내용을 데이터 노드에 배포
        - 데이터를 관리할 때는 하둡 명령어 사용
        - 현재는 윈도우 위에 네임노드 1개와 데이터노드 3개로 구성되어 있음
            - 윈도우에 폴더를 만들고, 리눅스도 폴더를 하나 만들어서 연결
        - 먼저 윈도우에 폴더 먼저 생성하기(wshare)
            
            ![](/media/posts/imported/dev/BD-General_Untitled-50.png)
            
        - 리눅스에 공유 폴더 설정하기
            
            ![](/media/posts/imported/dev/BD-General_Untitled-51.png)
            
            ![](/media/posts/imported/dev/BD-General_Untitled-52.png)
            
            ![](/media/posts/imported/dev/BD-General_Untitled-53.png)
            
            ![](/media/posts/imported/dev/BD-General_Untitled-54.png)
            
            ![](/media/posts/imported/dev/BD-General_Untitled-55.png)
            
            - wshare폴더에 빈 test.txt파일 생성
                
                ![](/media/posts/imported/dev/BD-General_Untitled-56.png)
                
        - 공유폴더 설정 후 디렉토리 확인
            
            ![](/media/posts/imported/dev/BD-General_Untitled-57.png)
            
            - Name노드에서 lshare 폴더를 생성 한 후
            - 관리자 권한으로 생성
            - `sudo mount -t vboxsf wshare /lshare`을 이용하여, 연결 디렉토리 설정
    - HADOOP 설치
        - 자바 세팅(모든 노드)
            - java ppa APT 추가
                - `sudo add-apt-repository ppa:openjdk-r/ppa`
                    - 입력 텍스트 출력시 키보드 엔터 or ctrl+c
                
                ![](/media/posts/imported/dev/BD-General_Untitled-58.png)
                
                - `sudo apt-get update`
                    - 패키지 업데이트
                    
                    ![](/media/posts/imported/dev/BD-General_Untitled-59.png)
                    
            - openjdk 8 설치
                - `sudo apt-get install openjdk-8-jdk`
                    
                    ![](/media/posts/imported/dev/BD-General_Untitled-60.png)
                    
                    - 설치 유무 물어보면 y입력
                    
                    ![](/media/posts/imported/dev/BD-General_Untitled-61.png)
                    
                    - 다소 다운로드 시간이 걸릴 수 있음
            - 자바 PATH 설정
                - `sudo gedit ~/.bashrc` → gedit: 홈 디렉토리 → 계정 관리 파일
                    - ls-la를 통해 확인 가능
                    
                    ![](/media/posts/imported/dev/BD-General_Untitled-62.png)
                    
                    - bashrc 파일이 열림
            - bashrc 파일 제일 하단에 PATH 추가 및 저장
                - `export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64`
                - `export PATH=$PATH:$JAVA_HOME/bin`
                - `export PATH`
                
                ![](/media/posts/imported/dev/BD-General_Untitled-63.png)
                
                - 이후 save 체크
            - 설치한 JAVA 버전 확인
                - `java –version`
                    
                    ![](/media/posts/imported/dev/BD-General_Untitled-64.png)
                    
            
            ![](/media/posts/imported/dev/BD-General_Untitled-65.png)
            
        - SSH 패키지 설치
            - 네트워크를 설치한 이유도, 내 서버끼리 데이터를 교환하기 위해서
            - 이때, SSH는 인증키 같은 역할을 한다
            - 즉, SSH키를 가진 내 서버끼리만 데이터를 교환하도록 한다.
            - SSH 패키지 설치 및 키 생성(모든 노드)
                - 패키지 설치
                    - `sudo apt-get install ssh`
                
                ![](/media/posts/imported/dev/BD-General_Untitled-66.png)
                
                - 키 생성(**네임노드만**)
                    - `ssh-keygen -t rsa -f ~/.ssh/id_rsa`
                    - 중간 enter passprhase 부분은 enter 입력!
                    
                    ![](/media/posts/imported/dev/BD-General_Untitled-67.png)
                    
                    - `keygen` - 프로그램 이름
                    - `rsa` - rsa 방식으로 보안
            - 생성한 키 등록(네임 노드만)
                - `cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys`
                    
                    >> : 오른쪽에도 append
                    
                    ![](/media/posts/imported/dev/BD-General_Untitled-68.png)
                    
            - 네임노드와 데이터노드 접근을 용이하기 위해 리눅스의 /etc/hosts 파일 수정(모든 노드)
                - [윈도우] OS에는 보통 hosts파일이 있음
                    - 그래서 굳이 도메인에 DNS에 IP를 묻지 않고, hosts를 사용
                - 현재 과정은 이 노드를 이 이름으로 사용할거야라고 설정하는 것
                - `sudo gedit /etc/hosts`
                    
                    ![](/media/posts/imported/dev/BD-General_Untitled-69.png)
                    
                - 수정
                    
                    ![](/media/posts/imported/dev/BD-General_Untitled-70.png)
                    
            - 생성한 공개키 DataNode에게 복사 (네임노드만)
                - `ssh-copy-id -i /home/hadoop/.ssh/id_rsa.pub hadoop@hadoop-data1`
                - `ssh-copy-id -i /home/hadoop/.ssh/id_rsa.pub hadoop@hadoop-data2`
                - `ssh-copy-id -i /home/hadoop/.ssh/id_rsa.pub hadoop@hadoop-data3`
                
                ![](/media/posts/imported/dev/BD-General_Untitled-71.png)
                
                - port22 error발생시, 데이터 노드에 ssh 설치했는지 제대로 확인하기!
                
        - 홈 디렉토리 아래 bigdata 디렉토리 생성 및 이동 (모든노드)
            - 생성
                - `cd ~`
                - `mkdir bigdata`
            - 이동
                - `cd bigdata/`
                
                ![](/media/posts/imported/dev/BD-General_Untitled-72.png)
                
        - 네임노드에서만 하둡 다운로드 및 압축해제(네임노드)
            - tar: 아카이브(파일을 하나로 묶음)
            - gz: 압축
            - 다운로드
                - `https://archive.apache.org/dist/hadoop/core/hadoop-3.2.2/hadoop-3.2.2.tar.gz`
                    
                    ![](/media/posts/imported/dev/BD-General_Untitled-73.png)
                    
                    ![](/media/posts/imported/dev/BD-General_Untitled-74.png)
                    
            - 압축 해제
                - `ls`
                - `tar xvf hadoop-3.2.2.tar.gz`
        - 하둡 다운시 버전이 붙어있어 불편하므로 hadoop으로 디렉토리명 변경(네임노드)
            - `mv hadoop-3.2.2 hadoop`
            
            ![](/media/posts/imported/dev/BD-General_Untitled-75.png)
            
            - 압축 해제 중…
            
            ![](/media/posts/imported/dev/BD-General_Untitled-76.png)
            
        - 하둡 설치시 파일 체크하기(네임노드)
            
            ![](/media/posts/imported/dev/BD-General_Untitled-77.png)
            
        - 파일 수정하기(네임노드)
            - lshare가 윈도우랑 연결 안되는 이슈
                
                ![](/media/posts/imported/dev/BD-General_Untitled-78.png)
                
            - [윈도우에서 파일명 수정하고, lshare에 세팅 코드 가져오기]
                
                ![](/media/posts/imported/dev/BD-General_Untitled-79.png)
                
                - lshare에 위 사진처럼 초록색으로 칠해져 있어야함
                - `cat`을 통해 파일 전문 열어보기
            - hadoop-env.sh 수정
                - 개념
                    - 하둡은 자바를 기반으로 동작됨
                    - `sudo gedit hadoop-env.sh` → 하둡에게 자바 경로를 알려 줌
                    - Shell Script - 리눅스의 명령어 모음집 = sh
                - `sudo gedit hadoop-env.sh`
                    
                    ![](/media/posts/imported/dev/BD-General_Untitled-80.png)
                    
                - 54라인 수정
                    
                    ![](/media/posts/imported/dev/BD-General_Untitled-81.png)
                    
            - core-site.xml 파일 수정
                - `sudo gedit core-site.xml`
                - 19라인 수정
                
                ![](/media/posts/imported/dev/BD-General_Untitled-82.png)
                
            - hdfs-site.xml 파일 수정
                - 19라인 수정
                
                ![](/media/posts/imported/dev/BD-General_Untitled-83.png)
                
            - mapred-site.xml 파일 수정
                - 개념
                    - 하둡은 1~3버전이 있고, 현재 3버전 사용 중
                    - 1버전이 처음 나오고 2버전으로 넘어가면서, 여러가지가 개설됨
                        - 1.a.b →  1로 갈수록 큰 변화
                        - yarn : 리소스 관리
                    - 2→ 3버전
                        - 보안측면 강화
                        - EC(eraser coding): RAID방식의 스토리지에서부터 분산개념이 발전됐는데, 복구를 위해 나옴
                            - RAID: 스토리지 여러 개를 연결하여 하나의 스토리지로 연결
                            - 짝수. 홀수를 분리하여 복구를 목적으로 했었음
                                - 부산을 가는데 100명이 버스 타는 케이스 , 10명씩 승용차 타는 케이스2 → 케이스2가 효율은 좋아도 병목현상 발생 가능
                            - 이 때, 이러한 병목현상을 해결하기 위해 …
                - 19번라인 수정
                
                ![](/media/posts/imported/dev/BD-General_Untitled-84.png)
                
            - yarn-site.xml 파일 수정
                - 하둡에서 여러군데에서 여러 파일을 설치하여, 여러 곳에 분산 저장을 함
                - 15라인 수정
                - port 8050
                
                ![](/media/posts/imported/dev/BD-General_Untitled-85.png)
                
            - workers 파일 수정
                - 데이터 노드가 누가 있는지 알려줌
                
                ![](/media/posts/imported/dev/BD-General_Untitled-86.png)
                
                ![](/media/posts/imported/dev/BD-General_Untitled-87.png)
                
        - 네임노드에서 데이터 노드에 하둡 배포(네임노드)
            - 다시 터미널 접속
            - `sudo rsync -avxP /home/hadoop/bigdata/hadoop/ hadoop@hadoop-data1:/home/hadoop/bigdata/hadoop` → data1부분만 2,3로 수정
                
                ![](/media/posts/imported/dev/BD-General_Untitled-88.png)
                
                ![](/media/posts/imported/dev/BD-General_Untitled-89.png)
                
        - 자바—하둡 경로 연결 (모든노드)
            - `sudo gedit ~/.bashrc`
            - 122라인부터 수정
            
            ![](/media/posts/imported/dev/BD-General_Untitled-90.png)
            

[... content truncated for processing ...]
