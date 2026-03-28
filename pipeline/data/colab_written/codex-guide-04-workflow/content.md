# Codex CLI 실전: 레거시 마이그레이션

:::info
이 글은 **Codex CLI Guide** 시리즈의 마지막 글이다. 시리즈 전체 목차:
1. [[codex-guide-01-setup|설치와 기본 사용법]]
2. [[codex-guide-02-core|핵심 기능: 샌드박스와 코드 생성]]
3. [[codex-guide-03-advanced|고급 활용: 자동화와 CI 통합]]
4. **실전: 레거시 마이그레이션** (현재 글)
:::

시리즈의 마지막 글에서는 Codex CLI를 실전에서 활용하는 구체적인 전략을 다룬다. 레거시 코드 마이그레이션, 대규모 리팩토링, 테스트 자동 생성, 그리고 다른 AI 코딩 도구와의 비교까지 실무에 필요한 내용을 종합한다.

---

## 1. AGENTS.md 설계 패턴

실전 마이그레이션에서 AGENTS.md는 에이전트의 행동을 제어하는 핵심 도구다. 작업 유형별로 최적화된 AGENTS.md 패턴을 살펴보자.

### 1.1 마이그레이션 전용 AGENTS.md

레거시 마이그레이션 프로젝트에서는 마이그레이션 규칙을 명확히 정의해야 한다.

```markdown
<!-- AGENTS.md -->
# 마이그레이션 프로젝트: Python 2 to Python 3

## 마이그레이션 원칙
1. 기능적 동치성 유지 - 동작이 변하지 않아야 한다
2. 최소 변경 원칙 - 마이그레이션에 필요한 변경만 수행
3. 테스트 우선 - 수정 전에 기존 테스트가 통과하는지 확인
4. 단계적 진행 - 한 번에 하나의 파일/모듈만 수정

## Python 2 to 3 변환 규칙
- `print` 문 -> `print()` 함수
- `unicode` -> `str`, `str` -> `bytes`
- `dict.keys()`, `dict.values()`, `dict.items()`는 이미 뷰 반환
- `xrange` -> `range`
- `raw_input` -> `input`
- `except Exception, e` -> `except Exception as e`
- `__future__` import 불필요 (Python 3 전용이므로)

## 변경 금지
- 비즈니스 로직 변경 금지
- 알고리즘 최적화 금지 (마이그레이션만 수행)
- 새로운 의존성 추가 금지
- 테스트의 기대값 변경 금지
```

### 1.2 안전 장치 패턴

마이그레이션에서 가장 중요한 것은 기존 동작을 깨뜨리지 않는 것이다.

```markdown
<!-- AGENTS.md -->
# 안전 장치

## 필수 검증 단계
모든 파일 수정 후 다음을 반드시 수행:
1. `python -m py_compile [수정된 파일]` - 구문 오류 확인
2. `python -m pytest tests/ -x` - 테스트 실행 (첫 실패 시 중단)
3. `git diff` - 의도하지 않은 변경이 없는지 확인

## 롤백 규칙
- 테스트 실패 시 해당 파일의 모든 변경을 되돌린다
- `git checkout -- [파일]`로 원래 상태 복원
- 실패 원인을 분석하고 다른 접근 방식 시도

## 파일 단위 진행
- 한 번에 하나의 파일만 수정한다
- 수정 -> 테스트 -> 커밋 사이클을 파일별로 반복한다
- 커밋 메시지: `migrate: convert [파일명] to Python 3`
```

### 1.3 모노레포 패턴

대규모 모노레포에서는 패키지별로 다른 규칙이 필요하다.

```text
monorepo/
  AGENTS.md                    # 공통 규칙 (린팅, 커밋 형식 등)
  packages/
    legacy-api/
      AGENTS.md                # Python 2->3 마이그레이션 규칙
    new-frontend/
      AGENTS.md                # React 18 -> 19 업그레이드 규칙
    shared-lib/
      AGENTS.md                # 하위 호환성 유지 규칙
```

---

## 2. 레거시 코드 마이그레이션 전략

### 2.1 Python 2에서 Python 3으로

