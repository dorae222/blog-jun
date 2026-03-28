# Codex CLI 시작하기: 설치와 기본 사용법

:::info
이 글은 **Codex CLI Guide** 시리즈의 첫 번째 글이다. 시리즈 전체 목차:
1. **설치와 기본 사용법** (현재 글)
2. [[codex-guide-02-core|핵심 기능: 샌드박스와 코드 생성]]
3. [[codex-guide-03-advanced|고급 활용: 자동화와 CI 통합]]
4. [[codex-guide-04-workflow|실전: 레거시 마이그레이션]]
:::

OpenAI가 공개한 **Codex CLI**는 터미널에서 직접 실행하는 AI 코딩 에이전트다. 로컬 환경에서 코드를 읽고, 수정하고, 실행할 수 있으며, Rust로 작성되어 빠르고 안전하다. 이 글에서는 Codex CLI의 설치부터 첫 사용까지를 단계별로 안내한다.

---

## 1. Codex CLI란 무엇인가

Codex CLI는 OpenAI가 개발한 오픈소스 AI 코딩 에이전트로, Apache-2.0 라이선스 하에 공개되어 있다. GitHub 저장소(`openai/codex`)에서 소스코드를 확인할 수 있다.

핵심 특징은 다음과 같다.

| 항목 | 설명 |
|------|------|
| 언어 | Rust (TypeScript에서 전환) |
| 라이선스 | Apache-2.0 |
| 플랫폼 | macOS, Linux (Windows는 실험적 지원) |
| 샌드박스 | 플랫폼 네이티브 (macOS: Seatbelt, Linux: Bubblewrap+Landlock) |
| 모델 | codex-mini-latest 기본, o4-mini, GPT-4.1 등 선택 가능 |
| 인증 | ChatGPT 계정 또는 API 키 |

초기 Codex CLI는 TypeScript와 Node.js 기반이었으나, 2025년 중반에 Rust로 완전히 재작성되었다. 이 전환으로 시작 시간이 약 150ms에서 50ms 미만으로 줄었고, 유휴 상태 메모리 사용량이 최대 60% 감소했다. Node.js 런타임 의존성이 제거되어 단일 바이너리로 설치할 수 있게 되었다.

:::tip
Codex CLI는 단순한 코드 생성 도구가 아니라 **에이전트(agent)**다. 파일을 읽고, 검색하고, 수정하고, 명령을 실행하는 전체 워크플로우를 자율적으로 수행할 수 있다.
:::

---

## 2. 사전 요구사항

Codex CLI를 설치하기 전에 다음 환경이 준비되어 있어야 한다.

### 운영체제

- **macOS** 12 (Monterey) 이상: Seatbelt 샌드박스 완전 지원
- **Linux**: 커널 5.13 이상 권장 (Landlock LSM 지원)
- **Windows**: 실험적 지원, WSL2 사용 권장

### 인증 수단

다음 중 하나가 필요하다.

- **ChatGPT 구독**: Plus($20/월), Pro($200/월), Team, Edu, Enterprise 플랜
- **OpenAI API 키**: platform.openai.com에서 발급

### 권장 환경

```bash
# Git이 설치되어 있어야 한다 (프로젝트 루트 탐지에 사용)
git --version

# Rust 설치 방법으로 진행할 경우 cargo 필요
cargo --version

# npm 설치 방법으로 진행할 경우 Node.js 필요
node --version
```

---

## 3. 설치 방법

Codex CLI는 세 가지 방법으로 설치할 수 있다.

### 3.1 npm을 통한 설치

가장 간단한 설치 방법이다. Node.js가 이미 설치되어 있다면 바로 사용할 수 있다.

```bash
npm install -g @openai/codex
```

설치 확인:

```bash
codex --version
```

### 3.2 Homebrew를 통한 설치 (macOS)

macOS 사용자는 Homebrew Cask로 설치할 수 있다.

```bash
brew install --cask codex
```

이 방법은 Rust 네이티브 바이너리를 직접 설치하므로 Node.js가 필요 없다.

### 3.3 GitHub Releases에서 바이너리 다운로드

`openai/codex`의 GitHub Releases 페이지에서 플랫폼별 바이너리를 직접 다운로드할 수 있다.

