# OpenCode 시작하기: 경량 터미널 AI 코딩 도구

:::info
이 글은 **OpenCode Guide** 시리즈의 첫 번째 글이다. 시리즈 전체 목차:
1. **경량 터미널 AI 코딩 도구** (현재 글)
2. [[opencode-guide-02-core|핵심 기능: 멀티 모델 지원과 TUI]]
3. [[opencode-guide-03-advanced|고급 활용: LSP 통합과 커스텀 설정]]
4. [[opencode-guide-04-workflow|실전: 팀 개발 환경 구축]]
:::

AI 코딩 도구의 시대가 열렸다. Cursor, GitHub Copilot, Claude Code 등 다양한 도구가 개발자의 생산성을 높이고 있지만, 대부분 특정 IDE에 종속되거나 하나의 모델 프로바이더만 지원한다. **OpenCode**는 이런 제약 없이 터미널에서 75개 이상의 AI 모델을 자유롭게 활용할 수 있는 오픈소스 코딩 에이전트다.

이 글에서는 OpenCode의 개념부터 설치, 초기 설정, 첫 사용까지 단계별로 살펴본다.

---

## OpenCode란 무엇인가

OpenCode는 터미널 기반의 AI 코딩 에이전트다. Go 언어로 작성되었으며, Charm 팀이 만든 **Bubble Tea** TUI(Terminal User Interface) 프레임워크를 기반으로 아름다운 터미널 인터페이스를 제공한다. 단순한 CLI 도구가 아니라, 파일 읽기/쓰기, 명령 실행, 코드 검색, LSP 통합 등 실질적인 코딩 작업을 수행할 수 있는 에이전트 시스템이다.

핵심 특징을 정리하면 다음과 같다.

| 항목 | 설명 |
|------|------|
| 언어 | Go (Golang) |
| TUI 프레임워크 | Bubble Tea (Charm) |
| 지원 모델 | 75+ (OpenAI, Anthropic, Google, Ollama 등) |
| 라이선스 | MIT |
| 세션 저장 | SQLite |
| LSP 지원 | 30+ 언어 서버 내장 |
| GitHub Stars | 95K+ (2026년 기준) |
| 플랫폼 | macOS, Linux, Windows (WSL) |

OpenCode의 가장 큰 강점은 **프로바이더 독립성**이다. Claude Code는 Anthropic 모델만, GitHub Copilot은 주로 OpenAI 모델만 사용할 수 있지만, OpenCode는 OpenAI, Anthropic, Google, Ollama, OpenRouter, Together AI 등 거의 모든 LLM 프로바이더를 지원한다. 심지어 Ollama를 통해 로컬 모델을 무료로 사용할 수도 있다.

---

## 프로젝트 상태: 아카이브와 Crush

OpenCode의 역사를 이해하는 것은 중요하다. 원래 OpenCode는 **Kujtim Hoxha**가 만든 프로젝트였다. 이후 SST(Serverless Stack) 팀의 Dax와 Adam이 주요 기여자로 참여하며 프로젝트가 성장했다.

2025년 7월, Charm 팀이 원저자 Kujtim을 영입하면서 프로젝트의 소유권 이전 과정에서 논란이 발생했다. Git 히스토리 재작성, 기여자 제거 등의 문제가 불거졌고, 결과적으로 다음과 같이 정리되었다.

| 프로젝트 | 관리 주체 | 저장소 | 상태 |
|----------|----------|--------|------|
| OpenCode | SST (Dax, Adam) → Anomaly | `anomalyco/opencode` | 활발히 개발 중 |
| Crush | Charm + 원저자 | `charmbracelet/crush` | 활발히 개발 중 |

:::warning
초기에는 OpenCode가 아카이브되고 Crush가 후속 프로젝트로 진행될 예정이었으나, 커뮤니티의 반발로 OpenCode는 SST 산하에서 독립적으로 계속 개발되고 있다. 2026년 현재 `anomalyco/opencode` 저장소에서 활발한 개발이 이루어지고 있으며, Crush는 별도 프로젝트로 병행 발전 중이다.
:::

