# Codex CLI 고급 활용: 자동화와 CI 통합

:::info
이 글은 **Codex CLI Guide** 시리즈의 세 번째 글이다. 시리즈 전체 목차:
1. [[codex-guide-01-setup|설치와 기본 사용법]]
2. [[codex-guide-02-core|핵심 기능: 샌드박스와 코드 생성]]
3. **고급 활용: 자동화와 CI 통합** (현재 글)
4. [[codex-guide-04-workflow|실전: 레거시 마이그레이션]]
:::

이전 글에서 Codex CLI의 샌드박스와 코드 생성 메커니즘을 분석했다. 이번 글에서는 full-auto 모드를 활용한 자동화, GitHub Actions 통합, 그리고 팀 환경에서의 고급 설정을 다룬다.

---

## 1. full-auto 모드 심층 분석

### 1.1 full-auto 모드의 동작 원리

`full-auto` 모드는 모든 도구 호출을 자동으로 승인한다. 파일 수정, 셸 명령 실행, 그리고 설정에 따라 네트워크 접근까지 사용자 개입 없이 수행된다.

```bash
# full-auto 모드로 실행
codex --full-auto "린트 에러를 수정하고 테스트를 통과시켜줘"

# 또는 codex exec 사용 (비대화형 실행에 더 적합)
codex exec --full-auto --sandbox workspace-write \
  "모든 TypeScript 에러를 수정해줘"
```

full-auto 모드에서 에이전트의 행동 패턴:

```text
[자동] shell: npx tsc --noEmit 2>&1
[자동] 에러 3개 발견, 파일 분석 중...
[자동] read_file: src/api/handler.ts
[자동] apply_patch: src/api/handler.ts (타입 에러 수정)
[자동] read_file: src/utils/format.ts
[자동] apply_patch: src/utils/format.ts (타입 에러 수정)
[자동] shell: npx tsc --noEmit 2>&1
[자동] 컴파일 성공 확인
[완료] 3개의 TypeScript 에러를 수정했습니다.
```

### 1.2 full-auto 모드의 안전장치

full-auto라 해도 무제한 자유가 주어지는 것은 아니다. 샌드박스가 핵심 안전장치 역할을 한다.

| 안전장치 | 설명 |
|---------|------|
| 샌드박스 격리 | OS 네이티브 샌드박스가 파일/네트워크 접근 제한 |
| 작업 디렉터리 제한 | `workspace-write`에서는 CWD 외부 쓰기 차단 |
| 네트워크 제어 | 기본적으로 네트워크 차단, 명시적 허용 필요 |
| 실행 시간 제한 | 무한 루프 방지를 위한 타임아웃 |

```toml
# full-auto 모드의 안전한 설정 예시
# .codex/config.toml

[profiles.auto]
model = "codex-mini-latest"
approval_policy = "full-auto"
sandbox_mode = "workspace-write"

[sandbox_workspace_write]
network_access = false  # 네트워크 접근 차단
```

:::warning
full-auto 모드를 사용할 때는 반드시 `workspace-write` 샌드박스를 함께 설정하자. `danger-full-access`와 결합하면 에이전트가 시스템 전체에 영향을 줄 수 있다.
:::

### 1.3 full-auto 모드 활용 시나리오

full-auto가 적합한 작업:

- **CI/CD 파이프라인**: 자동 코드 수정, 테스트 수정
- **일괄 포매팅**: 코드 스타일 일괄 적용
- **의존성 업데이트**: 패키지 업데이트 후 호환성 수정
- **린트 수정**: ESLint, Pylint 등의 경고/에러 일괄 수정
- **타입 에러 수정**: TypeScript strict 모드 전환 시 에러 수정

full-auto가 부적합한 작업:

- **아키텍처 변경**: 중요한 설계 결정이 필요한 작업
- **보안 관련 코드**: 인증, 암호화 로직 수정
- **데이터 마이그레이션**: 되돌리기 어려운 변경
- **프로덕션 배포 스크립트**: 실행 결과를 신중히 확인해야 하는 작업

