<!-- infographic-hero -->
![Gemini CLI Workflow Design 핵심 요약](figures/infographic.svg)

*Figure: Gemini CLI Workflow Design 한 장 요약 인포그래픽*

# Gemini CLI 실전: 프로젝트 적용 사례

:::info
이 글은 **Gemini CLI Guide** 시리즈의 마지막 글이다. 시리즈 전체 목차:
1. [[gemini-cli-guide-01-setup|설치와 기본 사용법]]
2. [[gemini-cli-guide-02-core|핵심 기능: 도구 시스템과 확장]]
3. [[gemini-cli-guide-03-advanced|고급 활용: Google 생태계 통합]]
4. **실전: 프로젝트 적용 사례** (현재 글)
:::

지금까지 Gemini CLI의 설치, 핵심 기능, 고급 활용법을 살펴보았다. 이 마지막 글에서는 실제 프로젝트에 Gemini CLI를 어떻게 적용하는지 구체적인 사례와 함께 다룬다. GEMINI.md 설계 패턴, Git 워크플로우, CI/CD 통합, 팀 협업, 그리고 Claude Code와의 비교까지 - 실전에서 필요한 모든 내용을 정리한다.

---

## 1. GEMINI.md 설계 패턴과 베스트 프랙티스

GEMINI.md는 Gemini CLI의 동작을 결정하는 핵심 파일이다. 잘 설계된 GEMINI.md는 AI의 코드 품질을 극적으로 향상시킨다.

### 패턴 1: 계층적 구조

글로벌, 프로젝트, 모듈별로 GEMINI.md를 분리하여 관심사를 분리한다.

```text
~/.gemini/GEMINI.md                    # 글로벌: 개인 코딩 스타일
프로젝트루트/GEMINI.md                   # 프로젝트: 아키텍처, 규칙
프로젝트루트/backend/GEMINI.md           # 백엔드: Django 규칙
프로젝트루트/frontend/GEMINI.md          # 프론트엔드: React 규칙
프로젝트루트/infrastructure/GEMINI.md    # 인프라: Terraform 규칙
```

#### 글로벌 GEMINI.md 예시

```markdown
# 글로벌 개발 지침

## 언어
- 코드 주석과 커밋 메시지는 한국어로 작성
- 변수/함수명은 영어 사용

## 코딩 스타일
- 함수는 단일 책임 원칙을 따름
- 매직 넘버 대신 상수 사용
- 에러 핸들링은 명시적으로 수행
```

#### 프로젝트 GEMINI.md 예시

```markdown
# blog-jun 프로젝트

## 아키텍처
- Backend: Django 5 + DRF (config/settings 분리: base/dev/prod)
- Frontend: React 19 + Vite + Tailwind CSS v4 + Framer Motion
- Database: PostgreSQL 15 with pgvector
- Infra: Docker Compose + Cloudflare Tunnel

## 디렉토리 구조
@.gemini/directory-structure.md

## 코딩 컨벤션
@.gemini/coding-conventions.md

## API 규칙
- RESTful 원칙 준수
- 모든 응답은 { data, error, meta } 형식
- 인증: JWT (access + refresh token)
- 페이지네이션: cursor-based

## 테스트 규칙
- 새 기능에는 반드시 테스트 작성
- 커버리지 80% 이상 유지
- 테스트 파일은 __tests__/ 디렉토리에 배치
```

### 패턴 2: 모듈화와 임포트

GEMINI.md가 길어지면 `@path` 구문으로 분리한다.

```markdown
# 프로젝트 지침

@.gemini/architecture.md
@.gemini/coding-style.md
@.gemini/testing-guide.md
@.gemini/deployment-guide.md
@.gemini/security-checklist.md
```

각 파일은 특정 주제에 집중한다.

```markdown
# .gemini/security-checklist.md

## 보안 체크리스트
- SQL 쿼리에 ORM 사용, raw SQL 금지
- 사용자 입력은 반드시 검증
- 비밀번호는 bcrypt로 해싱
- API 키는 환경 변수로 관리
- CORS 설정은 허용 도메인만 명시
- 파일 업로드시 확장자와 크기 검증
```

### 패턴 3: 금지 사항 명시

AI가 하지 말아야 할 것을 명확히 지정한다.

