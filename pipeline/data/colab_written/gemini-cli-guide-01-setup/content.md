<!-- infographic-hero -->
![Getting Started with Gemini CLI 핵심 요약](figures/infographic.svg)

*Figure: Getting Started with Gemini CLI 한 장 요약 인포그래픽*

# Gemini CLI 시작하기: 설치와 기본 사용법

:::info
이 글은 **Gemini CLI Guide** 시리즈의 첫 번째 글이다. 시리즈 전체 목차:
1. **설치와 기본 사용법** (현재 글)
2. [[gemini-cli-guide-02-core|핵심 기능: 도구 시스템과 확장]]
3. [[gemini-cli-guide-03-advanced|고급 활용: Google 생태계 통합]]
4. [[gemini-cli-guide-04-workflow|실전: 프로젝트 적용 사례]]
:::

Google이 오픈소스로 공개한 **Gemini CLI**는 터미널에서 직접 Gemini의 AI 능력을 활용할 수 있는 에이전틱 코딩 도구다. Claude Code가 Anthropic의 터미널 AI 에이전트라면, Gemini CLI는 Google의 답이다. Apache-2.0 라이선스로 완전히 공개되어 있으며, 개인 Google 계정만 있으면 하루 1,000회 요청을 무료로 사용할 수 있다. 이 글에서는 Gemini CLI의 설치부터 기본 사용법까지 차근차근 알아본다.

---

## 1. Gemini CLI란 무엇인가

Gemini CLI는 Google이 개발한 오픈소스 AI 코딩 에이전트로, 터미널 환경에서 자연어를 통해 코드 작성, 디버깅, 리팩토링, 파일 관리, 웹 검색 등 다양한 작업을 수행할 수 있다. 단순한 코드 자동완성 도구가 아니라, **ReAct(Reason and Act) 루프** 기반의 에이전틱 시스템이다.

### 핵심 특징

| 특징 | 설명 |
|------|------|
| **오픈소스** | Apache-2.0 라이선스, GitHub에서 소스코드 전체 공개 |
| **무료 사용** | 개인 Google 계정으로 하루 1,000회, 분당 60회 요청 가능 |
| **대규모 컨텍스트** | Gemini 2.5 Pro 기반, 100만 토큰 컨텍스트 윈도우 |
| **에이전틱 루프** | 스스로 판단하고 도구를 호출하며 작업을 완수 |
| **확장 가능** | MCP(Model Context Protocol) 기반 확장 시스템 지원 |
| **멀티모달** | 이미지, 비디오 등 다양한 입력 형식 지원 |

### Gemini Code Assist와의 관계

Gemini CLI는 **Gemini Code Assist** 생태계의 일부다. Gemini Code Assist가 VS Code 확장 프로그램으로 IDE 안에서 동작한다면, Gemini CLI는 터미널에서 동작한다. 동일한 무료 라이선스를 공유하며, Google Cloud의 Standard/Enterprise 플랜과도 연동된다.

---

## 2. 사전 요구사항

Gemini CLI를 설치하기 전에 다음 요구사항을 확인하자.

### Node.js 20 이상

Gemini CLI는 Node.js 기반으로 동작한다. **Node.js 20 이상**이 필요하다 (초기에는 18 이상이었으나 2025년 9월부터 20 이상으로 상향되었다).

```bash
# Node.js 버전 확인
node --version
# v20.x.x 이상이어야 한다
```

Node.js가 설치되어 있지 않다면 공식 사이트에서 다운로드하거나 nvm을 사용한다.

```bash
# nvm으로 Node.js 20 LTS 설치
nvm install 20
nvm use 20
```

### Google 계정

인증을 위해 Google 계정이 필요하다. 개인 계정(Gmail)이면 무료 티어를 바로 사용할 수 있고, Google Workspace 계정이면 조직의 Gemini Code Assist 라이선스에 따라 사용 가능하다.

### 운영체제

macOS, Linux, Windows(WSL 포함) 모두 지원한다. macOS의 경우 기본 샌드박스로 Seatbelt을 사용하며, Linux/Windows에서는 Docker 기반 샌드박스를 권장한다.