---

## 2. 프로그래매틱 출력

### 2.1 codex exec 명령

`codex exec`는 비대화형 실행을 위한 전용 명령이다. 스크립트나 CI 파이프라인에서 사용하기에 적합하다.

```bash
# 기본 사용
codex exec "이 프로젝트의 TODO를 목록으로 만들어줘"

# full-auto 모드로 실행
codex exec --full-auto "테스트가 실패하는 코드를 수정해줘"

# 출력을 파일로 저장
codex exec --output-file result.md "코드 리뷰를 작성해줘"
```

### 2.2 출력 파일 활용

`--output-file` 옵션으로 Codex의 최종 응답을 파일에 저장할 수 있다. CI 파이프라인에서 후속 단계에 전달하거나, 리뷰 코멘트로 사용할 수 있다.

```bash
# 코드 리뷰 결과를 파일로 저장
codex exec --output-file review.md \
  "git diff HEAD~1의 변경사항을 리뷰해줘. 버그 위험, 성능 이슈, 코드 스타일을 검사해줘"

# 저장된 결과를 PR 코멘트로 사용
cat review.md
```

### 2.3 종료 코드 처리

`codex exec`는 작업 성공/실패에 따라 종료 코드를 반환한다. 이를 스크립트에서 활용할 수 있다.

```bash
#!/bin/bash
# fix-and-verify.sh

# Codex로 린트 수정 시도
codex exec --full-auto --sandbox workspace-write \
  "ESLint 에러를 모두 수정해줘"

if [ $? -eq 0 ]; then
    echo "Codex 수정 완료, 검증 중..."
    npm run lint
    if [ $? -eq 0 ]; then
        echo "린트 통과!"
        git add -A
        git commit -m "fix: auto-fix lint errors via Codex"
    else
        echo "린트 에러 잔존, 수동 확인 필요"
        exit 1
    fi
else
    echo "Codex 실행 실패"
    exit 1
fi
```

---

## 3. CI/CD 파이프라인 통합

### 3.1 GitHub Actions: codex-action

OpenAI는 공식 GitHub Action인 `openai/codex-action@v1`을 제공한다. 이 액션은 Codex CLI 설치, API 인증, 그리고 `codex exec` 실행을 자동으로 처리한다.

```yaml
# .github/workflows/codex-review.yml
name: Codex Code Review

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
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: openai/codex-action@v1
        with:
          api-key: ${{ secrets.OPENAI_API_KEY }}
          codex-args: |
            ["--full-auto", "--sandbox", "read-only"]
          prompt: |
            이 PR의 변경사항을 리뷰해줘.
            git diff origin/main...HEAD를 분석하고,
            버그 위험, 성능 이슈, 보안 취약점을 찾아줘.
          output-file: review-result.md

      - name: Post review comment
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const review = fs.readFileSync('review-result.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## Codex 코드 리뷰\n\n${review}`
            });
```

### 3.2 CI 실패 자동 수정

가장 강력한 활용 사례 중 하나는 **CI 실패 시 자동 수정**이다. CI가 실패하면 Codex가 자동으로 수정 PR을 생성한다.

```yaml
# .github/workflows/codex-autofix.yml
name: Codex Auto-Fix

on:
  workflow_run:
    workflows: ["CI"]
    types: [completed]

permissions:
  contents: write
  pull-requests: write