두 프로젝트 모두 같은 뿌리에서 출발했지만, 현재는 각자의 방향으로 진화하고 있다. 이 시리즈에서는 OpenCode를 중심으로 다루되, 마지막 글에서 Crush와의 비교 및 마이그레이션도 함께 안내한다.

---

## 사전 요구사항

OpenCode를 설치하기 전에 다음 환경을 확인하자.

### 운영체제

- **macOS** 12 이상
- **Linux** - 대부분의 최신 배포판
- **Windows** 10/11 - WSL(Windows Subsystem for Linux) 필요

### 터미널 요구사항

- 모던 셸 지원 (bash, zsh, fish, PowerShell)
- 트루컬러(24-bit color) 지원 터미널 권장 (테마가 올바르게 표시됨)
- 권장 터미널: iTerm2 (macOS), WezTerm, Alacritty, Kitty, Windows Terminal

### Go (선택사항)

`go install`로 설치하려면 Go 1.23 이상이 필요하다.

```bash
# Go 버전 확인
go version
# go version go1.23.0 linux/amd64 이상이어야 함
```

Go가 없어도 다른 설치 방법을 사용할 수 있으므로 필수는 아니다.

---

## 설치 방법

OpenCode는 여러 가지 방법으로 설치할 수 있다. 환경에 맞는 방법을 선택하자.

### 방법 1: 빠른 설치 스크립트 (권장)

가장 간단한 방법이다. CPU 아키텍처(amd64/arm64)를 자동 감지하여 `~/.opencode/bin/opencode`에 설치한다.

```bash
curl -fsSL https://opencode.ai/install | bash
```

설치 후 PATH에 추가되었는지 확인하자.

```bash
# 설치 확인
opencode --version
```

### 방법 2: npm

Node.js 환경에서는 npm으로 설치할 수 있다.

```bash
npm i -g opencode-ai@latest
```

### 방법 3: Homebrew (macOS/Linux)

```bash
brew install anomalyco/tap/opencode
```

### 방법 4: go install

Go 개발자라면 소스에서 직접 빌드할 수 있다.

```bash
go install github.com/anomalyco/opencode@latest
```

:::tip
어떤 방법을 선택하든, 설치 후 `opencode --version`으로 정상 설치를 확인하자. 만약 명령어를 찾을 수 없다면 PATH 설정을 확인해야 한다.
:::

### 방법 5: 바이너리 직접 다운로드

GitHub Releases 페이지에서 플랫폼에 맞는 바이너리를 직접 다운로드할 수도 있다.

```bash
# 예: Linux amd64
wget https://github.com/anomalyco/opencode/releases/latest/download/opencode-linux-amd64
chmod +x opencode-linux-amd64
sudo mv opencode-linux-amd64 /usr/local/bin/opencode
```

### 설치 방법 비교

| 방법 | 장점 | 단점 |
|------|------|------|
| 설치 스크립트 | 가장 간단, 자동 감지 | curl 파이프 실행에 대한 보안 우려 |
| npm | Node.js 프로젝트와 통합 | Node.js 필요 |
| Homebrew | macOS 표준 패키지 관리 | macOS/Linux 전용 |
| go install | 소스 빌드, 최신 버전 | Go 1.23+ 필요 |
| 바이너리 | 의존성 없음 | 수동 업데이트 필요 |

---

## 초기 설정

설치가 완료되면 기본 설정을 진행한다.

### 설정 파일 구조

OpenCode의 설정은 여러 위치에서 로드되며, 나중에 로드되는 설정이 우선한다.

```text
1. Remote config    (.well-known/opencode)
2. Global config    (~/.config/opencode/opencode.json)
3. Custom config    (OPENCODE_CONFIG 환경 변수)
4. Project config   (프로젝트 루트의 opencode.json)
```

글로벌 설정 파일을 생성하자.

```bash
mkdir -p ~/.config/opencode
```

### API 키 설정

OpenCode를 사용하려면 최소 하나의 AI 프로바이더 API 키가 필요하다. 가장 일반적인 방법은 환경 변수를 통한 설정이다.

