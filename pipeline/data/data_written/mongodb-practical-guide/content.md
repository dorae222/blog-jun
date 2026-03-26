# MongoDB 실전 가이드: 설치부터 CRUD 연산, 갱신 연산자까지

## 개요

MongoDB는 문서형(Document) NoSQL 데이터베이스로, JSON과 유사한 BSON 형식으로 데이터를 저장합니다. 고정된 테이블 스키마 없이 유연한 구조의 데이터를 다룰 수 있어, 빠른 프로토타이핑과 스키마 변경이 잦은 서비스에서 널리 쓰이고 있습니다.

이 글에서는 MongoDB를 Ubuntu 환경에 설치하는 과정부터 시작하여, MongoDB Compass를 활용한 GUI 관리, 그리고 Mongo Shell에서의 CRUD 연산과 다양한 갱신 연산자(Update Operator)를 코드 예제와 함께 다룹니다. RDBMS에 익숙한 개발자가 MongoDB의 데이터 조작 방식을 빠르게 익히는 것을 목표로 합니다.

## 핵심 개념

### RDBMS와 MongoDB 용어 대응

MongoDB를 처음 접하면 용어부터 혼란스러울 수 있습니다. RDBMS의 개념과 1:1로 대응시키면 이해가 빠릅니다.

| RDBMS | MongoDB | 설명 |
|-------|---------|------|
| Database | Database | 데이터베이스 단위 |
| Table | Collection | 데이터를 담는 그룹 |
| Row | Document | 하나의 데이터 레코드 |
| Column | Field | 데이터의 속성 |
| Primary Key | _id | 문서의 고유 식별자 |
| JOIN | Embedded Document / $lookup | 관계 표현 방식 |

RDBMS에서 테이블에 행(Row)을 삽입하듯, MongoDB에서는 컬렉션(Collection)에 문서(Document)를 삽입합니다. 가장 큰 차이는 같은 컬렉션 안의 문서라도 서로 다른 필드 구조를 가질 수 있다는 점입니다. 이를 유연한 스키마(Flexible Schema)라고 합니다.

### 문서(Document)와 필드(Field)

MongoDB의 기본 데이터 단위는 문서입니다. 문서는 BSON(Binary JSON) 형식으로 저장되며, 내장 문서(Embedded Document)와 배열을 포함할 수 있습니다.

```json
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "name": "Hyeong-Jun Do",
  "age": 30,
  "address": {
    "city": "Seoul",
    "district": "Gangnam"
  },
  "hobbies": ["reading", "coding"]
}
```

위 예시에서 `address`는 내장 문서이고, `hobbies`는 배열입니다. 이처럼 관련 데이터를 하나의 문서 안에 중첩하여 저장할 수 있으므로, RDBMS에서 여러 테이블에 나눠 저장하던 데이터를 하나의 문서로 표현할 수 있습니다.

### _id 필드의 역할

모든 MongoDB 문서는 `_id` 필드를 갖습니다. 직접 지정하지 않으면 MongoDB가 `ObjectId` 타입으로 자동 생성합니다. `_id`는 컬렉션 내에서 고유해야 하므로, 중복되는 `_id`로 문서를 삽입하면 `duplicate key error`가 발생합니다.

일반적으로는 MongoDB가 자동 생성하는 ObjectId를 그대로 사용하는 것이 권장됩니다. ObjectId에는 타임스탬프 정보가 포함되어 있어 생성 시점 순서를 보장하기 때문입니다.

## 실전 코드

### 1단계: Ubuntu에서 MongoDB 설치

다음은 Ubuntu 20.04(Focal) 기준으로 MongoDB 4.4를 설치하는 과정입니다.

GPG 키를 등록하고 리포지토리를 추가합니다.