jobs:
  autofix:
    # CI가 실패한 경우에만 실행
    if: ${{ github.event.workflow_run.conclusion == 'failure' }}
    runs-on: ubuntu-latest

    steps:
      - name: Get failed branch
        id: get-branch
        run: |
          echo "branch=${{ github.event.workflow_run.head_branch }}" >> $GITHUB_OUTPUT

      - uses: actions/checkout@v4
        with:
          ref: ${{ steps.get-branch.outputs.branch }}
          fetch-depth: 0

      - uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Install Codex CLI
        run: npm install -g @openai/codex

      - name: Authenticate Codex
        run: codex login --api-key
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

      - name: Auto-fix with Codex
        run: |
          codex exec --full-auto --sandbox workspace-write \
            "이 저장소를 분석하고, 테스트 스위트를 실행한 뒤,
             테스트를 통과시키기 위한 최소한의 변경을 식별하고,
             그 변경만 구현해줘."
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

      - name: Create fix PR
        uses: peter-evans/create-pull-request@v6
        with:
          commit-message: "fix(ci): auto-fix failing tests via Codex"
          branch: codex/auto-fix-${{ github.event.workflow_run.run_id }}
          base: ${{ steps.get-branch.outputs.branch }}
          title: "[Codex] CI 실패 자동 수정"
          body: |
            Codex CLI가 CI 실패를 감지하고 자동으로 수정을 시도했습니다.

            - 원인 워크플로우: ${{ github.event.workflow_run.name }}
            - 실패 Run ID: ${{ github.event.workflow_run.id }}

            **변경사항을 반드시 리뷰한 후 머지하세요.**
```

:::tip
자동 수정 PR은 반드시 사람이 리뷰해야 한다. Codex가 테스트를 통과시키기 위해 테스트 자체를 약화시킬 수 있기 때문이다. AGENTS.md에 "테스트의 기대값을 변경하지 말 것" 같은 지시를 추가하면 이를 방지할 수 있다.
:::

### 3.3 자동 테스트 생성

새로운 코드가 추가될 때 자동으로 테스트를 생성하는 워크플로우:

```yaml
# .github/workflows/codex-test-gen.yml
name: Codex Test Generation

on:
  pull_request:
    types: [opened, synchronize]
    paths:
      - 'src/**/*.ts'
      - '!src/**/*.test.ts'
      - '!src/**/*.spec.ts'

permissions:
  contents: write
  pull-requests: write

jobs:
  generate-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.head_ref }}
          fetch-depth: 0

      - uses: actions/setup-node@v4
        with:
          node-version: '20'

      - run: npm ci

      - name: Find changed files without tests
        id: changed
        run: |
          FILES=$(git diff --name-only origin/main...HEAD \
            | grep '^src/.*\.ts$' \
            | grep -v '\.test\.\|\.spec\.' \
            | while read f; do
                TEST_FILE="${f%.ts}.test.ts"
                if [ ! -f "$TEST_FILE" ]; then
                  echo "$f"
                fi
              done)
          echo "files=$FILES" >> $GITHUB_OUTPUT

      - name: Generate tests with Codex
        if: steps.changed.outputs.files != ''
        run: |
          codex exec --full-auto --sandbox workspace-write \
            "다음 파일들에 대한 단위 테스트를 작성해줘: ${{ steps.changed.outputs.files }}
             - Jest와 TypeScript 사용
             - 각 public 함수에 대해 최소 3개의 테스트 케이스
             - 엣지 케이스와 에러 케이스 포함
             - 테스트 파일은 소스 파일 옆에 .test.ts 확장자로 생성"
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

      - name: Run generated tests
        run: npm test -- --passWithNoTests

      - name: Create test PR
        uses: peter-evans/create-pull-request@v6
        with:
          commit-message: "test: add auto-generated tests via Codex"
          branch: codex/tests-${{ github.event.pull_request.number }}
          base: ${{ github.head_ref }}
          title: "[Codex] 테스트 자동 생성"
          body: |
            Codex CLI가 테스트가 없는 새 파일에 대해 자동으로 테스트를 생성했습니다.
            생성된 테스트를 리뷰하고 필요한 경우 수정해주세요.
```

---

## 4. 환경변수와 보안 설정

### 4.1 환경변수 정책

Codex CLI는 에이전트가 실행하는 하위 프로세스에 전달되는 환경변수를 제어한다. 이는 API 키나 비밀 토큰이 의도치 않게 노출되는 것을 방지한다.

```toml
# ~/.codex/config.toml

