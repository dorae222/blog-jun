<!-- infographic-hero -->
![Getting Started with Claude Code 핵심 요약](figures/infographic.svg)

*Figure: Getting Started with Claude Code 한 장 요약 인포그래픽*

# Claude Code 시작하기: 설치부터 첫 대화까지

## 들어가며

:::info
이 글은 **Claude Code Guide** 시리즈의 첫 번째 글로, 설치부터 기본 사용법까지 다룬다. 시리즈 전체 목차는 다음과 같다:
1. **설치와 기본 사용법** (현재 글)
2. [[claude-code-guide-02-core|핵심 기능: 도구 시스템과 에이전틱 루프]]
3. [[claude-code-guide-03-advanced|고급 활용: MCP 서버와 서브에이전트]]
4. [[claude-code-guide-04-workflow|실전: 프로젝트 관리와 워크플로우]]
5. [[claude-code-guide-05-comparison|AI 코딩 에이전트 비교]]
:::

Claude Code는 Anthropic이 개발한 **에이전틱 코딩 CLI 도구**로, 터미널에서 직접 실행되는 AI 소프트웨어 엔지니어링 보조도구다. 기존 Copilot류 자동완성과 근본적으로 다른 점은, 코드베이스 전체를 이해하고 파일 읽기/쓰기, 명령 실행, Git 조작, 웹 검색까지 **에이전틱 방식**으로 수행한다는 것이다.

이 글에서는 Claude Code를 처음 설치하고, 환경을 설정한 뒤, 실제 프로젝트에서 첫 대화를 시작하는 전 과정을 단계별로 안내한다.

---

## 설치

### 사전 요구사항

