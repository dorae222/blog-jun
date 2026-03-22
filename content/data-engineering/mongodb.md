---
title: "[MongoDB]"
slug: mongodb
category: "data-engineering"
tags: ["database", "installation", "mongodb", "mongodb-compass", "mongo-shell", "nosql", "query", "rdbms", "update-operators"]
status: published
post_type: tutorial
quality_score: 9.0
created_at: "2026-03-02T01:08:09.353351+00:00"
---

# [MongoDB]


### MONGODB 이론

- 데이터베이스란?
    
    ![](/media/posts/imported/dev/DEV-Web_Untitled.png)
    
    - 여러 사람이 공유하여 사용하도록 통합해 관리하는 데이터의 집합
    - 자료 항목의 중복을 줄이고 데이터를 구조화하여 저장함으로써 검색과 갱신의 효율을 높인 것
- DBMS란?
    
    ![](/media/posts/imported/dev/DEV-Web_Untitled-1.png)
    
    - 데이터베이스를 관리하는 시스템
    - 데이터베이스를 정의하고 질의어(SQL)를 지원하는 등의 작업을 수행함
    - 관계형 데이터베이스(RDBMS), 비관계형 데이터베이스(NoSQL)
    - 관계형 데이터베이스(RDBMS)
        
        ![](/media/posts/imported/dev/DEV-Web_Untitled-2.png)
        
        - 데이터를 표(Relation) 형태로 표현하는 데이터베이스
        - 정형화된 데이터 항목들의 집합
    - 비관계형 데이터베이스(NoSQL)
        
        ![](/media/posts/imported/dev/DEV-Web_Untitled-3.png)
        
        - 데이터의 형태와 볼륨이 다양해지면서 새로운 저장 기술이 필요해짐
        - RDBMS의 한계를 보완하기 위해 등장한 다양한 형태의 DBMS
- RDBMS의 한계
    
    ![](/media/posts/imported/dev/DEV-Web_Untitled-4.png)
    
    - 스키마 문제
        - 빅데이터를 RDB의 스키마에 맞추려면 긴 다운타임이 발생할 수 있음
    - 스케일업의 한계
        - 전통적 RDBMS는 스케일 아웃(Scale Out)에 맞춰 설계되지 않음
        - 관계 모델과 트랜잭션의 연산, 일관성을 유지하면서 분산 환경에서 운용하기 어려움
- RDBMS vs NoSQL 비교
    
    ![](/media/posts/imported/dev/DEV-Web_Untitled-5.png)
    
    - RDBMS는 테이블 기반이며, NoSQL은 테이블로 데이터를 정의하지 않는 등 모델이 다름
- NoSQL의 확장성
    
    ![](/media/posts/imported/dev/DEV-Web_Untitled-6.png)
    
    - NoSQL은 RDBMS에 비해 수평 확장성(스케일 아웃)이 용이함
- 트랜잭션 성질 비교
    
    ![](/media/posts/imported/dev/DEV-Web_Untitled-7.png)
    
    - 트랜잭션이 안전하게 수행되도록 보장하는 특성
        - RDBMS → ACID
            - ACID
                - 원자성(Atomicity)
                    - 트랜잭션이 부분적으로 실행되다가 중단되는 것을 방지하는 성질
                - 일관성(Consistency)
                    - 데이터는 항상 일관된 상태를 유지해야 하며, 조작 후에도 무결성을 지켜야 함
                - 고립성(Isolation)
                    - 한 트랜잭션의 수행 중 다른 트랜잭션의 연산이 개입하지 못하도록 보장
                - 지속성(Durability)
                    - 성공적으로 완료된 트랜잭션의 결과는 영구히 반영되어야 함
            - ACID 예시
        - NoSQL → CAP Theorem
            - CAP Theorem
                
                ![](/media/posts/imported/dev/DEV-Web_Untitled-8.png)
                
- NoSQL의 데이터 모델
    
    ![](/media/posts/imported/dev/DEV-Web_Untitled-9.png)
    
    - 데이터베이스 구조를 정의하는 여러 모델
        - 키-값 모델 (Key-Value Store)
            
            ![](/media/posts/imported/dev/DEV-Web_Untitled-10.png)
            
        - 문서형 모델 (Document Store)
            
            ![](/media/posts/imported/dev/DEV-Web_Untitled-11.png)
            
        - 컬럼형 모델 (Column Family Store)
            
            ![](/media/posts/imported/dev/DEV-Web_Untitled-12.png)
            
        - 그래프형 모델 (Graph Store)
            
            ![](/media/posts/imported/dev/DEV-Web_Untitled-13.png)
            