# 환경변수 상속 정책
[shell_environment_policy]
# "none": 빈 환경에서 시작 (가장 안전)
# "core": 필수 변수만 상속 (PATH, HOME 등)
inherit = "core"

# 명시적으로 제외할 변수
exclude = [
  "OPENAI_API_KEY",
  "AWS_SECRET_ACCESS_KEY",
  "GITHUB_TOKEN",
  "DATABASE_URL"
]

# 명시적으로 포함할 변수
include = [
  "NODE_ENV",
  "LANG",
  "LC_ALL"
]

# 환경변수 오버라이드
[shell_environment_policy.overrides]
NODE_ENV = "test"
CI = "true"
```

### 4.2 API 키 보안

CI/CD 환경에서 API 키를 안전하게 관리하는 방법:

```yaml
# GitHub Actions에서 시크릿 사용
env:
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

# 절대 하지 말아야 할 것
# env:
#   OPENAI_API_KEY: "sk-실제키를여기에넣지마세요"
```

로컬 개발 환경에서의 권장 설정:

```bash
# 1. 시스템 키체인 사용 (macOS)
security add-generic-password -a "codex" -s "openai-api-key" -w "sk-..."
export OPENAI_API_KEY=$(security find-generic-password -a "codex" -s "openai-api-key" -w)

# 2. direnv 사용 (프로젝트별)
# .envrc (반드시 .gitignore에 추가)
export OPENAI_API_KEY="sk-..."

# 3. 1Password CLI 사용
export OPENAI_API_KEY=$(op item get "OpenAI" --fields credential)
```

### 4.3 프로젝트별 보안 설정

```toml
# .codex/config.toml (프로젝트 루트)

# 프로젝트에서는 안전한 모드만 허용
approval_policy = "auto-edit"
sandbox_mode = "workspace-write"

[sandbox_workspace_write]
network_access = false

# 민감한 파일 수정 차단을 AGENTS.md에서 지시
```

```markdown
<!-- AGENTS.md -->
# 보안 규칙

## 절대 수정 금지 파일
- `.env`, `.env.*` 파일
- `credentials.json`, `serviceaccount.json`
- `docker-compose.prod.yml`의 환경변수 섹션
- `config/secrets/` 디렉터리

## 절대 실행 금지 명령
- `rm -rf` 명령
- `git push --force`
- `DROP TABLE`, `DELETE FROM` 쿼리
- `chmod 777`
```

---

## 5. 멀티모델 전략

### 5.1 작업별 모델 선택

모든 작업에 같은 모델을 사용할 필요는 없다. 작업의 복잡도와 요구사항에 따라 모델을 선택하면 비용과 품질을 최적화할 수 있다.

| 작업 유형 | 권장 모델 | 이유 |
|----------|----------|------|
| 린트/포매팅 수정 | codex-mini-latest | 단순 반복 작업, 빠른 응답 |
| 단위 테스트 생성 | codex-mini-latest | 패턴화된 작업 |
| 버그 수정 | o4-mini | 추론 능력 필요 |
| 아키텍처 리뷰 | GPT-4.1 | 넓은 컨텍스트 이해 |
| 보안 감사 | GPT-4.1 | 섬세한 분석 필요 |
| 대규모 리팩토링 | o4-mini | 복잡한 의존성 추적 |

### 5.2 프로필을 활용한 모델 전환

```toml
# ~/.codex/config.toml

# 빠른 수정 작업용
[profiles.quick]
model = "codex-mini-latest"
approval_policy = "auto-edit"
sandbox_mode = "workspace-write"

# 심층 분석용
[profiles.deep]
model = "o4-mini"
approval_policy = "suggest"
sandbox_mode = "read-only"

# CI 자동화용
[profiles.ci]
model = "codex-mini-latest"
approval_policy = "full-auto"
sandbox_mode = "workspace-write"

# 보안 감사용
[profiles.security]
model = "gpt-4.1"
approval_policy = "suggest"
sandbox_mode = "read-only"
```

사용 예시:

```bash
# 빠른 린트 수정
codex --profile quick "ESLint 에러를 수정해줘"