```bash
# ~/.zshrc 또는 ~/.bashrc에 추가
export OPENAI_API_KEY="sk-your-openai-key-here"
export ANTHROPIC_API_KEY="sk-ant-your-anthropic-key-here"
export GOOGLE_API_KEY="your-google-api-key-here"
```

환경 변수를 설정한 후 셸을 재시작하거나 `source` 명령을 실행한다.

```bash
source ~/.zshrc
```

또는 `opencode auth login` 명령으로 인증할 수도 있다. 이 경우 자격 증명은 `~/.local/share/opencode/auth.json`에 저장된다.

```bash
opencode auth login
```

---

## 멀티 모델 프로바이더 설정

OpenCode의 핵심 강점인 멀티 프로바이더 설정을 살펴보자. `~/.config/opencode/opencode.json`에서 프로바이더를 설정한다.

### 기본 프로바이더 설정

```json
{
  "provider": {
    "openai": {
      "apiKey": "{env:OPENAI_API_KEY}"
    },
    "anthropic": {
      "apiKey": "{env:ANTHROPIC_API_KEY}"
    },
    "google": {
      "apiKey": "{env:GOOGLE_API_KEY}"
    }
  },
  "model": "anthropic/claude-sonnet-4-20250514",
  "small_model": "openai/gpt-4.1-mini"
}
```

:::tip
`{env:VARIABLE_NAME}` 구문을 사용하면 API 키를 설정 파일에 직접 하드코딩하지 않아도 된다. 보안상 환경 변수 참조를 권장한다.
:::

### 주요 프로바이더별 설정

#### OpenAI

```json
{
  "provider": {
    "openai": {
      "apiKey": "{env:OPENAI_API_KEY}"
    }
  },
  "model": "openai/gpt-4.1"
}
```

사용 가능한 주요 모델: `gpt-4.1`, `gpt-4.1-mini`, `gpt-4.1-nano`, `o4-mini`

#### Anthropic

```json
{
  "provider": {
    "anthropic": {
      "apiKey": "{env:ANTHROPIC_API_KEY}"
    }
  },
  "model": "anthropic/claude-sonnet-4-20250514"
}
```

사용 가능한 주요 모델: `claude-opus-4-20250514`, `claude-sonnet-4-20250514`

#### Google Gemini

```json
{
  "provider": {
    "google": {
      "apiKey": "{env:GOOGLE_API_KEY}"
    }
  },
  "model": "google/gemini-2.5-pro"
}
```

#### Ollama (로컬 모델)

Ollama를 사용하면 API 비용 없이 로컬에서 모델을 실행할 수 있다.

```bash
# Ollama 설치 (macOS)
brew install ollama

# Ollama 서버 시작
ollama serve

# 모델 다운로드
ollama pull qwen2.5-coder:32b
```

OpenCode에서 Ollama를 사용하려면 별도의 API 키가 필요 없다. Ollama가 실행 중이면 자동으로 감지된다.

```json
{
  "provider": {
    "ollama": {}
  },
  "model": "ollama/qwen2.5-coder:32b"
}
```

#### OpenRouter

OpenRouter를 사용하면 하나의 API 키로 여러 프로바이더의 모델에 접근할 수 있다.

```json
{
  "provider": {
    "openrouter": {
      "apiKey": "{env:OPENROUTER_API_KEY}"
    }
  },
  "model": "openrouter/anthropic/claude-sonnet-4-20250514"
}
```

### 프로바이더 필터링

사용할 프로바이더를 명시적으로 제한할 수 있다.

```json
{
  "enabled_providers": ["openai", "anthropic", "ollama"]
}
```

이렇게 설정하면 지정된 프로바이더만 활성화되고 나머지는 무시된다.

---

## TUI 인터페이스 소개

OpenCode를 실행하면 Bubble Tea 기반의 아름다운 TUI가 나타난다.

### 실행

프로젝트 디렉토리에서 OpenCode를 실행한다.

```bash
cd ~/my-project
opencode
```