Python 2에서 3으로의 마이그레이션은 가장 흔한 레거시 마이그레이션 시나리오 중 하나다.

#### 단계 1: 현황 분석

```bash
codex --suggest --sandbox read-only \
  "이 프로젝트의 Python 2 코드를 분석해줘.
   1. Python 2 전용 구문 사용 현황 (print문, unicode, xrange 등)
   2. 파일별 마이그레이션 난이도 (상/중/하)
   3. 의존성 중 Python 3 미지원 패키지
   4. 권장 마이그레이션 순서"
```

#### 단계 2: 자동 변환 가능한 부분 처리

```bash
codex --auto-edit \
  "다음 파일의 Python 2 구문을 Python 3으로 변환해줘: src/utils/helpers.py
   - print문 -> print() 함수
   - unicode -> str
   - dict.iteritems() -> dict.items()
   - except Exception, e -> except Exception as e
   변환 후 python -m py_compile로 구문 확인"
```

#### 단계 3: 테스트 검증

```bash
codex --auto-edit \
  "src/utils/helpers.py를 Python 3으로 변환했다.
   기존 테스트(tests/test_helpers.py)를 실행하고,
   실패하는 테스트가 있으면 원인을 분석해줘.
   테스트의 기대값은 변경하지 마."
```

#### Python 2 to 3 변환 체크리스트

| 항목 | Python 2 | Python 3 | 자동 변환 |
|------|----------|----------|---------|
| print 문 | `print "hello"` | `print("hello")` | 가능 |
| 문자열 | `unicode`, `str` | `str`, `bytes` | 주의 필요 |
| 정수 나눗셈 | `5/2 = 2` | `5/2 = 2.5` | 주의 필요 |
| range | `xrange()` | `range()` | 가능 |
| 딕셔너리 | `.iteritems()` | `.items()` | 가능 |
| 예외 처리 | `except E, e:` | `except E as e:` | 가능 |
| 입력 | `raw_input()` | `input()` | 가능 |
| 모듈 이동 | `urllib2` | `urllib.request` | 수동 확인 |
| metaclass | `__metaclass__` | `metaclass=` | 수동 확인 |

:::warning
문자열 처리(`unicode`/`str`/`bytes`)와 정수 나눗셈은 자동 변환 시 동작이 변할 수 있다. 반드시 테스트로 검증해야 한다.
:::

---

### 2.2 JavaScript에서 TypeScript로

JavaScript 프로젝트를 TypeScript로 전환하는 마이그레이션 전략이다.

#### AGENTS.md 설정

```markdown
<!-- AGENTS.md -->
# JS -> TS 마이그레이션

## 전환 규칙
- `.js` -> `.ts` (또는 `.jsx` -> `.tsx`) 파일명 변경
- `any`는 초기 단계에서 허용하되, TODO 주석 추가
- 인터페이스/타입은 해당 모듈의 types.ts에 정의
- 기존 JSDoc 주석에서 타입 정보 추출
- import 경로의 확장자 업데이트

## tsconfig.json 설정
- strict: true
- noImplicitAny: false (초기), true (최종 목표)
- allowJs: true (점진적 전환)

## 우선순위
1. 유틸리티 함수 (의존성이 적은 것부터)
2. 타입 정의 파일
3. API 레이어
4. 비즈니스 로직
5. UI 컴포넌트
```

#### 단계적 마이그레이션

```bash
# 1단계: 프로젝트 분석
codex --suggest --sandbox read-only \
  "이 JavaScript 프로젝트를 TypeScript로 전환하려고 한다.
   의존성 그래프를 분석하고, 전환 순서를 제안해줘.
   가장 의존성이 적은 모듈부터 시작."

# 2단계: 유틸리티부터 전환
codex --auto-edit \
  "src/utils/format.js를 TypeScript로 전환해줘.
   - 파일명을 format.ts로 변경
   - 함수 시그니처에 타입 추가
   - 반환 타입 명시
   - 필요한 인터페이스를 types.ts에 정의"

# 3단계: 타입 체크 및 수정
codex --auto-edit \
  "npx tsc --noEmit을 실행하고 타입 에러를 수정해줘.
   any 사용은 최소화하되, 복잡한 타입은 TODO 주석과 함께 any로 남겨둬."
```