```markdown
## 절대 금지
- node_modules/, .env, credentials.json 파일 수정 금지
- main 브랜치에 직접 커밋 금지
- 기존 데이터베이스 마이그레이션 파일 수정 금지
- console.log 디버깅 코드 커밋 금지
- any 타입 사용 금지 (TypeScript)
```

### 패턴 4: 출력 형식 지정

AI의 응답 형식을 지정하여 일관성을 유지한다.

```markdown
## 코드 변경 보고 형식
변경을 완료하면 다음 형식으로 보고할 것:

### 변경 요약
- 변경한 파일 목록
- 각 변경의 이유

### 테스트 결과
- 실행한 테스트 명령어
- 통과/실패 결과

### 주의 사항
- 추가로 필요한 작업 (마이그레이션, 환경 변수 등)
```

---

## 2. Git 워크플로우

### 커밋 메시지 생성

```bash
# 스테이징된 변경사항으로 커밋 메시지 생성
gemini> git diff --staged를 보고 Conventional Commits 형식으로 커밋 메시지를 작성해줘
```

커스텀 명령어로 자동화할 수 있다.

```toml
# ~/.gemini/commands/commit.toml
[command]
name = "commit"
description = "커밋 메시지 생성 및 커밋"

[prompt]
template = """
현재 스테이징된 변경사항을 분석하고 Conventional Commits 형식의 커밋 메시지를 생성해줘.
형식: <type>(<scope>): <description>

변경사항:
```
{{shell "git diff --staged"}}
```

커밋 메시지를 생성한 후 `git commit -m "메시지"` 명령으로 커밋까지 수행해줘.
"""
```

### PR 생성 및 설명 작성

```bash
gemini> 현재 브랜치의 모든 커밋을 분석하고 GitHub PR을 생성해줘.
       PR 제목과 설명을 자동으로 작성하고,
       변경사항 요약, 테스트 계획, 리뷰 포인트를 포함해줘.
```

### 코드 리뷰

```bash
# 특정 PR의 변경사항 리뷰
gemini> git diff main...feature/auth-refactor를 코드 리뷰해줘.
       보안, 성능, 가독성 관점에서 분석하고 개선점을 제시해줘.
```

### Git 워크플로우 자동화 시나리오

```bash
# 1. 기능 브랜치 생성부터 PR까지 자동화
gemini> 다음 작업을 수행해줘:
1. feature/user-profile 브랜치 생성
2. UserProfile 컴포넌트 구현 (props: name, email, avatar)
3. 유닛 테스트 작성
4. 린트 실행
5. 커밋 메시지 작성 후 커밋
```

---

## 3. CI/CD 통합

### GitHub Actions - Gemini CLI Action

Google은 공식 GitHub Action인 `google-github-actions/run-gemini-cli`를 제공한다. 이를 통해 PR 리뷰, 이슈 분류, 코드 분석 등을 자동화할 수 있다.

#### PR 자동 리뷰 워크플로우

```yaml
# .github/workflows/gemini-review.yml
name: Gemini PR Review

on:
  pull_request:
    types: [opened, synchronize]

permissions:
  contents: read
  pull-requests: write

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Gemini Code Review
        uses: google-github-actions/run-gemini-cli@v1
        with:
          prompt: |
            이 PR의 변경사항을 리뷰해줘.
            보안 취약점, 성능 이슈, 코딩 컨벤션 위반을 확인하고
            개선 제안을 PR 코멘트로 작성해줘.
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
```

#### 이슈 자동 분류 워크플로우

```yaml
# .github/workflows/gemini-triage.yml
name: Gemini Issue Triage

on:
  issues:
    types: [opened]

permissions:
  issues: write

jobs:
  triage:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Triage Issue
        uses: google-github-actions/run-gemini-cli@v1
        with:
          prompt: |
            새로 생성된 이슈를 분석하고:
            1. 적절한 라벨을 추가 (bug, feature, docs, question)
            2. 우선순위를 판단 (P0-P3)
            3. 관련 코드 영역을 파악하여 코멘트 작성
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
```

#### @gemini-cli 멘션

이슈나 PR에서 `@gemini-cli`를 멘션하면 Gemini CLI가 응답한다.

```markdown
<!-- PR 코멘트에서 -->
@gemini-cli 이 함수의 시간 복잡도를 분석해줘
@gemini-cli 이 변경사항에 대한 유닛 테스트를 제안해줘
```