### 인터페이스 구성

TUI는 다음과 같은 영역으로 구성된다.

| 영역 | 설명 |
|------|------|
| 프롬프트 입력 | 하단의 텍스트 입력 영역. AI에게 지시를 입력한다 |
| 대화 영역 | 중앙의 메인 영역. AI 응답과 도구 실행 결과가 표시된다 |
| 상태 바 | 현재 모델, 세션, 토큰 사용량 등 상태 정보 |
| 사이드 패널 | 파일 트리, 세션 목록 등 보조 정보 |

### 상호작용 방식

OpenCode TUI에서는 세 가지 방식으로 상호작용한다.

1. **슬래시 명령** - 프롬프트에 `/`로 시작하는 명령 입력 (예: `/help`, `/theme`, `/model`)
2. **커맨드 팔레트** - `Ctrl+K`로 열어 모든 명령 검색
3. **키보드 단축키** - 자주 쓰는 동작에 직접 단축키 사용

### 파일 참조와 셸 명령

프롬프트에서 `@` 기호로 파일을 참조할 수 있다. 퍼지 검색으로 현재 프로젝트의 파일을 빠르게 찾는다.

```text
이 파일을 리팩토링해줘 @src/main.go
```

`!` 기호로 시작하면 셸 명령의 출력을 프롬프트에 주입할 수 있다.

```text
!git diff HEAD~3 이 변경사항을 리뷰해줘
```

---

## 첫 사용 예시

실제로 OpenCode를 사용해보자. 간단한 Go 프로젝트를 만들어보겠다.

### 1단계: 프로젝트 초기화

```bash
mkdir ~/hello-opencode && cd ~/hello-opencode
go mod init hello-opencode
opencode
```

### 2단계: 코드 생성 요청

OpenCode TUI가 열리면 프롬프트에 다음과 같이 입력한다.

```text
간단한 HTTP 서버를 만들어줘. /hello 엔드포인트에서 JSON 응답을 반환하도록 해줘.
```

OpenCode는 AI 모델을 호출하고, 필요한 도구(파일 쓰기, 명령 실행 등)를 자동으로 사용하여 코드를 생성한다.

### 3단계: 결과 확인

AI가 생성한 파일을 확인한다.

```text
@main.go 이 코드를 설명해줘
```

### 4단계: 실행과 테스트

```text
이 서버를 실행하고 테스트해줘
```

OpenCode는 `go run main.go`를 실행하고, 별도의 요청으로 테스트까지 수행할 수 있다.

### 5단계: AGENTS.md 생성

프로젝트에 맞는 커스텀 지시사항을 생성하자.

```text
/init
```

`/init` 명령은 프로젝트를 스캔하고 자동으로 `AGENTS.md` 파일을 생성한다. 이 파일은 AI에게 프로젝트의 컨텍스트와 규칙을 알려주는 역할을 한다.

---

## 키보드 단축키

OpenCode는 **리더 키(Leader Key)** 시스템을 사용한다. 기본 리더 키는 `Ctrl+X`이며, 대부분의 단축키는 리더 키를 먼저 누른 후 조합 키를 입력하는 방식이다.

### 기본 단축키

| 단축키 | 동작 |
|--------|------|
| `Ctrl+K` | 커맨드 팔레트 열기 |
| `Ctrl+X` → `h` | 도움말 표시 |
| `Ctrl+X` → `n` | 새 세션 |
| `Ctrl+X` → `s` | 세션 목록 |
| `Ctrl+X` → `m` | 모델 변경 |
| `Ctrl+C` | 현재 작업 중단 |
| `Ctrl+D` | OpenCode 종료 |
| `Enter` | 메시지 전송 |
| `Shift+Enter` | 줄바꿈 |

### 슬래시 명령

| 명령 | 설명 |
|------|------|
| `/help` | 사용 가능한 명령 목록 |
| `/model` | 모델 변경 |
| `/theme` | 테마 변경 |
| `/init` | AGENTS.md 생성 |
| `/compact` | 대화 요약 (컨텍스트 정리) |
| `/clear` | 대화 내용 초기화 |
| `/session` | 세션 관리 |