```bash
# 예시: Linux x86_64
curl -LO https://github.com/openai/codex/releases/latest/download/codex-linux-x86_64.tar.gz
tar xzf codex-linux-x86_64.tar.gz
sudo mv codex /usr/local/bin/
```

### 3.4 Cargo를 통한 빌드 (소스에서 직접)

Rust 개발 환경이 있다면 소스에서 직접 빌드할 수도 있다.

```bash
git clone https://github.com/openai/codex.git
cd codex/codex-rs
cargo build --release
```

빌드된 바이너리는 `target/release/codex`에 생성된다.

:::warning
소스 빌드는 최신 기능을 사용할 수 있지만, 안정성이 보장되지 않는 개발 버전일 수 있다. 프로덕션 환경에서는 공식 릴리즈 바이너리를 권장한다.
:::

---

## 4. OpenAI 인증 설정

Codex CLI를 사용하려면 OpenAI 인증이 필요하다. 두 가지 방식이 있다.

### 4.1 ChatGPT 계정으로 로그인 (권장)

처음 `codex`를 실행하면 로그인 프롬프트가 나타난다.

```bash
codex
# "Sign in with ChatGPT" 선택
# 브라우저가 열리며 OAuth 인증 진행
```

ChatGPT Plus, Pro, Team, Edu, Enterprise 플랜 구독자라면 추가 비용 없이 사용할 수 있다. 이 방법이 OpenAI에서 권장하는 인증 방식이다.

### 4.2 API 키를 통한 인증

CI/CD 파이프라인이나 브라우저가 없는 서버 환경에서는 API 키를 사용한다.

```bash
# 환경변수로 설정
export OPENAI_API_KEY="sk-your-api-key-here"

# 또는 codex login 명령 사용
codex login --api-key
```

API 키는 platform.openai.com/api-keys에서 발급받을 수 있다. 보안을 위해 셸 설정 파일에 직접 키를 넣는 대신, 비밀 관리 도구를 사용하는 것을 권장한다.

```bash
# .zshrc 또는 .bashrc에 추가하는 방법 (개인 환경만)
export OPENAI_API_KEY="sk-..."

# 또는 direnv를 사용하는 방법 (프로젝트별)
# .envrc 파일에 작성
export OPENAI_API_KEY="sk-..."
```

:::warning
API 키를 Git 저장소에 커밋하지 않도록 주의한다. `.gitignore`에 `.envrc`와 `.env` 파일을 반드시 추가하자.
:::

---

## 5. 모델 선택

Codex CLI는 여러 OpenAI 모델을 지원한다. 기본 모델은 **codex-mini-latest**로, 코딩 작업에 최적화된 경량 모델이다.

### 사용 가능한 주요 모델

| 모델 | 특징 | API 가격 (입력/출력, 1M 토큰) |
|------|------|------|
| codex-mini-latest | 코딩 최적화, 빠른 응답 (기본) | $1.50 / $6.00 |
| o4-mini | 추론 능력 강화 | 모델별 상이 |
| GPT-4.1 | 범용 고성능 | 모델별 상이 |

### 모델 변경 방법

```bash
# 명령줄 옵션으로 지정
codex --model o4-mini "테스트 코드를 작성해줘"

# 세션 중 변경
/model o4-mini
```

또는 설정 파일에서 기본 모델을 변경할 수 있다.

```toml
# ~/.codex/config.toml
model = "o4-mini"
model_provider = "openai"
```

:::tip
일반적인 코딩 작업에는 **codex-mini-latest**가 가장 효율적이다. 복잡한 아키텍처 설계나 대규모 리팩토링에는 GPT-4.1이나 o4-mini를 고려해보자. ChatGPT 계정으로 로그인한 경우, 세션 중 `/model` 명령으로 사용 가능한 모델 목록을 확인할 수 있다.
:::

---

## 6. 3가지 실행 모드

Codex CLI의 핵심 개념 중 하나는 **승인 정책(Approval Policy)**이다. 에이전트가 수행하는 작업에 대해 사용자가 어느 정도의 제어권을 가질지 결정한다.

### 모드 비교

