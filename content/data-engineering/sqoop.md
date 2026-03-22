---
title: "[SQOOP]"
slug: sqoop
category: "data-engineering"
tags: ["bigdata", "data-engineering", "hadoop", "hortonworks", "jdbc", "mysql", "sqoop", "sqoop-export", "sqoop-import"]
status: published
post_type: tutorial
quality_score: 8.0
created_at: "2026-03-02T01:08:09.297250+00:00"
---

### Mysql 설치

- MySQL APT Repository 추가
- 확인한 deb 파일 다운로드 후 확인
- MySQL APT 패키지 추가
- 설치된 패키지 업데이트
- MySQL 설치
- MySQL 설정

(Hortonworks에는 MySQL이 설치되어 있음)

---

- MySQL 접속
    - `mysql -u root -p`
    
    ![](/media/posts/imported/dev/BD-General_Untitled_7.png)
    
- MySQL 작동 확인
    - `show databases;`
        - 존재하는 database 확인
    
    ![](/media/posts/imported/dev/BD-General_Untitled-1_7.png)
    
- DB 조회 및 테이블 생성
    - 테이블 생성
        - `create table salaries (gender varchar(1),age int,salary double,zipcode int);`
        - `alter table salaries add column ‘id’ int(10)`
            
            `unsigned primary KEY AUTO_INCREMENT;`
            
            - 생성한 salaries 테이블에 id 컬럼을 추가하고, id 컬럼을 기본키로 지정하여 인덱스 값이 1씩 자동 증가하도록 수정
        - `desc 테이블명;`
            - 테이블 구조 확인
        
        ![](/media/posts/imported/dev/BD-General_Untitled-2_7.png)
        
    - 데이터 입력
        - `insert into 테이블명 (컬럼명,컬럼명~) values (컬럼값,컬럼값~)`
        
        ![](/media/posts/imported/dev/BD-General_Untitled-3_6.png)
        
    - 테이블에 계정 생성 후 권한 부여 및 적용
        - `CREATE USER 'root'@'%' IDENTIFIED BY 'bigdata';`
        - `GRANT ALL PRIVILEGES ON **.** TO 'root'@'%' WITH GRANT OPTION;`
        - `flush privileges;`
            - 권한 부여 적용
        
        ![](/media/posts/imported/dev/BD-General_Untitled-4_5.png)
        

### Sqoop 설치

- Hortonworks에는 이미 설치되어 있음
- `sqoop`

![](/media/posts/imported/dev/BD-General_Untitled-5_5.png)

- sqoop의 경로가 이미 설정되어 있어, 경로 없이 바로 `sqoop` 명령을 실행해도 인식됨

### Sqoop Import (DB→Hadoop)

- Import 실행
    - `sqoop import --connect jdbc:mysql://localhost/test --table salaries --username root --password hortonworks1--target-dir /tmp/sqoop_out`
        - MySQL에서 생성했던 salaries 테이블을 import 수행
        - `localhost`: 내 Windows IP를 전달하면, 윈도우에 설치된 MySQL과 연동 가능
    - `hadoop fs -ls /sqoop_out/`
    
    ![](/media/posts/imported/dev/BD-General_Untitled-6_5.png)
    
    - `hadoop fs -cat /sqoop_out/*`
    
    ![](/media/posts/imported/dev/BD-General_Untitled-7_5.png)
    
- 에러 발생
    - Sqoop은 Hadoop 2.6 버전을 기준으로 개발되었고 현재 개발이 중지되어 있어 Hadoop 3.0에 필요한 일부 jar 파일이 없어 오류가 발생할 수 있음
- 컬럼의 순서를 MySQL과 동일하게 수집
    
    ![](/media/posts/imported/dev/BD-General_Untitled-8_5.png)
    
    ![](/media/posts/imported/dev/BD-General_Untitled-9_5.png)
    
---