```bash
# GPG 키 등록
wget -qO - https://www.mongodb.org/static/pgp/server-4.4.asc | sudo apt-key add -

# gnupg 패키지가 없어 에러가 발생하는 경우
sudo apt-get install gnupg
wget -qO - https://www.mongodb.org/static/pgp/server-4.4.asc | sudo apt-key add -

# MongoDB 리포지토리 추가
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/4.4 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.4.list

# 패키지 목록 갱신 후 설치
sudo apt-get update
sudo apt-get install -y mongodb-org
```

설치 후 패키지 버전이 자동으로 업그레이드되는 것을 방지하려면, 패키지 고정 설정을 적용합니다.

```bash
echo "mongodb-org hold" | sudo dpkg --set-selections
echo "mongodb-org-server hold" | sudo dpkg --set-selections
echo "mongodb-org-shell hold" | sudo dpkg --set-selections
echo "mongodb-org-mongos hold" | sudo dpkg --set-selections
echo "mongodb-org-tools hold" | sudo dpkg --set-selections
```

서비스를 시작하고 상태를 확인합니다.

```bash
# 서비스 시작
sudo systemctl start mongod

# 상태 확인 (active (running) 표시 확인)
sudo systemctl status mongod

# 부팅 시 자동 시작 설정
sudo systemctl enable mongod

# Mongo Shell 접속
mongo
```

`systemctl status mongod`의 결과가 `active (running)`으로 표시되면 정상적으로 동작하는 것입니다.

### 2단계: MongoDB Compass 설치 (GUI 도구)

MongoDB Compass는 공식 GUI 클라이언트로, 데이터를 시각적으로 탐색하고 쿼리를 실행할 수 있습니다.

```bash
# Compass 패키지 다운로드
wget https://downloads.mongodb.com/compass/mongodb-compass_1.35.0_amd64.deb

# 설치
sudo dpkg -i mongodb-compass_1.35.0_amd64.deb

# 실행
mongodb-compass
```

Compass가 실행되면 기본 연결 문자열 `mongodb://localhost:27017`로 로컬 MongoDB에 접속할 수 있습니다. 컬렉션 목록 확인, 문서 편집, 인덱스 관리 등의 작업을 GUI에서 수행할 수 있어, Mongo Shell에 익숙하지 않은 초기 단계에서 유용합니다.

### 3단계: 데이터베이스와 컬렉션 관리

Mongo Shell에서 데이터베이스와 컬렉션을 확인하고 관리하는 기본 명령어입니다.

```javascript
// 데이터베이스 목록 확인
show dbs
show databases

// 현재 데이터베이스 확인
db

// 데이터베이스 전환 (없으면 데이터 삽입 시 자동 생성)
use mydb

// 컬렉션 목록 확인
show collections

// 컬렉션 삭제
db.myCollection.drop()
```

MongoDB는 데이터베이스나 컬렉션을 명시적으로 생성하지 않아도, 첫 번째 문서를 삽입하는 시점에 자동으로 생성합니다. 이 점이 RDBMS에서 `CREATE TABLE`을 먼저 실행해야 하는 것과 다릅니다.

### 4단계: 문서 삽입 (Create)

```javascript
// 단일 문서 삽입
db.users.insertOne({
    name: "Hyeong-Jun Do",
    age: 30,
    city: "Seoul"
})

// 다중 문서 삽입
db.users.insertMany([
    { _id: 1, name: "Alice", age: 25 },
    { _id: 2, name: "Bob", age: 35 },
    { _id: 3, name: "Charlie", age: 28 }
])
```

`insertMany`에서 `_id` 중복이 발생하는 경우의 동작을 살펴보겠습니다.

```javascript
// 기본 동작 (ordered: true) - 에러 발생 시점에서 중단
db.fruit.insertMany([
    { _id: 1, name: "apple" },
    { _id: 2, name: "banana" },
    { _id: 2, name: "cherry" },   // duplicate key error 발생
    { _id: 4, name: "date" }      // 삽입되지 않음
])
// 결과: nInserted: 2 (apple, banana만 삽입)

// ordered: false - 에러를 건너뛰고 나머지 삽입 계속
db.fruit.insertMany([
    { _id: 1, name: "apple" },    // 중복 - 건너뜀
    { _id: 5, name: "elderberry" },
    { _id: 2, name: "cherry" },    // 중복 - 건너뜀
    { _id: 6, name: "fig" }
], { ordered: false })
// 결과: elderberry와 fig가 삽입됨
```