| 모드 | 파일 편집 | 셸 명령 실행 | 네트워크 접근 | 사용 시나리오 |
|------|-----------|-------------|-------------|-------------|
| `suggest` | 승인 필요 | 승인 필요 | 차단 | 처음 사용, 민감한 코드 |
| `auto-edit` | 자동 허용 | 승인 필요 | 차단 | 일반 개발 작업 |
| `full-auto` | 자동 허용 | 자동 허용 | 허용 가능 | CI/CD, 자동화 |

### suggest 모드 (기본값)

가장 안전한 모드다. 모든 파일 수정과 명령 실행에 사용자 승인이 필요하다.

```bash
codex --suggest "이 프로젝트의 README를 업데이트해줘"
```

에이전트가 파일을 수정하거나 명령을 실행하려고 하면 diff를 보여주고 승인을 요청한다. `y`(승인), `n`(거부), `e`(편집 후 승인) 중 선택할 수 있다.

### auto-edit 모드

파일 생성과 수정은 자동으로 허용하지만, 셸 명령 실행은 여전히 승인이 필요하다.

```bash
codex --auto-edit "TypeScript 타입 에러를 모두 수정해줘"
```

코드 수정이 주된 작업일 때 효율적이다. 에이전트가 파일을 직접 수정하면서 `npm test` 같은 명령은 사용자에게 확인을 요청한다.

### full-auto 모드

모든 작업을 자동으로 수행한다. 셸 명령 실행과 네트워크 접근까지 허용할 수 있다.

```bash
codex --full-auto "테스트를 실행하고 실패하는 테스트를 수정해줘"
```

:::warning
`full-auto` 모드는 강력하지만, 에이전트가 예상치 못한 명령을 실행할 수 있다. 반드시 샌드박스가 활성화된 상태에서 사용하고, 신뢰할 수 있는 프로젝트에서만 사용하자.
:::

### 세션 중 모드 전환

대화형 세션에서는 `/mode` 명령으로 모드를 전환할 수 있다.

```bash
# 세션 중
/mode auto-edit
```

---

## 7. config.toml 설정 파일

Codex CLI의 모든 설정은 TOML 형식의 설정 파일로 관리된다.

### 설정 파일 위치와 우선순위

설정은 다음 순서로 적용된다 (위쪽이 높은 우선순위):

1. CLI 플래그 (`--model`, `--full-auto` 등)
2. 프로필 값
3. 프로젝트 설정 (`.codex/config.toml`)
4. 사용자 설정 (`~/.codex/config.toml`)
5. 시스템 설정 (`/etc/codex/config.toml`)
6. 기본값

### 기본 설정 파일 예시

```toml
# ~/.codex/config.toml

# 기본 모델 설정
model = "codex-mini-latest"
model_provider = "openai"

# 승인 정책: suggest, auto-edit, full-auto
# 또는 새로운 방식: untrusted, on-request, never
approval_policy = "on-request"

# 샌드박스 모드: read-only, workspace-write, danger-full-access
sandbox_mode = "workspace-write"
```

### 프로필 기능

서로 다른 작업 환경에 맞는 프로필을 정의할 수 있다.

```toml
# ~/.codex/config.toml

[profiles.safe]
model = "codex-mini-latest"
approval_policy = "suggest"
sandbox_mode = "read-only"

[profiles.dev]
model = "o4-mini"
approval_policy = "auto-edit"
sandbox_mode = "workspace-write"

[profiles.ci]
model = "codex-mini-latest"
approval_policy = "full-auto"
sandbox_mode = "workspace-write"
```

프로필 사용:

```bash
codex --profile dev "버그를 찾아서 수정해줘"
```

---

## 8. AGENTS.md 프로젝트 설정

Codex CLI는 프로젝트별 지시사항을 **AGENTS.md** 파일을 통해 전달받는다. 이는 Claude Code의 CLAUDE.md에 해당하는 기능이다.

### AGENTS.md 탐색 순서

Codex는 시작 시 다음 순서로 지시사항 파일을 찾는다:

1. **글로벌**: `~/.codex/AGENTS.override.md` 또는 `~/.codex/AGENTS.md`
2. **프로젝트**: Git 루트에서 현재 디렉터리까지의 경로를 순회하며 각 디렉터리에서 `AGENTS.override.md`, `AGENTS.md` 순서로 확인