# 코드 보안 감사
codex --profile security "이 프로젝트의 인증 로직에 보안 취약점이 있는지 분석해줘"

# CI 파이프라인에서 사용
codex --profile ci "실패하는 테스트를 수정해줘"
```

### 5.3 세션 중 모델 전환

대화형 세션에서는 `/model` 명령으로 모델을 전환할 수 있다.

```text
> /model o4-mini
모델이 o4-mini로 변경되었습니다.

> 이 함수의 시간 복잡도를 분석하고 최적화해줘
[o4-mini가 복잡한 분석 수행]

> /model codex-mini-latest
모델이 codex-mini-latest로 변경되었습니다.

> 방금 제안한 최적화를 코드에 적용해줘
[codex-mini-latest가 코드 수정 수행]
```

---

## 6. 커스텀 프롬프트와 지시사항

### 6.1 AGENTS.md 고급 활용

AGENTS.md는 단순한 규칙 목록이 아니라, 에이전트의 행동을 세밀하게 제어하는 도구다.

```markdown
<!-- AGENTS.md -->
# 프로젝트: my-app

## 기술 스택
- Runtime: Node.js 20
- Language: TypeScript 5.4 (strict mode)
- Framework: Express.js 4
- Database: PostgreSQL 16 + Prisma ORM
- Testing: Jest + Supertest
- Linting: ESLint flat config + Prettier

## 코드 규칙

### 필수 패턴
- 모든 API 엔드포인트에 입력 검증 (zod schema)
- 에러 응답은 RFC 7807 Problem Details 형식
- 데이터베이스 쿼리는 항상 Prisma client 사용
- 환경변수는 src/config.ts의 envSchema를 통해 접근

### 금지 패턴
- `any` 타입 사용 금지
- `console.log` 대신 `logger` 사용
- 동기식 파일 I/O 금지 (`fs.readFileSync` 등)
- `eval()`, `new Function()` 사용 금지

### 테스트 규칙
- 각 서비스 함수에 최소 3개의 테스트
- 테스트 이름은 "should [행위] when [조건]" 형식
- 외부 서비스는 반드시 mock 처리
- 데이터베이스 테스트는 test container 사용

## 커밋 규칙
- Conventional Commits 형식 (feat, fix, test, refactor, docs)
- 한글 커밋 메시지 허용
- Breaking change는 반드시 BREAKING CHANGE 푸터 추가

## 디렉터리 구조
```
src/
  config/        # 환경변수, 앱 설정
  controllers/   # Express 라우트 핸들러
  services/      # 비즈니스 로직
  repositories/  # 데이터 접근 계층
  middlewares/    # Express 미들웨어
  types/         # TypeScript 타입 정의
  utils/         # 유틸리티 함수
```
```

### 6.2 계층적 지시사항 구성

대규모 프로젝트에서는 디렉터리별로 다른 지시사항을 둘 수 있다.

```text
my-monorepo/
  AGENTS.md              # 전체 프로젝트 공통 규칙
  packages/
    frontend/
      AGENTS.md          # 프론트엔드 전용 규칙
    backend/
      AGENTS.md          # 백엔드 전용 규칙
    shared/
      AGENTS.md          # 공유 패키지 규칙
```

Codex는 현재 작업 디렉터리에서 Git 루트까지의 경로에 있는 모든 AGENTS.md를 읽어 지시사항 체인을 구성한다.

### 6.3 AGENTS.override.md

팀 공유 AGENTS.md를 개인적으로 오버라이드하고 싶을 때 사용한다.

```markdown
<!-- AGENTS.override.md (개인용, .gitignore에 추가) -->
# 개인 설정