#### 전환 전후 비교

```javascript
// 전환 전: src/utils/format.js
export function formatCurrency(amount, currency) {
  const formatter = new Intl.NumberFormat('ko-KR', {
    style: 'currency',
    currency: currency || 'KRW',
  });
  return formatter.format(amount);
}

export function formatDate(date, options) {
  if (!date) return '';
  const d = new Date(date);
  return d.toLocaleDateString('ko-KR', options);
}
```

```typescript
// 전환 후: src/utils/format.ts
interface FormatDateOptions {
  year?: 'numeric' | '2-digit';
  month?: 'numeric' | '2-digit' | 'long' | 'short' | 'narrow';
  day?: 'numeric' | '2-digit';
}

export function formatCurrency(
  amount: number,
  currency: string = 'KRW'
): string {
  const formatter = new Intl.NumberFormat('ko-KR', {
    style: 'currency',
    currency,
  });
  return formatter.format(amount);
}

export function formatDate(
  date: string | Date | null,
  options?: FormatDateOptions
): string {
  if (!date) return '';
  const d = new Date(date);
  return d.toLocaleDateString('ko-KR', options);
}
```

---

### 2.3 프레임워크 버전 업그레이드

프레임워크 메이저 버전 업그레이드도 Codex CLI로 효율적으로 수행할 수 있다.

#### React 18에서 19로 업그레이드 예시

```markdown
<!-- AGENTS.md -->
# React 18 -> 19 마이그레이션

## Breaking Changes 목록
- `ReactDOM.render` -> `createRoot`
- `forwardRef` 불필요 (ref가 일반 prop으로)
- `useContext` 사용 방식 변경
- Suspense 동작 변경

## 검증 방법
- 각 컴포넌트 수정 후 개별 테스트 실행
- Storybook 스토리가 있으면 시각적 확인
```

```bash
# 업그레이드 분석
codex --suggest --sandbox read-only \
  "package.json에서 React 버전을 확인하고,
   React 18에서 19로 업그레이드할 때 영향받는 코드를 찾아줘.
   - forwardRef 사용처
   - ReactDOM.render 사용처
   - useContext 패턴
   - 기타 deprecated API 사용처"

# 자동 수정
codex --auto-edit \
  "React 18에서 19로의 마이그레이션을 수행해줘.
   src/components/ 디렉터리의 컴포넌트들을 순서대로 수정하되,
   각 컴포넌트 수정 후 npm test를 실행해서 확인해줘."
```

#### Django 4에서 5로 업그레이드 예시

```bash
codex --auto-edit \
  "Django 4에서 5로 업그레이드하려고 한다.
   1. deprecation warning을 모두 확인해줘
   2. settings.py의 변경 필요 사항을 분석해줘
   3. URL 패턴의 변경 사항을 수정해줘
   4. 테스트를 실행하여 호환성을 검증해줘"
```

---

## 3. 대규모 리팩토링 워크플로우

### 3.1 리팩토링 계획 수립

대규모 리팩토링은 계획이 핵심이다. Codex CLI로 분석과 계획 수립부터 시작한다.

```bash
codex --suggest --sandbox read-only \
  "이 프로젝트를 분석하고 리팩토링 계획을 세워줘.

   분석 관점:
   1. 순환 의존성
   2. God Object/God Function (500줄 이상)
   3. 중복 코드 (유사도 80% 이상)
   4. 테스트 커버리지 사각지대
   5. 레이어 위반 (UI에서 직접 DB 접근 등)

   출력 형식:
   - 문제점별 심각도 (상/중/하)
   - 리팩토링 순서 제안
   - 각 단계의 예상 영향 범위"
```

### 3.2 함수 추출 패턴

거대한 함수를 작은 단위로 분리하는 작업이다.

```bash
codex --auto-edit \
  "src/services/orderService.ts의 processOrder 함수가 300줄이 넘는다.
   다음 기준으로 함수를 분리해줘:
   1. 입력 검증 -> validateOrderInput()
   2. 재고 확인 -> checkInventory()
   3. 가격 계산 -> calculateTotal()
   4. 결제 처리 -> processPayment()
   5. 주문 저장 -> saveOrder()

   각 함수는 단일 책임을 가져야 하고,
   기존 테스트가 모두 통과해야 한다."
```