### AGENTS.md 작성 예시

프로젝트 루트에 `AGENTS.md` 파일을 생성한다.

```markdown
# 프로젝트 지시사항

## 코드 스타일
- TypeScript strict 모드 사용
- ESLint + Prettier 설정을 따를 것
- 함수에는 JSDoc 주석을 반드시 포함

## 테스트
- Jest를 사용하며, 새 기능에는 반드시 테스트 추가
- 테스트 파일은 `__tests__` 디렉터리에 위치

## 금지 사항
- `any` 타입 사용 금지
- `console.log`를 프로덕션 코드에 남기지 않기
- 외부 패키지 추가 시 반드시 사유 설명

## 커밋 규칙
- Conventional Commits 형식 사용
- 한글 커밋 메시지 허용
```

:::tip
AGENTS.md는 에이전트의 행동을 제어하는 가장 중요한 수단이다. 팀 컨벤션, 금지 패턴, 테스트 정책 등을 명시하면 에이전트가 프로젝트 맥락에 맞는 코드를 생성한다.
:::

### 대체 파일명 설정

이미 다른 이름의 가이드 파일을 사용하고 있다면, config.toml에서 대체 파일명을 지정할 수 있다.

```toml
# .codex/config.toml
project_doc_fallback_filenames = ["TEAM_GUIDE.md", ".agents.md"]
```

이렇게 설정하면 Codex는 각 디렉터리에서 `AGENTS.override.md`, `AGENTS.md`, `TEAM_GUIDE.md`, `.agents.md` 순서로 탐색한다.

---

## 9. 대화형 모드와 원샷 모드

Codex CLI는 두 가지 사용 방식을 제공한다.

### 대화형 모드 (Interactive)

인자 없이 `codex`를 실행하면 대화형 TUI(Terminal User Interface)가 시작된다.

```bash
codex
```

대화형 모드에서는 여러 작업을 연속으로 지시할 수 있고, 이전 대화의 컨텍스트가 유지된다.

```
> 이 프로젝트의 구조를 분석해줘
[Codex가 파일 구조를 분석하고 설명]

> src/utils.ts에 있는 formatDate 함수에 테스트를 추가해줘
[Codex가 테스트 파일을 생성]

> 방금 만든 테스트를 실행해봐
[Codex가 테스트 실행 명령을 제안]
```

대화형 모드에서 사용할 수 있는 주요 슬래시 명령:

| 명령 | 설명 |
|------|------|
| `/mode` | 승인 모드 전환 |
| `/model` | 모델 변경 |
| `/help` | 도움말 표시 |
| `/clear` | 대화 기록 초기화 |

### 원샷 모드 (Non-interactive)

명령줄에 직접 프롬프트를 전달하면 원샷 모드로 실행된다.

```bash
# 단일 작업 수행
codex "이 프로젝트에서 사용하지 않는 import를 모두 제거해줘"

# full-auto 모드로 원샷 실행
codex --full-auto "package.json의 의존성 버전을 모두 최신으로 업데이트해줘"
```

원샷 모드는 스크립트나 자동화 파이프라인에서 유용하다. `codex exec` 명령을 사용하면 더 명시적으로 비대화형 실행을 지정할 수 있다.

```bash
codex exec --full-auto --sandbox workspace-write "린트 에러를 모두 수정해줘"
```

### 세션 이어가기

중단된 세션을 이어서 작업할 수도 있다.

```bash
codex resume
```

이 기능은 긴 작업이 중단되었거나, 이전 세션의 컨텍스트를 유지하고 싶을 때 유용하다. 컨텍스트 윈도우 한계에 가까워지면 자동으로 세션 요약(context compaction)이 수행된다.

---

## 10. 첫 사용 예시

실제로 Codex CLI를 사용하는 과정을 처음부터 끝까지 따라가 보자.

### 예시 1: 프로젝트 분석

```bash
# 프로젝트 디렉터리로 이동
cd ~/projects/my-app

# Codex 대화형 모드 시작
codex
```

대화형 모드에서:

```
> 이 프로젝트의 구조와 기술 스택을 분석해서 요약해줘
```