## 추가 규칙
- 코드 코멘트는 한국어로 작성
- 변수명 제안 시 camelCase 사용
- 디버깅용 console.log는 허용 (커밋 전 제거 확인)
```

```bash
# .gitignore에 추가
echo "AGENTS.override.md" >> .gitignore
```

---

## 7. 네트워크 접근 제어

### 7.1 기본 네트워크 정책

Codex CLI는 기본적으로 에이전트의 네트워크 접근을 차단한다. 이는 다음을 방지한다:

- 코드나 데이터가 외부로 유출되는 것
- 에이전트가 임의의 URL에서 코드를 다운로드하는 것
- 악성 패키지 설치

### 7.2 네트워크 접근 허용

특정 작업에서 네트워크가 필요한 경우, 명시적으로 허용해야 한다.

```toml
# .codex/config.toml

# workspace-write 모드에서 네트워크 허용
[sandbox_workspace_write]
network_access = true
```

또는 CLI 플래그로:

```bash
# 네트워크 접근이 필요한 작업
codex --full-auto --sandbox workspace-write \
  "npm install을 실행하고, 새 패키지의 타입 에러를 수정해줘"
```

### 7.3 네트워크가 필요한 작업 구분

| 네트워크 필요 | 네트워크 불필요 |
|-------------|-------------|
| `npm install`, `pip install` | 코드 수정, 리팩토링 |
| `git fetch`, `git pull` | 로컬 테스트 실행 |
| API 테스트 (외부 서비스) | 린트/포매팅 |
| 패키지 버전 확인 | 파일 분석, 검색 |

:::tip
가능하면 네트워크가 필요한 작업(패키지 설치 등)은 Codex 실행 전에 미리 수행하고, Codex에게는 네트워크 없이 수행할 수 있는 작업만 맡기는 것이 안전하다.
:::

---

## 8. 로깅과 디버깅

### 8.1 로그 파일 위치

Codex CLI의 로그는 `~/.codex/log/` 디렉터리에 저장된다.

```bash
# 로그 디렉터리 확인
ls ~/.codex/log/

# 최신 로그 확인
ls -lt ~/.codex/log/ | head -5
```

### 8.2 디버그 로깅 활성화

상세한 디버그 정보가 필요할 때:

```bash
# Rust 로그 레벨 설정
RUST_LOG=debug codex "테스트를 실행해줘"

# Codex 전용 로그 레벨
CODEX_LOG=debug codex "코드를 분석해줘"

# 더 상세한 로그
RUST_LOG=trace codex exec --full-auto "린트를 수정해줘"
```

### 8.3 샌드박스 디버깅

샌드박스 관련 문제가 발생하면 디버그 명령으로 진단할 수 있다.

```bash
# macOS: Seatbelt 동작 확인
codex debug seatbelt -- ls /tmp
codex debug seatbelt -- touch /tmp/test.txt  # 쓰기 차단 확인

# Linux: Landlock 동작 확인
codex debug landlock -- cat /etc/hostname
codex debug landlock -- rm /tmp/some-file    # 쓰기 차단 확인
```

### 8.4 일반적인 문제와 해결

| 문제 | 원인 | 해결 |
|------|------|------|
| `Network Access Restricted` | 샌드박스가 네트워크 차단 | `network_access = true` 설정 |
| `Permission denied` (파일 쓰기) | read-only 샌드박스 | `workspace-write` 모드로 변경 |
| `401 Unauthorized` | API 키 만료/잘못됨 | 키 재발급 후 재설정 |
| `Context window exceeded` | 대화가 너무 길어짐 | `codex resume` 또는 새 세션 |
| `Ink raw mode error` (CI) | TTY 없는 환경 | `codex exec` 사용 |

CI 환경에서 자주 발생하는 "Ink raw mode error"는 대화형 TUI를 CI 환경에서 실행하려 할 때 발생한다. 비대화형 모드인 `codex exec`를 사용하면 해결된다.

```bash
# CI 환경에서의 올바른 사용법
codex exec --full-auto --sandbox workspace-write "작업 지시"

# 잘못된 사용법 (CI에서 에러 발생)
codex --full-auto "작업 지시"
```

---

## 9. MCP(Model Context Protocol) 통합

### 9.1 MCP 서버 설정

Codex CLI는 MCP(Model Context Protocol)를 지원하여 외부 도구와 컨텍스트 소스를 통합할 수 있다.

```toml
# ~/.codex/config.toml