`ordered` 옵션은 대량 데이터 적재 시 중요합니다. 기본값인 `true`에서는 중복 에러가 발생하면 그 시점에서 전체 작업이 중단됩니다. `false`로 설정하면 에러가 발생한 문서만 건너뛰고 나머지를 계속 처리하므로, 일부 실패를 허용하는 배치 삽입에 적합합니다.

### 5단계: 문서 조회 (Read)

```javascript
// 전체 조회
db.users.find()
db.users.find().pretty()  // 들여쓰기된 형태로 출력

// 조건 조회
db.users.find({ name: "Alice" })

// 비교 연산자 활용
db.users.find({ age: { $gte: 25, $lte: 35 } })  // 25 이상 35 이하
db.users.find({ age: { $ne: 30 } })              // 30이 아닌 문서
db.users.find({ age: { $in: [25, 30, 35] } })    // 25, 30, 35 중 하나

// 논리 연산자
db.users.find({ $or: [
    { name: "Alice" },
    { age: { $gt: 30 } }
]})

// 특정 필드만 조회 (Projection)
db.users.find({}, { name: 1, age: 1, _id: 0 })

// null 조회 - 값이 null이거나 필드가 존재하지 않는 문서
db.users.find({ email: null })
```

`find()` 메서드의 두 번째 인자인 Projection을 활용하면 필요한 필드만 선택적으로 가져올 수 있습니다. 1은 포함, 0은 제외를 의미하며, `_id`를 제외한 필드에서는 포함과 제외를 혼합하여 사용할 수 없습니다.

### 6단계: 문서 갱신 (Update)

MongoDB의 갱신 연산은 다양한 갱신 연산자(Update Operator)를 통해 세밀한 제어가 가능합니다. 이 부분이 MongoDB 쿼리에서 가장 많은 기능을 제공하는 영역입니다.

#### $set - 필드 값 설정 또는 생성

```javascript
// hobby 필드를 "Piano"로 설정 (필드가 없으면 새로 생성)
db.users.updateOne(
    { name: "Alice" },
    { $set: { hobby: "Piano" } }
)

// 데이터 타입 변경도 가능 (문자열을 배열로)
db.users.updateOne(
    { name: "Alice" },
    { $set: { hobby: ["Piano", "Reading", "Coding"] } }
)
```

`$set`은 지정한 필드의 값을 변경합니다. 해당 필드가 존재하지 않으면 새로 생성합니다. 기존 값의 데이터 타입과 다른 타입으로 변경하는 것도 가능합니다.

#### $inc - 숫자 값 증감

```javascript
// age를 1 증가
db.users.updateOne(
    { name: "Bob" },
    { $inc: { age: 1 } }
)

// 내장 문서의 필드 접근 (점 표기법)
db.products.updateOne(
    { sku: "abc123" },
    { $inc: { quantity: -2, "metrics.orders": 1 } }
)
```

`$inc`는 숫자 필드의 값을 지정한 양만큼 증가시킵니다. 음수를 넣으면 감소합니다. 위 예시에서 `quantity`는 2만큼 감소하고, 내장 문서 `metrics`의 `orders` 필드는 1 증가합니다. 내장 문서의 필드에 접근할 때는 점 표기법(dot notation)을 사용합니다.

#### $unset - 필드 제거

```javascript
// hobby 필드를 문서에서 완전히 제거
db.users.updateOne(
    { name: "Alice" },
    { $unset: { hobby: "" } }
)
```

`$unset`에 전달하는 값(빈 문자열)은 의미가 없습니다. 어떤 값을 넣든 해당 필드가 문서에서 제거됩니다.