### 인증 방법

CI/CD 환경에서의 인증 옵션은 다음과 같다.

| 방법 | 보안 수준 | 설정 복잡도 | 권장 용도 |
|------|-----------|------------|-----------|
| API 키 (`GEMINI_API_KEY`) | 보통 | 쉬움 | 개인 프로젝트, 빠른 설정 |
| Workload Identity Federation | 높음 | 중간 | 프로덕션, 팀 프로젝트 |
| GitHub App (커스텀) | 높음 | 높음 | 엔터프라이즈 |

:::tip
프로덕션 환경에서는 Workload Identity Federation을 권장한다. API 키 관리의 부담이 없고, 키 유출 위험도 없다.
:::

### Headless 모드 활용

CI/CD 파이프라인에서는 headless 모드(`-p` 플래그)를 사용한다.

```bash
# CI 스크립트에서 코드 품질 체크
gemini -p "src/ 디렉토리의 코드를 분석하고 잠재적 버그를 리포트해줘" \
  --yolo \
  > quality-report.md

# 테스트 결과 분석
npm test 2>&1 | gemini -p "테스트 결과를 분석하고 실패 원인을 요약해줘"
```

---

## 4. 대규모 프로젝트 전략

### 컨텍스트 윈도우 관리

100만 토큰의 컨텍스트 윈도우는 넉넉하지만, 대규모 프로젝트에서는 전략적 관리가 필요하다.

```markdown
# GEMINI.md - 대규모 프로젝트 설정

## 컨텍스트 관리 규칙
- 전체 프로젝트를 한번에 읽지 말 것
- 작업에 관련된 모듈만 분석할 것
- codebase_investigator 도구를 활용하여 관련 코드를 체계적으로 탐색할 것

## 모듈 경계
- auth/: 인증/인가 (독립)
- api/: REST API 엔드포인트 (auth 의존)
- core/: 비즈니스 로직 (독립)
- infra/: 인프라 설정 (독립)
```

### /compress 활용

대화가 길어지면 `/compress`로 컨텍스트를 압축한다.

```bash
# 긴 디버깅 세션 후
gemini> /compress
# 대화 내용이 요약으로 대체되어 토큰 절약
# 이후 작업은 요약된 컨텍스트 위에서 진행
```

### 모노레포 전략

모노레포에서는 서브 디렉토리별 GEMINI.md를 활용한다.

```text
monorepo/
  GEMINI.md              # 공통 규칙
  packages/
    api/
      GEMINI.md          # API 패키지 규칙
    web/
      GEMINI.md          # 웹 프론트엔드 규칙
    shared/
      GEMINI.md          # 공유 라이브러리 규칙
```

각 패키지의 GEMINI.md는 해당 디렉토리에서 작업할 때만 로드된다.

---

## 5. 팀 협업 패턴

### GEMINI.md를 코드 리뷰에 포함

GEMINI.md는 Git에 커밋하여 팀 전체가 공유한다. GEMINI.md의 변경도 코드 리뷰 대상이다.

```bash
# GEMINI.md 변경사항도 PR에 포함
git add GEMINI.md .gemini/
git commit -m "docs: GEMINI.md에 새 API 규칙 추가"
```

### 팀 표준 설정 공유

팀 전체가 사용할 표준 설정을 `.gemini/` 디렉토리에 관리한다.

```text
.gemini/
  settings.json          # 프로젝트 설정 (승인 모드, MCP 서버 등)
  GEMINI.md              # 프로젝트 컨텍스트
  commands/              # 공유 커스텀 명령어
    review.toml
    commit.toml
    test-gen.toml
  sandbox.Dockerfile     # 프로젝트 샌드박스 환경
```

### 신규 팀원 온보딩

새로운 팀원이 합류하면 Gemini CLI를 통해 프로젝트를 빠르게 파악할 수 있다.

```bash
# 프로젝트 개요 파악
gemini> 이 프로젝트의 전체 구조와 아키텍처를 설명해줘

# 특정 기능의 동작 방식 이해
gemini> 사용자 인증 흐름을 처음부터 끝까지 추적해줘

# 개발 환경 셋업 도움
gemini> 이 프로젝트의 개발 환경을 셋업하는 과정을 안내해줘
```

