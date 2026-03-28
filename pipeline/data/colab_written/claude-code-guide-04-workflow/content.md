# Claude Code 실전: 프로젝트 관리와 워크플로우 설계

:::info
이 글은 **Claude Code Guide** 시리즈의 네 번째 글로, 프로젝트 관리와 워크플로우 설계를 다룬다. 시리즈 전체 목차는 다음과 같다:
1. [[claude-code-guide-01-setup|설치와 기본 사용법]]
2. [[claude-code-guide-02-core|핵심 기능: 도구 시스템과 에이전틱 루프]]
3. [[claude-code-guide-03-advanced|고급 활용: MCP 서버와 서브에이전트]]
4. **실전: 프로젝트 관리와 워크플로우** (현재 글)
5. [[claude-code-guide-05-comparison|AI 코딩 에이전트 비교]]
:::

이전 글에서 MCP 서버와 서브에이전트 같은 고급 기능을 다뤘다면, 이번 글에서는 실제 프로젝트에서 Claude Code를 어떻게 체계적으로 운용하는지를 다룬다. 개인 프로젝트든 팀 프로젝트든, Claude Code의 진가는 단발성 코드 생성이 아니라 **지속 가능한 워크플로우 설계**에 있다.

이 글에서 다루는 핵심 주제는 다음과 같다:

- `CLAUDE.md`를 통한 프로젝트 지식 관리
- Git/GitHub 워크플로우 자동화
- CI/CD 파이프라인 통합
- 대규모 프로젝트에서의 전략
- 팀 협업 패턴
- 실전 시나리오별 워크플로우

---

## 1. CLAUDE.md 설계 패턴

`CLAUDE.md`는 Claude Code가 프로젝트를 이해하는 데 사용하는 핵심 파일이다. 사람에게 README가 있다면, Claude Code에게는 `CLAUDE.md`가 있다. 이 파일의 품질이 Claude Code의 응답 품질을 직접적으로 결정한다.

### 1.1 효과적인 CLAUDE.md 구조

잘 설계된 `CLAUDE.md`는 다음 다섯 가지 섹션을 포함한다.

**1) 프로젝트 개요와 기술 스택**

```markdown
# my-project

Django 5 + DRF 백엔드, React 19 + Vite + Tailwind CSS 프론트엔드.

## Architecture
- Backend: Django 5 + DRF + Gunicorn + PostgreSQL + Redis
- Frontend: React 19 + Vite + Tailwind CSS v4 + Framer Motion
- Auth: JWT (simplejwt)
- Deploy: Docker Compose + Cloudflare Tunnel
```

프로젝트가 무엇이고, 어떤 기술로 구성되었는지를 첫 세 줄 안에 전달한다. Claude Code는 이 정보를 바탕으로 코드 생성 시 올바른 라이브러리와 패턴을 선택한다.

**2) 빌드/테스트 명령어**

```markdown
## Commands
- `make dev` - Start dev environment (docker compose)
- `make test` - Run all tests
- `make migrate` - Run Django migrations
- `python manage.py test blog.tests.test_api` - Run specific test
- `cd frontend && npm run build` - Build frontend
```

Claude Code가 코드를 변경한 뒤 직접 빌드하고 테스트할 수 있도록 정확한 명령어를 명시한다. 이것이 없으면 Claude Code는 추측에 의존하게 된다.

**3) 코딩 컨벤션**

```markdown
## Conventions
- Python: Black formatter, isort, type hints 필수
- TypeScript: ESLint + Prettier, 함수형 컴포넌트만 사용
- 커밋 메시지: Conventional Commits (feat:, fix:, docs:)
- 브랜치명: feature/이슈번호-설명, fix/이슈번호-설명
- 테스트: 새 기능 추가 시 반드시 테스트 동반
```

명시하지 않으면 Claude Code는 자체 판단으로 스타일을 결정한다. 팀 컨벤션과 충돌을 방지하려면 반드시 기재한다.

**4) 디렉토리 구조**

```markdown
## Project Structure
- `backend/` - Django DRF API
  - `blog/` - 포스트, 카테고리, 태그
  - `accounts/` - JWT 인증
- `frontend/` - React SPA
  - `src/pages/` - 페이지 컴포넌트
  - `src/components/` - 재사용 컴포넌트
- `e2e/` - Playwright E2E 테스트
```