#### $push - 배열에 요소 추가

```javascript
// scores 배열 끝에 95 추가
db.users.updateOne(
    { name: "Alice" },
    { $push: { scores: 95 } }
)

// 존재하지 않는 키에 $push 사용 시 새 배열 생성
db.users.updateOne(
    { name: "Bob" },
    { $push: { tags: "developer" } }
)
// Bob 문서에 tags 필드가 없으면 ["developer"]로 생성
```

`$push`는 대상 필드가 배열이면 끝에 요소를 추가하고, 필드가 존재하지 않으면 해당 요소를 포함하는 새 배열을 생성합니다.

#### $each, $sort, $slice - 배열 고급 조작

여러 요소를 한 번에 추가하면서 정렬과 개수 제한까지 적용할 수 있습니다.

```javascript
// $each로 여러 값을 한 번에 추가
db.users.updateOne(
    { name: "Alice" },
    { $push: { scores: { $each: [88, 72, 95] } } }
)

// $each + $sort + $slice 조합
// quizzes 배열에 3개 항목 추가 후, score 기준 내림차순 정렬, 상위 3개만 유지
db.students.updateOne(
    { _id: 1 },
    { $push: {
        quizzes: {
            $each: [
                { id: 4, score: 78 },
                { id: 5, score: 92 },
                { id: 6, score: 65 }
            ],
            $sort: { score: -1 },
            $slice: 3
        }
    }}
)
```

`$sort`에서 1은 오름차순, -1은 내림차순을 의미합니다. `$slice`는 정렬 후 배열에 남길 요소의 최대 개수를 지정합니다. 이 세 연산자를 조합하면 "상위 N개의 점수만 유지"와 같은 패턴을 구현할 수 있습니다.

#### replaceOne - 문서 전체 교체

```javascript
// _id가 1인 문서를 완전히 새로운 문서로 교체
db.users.replaceOne(
    { _id: 1 },
    { name: "Alice Park", age: 31, city: "Seoul", status: "active" }
)

// upsert 옵션: 조건에 맞는 문서가 없으면 새로 삽입
db.users.replaceOne(
    { name: "NewUser" },
    { name: "NewUser", age: 25, city: "Busan" },
    { upsert: true }
)
```

`replaceOne`은 `$set`처럼 특정 필드만 수정하는 것이 아니라, 문서 전체를 두 번째 인자로 교체합니다. `_id` 필드는 변경할 수 없으므로 교체 문서에 포함하지 않아도 됩니다.

#### updateMany - 다중 문서 갱신

```javascript
// birthday가 "01/01"인 모든 문서에 gift 필드 추가
db.users.updateMany(
    { birthday: "01/01" },
    { $set: { gift: "Happy New Year" } }
)
```

`updateOne`은 조건에 맞는 첫 번째 문서만 수정하지만, `updateMany`는 조건에 맞는 모든 문서를 수정합니다. 대량의 데이터를 일괄 갱신할 때 사용합니다.

#### upsert - Update + Insert

```javascript
// age가 40인 문서를 찾아 3 증가, 없으면 새로 생성
db.users.updateOne(
    { age: 40 },
    { $inc: { age: 3 } },
    { upsert: true }
)
// 조건에 맞는 문서가 없으면 { age: 43 } 문서가 새로 생성됨
```

`upsert: true` 옵션을 사용하면, 조건에 맞는 문서가 있으면 갱신하고 없으면 새 문서를 삽입합니다. 별도의 존재 여부 확인 쿼리 없이 "있으면 수정, 없으면 생성" 로직을 원자적으로 처리할 수 있습니다.

### 7단계: 문서 삭제 (Delete)

```javascript
// 단일 문서 삭제 - 조건에 맞는 첫 번째 문서
db.users.deleteOne({ name: "Charlie" })

// 다중 문서 삭제 - 조건에 맞는 모든 문서
db.users.deleteMany({ age: { $lt: 25 } })

// 컬렉션의 모든 문서 삭제
db.users.deleteMany({})
```