### 3.3 아키텍처 레이어 분리

```bash
codex --auto-edit \
  "src/api/users.ts에 컨트롤러, 서비스, 리포지토리 로직이 섞여 있다.
   다음 구조로 분리해줘:

   src/controllers/userController.ts - HTTP 요청/응답 처리
   src/services/userService.ts - 비즈니스 로직
   src/repositories/userRepository.ts - 데이터 접근

   의존성 방향: Controller -> Service -> Repository
   각 레이어 간 인터페이스를 types/에 정의해줘."
```

### 3.4 점진적 리팩토링 전략

한 번에 모든 것을 바꾸는 것은 위험하다. Codex CLI와 함께 점진적으로 진행하는 전략이다.

```bash
# 1단계: 인터페이스 먼저 정의 (기존 코드 변경 없음)
codex --auto-edit \
  "src/services/orderService.ts의 public API를 분석하고,
   src/types/order.ts에 인터페이스를 정의해줘.
   기존 코드는 수정하지 마."

# 2단계: 새 구현 작성 (기존 코드와 병행)
codex --auto-edit \
  "src/services/orderServiceV2.ts를 새로 작성해줘.
   order.ts의 인터페이스를 구현하되,
   레이어가 분리된 새 구조로 작성해.
   기존 orderService.ts는 건드리지 마."

# 3단계: 테스트로 동치성 검증
codex --auto-edit \
  "orderService.ts와 orderServiceV2.ts의 동작이 동일한지
   검증하는 테스트를 작성해줘.
   같은 입력에 대해 같은 출력이 나와야 한다."

# 4단계: 전환
codex --auto-edit \
  "모든 테스트가 통과하면, import를 orderServiceV2로 전환하고
   기존 orderService.ts를 deprecated로 표시해줘."
```

---

## 4. 테스트 자동 생성

### 4.1 단위 테스트 생성

```bash
codex --auto-edit \
  "src/utils/ 디렉터리의 모든 .ts 파일에 대해 단위 테스트를 생성해줘.

   테스트 규칙:
   - Jest 사용
   - 각 public 함수에 최소 3개의 테스트
   - 정상 케이스, 엣지 케이스, 에러 케이스 포함
   - 테스트 이름: 'should [행위] when [조건]'
   - 파일 위치: src/utils/__tests__/[원본명].test.ts

   생성 후 npm test -- --watchAll=false로 전체 테스트 실행"
```

### 4.2 통합 테스트 생성

```bash
codex --auto-edit \
  "src/api/routes/users.ts의 엔드포인트에 대한 통합 테스트를 작성해줘.

   테스트 환경:
   - Supertest + Jest
   - 테스트 DB는 SQLite in-memory
   - 외부 서비스 (결제, 이메일)는 mock 처리

   테스트할 엔드포인트:
   - GET /api/users - 목록 조회 (페이지네이션, 필터링)
   - GET /api/users/:id - 상세 조회 (존재/미존재)
   - POST /api/users - 생성 (정상/검증 실패/중복)
   - PUT /api/users/:id - 수정 (정상/권한 없음)
   - DELETE /api/users/:id - 삭제 (정상/종속 데이터)"
```

### 4.3 테스트 커버리지 개선

```bash
codex --auto-edit \
  "npm test -- --coverage 결과를 확인하고,
   커버리지 80% 미만인 파일에 테스트를 추가해줘.
   특히 분기(branch) 커버리지에 집중해서,
   아직 테스트되지 않은 조건 분기에 대한 테스트를 작성해."
```

:::tip
테스트 생성 시 AGENTS.md에 프로젝트의 테스트 컨벤션을 상세히 기술하면, 기존 테스트와 일관된 스타일의 테스트가 생성된다.
:::

---

## 5. 코드 리뷰 자동화

### 5.1 PR 자동 리뷰