---

## 3. 설치 방법

### npm 글로벌 설치 (권장)

가장 일반적인 설치 방법이다.

```bash
npm install -g @google/gemini-cli
```

설치가 완료되면 `gemini` 명령어를 사용할 수 있다.

```bash
# 설치 확인
gemini --version
```

### npx로 설치 없이 실행

글로벌 설치 없이 바로 실행할 수도 있다.

```bash
npx @google/gemini-cli
```

npx는 항상 최신 버전을 가져오므로 일회성 사용이나 테스트에 적합하다.

### 릴리스 채널

Gemini CLI는 세 가지 릴리스 채널을 제공한다.

| 채널 | 설명 | 설치 명령 |
|------|------|-----------|
| **stable** | 안정 버전 (기본값), 매주 릴리스 | `npm install -g @google/gemini-cli` |
| **preview** | 미리보기 버전, 새 기능 먼저 체험 | `npm install -g @google/gemini-cli@preview` |
| **nightly** | 야간 빌드, 최신 변경사항 포함 | `npm install -g @google/gemini-cli@nightly` |

:::tip
일반 사용자는 stable 채널을 권장한다. 새 기능을 먼저 써보고 싶다면 preview 채널을 사용하자.
:::

---

## 4. 인증 설정

Gemini CLI는 세 가지 인증 방법을 지원한다.

### 방법 1: Google OAuth 로그인 (권장)

가장 간편한 방법이다. 처음 `gemini`를 실행하면 자동으로 브라우저가 열리며 Google 로그인을 요청한다.

```bash
# 처음 실행시 자동으로 인증 흐름 시작
gemini
```

브라우저에서 Google 계정으로 로그인하면 인증 정보가 로컬에 캐시되어 이후 세션에서는 별도 로그인 없이 사용할 수 있다. 개인 Google 계정으로 로그인하면 무료 Gemini Code Assist 라이선스가 자동 부여된다.

### 방법 2: API 키

Google AI Studio에서 API 키를 발급받아 환경 변수로 설정하는 방법이다.

```bash
# API 키를 환경 변수로 설정
export GEMINI_API_KEY="your-api-key-here"
```

셸 프로필에 추가하면 영구적으로 적용된다.

```bash
# ~/.zshrc 또는 ~/.bashrc에 추가
echo 'export GEMINI_API_KEY="your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

:::warning
API 키는 민감한 정보이므로 Git 저장소에 절대 커밋하지 않도록 주의하자. `.env` 파일을 사용한다면 반드시 `.gitignore`에 추가해야 한다.
:::

### 방법 3: Vertex AI (Google Cloud)

엔터프라이즈 환경이나 Google Cloud를 사용하는 경우 Vertex AI를 통해 인증할 수 있다.

```bash
# gcloud CLI로 ADC(Application Default Credentials) 설정
gcloud auth application-default login

# 프로젝트와 리전 설정
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"
```

Vertex AI를 사용하면 조직의 보안 정책과 IAM 제어를 적용할 수 있으며, VPC 내부에서의 통신도 가능하다.

### 인증 방법 비교

| 방법 | 설정 난이도 | 비용 | 적합한 용도 |
|------|------------|------|------------|
| Google OAuth | 매우 쉬움 | 무료 (일일 한도 내) | 개인 개발, 학습 |
| API 키 | 쉬움 | 사용량 기반 | CI/CD, 자동화 |
| Vertex AI | 중간 | 사용량 기반 | 엔터프라이즈, 팀 |

---

## 5. GEMINI.md - 프로젝트 설정 파일

**GEMINI.md**는 Gemini CLI에게 프로젝트별 컨텍스트와 지시사항을 전달하는 마크다운 파일이다. Claude Code의 `CLAUDE.md`와 동일한 역할을 한다.

### GEMINI.md의 위치와 계층 구조

Gemini CLI는 여러 위치의 GEMINI.md를 자동으로 로드하고 병합한다.

```text
~/.gemini/GEMINI.md          # 글로벌 - 모든 프로젝트에 적용
프로젝트루트/GEMINI.md        # 프로젝트 루트 - 해당 프로젝트에 적용
프로젝트루트/.gemini/GEMINI.md # .gemini 디렉토리 내 - 해당 프로젝트에 적용
하위디렉토리/GEMINI.md        # 하위 디렉토리 - 해당 디렉토리에서만 적용
```

모든 발견된 파일의 내용이 연결(concatenate)되어 매 프롬프트와 함께 모델에 전달된다.

### GEMINI.md 작성 예시

```markdown
# Project: blog-jun

