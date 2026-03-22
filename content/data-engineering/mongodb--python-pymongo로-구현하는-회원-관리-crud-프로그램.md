---
title: "MongoDB + Python: pymongo로 구현하는 회원 관리 CRUD 프로그램"
slug: "mongodb--python-pymongo로-구현하는-회원-관리-crud-프로그램"
category: "data-engineering"
tags: ["crud", "document-database", "mongodb", "nosql", "pymongo", "python"]
status: published
post_type: tutorial
quality_score: 7.5
created_at: "2026-03-02T01:08:46.822253+00:00"
---

## MongoDB를 활용한 사용자 회원 정보 프로그램

pymongo 라이브러리를 사용하여 MongoDB에 회원 정보를 저장하고 CRUD 기능을 구현한 Python 프로그램입니다.

## MongoDB 문서 모델 개요

MongoDB는 관계형 데이터베이스와 달리 **문서(Document)** 기반의 NoSQL 데이터베이스입니다. 데이터를 JSON 형태의 BSON(Binary JSON)으로 저장하며, 스키마가 유연하여 필드를 동적으로 추가할 수 있습니다.

- **관계형 DB**: 테이블(Table) → 행(Row) → 열(Column)
- **MongoDB**: 컬렉션(Collection) → 문서(Document) → 필드(Field)

## 프로그램 구성

회원 데이터 구조: `_id`, `name`, `age`, `address`, `phone`, `id`

메뉴 구성:
- 1: 전체 회원 조회
- 2: 특정 회원 조회
- 3: 회원 가입
- 4: 회원 수정
- 5: 회원 삭제
- 그 외: 프로그램 종료

## 전체 코드

```python
import pandas as pd
from pymongo import MongoClient
from tabulate import tabulate
import json

def connect_mongodb():
    myclient = MongoClient("mongodb://localhost:27017")  # DB경로 설정
    mydb = myclient["membership"]  # DB명 설정
    mycol = mydb["test1"]  # collection명 설정
    return mycol

def select_all(mycol):
    result_list = list(mycol.find())
    return result_list

def select_one(mycol, con_id):
    result_list = list(mycol.find({"id": con_id}))
    return result_list

def insert_one(mycol):
    mydict = {"name": data_args_list[0],
              "age": int(data_args_list[1]),
              "address": data_args_list[2],
              "phone": data_args_list[3],
              "id": id_x + 1}
    mycol.insert_one(mydict)

def update_one(mycol, update_id, update_value):
    update_args_1 = {"id": update_id}
    update_args_2 = {"$set": {"id": update_value}}
    mycol.update_one(update_args_1, update_args_2)
    result_list = list(mycol.find())
    return result_list

def delete_one(mycol, delete_value):
    delete_args_1 = {"id": delete_value}
    mycol.delete_one(delete_args_1)
    result_list = list(mycol.find())
    return result_list

if __name__ == '__main__':
    while True:
        mycol = connect_mongodb()
        try:
            max_id_query = (mycol.find_one(sort=[("id", -1)])).get('id')
        except:
            max_id_query = 0
        id_x = int(max_id_query)
        select_process = input('[1.전체 회원 조회//2.특정 회원 조회//3.회원 가입//4.회원 수정//5.회원 삭제//종료: 1~5를 제외한 아무키 입력]: ')

        if select_process == '1':
            result_list = select_all(mycol)
        if select_process == '2':
            con_id = int(input('조회할 회원번호를 입력해주세요: '))
            result_list = list(select_one(mycol, con_id))
        if select_process == '3':
            data_args1 = input("이름:")
            data_args2 = input("나이:")
            data_args3 = input("주소:")
            data_args4 = input("번호:")
            data_args_list = [data_args1, data_args2, data_args3, data_args4]
            insert_one(mycol)
            result_list = list(mycol.find())
        if select_process == '4':
            update_id = int(input("업데이트 할 키 입력: "))
            update_value = int(input("업데이트 할 값 입력: "))
            result_list = update_one(mycol, update_id, update_value)
        if select_process == '5':
            delete_value = int(input("삭제할 회원번호 입력: "))
            result_list = delete_one(mycol, delete_value)

        if select_process not in ['1', '2', '3', '4', '5']:
            break

        df = pd.DataFrame(result_list)
        print(tabulate(df, headers="keys", tablefmt="psql", showindex=False))
```

## 기능별 설명

### 0. 전체 구조

```python
if __name__ == '__main__':
    while True:
        # 1~5 로직 처리
        if select_process not in ['1', '2', '3', '4', '5']:
            break
        # 결과를 DataFrame으로 출력
        df = pd.DataFrame(result_list)
        print(tabulate(df, headers="keys", tablefmt="psql", showindex=False))
```

### 1. 회원 가입 기능

자동 증가 ID를 구현하기 위해 id 필드를 내림차순 정렬 후 최대값에 +1 하는 방식을 사용합니다.

```python
try:
    max_id_query = (mycol.find_one(sort=[("id", -1)])).get('id')
    # id가 최대인 문서를 찾아 id 값만 추출
    # 이후 실행 시 +1 하여 새 id 생성
except:
    max_id_query = 0
id_x = int(max_id_query)
```

### 2. 전체 회원 조회

```python
def select_all(mycol):
    result_list = list(mycol.find())  # 전체 문서 리스트화
    return result_list
```

### 3. 특정 회원 조회

```python
def select_one(mycol, con_id):
    result_list = list(mycol.find({"id": con_id}))
    return result_list
```

입력받은 `con_id`에 해당하는 문서만 필터링하여 반환합니다.

### 4. 회원 수정

```python
def update_one(mycol, update_id, update_value):
    update_args_1 = {"id": update_id}       # 업데이트 대상 조건
    update_args_2 = {"$set": {"id": update_value}}  # 변경할 값
    mycol.update_one(update_args_1, update_args_2)
    result_list = list(mycol.find())
    return result_list
```

`$set` 연산자로 특정 필드만 수정합니다.

### 5. 회원 삭제

```python
def delete_one(mycol, delete_value):
    delete_args_1 = {"id": delete_value}  # 삭제 대상 조건
    mycol.delete_one(delete_args_1)       # 해당 문서 삭제
    result_list = list(mycol.find())      # 삭제 후 전체 목록 확인
    return result_list
```

### 6. 프로그램 종료

```python
if select_process not in ['1', '2', '3', '4', '5']:
    break  # 1~5 외 입력 시 while 루프 종료
```