```bash
# 로컬에서 PR 리뷰
codex --suggest --sandbox read-only \
  "git diff origin/main...HEAD를 분석하고 코드 리뷰를 수행해줘.

   리뷰 관점:
   1. 버그 위험 (null 참조, 경쟁 조건, 리소스 누수)
   2. 성능 이슈 (N+1 쿼리, 불필요한 재렌더링, 메모리 누수)
   3. 보안 취약점 (SQL 인젝션, XSS, 인증 우회)
   4. 코드 품질 (DRY 위반, SOLID 위반, 복잡도)
   5. 테스트 충분성 (새 코드에 테스트가 있는지)

   각 이슈에 대해:
   - 파일명과 줄 번호
   - 심각도 (Critical/Major/Minor/Suggestion)
   - 문제 설명
   - 수정 제안"
```

### 5.2 보안 감사

```bash
codex --suggest --sandbox read-only \
  "이 프로젝트의 보안 감사를 수행해줘.

   검사 항목:
   1. 인증/인가 로직의 취약점
   2. 입력 검증 누락 (SQL 인젝션, XSS, SSRF)
   3. 하드코딩된 비밀 정보 (API 키, 비밀번호)
   4. 안전하지 않은 의존성 (npm audit 기반)
   5. CORS 설정 검토
   6. 암호화 관련 이슈 (약한 해시, 평문 저장)
   7. 에러 메시지의 정보 노출

   결과를 심각도별로 정리하고, 각 항목에 수정 방법을 제안해줘."
```

### 5.3 성능 분석

```bash
codex --suggest --sandbox read-only \
  "이 프로젝트의 성능 병목 가능 지점을 분석해줘.

   분석 대상:
   1. 데이터베이스 쿼리 (N+1, 인덱스 미사용)
   2. API 응답 시간 (불필요한 데이터 페치)
   3. 프론트엔드 렌더링 (불필요한 리렌더링)
   4. 메모리 사용 (대용량 배열, 미해제 리소스)
   5. 네트워크 (불필요한 API 호출, 캐싱 미적용)"
```

---

## 6. 실전 시나리오

### 6.1 시나리오: Express에서 Fastify로 전환

```markdown
<!-- AGENTS.md -->
# Express -> Fastify 마이그레이션

## 전환 규칙
- express.Router -> fastify.register (plugin)
- req.body -> request.body (JSON Schema 검증 추가)
- res.json() -> reply.send()
- middleware -> hook (onRequest, preHandler 등)
- express-validator -> @sinclair/typebox + ajv

## 유지 사항
- API 스펙 (경로, 메서드, 응답 형식) 동일하게 유지
- 기존 통합 테스트가 모두 통과해야 함
```

```bash
# 1단계: 라우트 매핑 분석
codex --suggest --sandbox read-only \
  "현재 Express 라우트를 분석하고,
   Fastify 플러그인 구조로의 매핑 계획을 세워줘."

# 2단계: 플러그인 단위로 전환
codex --auto-edit \
  "src/routes/users.ts를 Express에서 Fastify 플러그인으로 전환해줘.
   JSON Schema를 사용한 입력 검증을 추가하고,
   기존 테스트가 통과하는지 확인해줘."

# 3단계: 미들웨어 전환
codex --auto-edit \
  "src/middleware/auth.ts를 Fastify 데코레이터/훅으로 전환해줘.
   onRequest 훅으로 인증을 처리하고,
   preHandler로 권한 검사를 수행하는 구조로 변경해줘."
```

### 6.2 시나리오: 모놀리스에서 모듈 분리

```bash
# 분석 단계
codex --suggest --sandbox read-only \
  "이 모놀리스 프로젝트에서 독립적으로 분리할 수 있는 모듈을 식별해줘.
   각 모듈의 경계, 의존성, 데이터 공유 지점을 분석해줘."

# 모듈 경계 정의
codex --auto-edit \
  "주문(Order) 모듈을 분리하려고 한다.
   1. src/modules/order/ 디렉터리를 생성
   2. 주문 관련 코드를 해당 디렉터리로 이동
   3. 모듈 간 의존성은 인터페이스로 추상화
   4. 모듈 내부 의존성과 외부 의존성을 명확히 분리
   5. 기존 import 경로를 모두 업데이트"
```