`deleteOne`은 조건과 일치하는 문서가 여러 개라도 첫 번째 하나만 삭제합니다. 특정 조건의 모든 문서를 삭제하려면 `deleteMany`를 사용해야 합니다.

### 8단계: 갱신된 문서 반환 (findOneAnd 계열)

일반적인 `updateOne`이나 `deleteOne`은 작업 결과(수정/삭제된 건수)만 반환합니다. 실제 문서 내용이 필요한 경우에는 `findOneAnd` 계열 메서드를 사용합니다.

```javascript
// findOneAndDelete - 삭제하면서 삭제된 문서 반환
db.users.findOneAndDelete(
    { name: "Alice" },
    { sort: { age: 1 } }  // age 오름차순 중 첫 번째를 삭제
)

// findOneAndUpdate - 갱신하면서 갱신된 문서 반환
db.users.findOneAndUpdate(
    { _id: 1 },
    { $set: { status: "active" } },
    { returnDocument: "after" }  // 갱신 후 문서 반환 (기본값은 "before")
)

// findOneAndReplace - 교체하면서 교체된 문서 반환
db.scores.findOneAndReplace(
    { score: { $lt: 50 } },
    { name: "Reset", score: 0, status: "retry" },
    {
        sort: { score: 1 },
        projection: { _id: 0, name: 1, score: 1 }
    }
)
```

`findOneAndUpdate`의 `returnDocument` 옵션에서 `"before"`(기본값)는 갱신 전 문서를, `"after"`는 갱신 후 문서를 반환합니다. 큐(Queue) 패턴이나 상태 머신 구현처럼 "가져오면서 동시에 수정"하는 원자적 연산이 필요한 경우에 유용합니다.

## 활용 사례

### 사례 1: 게임 서버 랭킹 시스템

게임 서버에서 플레이어의 최근 상위 점수만 유지하는 랭킹 시스템을 구현할 수 있습니다.

```javascript
// 플레이어의 최근 점수 추가, 상위 10개만 유지
db.players.updateOne(
    { player_id: "user_001" },
    { $push: {
        high_scores: {
            $each: [{ score: 8500, stage: "boss_3", date: new Date() }],
            $sort: { score: -1 },
            $slice: 10
        }
    }},
    { upsert: true }
)
```

`$push`에 `$sort`와 `$slice`를 조합하면, 배열에 새 점수를 추가한 뒤 내림차순으로 정렬하고 상위 10개만 남깁니다. `upsert: true`를 사용하므로 해당 플레이어의 문서가 없으면 자동 생성됩니다. RDBMS에서는 별도의 INSERT/UPDATE 분기와 ORDER BY + LIMIT 쿼리가 필요한 작업을 하나의 원자적 연산으로 처리할 수 있습니다.

### 사례 2: 이커머스 재고 관리

상품 주문 시 재고를 감소시키고 주문 횟수를 증가시키는 패턴입니다.

```javascript
// 재고 차감과 주문 횟수 증가를 원자적으로 처리
db.products.updateOne(
    { sku: "WIDGET-001", quantity: { $gte: 1 } },
    {
        $inc: { quantity: -1, "metrics.orders": 1 },
        $set: { "metrics.last_order": new Date() }
    }
)
```

조건에 `quantity: { $gte: 1 }`을 포함시켜 재고가 0 이하인 경우 갱신이 수행되지 않도록 합니다. `$inc`로 `quantity`를 1 감소시키면서 동시에 `metrics.orders`를 1 증가시키고, `$set`으로 마지막 주문 일시를 기록합니다. 이 모든 연산이 하나의 원자적 갱신으로 처리됩니다.

### 사례 3: 작업 큐(Task Queue) 구현

`findOneAndUpdate`를 활용하여 간단한 작업 큐를 구현할 수 있습니다.