### PR 리뷰 가이드라인 통합

```markdown
# .gemini/GEMINI.md - 코드 리뷰 섹션

## PR 리뷰 기준
코드 리뷰를 요청받으면 다음 항목을 확인할 것:

### 필수 체크
- [ ] 타입 안전성 확보 (any 사용 여부)
- [ ] 에러 핸들링 존재 여부
- [ ] SQL 인젝션 등 보안 취약점
- [ ] 테스트 코드 포함 여부

### 권장 체크
- [ ] 함수 길이 (50줄 이내)
- [ ] 순환 복잡도 (10 이하)
- [ ] 주석 적절성
- [ ] 불필요한 의존성 추가 여부
```

---

## 6. 실전 시나리오

### 시나리오 1: 새 기능 개발

REST API에 새 엔드포인트를 추가하는 전체 과정이다.

```bash
# 1단계: 요구사항 분석
gemini> 사용자 프로필 CRUD API를 구현해야 해.
       기존 API 패턴을 분석하고, 동일한 패턴으로 구현 계획을 세워줘.

# 2단계: 구현
gemini> 계획대로 UserProfile 모델, 시리얼라이저, 뷰셋, URL을 구현해줘.
       기존 코드 스타일과 일관되게 작성해줘.

# 3단계: 테스트
gemini> 방금 구현한 UserProfile API에 대한 유닛 테스트와 통합 테스트를 작성해줘.
       기존 테스트 패턴을 따르고, 엣지 케이스도 포함해줘.

# 4단계: 검증
gemini> 테스트를 실행하고, 린트를 돌리고, 모든 것이 통과하는지 확인해줘.
       실패하는 것이 있으면 수정해줘.

# 5단계: 커밋
gemini> 모든 변경사항을 확인하고 적절한 커밋 메시지를 작성해서 커밋해줘.
```

### 시나리오 2: 버그 수정

프로덕션에서 발견된 버그를 추적하고 수정한다.

```bash
# 에러 로그 분석
cat /var/log/app/error.log | gemini -p "이 에러 로그에서 반복되는 패턴을 찾고
루트 원인을 추정해줘"

# 대화형 모드로 디버깅
gemini> 에러 로그에서 "ConnectionResetError"가 반복적으로 발생하고 있어.
       관련 코드를 찾고, 원인을 분석하고, 수정안을 제시해줘.

# 수정 후 회귀 테스트
gemini> 수정한 코드가 기존 테스트를 통과하는지 확인하고,
       이 버그에 대한 회귀 테스트도 추가해줘.
```

### 시나리오 3: 리팩토링

기존 코드를 개선한다.

```bash
gemini> src/services/UserService.ts를 리팩토링해줘.
       다음 문제를 해결해야 해:
       1. 함수가 너무 길다 (300줄 이상)
       2. 중복 코드가 많다
       3. 에러 핸들링이 일관되지 않다
       4. 테스트가 없다

       단계별로 진행하고, 각 단계에서 기존 기능이 유지되는지 확인해줘.
```

### 시나리오 4: 문서 생성

```bash
gemini> src/api/ 디렉토리의 모든 엔드포인트를 분석하고
       OpenAPI 3.0 스펙 문서를 생성해줘.
       각 엔드포인트의 요청/응답 형식, 인증 요구사항, 에러 코드를 포함해줘.
```

### 시나리오 5: 마이그레이션

```bash
gemini> 이 프로젝트를 JavaScript에서 TypeScript로 마이그레이션해야 해.
       다음 순서로 진행해줘:
       1. tsconfig.json 설정
       2. 타입 패키지 설치
       3. 공통 타입 정의
       4. 파일별 순차 변환 (의존성이 없는 유틸리티부터)
       5. 각 변환 후 테스트 확인
```

---

## 7. Claude Code와의 비교 및 사용 분담 전략

Gemini CLI와 Claude Code는 모두 터미널 AI 코딩 에이전트지만 각각의 강점이 다르다. 상황에 따라 적절한 도구를 선택하면 생산성을 극대화할 수 있다.

### 핵심 비교