### 6.3 시나리오: 데이터베이스 ORM 전환

```bash
codex --auto-edit \
  "Sequelize에서 Prisma로 ORM을 전환하려고 한다.

   단계:
   1. 현재 Sequelize 모델 분석
   2. prisma/schema.prisma 생성
   3. 리포지토리 레이어를 Prisma 클라이언트로 재작성
   4. 마이그레이션 파일 생성
   5. 기존 테스트 수정 및 검증

   주의: 데이터 마이그레이션은 하지 않는다. 코드 전환만 수행한다."
```

---

## 7. Claude Code, Gemini CLI와의 비교

Codex CLI를 다른 주요 AI 코딩 도구와 비교하여 각각의 강점과 적합한 사용 시나리오를 정리한다.

### 7.1 핵심 비교

| 항목 | Codex CLI | Claude Code | Gemini CLI |
|------|-----------|-------------|-----------|
| 개발사 | OpenAI | Anthropic | Google |
| 기반 언어 | Rust | TypeScript | TypeScript |
| 라이선스 | Apache-2.0 | 상용 | Apache-2.0 |
| 기본 모델 | codex-mini-latest | Claude Sonnet/Opus | Gemini 2.5 Pro |
| 샌드박스 | 플랫폼 네이티브 (Seatbelt/Landlock) | 컨테이너 기반 | Docker 기반 |
| 컨텍스트 윈도우 | 모델별 상이 | 200K 토큰 | 1M 토큰 |
| 코드 수정 | apply_patch (diff) | Edit tool | File edit |
| 무료 사용 | ChatGPT Plus 포함 | 유료 (API 키 또는 구독) | 무료 티어 있음 |
| MCP 지원 | 지원 | 지원 | 지원 |

### 7.2 강점별 비교

#### 안전성 (Codex CLI 우세)

Codex CLI의 가장 큰 강점은 **플랫폼 네이티브 샌드박스**다. OS 커널 수준에서 에이전트의 행동을 제한하므로, 컨테이너 기반 격리보다 오버헤드가 적고 탈출이 어렵다.

```text
Codex CLI: OS 커널 -> Seatbelt/Landlock -> 에이전트
Claude Code: Docker 컨테이너 -> 에이전트
Gemini CLI: Docker 컨테이너 -> 에이전트
```

3단계 승인 정책(suggest/auto-edit/full-auto)과 세분화된 샌드박스 모드(read-only/workspace-write/danger-full-access)의 조합으로 작업별 최적의 보안 수준을 설정할 수 있다.

#### 코드 일관성 (Claude Code 우세)

Claude Code는 **멀티파일 추론** 능력이 뛰어나다. 대규모 프로젝트에서 여러 파일에 걸친 변경을 일관되게 수행하는 데 강점이 있다. 코드베이스 전체를 자동으로 탐색하여 맥락을 파악하는 "에이전틱 검색" 기능이 특히 유용하다.

```bash
# Claude Code의 강점이 드러나는 작업
# 여러 파일에 걸친 인터페이스 변경
"User 인터페이스에 avatar 필드를 추가하고,
 이를 사용하는 모든 컴포넌트, API, 테스트를 수정해줘"
```

#### 대규모 컨텍스트 (Gemini CLI 우세)

Gemini CLI는 **1M 토큰 컨텍스트 윈도우**를 가지고 있어, 대규모 코드베이스를 한 번에 더 많이 볼 수 있다. 또한 Google Search를 통한 실시간 정보 접근이 가능하여 최신 API 문서나 모범 사례를 반영한 코드를 생성할 수 있다.

#### 비용 효율성

| 도구 | 무료 사용 | 최소 비용 |
|------|----------|----------|
| Codex CLI | ChatGPT Plus($20/월) 포함 | $20/월 (API: 종량제) |
| Claude Code | 없음 | Claude Pro($20/월) 또는 API 종량제 |
| Gemini CLI | 무료 티어 있음 | 무료 (제한적) |

### 7.3 사용 시나리오별 권장 도구