## 일반 지침
- TypeScript 코드를 작성할 때 기존 코딩 스타일을 따를 것
- 모든 새 함수와 클래스에 JSDoc 주석을 추가할 것
- 한국어 주석과 문서를 사용할 것

## 코딩 스타일
- 인덴트는 스페이스 2칸
- 세미콜론 항상 사용
- 타입은 명시적으로 선언

## 프로젝트 구조
- backend/: Django 5 + DRF
- frontend/: React 19 + Vite + Tailwind CSS v4
- pipeline/: 데이터 처리 파이프라인

## 금지 사항
- console.log 대신 적절한 로깅 라이브러리 사용
- any 타입 사용 금지
```

### 모듈화: 파일 임포트

GEMINI.md가 길어지면 `@path/to/file.md` 구문으로 다른 파일을 임포트할 수 있다.

```markdown
# 프로젝트 지침

@.gemini/coding-style.md
@.gemini/architecture.md
@.gemini/testing-guide.md
```

### 설정 파일 이름 커스터마이징

기본 파일 이름은 `GEMINI.md`이지만, `settings.json`에서 변경할 수 있다.

```json
{
  "context": {
    "fileName": ["GEMINI.md", "AI_CONTEXT.md"]
  }
}
```

---

## 6. 실행 모드

Gemini CLI는 세 가지 실행 모드를 제공한다.

### 대화형 모드 (Interactive Mode)

인자 없이 실행하면 대화형 REPL 환경이 시작된다.

```bash
# 기본 대화형 모드
gemini

# 초기 프롬프트와 함께 대화형 모드 시작
gemini -i "이 프로젝트의 구조를 분석해줘"
```

대화형 모드에서는 여러 번의 대화를 주고받으며 복잡한 작업을 수행할 수 있다. 이전 대화의 컨텍스트가 유지된다.

### 원샷 모드 (Headless/Prompt Mode)

`-p` 또는 `--prompt` 플래그를 사용하면 단일 질문에 대한 답변을 받고 바로 종료한다.

```bash
# 원샷 실행
gemini -p "package.json의 의존성을 분석하고 업데이트가 필요한 것을 알려줘"
```

원샷 모드는 TTY가 아닌 환경에서도 자동으로 활성화된다. CI/CD 파이프라인이나 스크립트에서 사용하기 적합하다.

### 파이프 모드 (Pipe Mode)

Unix 파이프(`|`)를 사용하여 다른 명령의 출력을 Gemini에게 전달할 수 있다.

```bash
# 로그 파일 분석
cat error.log | gemini -p "이 로그에서 에러 원인을 찾아줘"

# Git diff 리뷰
git diff | gemini -p "이 변경사항을 리뷰해줘"