| 항목 | Gemini CLI | Claude Code |
|------|-----------|-------------|
| **개발사** | Google (오픈소스) | Anthropic (독점) |
| **라이선스** | Apache-2.0 | 독점 라이선스 |
| **기본 모델** | Gemini 2.5 Pro / 3 Flash | Claude Sonnet 4.6 / Opus 4.6 |
| **컨텍스트** | 100만 토큰 | 100만 토큰 |
| **무료 사용** | 일 1,000회 (Google 계정) | 없음 (유료 구독 필요) |
| **에코시스템** | Google Cloud, Vertex AI | Anthropic API |
| **MCP 지원** | 완전 지원 | 완전 지원 |
| **샌드박스** | Seatbelt, Docker | 제한적 |
| **오픈소스** | 전체 소스 공개 | 비공개 |

### 각 도구의 강점

#### Gemini CLI가 유리한 경우

```text
- Google Cloud 프로젝트 (GCP, BigQuery, Cloud Run 등)
- 무료 사용이 중요한 경우
- 웹 검색이 빈번한 작업
- 멀티모달 입력이 필요한 경우
- 오픈소스 투명성이 필요한 경우
- Cloud Shell에서 바로 사용할 때
```

#### Claude Code가 유리한 경우

```text
- 복잡한 멀티파일 리팩토링
- 정교한 코드 생성 (코드 품질)
- 높은 자율성이 필요한 대규모 작업
- AWS/Azure 환경
- 장시간 에이전틱 세션
```

### 사용 분담 전략

두 도구를 함께 사용하는 전략이다.

| 작업 | 권장 도구 | 이유 |
|------|-----------|------|
| 빠른 질문/탐색 | Gemini CLI | 무료, 빠른 응답 |
| 최신 정보 조회 | Gemini CLI | Google Search 통합 |
| 새 기능 구현 | Claude Code | 높은 코드 품질 |
| 대규모 리팩토링 | Claude Code | 멀티파일 처리 우수 |
| 코드 리뷰 | Gemini CLI | 무료로 충분 |
| GCP 인프라 작업 | Gemini CLI | 네이티브 통합 |
| CI/CD 자동화 | Gemini CLI | 공식 GitHub Action |
| 디버깅/분석 | 둘 다 | 상황에 따라 |
| 문서 생성 | 둘 다 | 상황에 따라 |

### 프로젝트 설정 파일 병행

두 도구를 모두 사용하는 프로젝트에서는 양쪽 설정 파일을 모두 관리한다.

```text
프로젝트루트/
  GEMINI.md           # Gemini CLI 설정
  CLAUDE.md           # Claude Code 설정
  .gemini/
    settings.json     # Gemini CLI 동작 설정
  .claude/
    settings.json     # Claude Code 동작 설정
```

두 파일의 내용은 각 도구에 맞는 형식이지만, 핵심 규칙(코딩 컨벤션, 아키텍처 원칙 등)은 동일하게 유지해야 한다. 공통 규칙을 별도 파일로 분리하고 각각에서 임포트하는 것도 방법이다.

---

## 8. 실전 팁 모음

### 성능 최적화

```bash
# 토큰 사용량 모니터링
gemini> /stats

# 대화가 길어지면 압축
gemini> /compress

# 새로운 작업은 새 세션에서
gemini> /clear
```

### 안전한 사용

```bash
# 프로덕션 코드에서는 기본 승인 모드 사용
gemini  # default 모드

# 실험적 작업에서는 YOLO + 샌드박스
gemini --yolo --sandbox

# 중요한 작업 전에 체크포인팅 확인
gemini> /settings set checkpointing.enabled true
```

### 효과적인 프롬프팅

| 비효율적 | 효율적 |
|----------|--------|
| "코드 고쳐줘" | "UserService.ts의 getUser 함수에서 null 체크가 누락되어 있어. 수정해줘" |
| "테스트 만들어줘" | "UserService의 createUser 함수에 대한 유닛 테스트를 Jest로 작성해줘. 성공/실패/중복 이메일 케이스를 포함해줘" |
| "리팩토링해줘" | "auth.ts의 authenticateUser 함수를 토큰 검증과 사용자 조회로 분리하고, 각각에 대한 에러 핸들링을 추가해줘" |

### 디버깅 워크플로우