| 시나리오 | 권장 도구 | 이유 |
|---------|----------|------|
| CI/CD 자동화 | **Codex CLI** | 네이티브 샌드박스, full-auto 모드 |
| 대규모 리팩토링 | **Claude Code** | 멀티파일 추론, 일관된 변경 |
| 코드 탐색/학습 | **Gemini CLI** | 넓은 컨텍스트, 무료 티어 |
| 보안 감사 | **Codex CLI** | read-only 샌드박스, 안전한 분석 |
| 새 프로젝트 설정 | **Gemini CLI** | 최신 모범 사례 반영 (Google Search) |
| 레거시 마이그레이션 | **Codex CLI** / **Claude Code** | 안전한 점진적 수정 / 일관된 변경 |
| 테스트 생성 | 세 도구 모두 | 패턴화된 작업이므로 차이 적음 |

### 7.4 실용적 조합 전략

많은 개발자가 하나의 도구만 사용하기보다 상황에 따라 여러 도구를 조합한다.

```bash
# 1. Gemini CLI로 대규모 코드 분석 (넓은 컨텍스트)
gemini "이 프로젝트 전체를 분석하고 리팩토링 계획을 세워줘"

# 2. Claude Code로 복잡한 멀티파일 변경 수행
claude "리팩토링 계획에 따라 서비스 레이어를 분리해줘"

# 3. Codex CLI로 CI 파이프라인에서 자동 검증
codex exec --full-auto --sandbox workspace-write \
  "테스트를 실행하고 실패하는 부분을 수정해줘"
```

:::tip
도구 선택에 정답은 없다. 각 도구의 강점을 파악하고, 작업의 성격에 맞게 선택하는 것이 중요하다. Codex CLI는 특히 **안전성이 중요한 자동화 작업**과 **CI/CD 통합**에서 강점을 보인다.
:::

---

## 8. 마이그레이션 체크리스트

레거시 마이그레이션 프로젝트에서 공통으로 사용할 수 있는 체크리스트다.

### 마이그레이션 전

- [ ] 현재 코드의 테스트 커버리지 확인 (80% 이상 권장)
- [ ] 테스트가 부족한 모듈에 테스트 추가
- [ ] AGENTS.md에 마이그레이션 규칙 정의
- [ ] Git 브랜치 전략 수립 (feature 브랜치 per 모듈)
- [ ] 마이그레이션 순서 결정 (의존성이 적은 것부터)
- [ ] 롤백 계획 수립

### 마이그레이션 중

- [ ] 파일/모듈 단위로 진행
- [ ] 각 변경 후 테스트 실행
- [ ] 변경마다 의미 있는 커밋 (롤백 용이)
- [ ] 정기적으로 통합 테스트 실행
- [ ] 변경 로그 기록

### 마이그레이션 후

- [ ] 전체 테스트 스위트 통과 확인
- [ ] 성능 벤치마크 비교 (전후)
- [ ] 보안 스캔 실행
- [ ] 코드 리뷰 (자동 + 수동)
- [ ] 문서 업데이트
- [ ] 모니터링 설정 (배포 후)

---

## 마무리

이 글에서 다룬 실전 전략을 정리하면:

| 주제 | 핵심 포인트 |
|------|-----------|
| AGENTS.md 설계 | 마이그레이션 규칙, 안전장치, 검증 단계 명시 |
| Python 2->3 | 자동 변환 가능 항목 + 수동 검증 필요 항목 구분 |
| JS->TS | 점진적 전환, allowJs 활용, 의존성 순서 |
| 프레임워크 업그레이드 | Breaking Changes 목록화, 단계적 적용 |
| 대규모 리팩토링 | 인터페이스 우선 정의, 점진적 전환, 동치성 검증 |
| 테스트 생성 | 함수별 3+개 케이스, 엣지/에러 포함 |
| 도구 비교 | Codex CLI(안전성), Claude Code(일관성), Gemini CLI(컨텍스트) |

이것으로 **Codex CLI Guide** 시리즈를 마친다. Codex CLI는 Rust 기반의 뛰어난 성능과 플랫폼 네이티브 샌드박스라는 강점을 가진 AI 코딩 에이전트다.