Codex는 자동으로 `list_dir`, `read_file` 등의 도구를 사용하여 프로젝트를 탐색하고, `package.json`, `tsconfig.json`, `Dockerfile` 등의 설정 파일을 읽어 기술 스택을 분석한다.

### 예시 2: 버그 수정

```bash
codex --auto-edit "src/api/handler.ts에서 발생하는 null reference 에러를 수정해줘"
```

Codex는 다음 과정을 거친다:

1. 해당 파일을 읽는다
2. 코드를 분석하여 null 참조 가능 지점을 찾는다
3. 수정 패치를 `apply_patch` 형식으로 생성한다
4. auto-edit 모드이므로 자동으로 파일에 적용한다

### 예시 3: 테스트 작성 및 실행

```bash
codex --auto-edit "src/utils/parser.ts의 parseConfig 함수에 대한 단위 테스트를 작성하고 실행해줘"
```

Codex의 동작:

1. `parser.ts`를 읽고 `parseConfig` 함수 시그니처와 로직 분석
2. 테스트 파일 생성 (auto-edit: 자동 허용)
3. `npm test` 실행 제안 (셸 명령: 승인 요청)
4. 사용자가 승인하면 테스트 실행
5. 실패하는 테스트가 있으면 수정 제안

---

## 11. 비용 정보

Codex CLI는 오픈소스이므로 도구 자체는 무료다. 비용은 사용하는 OpenAI 모델에 따라 발생한다.

### ChatGPT 구독으로 사용

| 플랜 | 월 요금 | Codex CLI 사용량 |
|------|---------|-----------------|
| Plus | $20 | 5시간당 30-150 메시지 |
| Pro | $200 | 5시간당 300-1,500 메시지 |
| Team | 인당 $25 | 팀 공유 할당량 |
| Enterprise | 협의 | 맞춤 할당량 |

ChatGPT 계정으로 로그인하면 구독 플랜의 Codex 할당량에서 차감되며, 추가 요금이 발생하지 않는다.

### API 키로 사용 (종량제)

API 키를 사용하면 토큰 단위로 과금된다.

| 모델 | 입력 (1M 토큰) | 출력 (1M 토큰) |
|------|---------------|---------------|
| codex-mini-latest | $1.50 | $6.00 |
| GPT-4.1 | 모델별 상이 | 모델별 상이 |

:::tip
개인 개발자라면 ChatGPT Plus 구독이 가장 경제적이다. CI/CD 자동화에는 API 키 방식이 적합하며, 사용량에 따른 종량제로 운영할 수 있다.
:::

### 비용 최적화 팁

- **codex-mini-latest**를 기본 모델로 사용하면 비용을 최소화할 수 있다
- AGENTS.md에 명확한 지시사항을 작성하면 불필요한 탐색과 토큰 소비를 줄일 수 있다
- 프로젝트의 `.codexignore` 또는 `.gitignore`를 활용하여 불필요한 파일 탐색을 방지한다
- 원샷 모드로 단일 작업을 수행하면 대화형 모드보다 토큰을 절약할 수 있다

---

## 마무리

이 글에서 다룬 내용을 정리하면 다음과 같다.

| 항목 | 핵심 내용 |
|------|----------|
| 설치 | npm, Homebrew, 바이너리, cargo 빌드 |
| 인증 | ChatGPT 계정(권장) 또는 API 키 |
| 모델 | codex-mini-latest 기본, 다양한 모델 선택 가능 |
| 실행 모드 | suggest(안전), auto-edit(균형), full-auto(자동화) |
| 설정 | config.toml + AGENTS.md로 프로젝트 맞춤 |
| 사용 방식 | 대화형 TUI 또는 원샷 명령 |

Codex CLI는 Rust 기반의 빠른 성능과 플랫폼 네이티브 샌드박스로 안전한 코드 작업을 보장하면서도, 직관적인 인터페이스로 접근성이 높은 도구다. AGENTS.md를 잘 작성하면 프로젝트의 컨벤션을 일관되게 유지하면서 AI의 도움을 받을 수 있다.

다음 글 [[codex-guide-02-core|Codex CLI 핵심 기능]]에서는 샌드박스 시스템과 코드 생성 기능을 상세히 분석한다.