Claude Code가 파일을 어디에 만들고 어디서 찾아야 하는지 가이드한다. 특히 대규모 프로젝트에서 탐색 시간을 크게 줄여준다.

**5) 배포 절차**

```markdown
## Deployment
- Live: https://example.com
- `./deploy.sh` - SSH + git pull + docker compose build
- Docker Hub: username/project
- 배포 전 반드시 `make test` 통과 확인
```

배포 관련 정보를 명시하면 Claude Code가 인프라 관련 질문에도 정확하게 답할 수 있다.

### 1.2 계층 구조 활용

Claude Code는 `CLAUDE.md`를 세 개의 계층에서 읽는다.

| 계층 | 경로 | 용도 | 우선순위 |
|------|------|------|:--------:|
| 전역 | `~/.claude/CLAUDE.md` | 사용자 공통 설정 | 낮음 |
| 프로젝트 | `./CLAUDE.md` | 프로젝트별 설정 | 중간 |
| 하위 디렉토리 | `./backend/CLAUDE.md` | 서비스별 설정 | 높음 |

```text
~/.claude/CLAUDE.md          ← "한국어로 응답해줘, 커밋은 Conventional Commits"
├── project-a/CLAUDE.md      ← "Django + React, make test로 테스트"
│   ├── backend/CLAUDE.md    ← "Python 3.12, Black, type hints"
│   └── frontend/CLAUDE.md   ← "TypeScript strict, ESLint"
└── project-b/CLAUDE.md      ← "Go microservice, go test ./..."
```

전역 설정에는 언어 선호도나 공통 코딩 스타일을, 프로젝트 레벨에는 기술 스택과 빌드 명령어를, 하위 디렉토리에는 서비스별 세부 규칙을 배치한다.

### 1.3 CLAUDE.md에 넣으면 좋은 것 vs 나쁜 것

| 넣으면 좋은 것 | 넣으면 나쁜 것 |
|----------------|----------------|
| 빌드/테스트 명령어 | API 키, 시크릿 |
| 코딩 컨벤션 | 수천 줄의 API 문서 |
| 디렉토리 구조 설명 | 모든 파일의 상세 설명 |
| 배포 절차 | 자주 바뀌는 TODO 리스트 |
| 자주 하는 실수 패턴 | 개인 메모 |
| 외부 서비스 연동 방법 | 미완성 실험 코드 |

:::warning
`CLAUDE.md`는 Git에 커밋되는 파일이다. API 키, 비밀번호, 토큰 등의 민감 정보를 절대 넣지 말 것. 개인적인 설정은 `~/.claude/CLAUDE.md`를 활용한다.
:::

### 1.4 /init 명령으로 자동 생성

프로젝트에 `CLAUDE.md`가 없다면, `/init` 명령으로 자동 생성할 수 있다.

```bash
# Claude Code 세션에서
> /init
```

`/init`을 실행하면 Claude Code가 프로젝트 구조를 분석하여 초기 `CLAUDE.md`를 생성한다.

```text
분석 과정:
1. package.json, requirements.txt, go.mod 등으로 기술 스택 파악
2. 디렉토리 구조 스캔
3. 기존 README.md, Makefile 등 참고
4. CI/CD 설정 파일 확인
5. CLAUDE.md 초안 생성
```

자동 생성된 파일은 시작점일 뿐이다. 반드시 팀의 워크플로우와 컨벤션에 맞게 커스터마이징해야 한다.

### 1.5 실제 프로젝트 CLAUDE.md 예시

**Go 마이크로서비스 예시:**

```markdown
# payment-service

결제 처리 마이크로서비스. Go 1.22 + gRPC + PostgreSQL.

## Commands
- `make run` - 로컬 서버 실행 (포트 8080)
- `make test` - 전체 테스트 (단위 + 통합)
- `make proto` - protobuf 재생성
- `make lint` - golangci-lint 실행
- `make docker` - Docker 이미지 빌드

## Structure
- `cmd/server/` - 서버 엔트리포인트
- `internal/handler/` - gRPC 핸들러
- `internal/service/` - 비즈니스 로직
- `internal/repository/` - DB 접근 계층
- `proto/` - protobuf 정의
- `migrations/` - DB 마이그레이션 (golang-migrate)

## Conventions
- 에러 처리: fmt.Errorf("operation: %w", err) 패턴
- 로깅: slog 패키지 사용 (log 패키지 금지)
- 테스트: 테이블 드리븐 테스트 패턴
- context.Context는 항상 첫 번째 파라미터
```