### MongoDB 설치하기

- Ubuntu에서 MongoDB 설치
    
    ![](/media/posts/imported/dev/DEV-Web_Untitled-14.png)
    
    - `wget -qO - https://www.mongodb.org/static/pgp/server-4.4.asc | sudo apt-key add -`
        - 에러 발생 시
            - `sudo apt-get install gnupg`
            - `wget -qO - https://www.mongodb.org/static/pgp/server-4.4.asc | sudo apt-key add -`
    - `echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/4.4 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.4.list`
    - `sudo apt-get update`
    
    ![](/media/posts/imported/dev/DEV-Web_Untitled-15.png)
    
    - `sudo apt-get install -y mongodb-org`
- MongoDB 패키지 고정 설정
    
    ![](/media/posts/imported/dev/DEV-Web_Untitled-16.png)
    
    ```json
    echo "mongodb-org hold" | sudo dpkg --set-selections
    echo "mongodb-org-server hold" | sudo dpkg --set-selections
    echo "mongodb-org-shell hold" | sudo dpkg --set-selections
    echo "mongodb-org-mongos hold" | sudo dpkg --set-selections
    echo "mongodb-org-tools hold" | sudo dpkg --set-selections
    ```

- MongoDB 서비스 상태 확인
    - `sudo systemctl status mongod`
        - 초기에는 inactive (dead) 상태로 표시될 수 있음
        
        ![](/media/posts/imported/dev/DEV-Web_Untitled-17.png)
        
- MongoDB 서비스 시작 후 상태 확인
    - `sudo systemctl start mongod`
    - `sudo systemctl status mongod`
        - inactive (dead)에서 active (running)으로 변경됨
        
        ![](/media/posts/imported/dev/DEV-Web_Untitled-18.png)
        
- MongoDB 시작
    - `mongo`
        
        ![](/media/posts/imported/dev/DEV-Web_Untitled-19.png)
        


### MongoDB UI

- 세팅
    
    ![](/media/posts/imported/dev/DEV-Web_Untitled-20.png)
    
    `wget https://downloads.mongodb.com/compass/mongodb-compass_1.35.0_amd64.deb`
    
    `sudo dpkg -i mongodb-compass_1.35.0_amd64.deb`
    
    `mongodb-compass`
    
- 확인
    
    ![](/media/posts/imported/dev/DEV-Web_Untitled-21.png)
    


### MongoDB Basic Query

- JavaScript 기반 쿼리 지원
- DB 확인
    - `show dbs`
    - `show databases`
- 데이터 삽입
    
    ![](/media/posts/imported/dev/DEV-Web_Untitled-22.png)
    
    - `db.encore.insert("name","Hyeong-Jun Do")`
        - `encore` → collection
    - 직접 _id 설정 가능
        - `db.encore.insert("_id":12345,"name","Hyeong-Jun Do")`
        - 일반적으로는 MongoDB가 자동 생성한 `_id`를 사용하는 것이 권장됨
    - 예쁘게 출력
        - `db.encore.find().pretty()`
- 문서 vs 필드
    
    ![](/media/posts/imported/dev/DEV-Web_Untitled-23.png)
    
- 데이터 업데이트
    - `db.컬렉션.update({’키1’:’벨류1’},{$set:{”키2’:’벨류2’}})`
        - `{’키1’:’벨류1’}`: 검색 조건
        - `{$set:{”키2’:’벨류2’}}`: 변경할 값
        
        ![](/media/posts/imported/dev/DEV-Web_Untitled-24.png)
        
- collections 확인 및 제거
    
    ![](/media/posts/imported/dev/DEV-Web_Untitled-25.png)
    