- **Node.js 18+** (npm 포함)
- **운영체제**: macOS, Linux, Windows (WSL2 권장)
- **Anthropic 계정**: [console.anthropic.com](https://console.anthropic.com)에서 API 키 발급

### npm으로 설치 (권장)

```bash
npm install -g @anthropic-ai/claude-code
```

설치 후 버전을 확인한다:

```bash
claude --version
```

```output
claude-code v2.1.x
```

### Homebrew로 설치 (macOS/Linux)

```bash
brew install claude-code
```

### 업데이트

```bash
npm update -g @anthropic-ai/claude-code
```

---

## 초기 설정

### API 키 인증

최초 실행 시 Anthropic 계정으로 로그인이 필요하다:

```bash
claude
```

브라우저가 열리며 OAuth 인증 플로우를 진행한다. 인증이 완료되면 터미널로 돌아와 바로 사용할 수 있다.

API 키를 직접 설정할 수도 있다:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 모델 선택

Claude Code는 기본적으로 **Claude Opus 4.6**(최신 플래그십)을 사용한다. `--model` 플래그로 다른 모델을 지정할 수 있다:

```bash
claude --model claude-sonnet-4-6
```

사용 가능한 모델:
- `claude-opus-4-6` - 최고 성능, 복잡한 작업에 최적
- `claude-sonnet-4-6` - 빠른 속도, 일반 작업에 적합
- `claude-haiku-4-5-20251001` - 가장 빠름, 간단한 작업용

### 권한 모드 설정

Claude Code는 도구 실행 시 사용자 승인을 요청한다. `/permissions` 명령으로 권한 모드를 설정할 수 있다:

| 모드 | 설명 |
|------|------|
| 기본 | 모든 도구 실행 시 사용자 확인 요청 |
| 허용 목록 | 특정 도구를 자동 허용으로 설정 |
| Yolo 모드 | 모든 도구 자동 허용 (주의 필요) |

---

## 실행 방법

### 대화형 모드 (기본)

프로젝트 디렉토리에서 `claude` 명령을 실행하면 대화형 REPL이 시작된다:

```bash
cd my-project
claude
```

```output
╭──────────────────────────────────────╮
│ ● Claude Code                        │
│                                      │
│ /help for available commands          │
╰──────────────────────────────────────╯

>
```

프롬프트에 자연어로 요청을 입력하면 된다:

```text
> 이 프로젝트의 구조를 설명해줘
```

Claude Code는 자동으로 프로젝트 파일을 탐색하고, 구조를 파악하여 설명한다.

### 원샷 모드

단일 명령을 실행하고 종료하려면 `-p` (print) 플래그를 사용한다:

```bash
claude -p "이 프로젝트에서 사용되지 않는 import를 찾아서 제거해줘"
```

### 파이프 입력

stdin으로 입력을 파이프할 수 있다:

```bash
cat error.log | claude -p "이 에러 로그를 분석하고 해결 방법을 제안해줘"
```

```bash
git diff | claude -p "이 변경 사항에 대한 커밋 메시지를 작성해줘"
```

### 이전 대화 이어하기

`--continue` 또는 `--resume` 플래그로 이전 대화를 이어갈 수 있다:

```bash
claude --continue        # 가장 최근 대화 이어하기
claude --resume          # 대화 목록에서 선택
```

---

## CLAUDE.md - 프로젝트 설정 파일

### CLAUDE.md란?

`CLAUDE.md`는 Claude Code에게 프로젝트별 지침을 전달하는 설정 파일이다. 프로젝트 루트에 배치하면 매 세션 시작 시 자동으로 로드된다.

### 계층 구조

CLAUDE.md는 여러 위치에서 계층적으로 로드된다:

```text
~/.claude/CLAUDE.md              ← 전역 설정 (모든 프로젝트)
~/project/CLAUDE.md              ← 프로젝트 루트 설정
~/project/src/CLAUDE.md          ← 하위 디렉토리 설정
~/project/.claude/settings.json  ← 권한/도구 설정
```

하위 파일이 상위 파일을 오버라이드하지 않고, 모든 레벨이 **누적**된다.

### CLAUDE.md 작성 예시

```markdown
# my-project

Django 5 + DRF 백엔드, React 19 + Vite 프론트엔드.

## 명령어
- `make dev` - 개발 서버 시작
- `make test` - 테스트 실행
- `make lint` - 린트 검사

## 규칙
- 한국어 주석/문서 사용
- 컴포넌트 400줄 초과 시 분할
- API 호출은 api.js의 기존 함수 사용
```

:::tip
CLAUDE.md에는 **프로젝트 구조, 빌드 명령, 코딩 컨벤션, 배포 절차** 등을 간결하게 작성한다. Claude Code가 매 세션마다 이 정보를 참고하여 프로젝트에 맞는 작업을 수행한다.
:::

### `/init` 명령으로 자동 생성

프로젝트에서 아직 CLAUDE.md가 없다면 `/init` 명령으로 자동 생성할 수 있다:

```text
> /init
```

Claude Code가 프로젝트 구조를 분석하고 적절한 CLAUDE.md 초안을 생성한다.

---

## 슬래시 명령어

Claude Code 대화 중 `/`로 시작하는 명령어를 사용할 수 있다:

### 핵심 명령어

| 명령어 | 설명 |
|--------|------|
| `/help` | 사용 가능한 명령어 목록 |
| `/clear` | 대화 기록 초기화 |
| `/compact` | 대화를 압축하여 컨텍스트 절약 |
| `/model` | 모델 전환 |
| `/permissions` | 권한 설정 |
| `/init` | CLAUDE.md 자동 생성 |

### 작업 명령어

| 명령어 | 설명 |
|--------|------|
| `/commit` | Git 커밋 (변경 분석 + 메시지 자동 생성) |
| `/review-pr` | PR 리뷰 |
| `/pr` | PR 생성 |

### 유용한 팁

- **Escape 키**: 현재 작업 중단
- **Ctrl+C (2회)**: Claude Code 종료
- **`! command`**: 셸 명령 직접 실행 (예: `! git status`)

---

## 첫 번째 실전 예시

### 예시 1: 프로젝트 이해하기

새로운 프로젝트에 투입되었을 때:

```text
> 이 프로젝트의 전체 구조를 분석하고, 주요 모듈과 데이터 흐름을 설명해줘
```

Claude Code는:
1. `Glob`으로 파일 구조 탐색
2. `Read`로 핵심 파일(package.json, README, 설정 파일) 확인
3. `Grep`으로 진입점과 라우팅 파악
4. 분석 결과를 정리하여 설명

### 예시 2: 버그 수정

에러가 발생했을 때:

```text
> "TypeError: Cannot read properties of undefined" 에러가
> src/components/PostList.jsx에서 발생해. 원인을 찾고 수정해줘
```

Claude Code는:
1. 해당 파일을 `Read`로 확인
2. 관련 코드를 `Grep`으로 추적
3. 원인을 분석하고 `Edit`으로 수정
4. 수정 내용을 설명

### 예시 3: 새 기능 추가

기능을 추가할 때:

```text
> 사용자가 게시글에 좋아요를 누를 수 있는 기능을 추가해줘.
> 백엔드 API와 프론트엔드 UI 모두 구현해.
```

Claude Code는:
1. 기존 코드 패턴을 분석
2. 백엔드: 모델, 시리얼라이저, 뷰, URL 생성
3. 프론트엔드: API 함수, 컴포넌트 수정
4. 필요 시 마이그레이션 생성

---

## IDE 통합

### VS Code 확장

VS Code에서 Claude Code를 통합하여 사용할 수 있다:

1. VS Code 확장 마켓플레이스에서 "Claude Code" 검색 및 설치
2. `Cmd+Shift+P` → "Claude Code" 검색
3. 에디터 내에서 직접 Claude Code 대화 가능

### JetBrains 플러그인

IntelliJ IDEA, WebStorm 등 JetBrains IDE에서도 플러그인을 통해 사용할 수 있다.

### 데스크톱 앱

macOS, Windows용 데스크톱 앱도 제공되며, 터미널을 열지 않고도 Claude Code를 사용할 수 있다.

### 웹 앱

[claude.ai/code](https://claude.ai/code)에서 브라우저로 직접 접근할 수도 있다.

---

## 비용 관리

Claude Code는 Anthropic API를 사용하므로 토큰 사용량에 따른 비용이 발생한다.

### 비용 절약 팁

1. **Sonnet 모델 사용**: 일반 작업에는 `claude-sonnet-4-6`이 비용 대비 효율이 좋다
2. **`/compact` 활용**: 긴 대화가 이어지면 컨텍스트를 압축하여 토큰 절약
3. **구체적인 요청**: 모호한 요청은 불필요한 탐색을 유발 - 파일명, 함수명을 구체적으로 지정
4. **원샷 모드**: 단순 작업은 `-p` 플래그로 빠르게 처리
5. **Max 사용**: Anthropic Max 구독으로 고정 비용 사용 가능

### 토큰 사용량 확인

대화 종료 시 사용된 토큰 수가 표시된다. `/cost` 명령으로 현재 세션의 비용을 확인할 수도 있다.

---

## 문제 해결

### 일반적인 문제

| 문제 | 해결 |
|------|------|
| `command not found: claude` | `npm install -g @anthropic-ai/claude-code` 재설치 |
| 인증 실패 | `claude logout` 후 재로그인, 또는 API 키 환경변수 확인 |
| 느린 응답 | 모델을 Sonnet으로 전환하거나, `/compact`로 컨텍스트 축소 |
| 권한 오류 | `/permissions`에서 해당 도구의 권한 확인 |

### 도움 받기

- **공식 문서**: [docs.anthropic.com/claude-code](https://docs.anthropic.com/en/docs/claude-code/overview)
- **GitHub Issues**: [github.com/anthropics/claude-code](https://github.com/anthropics/claude-code/issues)
- **`/help`**: 대화 중 언제든 도움말 확인

---

## 정리

| 항목 | 내용 |
|------|------|
| 설치 | `npm install -g @anthropic-ai/claude-code` |
| 실행 | 프로젝트 디렉토리에서 `claude` |
| 설정 | `CLAUDE.md` 파일로 프로젝트별 지침 제공 |
| 모델 | `--model` 플래그 또는 `/model` 명령 |
| 비용 | 토큰 기반 과금, Sonnet이 비용 효율적 |
| 도움 | `/help` 명령 또는 공식 문서 |

다음 글 [[claude-code-guide-02-core|Claude Code 핵심 기능]]에서는 에이전틱 루프의 동작 원리와 도구 시스템을 심층적으로 분석한다.