:::tip
CLAUDE.md는 "살아있는 문서"다. 프로젝트가 발전하면서 계속 업데이트해야 한다. 새로운 컨벤션이 생기거나, 자주 하는 실수를 발견하면 즉시 반영한다.
:::

---

## 2. Git 워크플로우

Claude Code는 Git 워크플로우를 깊이 이해하고 있으며, 슬래시 명령어로 주요 작업을 자동화할 수 있다.

### 2.1 /commit - 변경 분석 + 커밋 메시지 자동 생성

`/commit`은 단순히 `git commit`을 실행하는 것이 아니다. Claude Code가 변경사항을 분석하고, 프로젝트의 커밋 스타일에 맞는 메시지를 생성한다.

`/commit` 실행 시 내부 동작은 다음과 같다:

```text
1. git status로 변경 파일 확인
2. git diff로 스테이지된 + 미스테이지된 변경 분석
3. git log로 최근 커밋 메시지 스타일 참고
4. 변경 내용 기반 커밋 메시지 초안 생성
5. 관련 파일 스테이징
6. 커밋 생성 (Co-Authored-By 자동 추가)
7. git status로 결과 검증
```

실제 사용 예시:

```bash
# 여러 파일을 수정한 후
> /commit

# Claude Code의 분석 결과:
# - backend/blog/views.py: 페이지네이션 로직 변경
# - backend/blog/serializers.py: 필드 추가
# - frontend/src/pages/PostsPage.jsx: 무한 스크롤 구현
#
# 생성되는 커밋 메시지:
# feat: 블로그 목록 무한 스크롤 구현
#
# 백엔드 커서 기반 페이지네이션 + 프론트엔드 Intersection
# Observer로 무한 스크롤을 구현한다.
#
# Co-Authored-By: Claude <noreply@anthropic.com>
```

:::tip
커밋 전에 변경사항을 선택적으로 스테이징하고 싶다면, `git add`로 원하는 파일만 먼저 스테이징한 뒤 `/commit`을 실행한다. Claude Code는 스테이지된 변경사항만 커밋한다.
:::

### 2.2 /pr - PR 생성

`/pr` 명령은 현재 브랜치의 전체 커밋을 분석하여 PR을 생성한다.

```bash
> /pr

# Claude Code 동작:
# 1. 브랜치의 모든 커밋 분석 (base branch 대비)
# 2. 전체 diff 확인
# 3. PR 제목 + 본문 + 테스트 계획 생성
# 4. gh pr create 실행
```

생성되는 PR 형식:

```markdown
## Summary
- 블로그 목록에 커서 기반 무한 스크롤 구현
- 백엔드 CursorPagination 클래스 추가
- 프론트엔드 useInfiniteScroll 커스텀 훅 작성

## Test plan
- [ ] 포스트 100개 이상 환경에서 스크롤 테스트
- [ ] 빈 결과셋 처리 확인
- [ ] 네트워크 에러 시 재시도 동작 확인
- [ ] 모바일 뷰포트에서 스크롤 성능 확인
```

### 2.3 /review-pr - PR 리뷰

`/review-pr`은 PR의 변경사항을 분석하고 코드 리뷰를 수행한다.

```bash
> /review-pr 42

# Claude Code 동작:
# 1. PR #42의 변경사항 가져오기
# 2. 파일별 diff 분석
# 3. 잠재적 문제점, 개선 사항, 보안 이슈 식별
# 4. 라인별 코멘트 생성
```

리뷰에서 확인하는 항목:

- 로직 오류 및 엣지 케이스
- 보안 취약점 (SQL 인젝션, XSS 등)
- 성능 이슈 (N+1 쿼리, 메모리 누수)
- 코딩 컨벤션 준수 여부
- 테스트 커버리지 충분 여부
- 에러 핸들링 누락

### 2.4 Git 안전 프로토콜

Claude Code는 Git 작업 시 엄격한 안전 규칙을 따른다.