:::tip
리더 키가 기존 터미널 단축키와 충돌하는 경우, `opencode.json`의 `keybinds` 설정에서 변경할 수 있다. 상세한 키 커스터마이징은 세 번째 글에서 다룬다.
:::

---

## CLI 모드

TUI 외에도 OpenCode는 CLI 모드를 지원한다. TUI 없이 명령줄에서 직접 사용할 수 있다.

```bash
# 단일 프롬프트 실행
opencode -m "이 프로젝트의 구조를 설명해줘"

# 파이프 입력
cat error.log | opencode -m "이 에러를 분석해줘"

# 디버그 모드
opencode -d
```

CI/CD 파이프라인이나 스크립트에서 OpenCode를 활용할 때 유용하다.

---

## 기본 에이전트 이해

OpenCode에는 두 가지 기본 에이전트가 있다.

| 에이전트 | 역할 | 도구 접근 |
|----------|------|-----------|
| **Build** | 기본 에이전트. 코드 작성, 파일 수정, 명령 실행 등 모든 개발 작업 수행 | 모든 도구 활성화 |
| **Plan** | 분석 전용 에이전트. 코드 탐색, 계획 수립, 리뷰 | 읽기 전용 (파일 수정 불가) |

에이전트를 전환하려면 커맨드 팔레트(`Ctrl+K`)에서 선택하거나 슬래시 명령을 사용한다. Plan 에이전트는 코드를 분석하고 계획을 세운 뒤, Build 에이전트가 실제 구현을 담당하는 워크플로우가 가능하다.

---

## 문제 해결

### 설치 후 명령어를 찾을 수 없는 경우

```bash
# PATH 확인 및 추가
export PATH="$HOME/.opencode/bin:$PATH"

# 영구 적용 (~/.zshrc 또는 ~/.bashrc에 추가)
echo 'export PATH="$HOME/.opencode/bin:$PATH"' >> ~/.zshrc
```

### API 키 인식 실패

```bash
# 환경 변수 확인
echo $OPENAI_API_KEY

# opencode.json에서 직접 확인
cat ~/.config/opencode/opencode.json
```

### 디버그 로그 활성화

문제가 발생하면 디버그 모드로 상세 로그를 확인할 수 있다.

```bash
# 디버그 모드 실행
opencode --debug

# 또는 로그 레벨 지정
opencode --log-level DEBUG
```

### 터미널 색상 문제

테마가 올바르게 표시되지 않는다면 터미널의 트루컬러 지원을 확인하자.

```bash
# 트루컬러 지원 테스트
printf "\x1b[38;2;255;100;0mTruecolor Test\x1b[0m\n"
```

위 명령의 텍스트가 주황색으로 표시되면 트루컬러가 지원되는 것이다.

---

## 정리

이 글에서 다룬 내용을 정리하면 다음과 같다.

- **OpenCode**는 Go + Bubble Tea 기반의 오픈소스 터미널 AI 코딩 에이전트다
- 75개 이상의 AI 모델을 지원하며, Ollama를 통해 로컬 모델도 무료로 사용 가능하다
- 설치는 `curl` 스크립트, npm, Homebrew, `go install`, 바이너리 다운로드 등 다양한 방법을 제공한다
- API 키는 환경 변수 또는 설정 파일에서 `{env:VARIABLE}` 구문으로 안전하게 관리한다
- TUI는 슬래시 명령, 커맨드 팔레트, 키보드 단축키로 조작한다
- Build(개발)와 Plan(분석) 두 가지 기본 에이전트를 제공한다

OpenCode는 특정 벤더에 종속되지 않으면서도 강력한 AI 코딩 경험을 제공하는 도구다. 오픈소스라는 특성 덕분에 자유롭게 커스터마이징하고 확장할 수 있다.

다음 글 [[opencode-guide-02-core|OpenCode 핵심 기능]]에서는 멀티 모델 지원과 TUI 인터페이스를 상세히 분석한다.
