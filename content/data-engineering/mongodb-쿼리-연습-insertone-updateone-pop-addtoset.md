---
title: "MongoDB 쿼리 연습: insertOne, updateOne, $pop, $addToSet"
slug: "mongodb-쿼리-연습-insertone-updateone-pop-addtoset"
category: "data-engineering"
tags: ["crud", "document-database", "mongodb", "nosql", "query"]
status: published
post_type: tutorial
quality_score: 6.0
created_at: "2026-03-02T01:08:46.828728+00:00"
---

## MongoDB 쿼리 연습문제

MongoDB Shell을 사용하여 문서 삽입, 갱신, 삭제 등의 CRUD 쿼리를 연습합니다.

## 문제1: 문서 삽입 (insertOne)

이름, 나이, 주소(내장 문서), 취미(배열), 특기(배열)를 encore 컬렉션에 저장합니다.

```javascript
db.encore.insertOne({
  "name": "Hyeong jun -Do",
  "age": 25,
  "address": {"si": "Seoul", "goo": "Seongdong", "dong": "HengDang"},
  "hobby": ["music", "game", "sleep"],
  "talent": ["focus"]
})

db.encore.find().pretty()
```

MongoDB의 내장 문서(Embedded Document)는 관계형 DB의 외래 키 조인 없이 연관 데이터를 하나의 문서에 포함할 수 있습니다.

## 문제2: 필드 추가 갱신 (updateOne + $set)

핸드폰 번호 필드를 추가합니다.

```javascript
db.encore.find().pretty()

db.encore.updateOne(
  {"_id": ObjectId("63e5e818b407327b2695378e")},
  {$set: {phone: "010-9999-9999"}}
)

db.encore.find().pretty()
```

`$set` 연산자는 지정한 필드만 수정하거나, 존재하지 않는 필드라면 새로 추가합니다.

## 문제3: 내장 문서를 단일 문자열로 변환 (updateOne + $set)

주소 내장 문서(si, goo, dong 3개 필드)를 하나의 문자열로 합칩니다.

```javascript
db.encore.find().pretty()

db.encore.updateOne(
  {"name": "Hyeong jun -Do"},
  {$set: {address: "Seoul Seongdong HengDang"}}
)

db.encore.find().pretty()
```

## 문제4: 배열의 마지막 요소 제거 ($pop)

취미 배열의 마지막 값을 제거합니다.

```javascript
db.encore.find().pretty()

db.encore.update(
  {"name": "Hyeong jun -Do"},
  {$pop: {hobby: 1}}
)

db.encore.find().pretty()
```

`$pop` 연산자: `1`이면 배열 마지막 요소, `-1`이면 첫 번째 요소를 제거합니다.

## 문제5: 중복 없이 배열 요소 추가 ($addToSet + $each)

특기 배열에 중복값 없이 2개의 요소를 추가합니다.

```javascript
db.encore.updateOne(
  {"name": "Hyeong jun -Do"},
  {$addToSet: {talent: {$each: ["focus", "leadership"]}}}
)
```

`$addToSet`은 배열에 중복값이 있으면 추가하지 않습니다. `$each`와 함께 사용하면 여러 값을 한 번에 추가할 수 있습니다.

## MongoDB 주요 배열 연산자 정리

| 연산자 | 설명 |
|--------|------|
| `$push` | 배열에 요소 추가 (중복 허용) |
| `$addToSet` | 배열에 중복 없이 요소 추가 |
| `$pop` | 배열의 첫/마지막 요소 제거 |
| `$pull` | 조건에 맞는 요소 제거 |
| `$each` | 여러 요소를 한 번에 처리 |