- “_id” 주의사항
    
    ![](/media/posts/imported/dev/DEV-Web_Untitled-26.png)
    
    - 삽입하려는 문서에 중복되는 `_id`가 있으면 에러가 발생하여 그 문서는 삽입되지 않음
        - 에러 메시지는 duplicate key error로 표시되고, 예시에서 세 번째 문서에서 에러가 발생함
    - 하지만 `nInserted: 2`를 통해 두 개의 문서는 정상적으로 삽입되었음을 확인할 수 있음
    
    ![](/media/posts/imported/dev/DEV-Web_Untitled-27.png)
    
    - fruit 컬렉션을 확인하면, 세 번째 문서 이전의 첫 번째와 두 번째 문서는 삽입 완료됨
    
    ![](/media/posts/imported/dev/DEV-Web_Untitled-28.png)
    
    - `_id` 값을 좌측과 같이 수정하고, 마지막에 `{"ordered" : false}` 옵션을 추가하면
    - 동일하게 중복되는 `_id`에서 에러가 발생하더라도 나머지 문서들이 삽입될 수 있음
    
    ![](/media/posts/imported/dev/DEV-Web_Untitled-29.png)
    
    - 기본적으로 InsertMany의 `ordered` 옵션은 true이며, 문서가 주어진 순서대로 삽입을 시도함
        - `ordered: false`로 지정하면 오류가 발생한 문서를 건너뛰고 나머지 문서를 계속 삽입함
- 문서 삭제
    - 예제 — deleteOne
        
        ![](/media/posts/imported/dev/DEV-Web_Untitled-30.png)
        
        - deleteOne 함수는 조건과 일치하는 첫 번째 문서만 삭제함
    - 예제 — deleteOne (조건이 여러 개인 경우)
        
        ![](/media/posts/imported/dev/DEV-Web_Untitled-31.png)
        
        - `{ "name": "park" }` 조건과 일치하는 첫 번째 문서가 삭제됨
    - 예제 — deleteMany (여러 문서 삭제)