| 규칙 | 설명 | 이유 |
|------|------|------|
| force push 방지 | `git push --force` 실행 금지 | 팀원의 작업 손실 방지 |
| amend 대신 새 커밋 | 기존 커밋 수정 대신 새 커밋 생성 | 히스토리 보존, hook 실패 시 이전 커밋 보호 |
| hook 건너뛰기 금지 | `--no-verify` 사용 금지 | lint, 테스트 등 품질 게이트 유지 |
| 민감 파일 커밋 방지 | `.env`, 인증서 파일 감지 시 경고 | 시크릿 노출 방지 |
| 파괴적 명령 방지 | `reset --hard`, `checkout .` 금지 | 작업 손실 방지 |

:::warning
pre-commit hook이 실패하면 커밋은 생성되지 않는다. 이때 `--amend`로 재시도하면 이전 커밋이 수정되어 작업이 유실될 수 있다. Claude Code는 항상 hook 실패를 수정한 뒤 새 커밋을 생성한다.
:::

```bash
# 안전한 패턴 (Claude Code의 기본 동작)
git add specific-file.py       # 특정 파일만 스테이징
git commit -m "feat: 기능 추가"  # 새 커밋 생성

# 위험한 패턴 (Claude Code가 거부하는 명령)
git add -A                     # 모든 파일 무차별 추가
git push --force               # 원격 히스토리 강제 덮어쓰기
git commit --amend --no-verify # hook 건너뛰고 이전 커밋 수정
git reset --hard               # 모든 로컬 변경 삭제
```

---

## 3. CI/CD 통합

Claude Code의 헤드리스 모드(`claude -p`)를 활용하면 CI/CD 파이프라인에 AI 기반 자동화를 통합할 수 있다.

### 3.1 헤드리스 모드 기본

`-p` 플래그는 프롬프트를 인자로 받아 비대화형으로 실행한다.

```bash
# 기본 사용
claude -p "이 프로젝트의 테스트 커버리지를 분석해줘"

# 파이프 입력
echo "에러 로그 내용..." | claude -p "이 에러의 원인을 분석해줘"

# JSON 출력
claude -p "변경사항을 리뷰해줘" --output-format json

# 파일 지정
cat src/api.py | claude -p "이 코드의 보안 취약점을 찾아줘"
```

### 3.2 GitHub Actions 통합

PR이 올라올 때 자동으로 코드 리뷰를 실행하는 워크플로우 예시:

```yaml
name: Claude Code Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Install Claude Code
        run: npm install -g @anthropic-ai/claude-code

      - name: Get PR diff
        id: diff
        run: |
          DIFF=$(git diff origin/${{ github.base_ref }}...HEAD)
          echo "diff<<EOF" >> $GITHUB_OUTPUT
          echo "$DIFF" >> $GITHUB_OUTPUT
          echo "EOF" >> $GITHUB_OUTPUT

      - name: Claude Review
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          echo "${{ steps.diff.outputs.diff }}" | \
          claude -p "이 PR의 변경사항을 리뷰해줘. 버그, 보안 이슈, 성능 문제를 중점적으로 확인해줘." \
          --output-format json > review.json

      - name: Post Review Comment
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const review = JSON.parse(fs.readFileSync('review.json', 'utf8'));
            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: review.result
            });
```

### 3.3 자동 테스트 생성 파이프라인

새로운 코드가 추가될 때 자동으로 테스트를 생성하는 워크플로우:

```yaml
name: Auto Test Generation
on:
  pull_request:
    paths:
      - 'backend/**/*.py'

jobs:
  generate-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Find changed files
        id: changed
        run: |
          FILES=$(git diff --name-only origin/main...HEAD -- 'backend/**/*.py' | grep -v test_)
          echo "files=$FILES" >> $GITHUB_OUTPUT

      - name: Generate tests
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          for file in ${{ steps.changed.outputs.files }}; do
            cat "$file" | claude -p \
              "이 Python 파일에 대한 pytest 테스트를 작성해줘.
               엣지 케이스와 에러 케이스를 포함해줘.
               기존 테스트 스타일을 따라줘." \
              > "tests/test_$(basename $file)"
          done

      - name: Create PR with tests
        run: |
          git checkout -b auto-tests-${{ github.event.number }}
          git add tests/
          git commit -m "test: PR #${{ github.event.number }}에 대한 자동 테스트 생성"
          git push -u origin auto-tests-${{ github.event.number }}
```