# MCP 서버 설정
[[mcp_servers]]
name = "filesystem"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-filesystem", "/home/dev/docs"]

[[mcp_servers]]
name = "github"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-github"]
env = { GITHUB_TOKEN = "ghp_..." }
```

### 9.2 MCP 활용 시나리오

- **파일시스템 서버**: 프로젝트 외부 문서 참조
- **GitHub 서버**: 이슈, PR 정보를 컨텍스트로 활용
- **데이터베이스 서버**: 스키마 정보 조회
- **커스텀 서버**: 팀 내부 API, 문서 시스템 연동

```text
# MCP를 통해 GitHub 이슈를 참조하며 작업
> GitHub 이슈 #42의 요구사항에 맞게 코드를 수정해줘
[Codex가 MCP를 통해 이슈 내용을 조회하고, 코드를 수정]
```

---

## 10. 자동화 워크플로우 패턴

### 10.1 일일 코드 품질 점검

```yaml
# .github/workflows/codex-daily-check.yml
name: Daily Code Quality Check

on:
  schedule:
    - cron: '0 9 * * 1-5'  # 평일 오전 9시

jobs:
  quality-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: openai/codex-action@v1
        with:
          api-key: ${{ secrets.OPENAI_API_KEY }}
          codex-args: '["--full-auto", "--sandbox", "read-only"]'
          prompt: |
            이 프로젝트의 코드 품질을 점검해줘:
            1. TODO/FIXME 코멘트 목록
            2. 사용하지 않는 import/변수
            3. 에러 핸들링이 누락된 곳
            4. 테스트 커버리지가 낮은 파일
          output-file: quality-report.md

      - name: Create issue
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('quality-report.md', 'utf8');
            const today = new Date().toISOString().split('T')[0];
            github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: `[Codex] 일일 코드 품질 리포트 - ${today}`,
              body: report,
              labels: ['code-quality', 'automated']
            });
```

### 10.2 릴리즈 노트 자동 생성

```bash
#!/bin/bash
# generate-release-notes.sh

VERSION=$1
PREV_TAG=$(git describe --tags --abbrev=0)

codex exec --full-auto --sandbox read-only \
  --output-file release-notes.md \
  "git log ${PREV_TAG}...HEAD의 커밋 히스토리를 분석하고,
   다음 형식의 릴리즈 노트를 한국어로 작성해줘:

   ## v${VERSION} 릴리즈 노트

   ### 새 기능
   ### 개선 사항
   ### 버그 수정
   ### Breaking Changes

   각 항목에 관련 커밋 해시와 간단한 설명을 포함해줘."
```

---

## 마무리

이 글에서 다룬 고급 활용 기법을 정리하면:

| 기법 | 핵심 내용 |
|------|----------|
| full-auto 모드 | 완전 자동화, 샌드박스와 함께 사용 필수 |
| codex exec | 비대화형 실행, CI/CD에 적합 |
| GitHub Actions | codex-action으로 코드 리뷰, 자동 수정, 테스트 생성 |
| 환경변수 보안 | shell_environment_policy로 비밀 노출 방지 |
| 멀티모델 전략 | 작업 복잡도에 따른 모델 선택 |
| 네트워크 제어 | 기본 차단, 필요 시 명시적 허용 |
| MCP 통합 | 외부 도구와 컨텍스트 소스 연동 |

Codex CLI를 CI/CD에 통합하면 코드 리뷰, 테스트 생성, 버그 수정 등 많은 반복 작업을 자동화할 수 있다. 핵심은 **샌드박스를 항상 활성화**하고, **AGENTS.md로 에이전트의 행동 범위를 명확히 지정**하는 것이다.

다음 글 [[codex-guide-04-workflow|Codex CLI 실전]]에서는 레거시 코드 마이그레이션 전략을 다룬다.