- 복수 테이블 import
    - 데이터 삽입
        
        ![](/media/posts/imported/dev/BD-General_Untitled-10_5.png)
        
    - 생성된 테이블 확인
        - `select 컬럼명 from 테이블명;`
        
        ![](/media/posts/imported/dev/BD-General_Untitled-11_5.png)
        
    - id 컬럼 생성하여 기본키로 지정 + 일정하게 증가
        - `alter table 테이블명 add column ‘컬럼명’ unsigned primary KEY AUTO_INCREMENT;`
            - `unsigned` : 컬럼에서 음수를 포함하지 않거나 값의 범위를 양수 쪽으로 넓히고 싶을 때 사용
            - `AUTO_INCREMENT`: 기본키에만 적용 가능하며 값이 자동 증가됨
        
        ![](/media/posts/imported/dev/BD-General_Untitled-12_5.png)
        
    - mysql에서 나와서 test3만 제외하고 테이블 import
        - `sqoop import-all-tables (generic-args) (import-args)`
            - `sqoop import-all-tables —connect jdbc:mysql://localhost/test —username root -password hortonworks1 —exclude table test3 —warehouse-dir /tmp/sqoop_out_3`
            - `--warehouse-dir` : 복수 테이블 import할 때 `--target-dir` 대신 사용
            
            [](https://data-flair.training/blogs/sqoop-import-all-tables/)
            
        
        ![](/media/posts/imported/dev/BD-General_Untitled-13_5.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-14_5.png)
        
        ![](/media/posts/imported/dev/BD-General_Untitled-15_5.png)
        

### Sqoop Export (Hadoop→DB)

- 지금까지는 DB에서 하둡으로 데이터를 가져왔음
- 이번에는 반대로 하둡에서 DB로 데이터를 보내는 작업을 진행함
- 이때 DB에 테이블이 없다면 어떻게 처리할지 차근차근 살펴봄
- mysql 내에 테이블 생성
    
    ![](/media/posts/imported/dev/BD-General_Untitled-16_5.png)
    
    ![](/media/posts/imported/dev/BD-General_Untitled-17_4.png)
    
- Hadoop → mysql로 export
    
    ![](/media/posts/imported/dev/BD-General_Untitled-18_4.png)
    
- 결과 확인
    
    ![](/media/posts/imported/dev/BD-General_Untitled-19_4.png)
    
    ![](/media/posts/imported/dev/BD-General_Untitled-20_3.png)
    

### Sqoop Query

[sqoop 명령어 정리](https://dlwjdcks5343.tistory.com/116)

- `eval`: 하둡에서 쿼리 사용
- SQOOP QUERY1
    - `sqoop eval —connect jdbc:mysql://localhost/test —username root —password hortonworks1 —query ‘SELECT*FROM salaries where gender=”M”’`
    
    ![](/media/posts/imported/dev/BD-General_Untitled-21_3.png)
    
- SQOOP QUERY2
    - INSERT
        - `sqoop eval --connect jdbc:mysql://localhost/test --username root --password hortonworks1 --query 'INSERT INTO salaries VALUES ("M", 30, 44000,51531, 5)'`
    - INSERT 확인
        1. sqoop
            
            ![](/media/posts/imported/dev/BD-General_Untitled-22_3.png)
            
        2. mysql
            - `mysql -u root -p`
            - `use test;`
            - `select * from salaries;`
            
            ![](/media/posts/imported/dev/BD-General_Untitled-23_3.png)
            
- MySQL DB 목록 확인
    - `sqoop list-databases —connect jdbc:mysql://hadoop-name/test —username root —password hortonworks1`
    
    ![](/media/posts/imported/dev/BD-General_Untitled-24_3.png)
    
- MySQL DB 테이블 확인
    - `sqoop list-tables —connect jdbc:mysql://localhost/test —username root —password hortonworks1`
    
    ![](/media/posts/imported/dev/BD-General_Untitled-25_3.png)