### 3.4 환경변수로 API 키 안전하게 전달

```yaml
# GitHub Actions secrets 설정
# Settings > Secrets and variables > Actions > New repository secret
# Name: ANTHROPIC_API_KEY
# Value: sk-ant-...

# 워크플로우에서 사용
env:
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

:::warning
API 키를 워크플로우 파일에 직접 하드코딩하지 말 것. 반드시 GitHub Secrets를 통해 주입한다. 로그에 키가 노출되지 않도록 `--output-format json`을 사용하여 출력을 구조화하는 것이 좋다.
:::

### 3.5 PR 체크 자동화

Claude Code를 활용한 PR 체크를 필수 상태 검사(required status check)로 설정하면, AI 리뷰를 통과해야만 머지가 가능해진다.

```yaml
name: PR Quality Gate
on:
  pull_request:

jobs:
  quality-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Claude Quality Check
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          RESULT=$(git diff origin/main...HEAD | claude -p \
            "이 변경사항의 품질을 평가해줘.
             - 보안 취약점이 있으면 FAIL
             - 테스트가 없으면 WARN
             - 코딩 컨벤션 위반이 있으면 WARN
             결과를 JSON으로: {\"status\": \"PASS|WARN|FAIL\", \"issues\": [...]}" \
            --output-format json)

          STATUS=$(echo "$RESULT" | jq -r '.result' | jq -r '.status')
          if [ "$STATUS" = "FAIL" ]; then
            echo "Quality check failed"
            exit 1
          fi
```

---

## 4. 대규모 프로젝트 전략

프로젝트 규모가 커질수록 Claude Code의 컨텍스트 윈도우 관리가 중요해진다. 200K 토큰의 컨텍스트도 대형 코드베이스 전체를 담기에는 부족하다.

### 4.1 컨텍스트 윈도우 관리

**구체적인 파일/함수명 지정**

```bash
# 나쁜 예: 모호한 요청
> "인증 로직을 개선해줘"

# 좋은 예: 구체적인 지정
> "backend/accounts/views.py의 LoginView.post 메서드에서
>  refresh 토큰 만료 처리를 추가해줘"
```

모호한 요청은 Claude Code가 관련 파일을 탐색하는 데 컨텍스트를 소모하게 만든다. 파일 경로와 함수명을 명시하면 즉시 핵심 작업에 집중할 수 있다.

**`/compact` 주기적 사용**

긴 대화가 이어지면 컨텍스트 윈도우가 채워진다. `/compact` 명령으로 대화를 요약하여 컨텍스트를 확보한다.

```bash
# 대화가 길어졌을 때
> /compact

# Claude Code가 수행하는 작업:
# 1. 현재까지의 대화 내용 요약
# 2. 핵심 결정사항과 컨텍스트 보존
# 3. 불필요한 중간 과정 제거
# 4. 압축된 상태로 대화 계속
```

:::tip
`/compact`는 "지금까지 뭘 했는지 기억하되, 세부 내역은 잊어도 된다"는 뜻이다. 작업 방향이 바뀌거나 새로운 모듈로 넘어갈 때 사용하면 효과적이다.
:::

**서브에이전트로 탐색 위임**

코드베이스를 분석해야 할 때 메인 컨텍스트를 소모하지 않으려면 서브에이전트를 활용한다.

```bash
> "서브에이전트를 사용해서 backend/ 디렉토리의 모든 API 엔드포인트 목록을 정리해줘.
>  결과만 메인 컨텍스트로 가져와줘."
```

서브에이전트는 독립된 컨텍스트에서 탐색을 수행하고, 결과만 메인 세션에 반환한다. 탐색 과정에서 소모된 컨텍스트는 메인 세션에 영향을 주지 않는다.

### 4.2 멀티 디렉토리 작업

모노레포나 관련 프로젝트를 동시에 다뤄야 할 때 `--add-dir` 플래그를 사용한다.

```bash
# 프론트엔드와 백엔드를 동시에 작업
claude --add-dir ../backend --add-dir ../shared-types

# 마이크로서비스 간 작업
claude --add-dir ../payment-service --add-dir ../notification-service
```

이렇게 하면 Claude Code가 여러 디렉토리의 파일을 동시에 읽고 수정할 수 있다. API 계약 변경처럼 여러 서비스에 걸친 작업에 특히 유용하다.

### 4.3 모노레포 전략

대규모 모노레포에서는 하위 디렉토리별 `CLAUDE.md`가 핵심이다.

```text
monorepo/
├── CLAUDE.md                    ← 전체 모노레포 규칙
├── packages/
│   ├── web/
│   │   └── CLAUDE.md            ← React 웹앱 규칙
│   ├── mobile/
│   │   └── CLAUDE.md            ← React Native 규칙
│   ├── api/
│   │   └── CLAUDE.md            ← Express API 규칙
│   └── shared/
│       └── CLAUDE.md            ← 공유 라이브러리 규칙
```

루트 `CLAUDE.md` 예시:

```markdown
# my-monorepo

pnpm workspace 기반 모노레포. 서비스별 독립 배포.

## 공통 규칙
- TypeScript strict mode 필수
- 공유 타입은 반드시 packages/shared에 정의
- 서비스 간 직접 import 금지 (shared를 통해서만)

## 서비스별 작업 분리
- web 수정 시 web/CLAUDE.md 참고
- api 수정 시 api/CLAUDE.md 참고
- shared 수정 시 의존 서비스 전체 테스트 필수
```

### 4.4 리팩토링 전략

대규모 리팩토링은 Claude Code의 강점이 빛나는 영역이다. 단, 체계적인 접근이 필요하다.

**1단계: Plan 모드로 계획 수립**

```bash
> /plan backend/blog/ 디렉토리를 DDD(Domain-Driven Design) 패턴으로 리팩토링하고 싶어.
> 현재 구조를 분석하고 마이그레이션 계획을 세워줘.
```

Claude Code가 현재 코드를 분석하고, 단계별 리팩토링 계획을 수립한다.

**2단계: Git worktree로 격리 실험**

```bash
# worktree 생성으로 메인 브랜치 보호
git worktree add ../blog-refactor feature/ddd-refactor

# 격리된 환경에서 Claude Code 실행
cd ../blog-refactor
claude
```

worktree를 사용하면 메인 브랜치를 건드리지 않고 안전하게 리팩토링을 실험할 수 있다. 문제가 생기면 worktree를 삭제하면 그만이다.

**3단계: 단계별 검증**

```bash
# 각 단계마다 테스트 실행
> "models.py를 domain/models/로 분리했으니 테스트를 돌려줘"

# 중간 커밋으로 롤백 포인트 확보
> /commit

# 다음 단계 진행
> "serializers.py를 application/serializers/로 이동해줘"
```

:::tip
대규모 리팩토링에서 가장 중요한 원칙: 한 번에 하나만 바꾸고, 매번 테스트하고, 자주 커밋한다. Claude Code도 이 원칙을 따르도록 명시적으로 요청하는 것이 좋다.
:::

---

## 5. 팀 협업 패턴

Claude Code는 개인 도구를 넘어 팀 단위의 생산성 도구로 활용할 수 있다.

### 5.1 CLAUDE.md를 Git에 커밋하여 팀 공유

```bash
# CLAUDE.md를 버전 관리
git add CLAUDE.md
git commit -m "docs: CLAUDE.md 초기 설정"
```

팀원 모두가 동일한 `CLAUDE.md`를 사용하면 Claude Code의 응답이 일관되게 유지된다. 새 팀원의 온보딩에도 효과적이다 - `CLAUDE.md`를 읽는 것만으로 프로젝트의 구조와 컨벤션을 빠르게 파악할 수 있다.

### 5.2 .claude/settings.json 프로젝트 레벨 설정

프로젝트 루트에 `.claude/settings.json`을 두면 팀 공통 설정을 강제할 수 있다.

```json
{
  "permissions": {
    "allow": [
      "Read",
      "Edit",
      "Write",
      "Bash(make test)",
      "Bash(make lint)",
      "Bash(npm run build)"
    ],
    "deny": [
      "Bash(rm -rf *)",
      "Bash(git push --force)"
    ]
  }
}
```

이 설정은 팀원 전체에게 적용되어 Claude Code가 허용된 명령만 실행하도록 제한한다.

### 5.3 코드 리뷰에서 Claude Code 활용

PR 리뷰에서 Claude Code를 보조 리뷰어로 활용하는 패턴:

```bash
# PR의 변경사항을 로컬에서 리뷰
gh pr checkout 42
claude -p "$(gh pr diff 42)" "이 PR을 리뷰해줘. 다음을 중점적으로:
1. 비즈니스 로직 정확성
2. 보안 취약점
3. 성능 이슈
4. 테스트 커버리지"
```

인간 리뷰어가 비즈니스 로직과 아키텍처 결정에 집중하는 동안, Claude Code는 보안, 성능, 코딩 스타일 같은 기계적 리뷰를 담당한다.

### 5.4 PR 템플릿과 Claude Code 연동

`.github/PULL_REQUEST_TEMPLATE.md`에 Claude Code 관련 가이드를 추가:

```markdown
## Description
<!-- 변경사항 설명 -->

## Test Plan
<!-- 테스트 계획 -->

## Claude Code Checklist
- [ ] CLAUDE.md 업데이트 필요 여부 확인
- [ ] Claude Code로 보안 리뷰 완료
- [ ] AI 생성 코드에 Co-Authored-By 태그 포함
```

### 5.5 팀 컨벤션을 CLAUDE.md로 강제

`CLAUDE.md`에 팀 컨벤션을 명시하면 Claude Code가 이를 자동으로 따른다.

```markdown
## 팀 컨벤션 (반드시 준수)

### 에러 핸들링
- 모든 API 핸들러에서 try-except 필수
- 커스텀 예외 클래스 사용 (exceptions.py에 정의)
- 에러 응답 포맷: {"error": {"code": "...", "message": "..."}}

### API 설계
- RESTful 원칙 준수
- 리스트 API는 반드시 페이지네이션 포함
- 응답 필드는 snake_case

### 테스트
- 새 기능 추가 시 최소 단위 테스트 3개 이상
- 외부 API 호출은 반드시 mock 처리
- fixture는 conftest.py에 중앙 관리
```

이렇게 하면 팀원이 Claude Code를 사용할 때, 누가 사용하든 동일한 컨벤션이 적용된 코드가 생성된다.

---

## 6. 실전 워크플로우 예시

### 시나리오 1: 새 기능 개발

"블로그에 댓글 기능을 추가한다"는 요구사항을 Claude Code로 처리하는 전체 흐름이다.

**Step 1: 이슈 분석 + 계획 수립**

```bash
> "GitHub 이슈 #23 '댓글 기능 추가'를 구현하려고 해.
>  현재 프로젝트 구조를 분석하고 구현 계획을 세워줘."

# Claude Code의 계획 예시:
# 1. Comment 모델 생성 (backend/blog/models.py)
# 2. CommentSerializer 작성 (backend/blog/serializers.py)
# 3. CommentViewSet 추가 (backend/blog/views.py)
# 4. URL 라우팅 (backend/blog/urls.py)
# 5. 프론트엔드 CommentSection 컴포넌트 (frontend/src/components/)
# 6. PostView에 댓글 섹션 통합
# 7. 테스트 작성
```

**Step 2: 브랜치 생성**

```bash
> "feature/23-comments 브랜치를 만들어줘"
```

**Step 3: 구현**

```bash
> "계획대로 Comment 모델부터 구현해줘.
>  author는 User ForeignKey, post는 Post ForeignKey,
>  content는 TextField, created_at은 auto_now_add로."
```

Claude Code가 모델, 시리얼라이저, 뷰, URL을 순서대로 구현한다. 각 단계에서 기존 코드의 패턴을 따른다.

**Step 4: 테스트 작성 + 실행**

```bash
> "Comment API에 대한 테스트를 작성하고 실행해줘.
>  CRUD 전체와 권한 체크를 포함해줘."
```

**Step 5: 커밋 + PR**

```bash
> /commit
> /pr
```

전체 과정이 하나의 세션 안에서 완결된다.

### 시나리오 2: 버그 핫픽스

프로덕션에서 500 에러가 발생한 상황이다.

**Step 1: 에러 로그 파이프 입력**

```bash
# 에러 로그를 직접 파이프
cat error.log | claude -p "이 에러 로그를 분석하고 원인을 찾아줘"

# 또는 대화형으로
> "프로덕션에서 다음 에러가 발생했어:
>  TypeError: 'NoneType' object is not subscriptable
>  at backend/blog/views.py:142 in get_queryset"
```

**Step 2: 원인 분석 + 수정**

```bash
> "해당 코드를 확인하고, NoneType 에러의 원인을 분석해서 수정해줘"

# Claude Code:
# 1. views.py:142 확인
# 2. get_queryset에서 category 파라미터가 None일 때의 처리 누락 발견
# 3. None 체크 추가
```

**Step 3: 회귀 테스트 추가**

```bash
> "이 버그에 대한 회귀 테스트를 추가해줘.
>  category 파라미터가 None, 빈 문자열, 존재하지 않는 값인 경우를 모두 테스트해줘."
```

**Step 4: 긴급 배포**

```bash
> /commit  # "fix: category 미지정 시 NoneType 에러 수정"
> /pr      # 긴급 PR 생성
```

### 시나리오 3: 레거시 코드 마이그레이션

Django 3.2에서 Django 5로 업그레이드하는 시나리오다.

**Step 1: 코드베이스 분석**

```bash
> "현재 프로젝트의 Django 버전 호환성을 분석해줘.
>  deprecated된 기능, 변경된 API, 제거된 기능을 목록으로 정리해줘."

# Claude Code가 분석하는 항목:
# - settings.py의 deprecated 설정
# - url() → path() 마이그레이션 필요 여부
# - 미들웨어 클래스 변경
# - Field 옵션 변경 (default=None 등)
# - 제거된 서드파티 라이브러리 호환성
```

**Step 2: 마이그레이션 계획 수립**

```bash
> "분석 결과를 바탕으로 단계별 마이그레이션 계획을 세워줘.
>  각 단계마다 테스트 가능한 단위로 나눠줘."
```

**Step 3: 단계별 변환**

```bash
# 1단계: 의존성 업데이트
> "requirements.txt에서 Django를 5.0으로, 관련 패키지를 호환 버전으로 업데이트해줘"

# 2단계: deprecated API 대체
> "url() 패턴을 path()로 변환해줘"

# 3단계: 설정 마이그레이션
> "settings.py의 deprecated 설정을 새 형식으로 변경해줘"

# 각 단계마다 커밋
> /commit
```

**Step 4: 테스트 커버리지 확인**

```bash
> "전체 테스트를 실행하고, 실패하는 테스트가 있으면 수정해줘.
>  마이그레이션으로 인한 실패인지 기존 버그인지 구분해서 알려줘."
```

:::tip
레거시 마이그레이션에서 Claude Code의 핵심 가치는 "변경해야 할 부분을 빠짐없이 찾아내는 것"이다. 수동으로 하면 놓치기 쉬운 deprecated API 사용처를 전체 코드베이스에서 빠르게 식별할 수 있다.
:::

---

## 정리

이 글에서 다룬 프로젝트 관리와 워크플로우 전략을 정리하면 다음과 같다.

| 영역 | 핵심 전략 | 주요 도구/명령 |
|------|-----------|----------------|
| 프로젝트 지식 | CLAUDE.md 계층 구조 설계 | `/init`, 전역/프로젝트/디렉토리 CLAUDE.md |
| Git 워크플로우 | 자동 커밋, PR, 리뷰 | `/commit`, `/pr`, `/review-pr` |
| CI/CD | 헤드리스 모드로 파이프라인 통합 | `claude -p`, GitHub Actions |
| 대규모 프로젝트 | 컨텍스트 관리 + 격리 실험 | `/compact`, `--add-dir`, worktree |
| 팀 협업 | 공유 설정 + 컨벤션 강제 | CLAUDE.md Git 커밋, settings.json |
| 실전 워크플로우 | 시나리오별 체계적 접근 | 계획 → 구현 → 테스트 → 배포 |

Claude Code를 단순한 코드 생성기가 아닌, 프로젝트의 전체 라이프사이클에 참여하는 팀원으로 활용하려면 이 글에서 다룬 패턴들이 필수적이다. 특히 `CLAUDE.md`의 품질이 전체 경험의 품질을 결정한다는 점을 기억하자.

다음 글 [[claude-code-guide-05-comparison|AI 코딩 에이전트 비교]]에서는 Claude Code, Gemini CLI, Codex CLI를 다각도로 비교 분석한다.