# 파일 내용을 리디렉션으로 전달
gemini -p "이 코드를 리팩토링해줘" < legacy_code.py
```

파이프 모드는 기존 셸 워크플로우와 자연스럽게 통합된다.

### 모드 비교

| 모드 | 플래그 | 용도 | 컨텍스트 유지 |
|------|--------|------|--------------|
| 대화형 | 없음 또는 `-i` | 탐색적 작업, 복잡한 태스크 | O |
| 원샷 | `-p` | 단일 질문, 자동화 | X |
| 파이프 | `\|` + `-p` | 외부 데이터 분석 | X |

---

## 7. 슬래시 명령어와 뱅 명령어

대화형 모드에서 사용할 수 있는 특수 명령어들이 있다.

### 주요 슬래시 명령어

| 명령어 | 설명 |
|--------|------|
| `/help` | 사용 가능한 명령어 목록 표시 |
| `/tools` | 활성화된 도구 목록 표시 |
| `/stats` | 세션 통계 (토큰 사용량, 도구 호출 횟수 등) |
| `/clear` | 대화 컨텍스트 초기화 (새 대화 시작) |
| `/compress` | 현재 대화를 요약하여 컨텍스트 절약 |
| `/chat save` | 현재 대화를 태그 체크포인트로 저장 |
| `/chat load` | 저장된 체크포인트 불러오기 |
| `/chat export` | 대화를 마크다운 또는 JSON으로 내보내기 |
| `/memory show` | 현재 로드된 GEMINI.md 내용 표시 |
| `/memory reload` | GEMINI.md 파일 다시 로드 |
| `/settings` | 설정 확인 및 변경 |
| `/commands reload` | 커스텀 명령어 다시 로드 |

### 뱅 명령어

`!`로 시작하면 셸 명령어를 직접 실행할 수 있다.

```bash
# Gemini CLI 대화 중 셸 명령 실행
> !git status
> !ls -la src/
> !npm test
```

뱅 명령어는 Gemini 대화 컨텍스트를 벗어나지 않고 빠르게 시스템 명령을 확인할 때 유용하다.

### 키보드 단축키

| 단축키 | 기능 |
|--------|------|
| `Ctrl+L` | 화면 정리 (clear) |
| `Ctrl+Y` | YOLO 모드 토글 (자동 승인 on/off) |
| `Esc` 2회 | 입력 지우기 또는 이전 대화 탐색 |
| `Alt+Z` / `Cmd+Z` | 입력 실행 취소 |
| `Shift+Alt+Z` / `Shift+Cmd+Z` | 실행 취소 되돌리기 |

---

## 8. 첫 사용 예시

### 예시 1: 프로젝트 구조 파악

```bash
$ gemini
gemini> 이 프로젝트의 디렉토리 구조를 분석하고 아키텍처를 설명해줘
```

Gemini CLI가 자동으로 파일 시스템을 탐색하고, 주요 파일을 읽어 프로젝트 구조를 파악한다.

### 예시 2: 코드 설명

```bash
gemini> src/utils/auth.ts 파일의 로직을 설명해줘
```

지정된 파일을 읽고 코드의 동작 원리를 한국어로 설명한다.

### 예시 3: 버그 수정

```bash
gemini> npm test를 실행했더니 UserService.test.ts에서 실패해. 원인을 찾고 수정해줘
```

테스트를 실행하고, 실패 원인을 분석한 후, 코드를 수정하는 전체 과정을 자동으로 수행한다.

### 예시 4: 원샷으로 빠른 질문

```bash
$ gemini -p "Python에서 dataclass와 Pydantic BaseModel의 차이점을 표로 정리해줘"
```

### 예시 5: 파이프로 로그 분석

```bash
$ kubectl logs deployment/api-server --tail=100 | gemini -p "에러 패턴을 찾아서 원인과 해결방안을 제시해줘"
```

---

## 9. settings.json 설정

Gemini CLI의 동작을 세밀하게 조정하려면 `settings.json`을 편집한다.

### 설정 파일 위치

```text
~/.gemini/settings.json           # 글로벌 설정 (모든 프로젝트)
프로젝트루트/.gemini/settings.json  # 프로젝트 설정 (해당 프로젝트만)
```

프로젝트 설정이 글로벌 설정보다 우선한다.

### 주요 설정 항목

```json
{
  "general": {
    "defaultApprovalMode": "default",
    "theme": "system"
  },
  "context": {
    "fileName": "GEMINI.md"
  },
  "sandbox": {
    "enabled": true,
    "type": "seatbelt",
    "profile": "permissive-open"
  },
  "checkpointing": {
    "enabled": true
  }
}
```

### 승인 모드 설정

| 모드 | 설명 |
|------|------|
| `default` | 매 도구 호출마다 승인 요청 (기본값) |
| `auto_edit` | 파일 편집 도구는 자동 승인, 나머지는 확인 |
| `yolo` | 모든 도구 호출 자동 승인 (주의 필요!) |

```bash
# YOLO 모드로 시작 (명령줄 플래그)
gemini --yolo