```javascript
// 대기 중인 작업을 하나 가져오면서 동시에 상태를 변경
var task = db.tasks.findOneAndUpdate(
    { status: "pending" },
    {
        $set: {
            status: "processing",
            worker: "worker-01",
            started_at: new Date()
        }
    },
    {
        sort: { priority: -1, created_at: 1 },
        returnDocument: "after"
    }
)
```

`findOneAndUpdate`는 문서를 찾고 수정하는 것을 원자적으로 수행하므로, 여러 워커가 동시에 같은 작업을 가져가는 경쟁 조건(race condition)을 방지할 수 있습니다. `sort` 옵션으로 우선순위가 높고(`priority: -1`) 먼저 생성된(`created_at: 1`) 작업부터 처리합니다.

### 사례 4: 사용자 프로필 유연한 관리

MongoDB의 유연한 스키마를 활용하면, 사용자마다 다른 구조의 프로필 데이터를 하나의 컬렉션에서 관리할 수 있습니다.

```javascript
// 일반 사용자
db.profiles.insertOne({
    user_id: "u001",
    name: "Alice",
    type: "individual",
    preferences: { theme: "dark", language: "ko" }
})

// 기업 사용자 - 다른 필드 구조
db.profiles.insertOne({
    user_id: "u002",
    company_name: "TechCorp",
    type: "business",
    employees: 50,
    departments: ["engineering", "marketing"]
})

// $addToSet으로 중복 없이 배열에 요소 추가
db.profiles.updateOne(
    { user_id: "u002" },
    { $addToSet: { departments: "sales" } }
)
```

RDBMS에서는 사용자 타입별로 별도 테이블을 만들거나, 사용하지 않는 NULL 컬럼이 많은 범용 테이블을 설계해야 합니다. MongoDB에서는 같은 컬렉션에 서로 다른 구조의 문서를 자연스럽게 저장할 수 있습니다.

## 정리

MongoDB의 핵심 CRUD 연산과 갱신 연산자를 정리하면 다음과 같습니다.

| 연산 | 단일 문서 | 다중 문서 | 반환형 |
|------|-----------|-----------|--------|
| 삽입 | insertOne() | insertMany() | - |
| 조회 | findOne() | find() | 문서 |
| 갱신 | updateOne() | updateMany() | 결과 통계 |
| 교체 | replaceOne() | - | 결과 통계 |
| 삭제 | deleteOne() | deleteMany() | 결과 통계 |
| 갱신+반환 | findOneAndUpdate() | - | 문서 |
| 삭제+반환 | findOneAndDelete() | - | 문서 |
| 교체+반환 | findOneAndReplace() | - | 문서 |

주요 갱신 연산자의 용도를 정리합니다.

| 연산자 | 용도 | 예시 |
|--------|------|------|
| $set | 필드 값 설정/생성 | 프로필 정보 수정 |
| $unset | 필드 제거 | 불필요한 필드 정리 |
| $inc | 숫자 증감 | 조회수, 재고 수량 |
| $push | 배열에 요소 추가 | 로그, 점수 기록 |
| $each | 여러 요소 일괄 추가 | 대량 태그 추가 |
| $sort | 배열 정렬 | 점수 내림차순 정렬 |
| $slice | 배열 개수 제한 | 최근 N개만 유지 |
| $addToSet | 중복 없이 배열 추가 | 고유 태그 관리 |

MongoDB를 처음 다룰 때는 RDBMS의 UPDATE 문과 비교하며 각 연산자의 동작을 이해하는 것이 효과적입니다. 특히 `$push`와 `$each`, `$sort`, `$slice`의 조합은 RDBMS에서 별도 쿼리 여러 개로 처리해야 할 작업을 하나의 원자적 연산으로 수행할 수 있게 해주므로, 실무에서 자주 활용되는 패턴입니다.

설치와 기본 CRUD를 익힌 뒤에는 인덱스 설계, Aggregation Pipeline, Replica Set 구성 등으로 학습 범위를 넓혀 나가는 것을 권장합니다.