- 문서 교체/갱신
    - replaceOne
        - 예제 — replaceOne
            
            ![](/media/posts/imported/dev/DEV-Web_Untitled-32.png)
            
            - replaceOne은 필터로 문서를 찾고, 두 번째 인수로 제공한 전체 문서로 교체함
            - 예: `_id`가 1인 문서의 잘못된 필드 값을 전체 문서로 교체
        - 예제 — replaceOne + upsert 옵션 (조건과 일치하면 교체, 불일치 시 새로 생성)
            
            ![](/media/posts/imported/dev/DEV-Web_Untitled-33.png)
            
            - upsert는 update와 insert의 혼합 개념으로, 조건에 맞는 문서가 없으면 새로 삽입함
    - updateOne
        - 예제 — $inc 제한자 (값 증가)
            
            ![](/media/posts/imported/dev/DEV-Web_Untitled-34.png)
            
            ![](/media/posts/imported/dev/DEV-Web_Untitled-35.png)
            
            - `$inc`는 일치하는 키의 값을 증가(또는 음수를 사용하면 감소)시킴
            - 같은 연산을 두 번 수행하면 값이 연속해서 증가함
        - 예제 — $inc 제한자 (내장 문서 접근)
            
            ![](/media/posts/imported/dev/DEV-Web_Untitled-36.png)
            
            - `$inc`로 `quantity` 값을 -2만큼 조정하고, 내장 문서 `metrics.orders` 값을 1 증가시킴
            - 내장 문서의 필드에는 점 표기법(`metrics.orders`)으로 접근함
        - 예제 — $set 제한자 (필드값 수정)
            
            ![](/media/posts/imported/dev/DEV-Web_Untitled-37.png)
            
            - `$set`은 필드 값을 설정하거나, 필드가 없으면 새로 생성함
            - 예제에서는 `_id`로 문서를 찾아 `hobby`를 `Piano`로 설정함
                - 각 환경의 `_id` 값이 다를 수 있으니 반드시 확인 후 실행할 것
        - 예제 — $set 제한자 (데이터 타입 변경)
            
            ![](/media/posts/imported/dev/DEV-Web_Untitled-38.png)
            
            - `$set`으로 키의 데이터형도 변경할 수 있음
            - 예: `name`이 `Lee Eun Jin`인 문서의 `hobby`를 배열로 변경
        - 예제 — $unset 제한자 (필드 제거)
            
            ![](/media/posts/imported/dev/DEV-Web_Untitled-39.png)
            
            - `$unset`은 문서 내 특정 필드와 값을 제거함
        - 예제 — $push 제한자 (배열에 요소 추가)
            
            ![](/media/posts/imported/dev/DEV-Web_Untitled-40.png)
            
            - `$push`는 배열이 이미 존재하면 끝에 요소를 추가하고, 없으면 새 배열을 생성함
        - 예제 — $push 제한자 (새 배열 생성)
            
            ![](/media/posts/imported/dev/DEV-Web_Untitled-41.png)
            
            - 존재하지 않는 키에 대해 `$push`를 사용하면 해당 키를 새 배열로 생성함
        - 예제 — $each 제한자 ($push와 함께 여러 값 추가)
            
            ![](/media/posts/imported/dev/DEV-Web_Untitled-42.png)
            
            - `$each`는 `$push`와 함께 여러 값을 한 번에 추가할 때 사용함
        - 예제 — $push 제한자 (중복 설명 정리)
            
            ![](/media/posts/imported/dev/DEV-Web_Untitled-43.png)
            
            ![](/media/posts/imported/dev/DEV-Web_Untitled-44.png)
            
            - 이미 존재하는 배열에 요소를 추가하거나, 없는 경우 새 배열로 생성되는 동작 예시
        - 예제 — $each 제한자 (중복 설명 정리)
            
            ![](/media/posts/imported/dev/DEV-Web_Untitled-45.png)
            
            - `$each`를 사용해 `scores`에 여러 값을 추가한 예시
        - 예제 — $sort & $slice 제한자
            
            ![](/media/posts/imported/dev/DEV-Web_Untitled-46.png)
            
            - 테스트용 데이터를 입력하고 `$sort`, `$slice`를 사용한 배열 조작 예시
            
            ![](/media/posts/imported/dev/DEV-Web_Untitled-47.png)
            
            - `$sort`: 오름차순(1) 또는 내림차순(-1)
            - `$slice`: 배열에 남길 요소의 개수 제한
            - 예: `quizzes` 배열에 `$each`로 3개 항목을 추가하고, `score` 기준으로 내림차순 정렬한 후 `$slice: 3`으로 상위 3개만 유지
        - 예제 — $addToSet 제한자
        - 예제 — $pop 제한자
        - 예제 — $pull 제한자
        - 예제 — $pop 제한자 (중복 항목)
        - 갱신 입력 (upsert 추가 예제)
            
            ![](/media/posts/imported/dev/DEV-Web_Untitled-48.png)
            
            - upsert: 조건에 맞는 문서가 있으면 갱신, 없으면 새 문서를 생성함
            - `{ upsert : true }`와 `$inc`를 사용해 `age`가 40인 문서를 찾아 3 증가시키려 했으나 없으면 새로 추가됨
        - 다중 문서 갱신 (updateMany)
            
            ![](/media/posts/imported/dev/DEV-Web_Untitled-49.png)
            
            - `updateOne`은 조건과 일치하는 첫 번째 문서만 갱신
            - `updateMany`는 조건과 일치하는 모든 문서를 갱신함
            - 예: `birthday`가 같은 여러 문서에 `gift` 필드를 추가
        - 갱신된 문서 반환
            - findOneAndDelete
                
                ![](/media/posts/imported/dev/DEV-Web_Untitled-50.png)
                
                - 조건에 맞는 하나의 문서를 찾아 삭제하고, 삭제된 문서를 반환함
                - 예: `name`이 `A.MacDyver`인 문서 중 `points`로 정렬해 첫 번째 문서를 삭제하고 반환
            - findOneAndUpdate
                
                ![](/media/posts/imported/dev/DEV-Web_Untitled-51.png)
                
                ![](/media/posts/imported/dev/DEV-Web_Untitled-52.png)
                
                - 조건에 맞는 하나의 문서를 찾아 갱신하고, 갱신된 문서를 반환함
                - 예: `_id`가 1인 문서를 찾아 `$set`과 `$sum`을 이용해 `grades` 배열의 `grade` 합계를 `total` 필드로 추가하여 반환
            - findOneAndReplace
                
                ![](/media/posts/imported/dev/DEV-Web_Untitled-53.png)
                
                - 조건에 맞는 하나의 문서를 찾아 전체 문서로 교체하고, 교체된 문서를 반환함
                - 예: `scores` 컬렉션을 재입력한 후 `score`가 특정 값보다 작은 문서를 찾아 정렬하여 교체


[... content truncated for processing ...]