# 또는 단축형
gemini -y
```

:::warning
YOLO 모드는 모든 도구 호출을 자동 승인하므로 위험할 수 있다. 샌드박스와 함께 사용하거나, 신뢰할 수 있는 프로젝트에서만 사용하자. `--yolo`와 `--sandbox`를 함께 사용하는 것이 권장된다.
:::

---

## 10. 비용과 요금제

### 무료 티어

개인 Google 계정으로 로그인하면 **무료 Gemini Code Assist 라이선스**가 자동 부여된다.

| 항목 | 무료 한도 |
|------|-----------|
| 일일 요청 수 | 1,000회 |
| 분당 요청 수 | 60회 |
| 모델 | Gemini 2.5 Pro |
| 컨텍스트 윈도우 | 100만 토큰 |

이 수준의 무료 제공량은 업계에서 가장 넉넉한 편이다. 일반적인 개인 개발에는 부족함이 없다.

### 유료 플랜

더 높은 한도가 필요하면 다음 옵션이 있다.

| 플랜 | 가격 | 대상 |
|------|------|------|
| Google AI Pro/Ultra | 개인 구독 | 높은 일일 한도 필요한 개인 |
| Code Assist Standard | $19/월/사용자 | 팀/비즈니스 |
| Code Assist Enterprise | $75/월/사용자 | 엔터프라이즈 조직 |

### API 키 사용시 비용

API 키로 직접 연결하는 경우 Gemini API의 표준 요금이 적용된다. 이 경우 무료 티어의 일일 한도와는 별도로 관리된다.

---

## 11. 문제 해결

### Node.js 버전 오류

```bash
# 오류: Node.js 버전이 20 미만인 경우
Error: Gemini CLI requires Node.js 20 or higher

# 해결: nvm으로 업그레이드
nvm install 20
nvm use 20
```

### 인증 오류

```bash
# OAuth 토큰 만료시 재인증
gemini auth login

# API 키가 올바른지 확인
echo $GEMINI_API_KEY
```

### 네트워크 오류

프록시 환경에서는 `HTTPS_PROXY` 환경 변수를 설정한다.

```bash
export HTTPS_PROXY="http://proxy.company.com:8080"
```

### 권한 오류 (macOS)

macOS에서 샌드박스 관련 권한 오류가 발생하면 다음을 확인한다.

```bash
# Seatbelt 샌드박스가 파일 접근을 차단하는 경우
# settings.json에서 샌드박스 프로필 조정
{
  "sandbox": {
    "profile": "permissive-open"
  }
}
```

---

## 12. 정리

이 글에서 다룬 내용을 정리하면 다음과 같다.

| 항목 | 내용 |
|------|------|
| **패키지 이름** | `@google/gemini-cli` |
| **설치 명령** | `npm install -g @google/gemini-cli` |
| **Node.js 요구사항** | 20 이상 |
| **인증 방법** | Google OAuth, API 키, Vertex AI |
| **설정 파일** | `GEMINI.md` (컨텍스트), `settings.json` (동작 설정) |
| **실행 모드** | 대화형, 원샷(`-p`), 파이프 |
| **무료 한도** | 일 1,000회, 분 60회 |
| **라이선스** | Apache-2.0 |

Gemini CLI는 설치가 간편하고, 무료 티어가 넉넉하며, Google 계정만 있으면 바로 시작할 수 있다. 오픈소스이기 때문에 내부 동작을 확인하고 필요하면 수정도 가능하다.

다음 글 [[gemini-cli-guide-02-core|Gemini CLI 핵심 기능]]에서는 도구 시스템과 확장 기능을 상세히 분석한다.