```bash
# 1. 에러 재현
gemini> npm test를 실행해줘

# 2. 에러 분석
gemini> 실패한 테스트의 원인을 분석해줘

# 3. 관련 코드 탐색
gemini> 원인이 되는 함수의 호출 체인을 추적해줘

# 4. 수정 및 검증
gemini> 수정하고 테스트를 다시 실행해줘
```

### .gitignore 설정

Gemini CLI 관련 파일 중 Git에 포함하지 않을 것들을 설정한다.

```gitignore
# .gitignore에 추가

# Gemini CLI 로컬 설정 (개인별)
.gemini/settings.local.json

# 세션 데이터
.gemini/tmp/

# 로컬 메모리
.gemini/memory/
```

반면 다음은 Git에 포함해야 한다.

```text
# Git에 커밋
GEMINI.md                     # 프로젝트 컨텍스트
.gemini/settings.json         # 공유 설정
.gemini/commands/             # 공유 커스텀 명령어
.gemini/sandbox.Dockerfile    # 샌드박스 설정
```

---

## 9. 종합 워크플로우 예시

하나의 기능을 처음부터 끝까지 Gemini CLI로 개발하는 전체 워크플로우를 정리한다.

```bash
# === 프로젝트 준비 ===
cd my-project
gemini

# 1. 프로젝트 파악
gemini> 이 프로젝트의 구조와 아키텍처를 설명해줘

# 2. 기능 브랜치 생성
gemini> git checkout -b feature/notification-system

# === 설계 ===
# 3. 기존 패턴 분석
gemini> 기존의 모델-시리얼라이저-뷰셋 패턴을 분석하고,
       알림 시스템 설계안을 제시해줘

# === 구현 ===
# 4. 모델 구현
gemini> 설계안에 따라 Notification 모델을 구현해줘

# 5. API 구현
gemini> Notification API 엔드포인트를 구현해줘
       (목록 조회, 읽음 처리, 삭제)

# 6. 테스트 작성
gemini> 구현한 API에 대한 테스트를 작성하고 실행해줘

# === 검증 ===
# 7. 린트 및 타입 체크
gemini> lint와 type check를 실행하고 문제가 있으면 수정해줘

# 8. 모든 테스트 실행
gemini> 전체 테스트 스위트를 실행해서 회귀 문제가 없는지 확인해줘

# === 마무리 ===
# 9. 커밋 및 푸시
gemini> 변경사항을 적절한 커밋으로 나누어 커밋하고 푸시해줘

# 10. 세션 저장
gemini> /chat save notification-feature
```

---

## 10. 정리 - 시리즈 마무리

이 시리즈에서 다룬 전체 내용을 요약한다.

### 시리즈 요약

| 글 | 핵심 내용 |
|----|-----------|
| [[gemini-cli-guide-01-setup\|1편: 설치와 기본 사용법]] | npm 설치, 인증, 실행 모드, 슬래시 명령어 |
| [[gemini-cli-guide-02-core\|2편: 핵심 기능]] | 빌트인 도구 13가지, Extensions, 샌드박스, Hooks |
| [[gemini-cli-guide-03-advanced\|3편: 고급 활용]] | Vertex AI, MCP 서버, Extension 개발, 멀티모달 |
| 4편: 실전 (현재 글) | GEMINI.md 패턴, CI/CD, 팀 협업, 비교 분석 |

### Gemini CLI를 선택해야 하는 이유

1. **무료**: 개인 Google 계정으로 일 1,000회 무료 사용
2. **오픈소스**: Apache-2.0, 완전한 투명성
3. **Google 통합**: Cloud Shell, Vertex AI, BigQuery 등 네이티브 연동
4. **확장성**: MCP 기반 무한 확장
5. **안전성**: 샌드박스, Hooks, 체크포인팅으로 안전한 사용

### 주의할 점

1. **YOLO 모드 남용 금지**: 반드시 샌드박스와 함께 사용
2. **GEMINI.md 관리**: 팀과 공유하고 코드 리뷰에 포함
3. **컨텍스트 관리**: 대화가 길어지면 `/compress` 또는 `/clear` 활용
4. **비밀 정보 주의**: API 키, 인증 정보는 환경 변수로 관리

이것으로 **Gemini CLI Guide** 시리즈를 마친다. Gemini CLI는 Google 생태계와의 긴밀한 통합과 오픈소스라는 강점을 가진 강력한 AI 코딩 에이전트다.
