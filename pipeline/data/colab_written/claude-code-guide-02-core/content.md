# Claude Code 핵심 기능: 도구 시스템과 에이전틱 루프

:::info
이 글은 **Claude Code Guide** 시리즈의 두 번째 글로, 핵심 도구 시스템과 에이전틱 루프를 다룬다. 시리즈 전체 목차는 다음과 같다:
1. [[claude-code-guide-01-setup|설치와 기본 사용법]]
2. **핵심 기능: 도구 시스템과 에이전틱 루프** (현재 글)
3. [[claude-code-guide-03-advanced|고급 활용: MCP 서버와 서브에이전트]]
4. [[claude-code-guide-04-workflow|실전: 프로젝트 관리와 워크플로우]]
5. [[claude-code-guide-05-comparison|AI 코딩 에이전트 비교]]
:::

Claude Code가 단순한 채팅봇이 아니라 **자율적인 소프트웨어 엔지니어**처럼 동작할 수 있는 이유는 두 가지 핵심 메커니즘에 있다. 하나는 반복적으로 스스로 판단하고 행동하는 **에이전틱 루프**(Agentic Loop)이고, 다른 하나는 파일 시스템, 셸, 검색 등 실제 개발 환경과 상호작용하는 **도구 시스템**(Tool System)이다.

이 글에서는 Claude Code의 에이전틱 루프가 어떻게 동작하는지, 어떤 도구들이 있고 각각 어떤 역할을 하는지, 권한은 어떻게 제어하는지, 그리고 컨텍스트를 어떻게 관리하는지를 실전 예시와 함께 상세히 다룬다.

---

## 에이전틱 루프 동작 원리

### 핵심 아키텍처: 계획 - 실행 - 관찰 - 반복

Claude Code의 에이전틱 루프는 LLM이 한 번의 응답으로 끝나는 것이 아니라, **목표가 달성될 때까지 스스로 판단하고 행동을 반복**하는 구조다. 전통적인 챗봇이 "질문 - 답변"의 1회성 패턴이라면, 에이전틱 루프는 "계획 - 실행 - 관찰 - 반복"의 순환 패턴이다.

```
사용자 메시지
    │
    ▼
┌──────────────────────────────┐
│  1. 작업 분석 (Planning)      │
│     - 요청 파악              │
│     - 필요한 정보 판단        │
│     - 실행 전략 수립          │
├──────────────────────────────┤
│  2. 도구 선택 (Tool Selection)│
│     - 적합한 도구 결정        │
│     - 파라미터 구성           │
├──────────────────────────────┤
│  3. 도구 실행 (Execution)     │
│     - 도구 호출              │
│     - 결과 수신              │
├──────────────────────────────┤
│  4. 결과 관찰 (Observation)   │
│     - 실행 결과 분석          │
│     - 성공/실패 판단          │
├──────────────────────────────┤
│  5. 다음 행동 결정 (Decision) │
│     - 추가 작업 필요? → 1로   │
│     - 완료? → 사용자에게 응답  │
└──────────────────────────────┘
```

예를 들어 "이 프로젝트의 미사용 import를 정리해줘"라고 요청하면, Claude Code는 다음과 같이 동작한다:

1. **작업 분석**: 프로젝트의 모든 소스 파일에서 사용되지 않는 import를 찾아 제거해야 한다
2. **도구 선택**: 먼저 `Glob`으로 소스 파일 목록을 파악한다
3. **도구 실행**: `Glob("**/*.ts")` 호출
4. **결과 관찰**: 파일 목록을 받아 각 파일을 분석할 필요가 있다고 판단
5. **다음 행동**: 각 파일을 `Read`로 읽고, 미사용 import를 찾아 `Edit`으로 제거

이 과정에서 핵심은 **5단계에서 1단계로 되돌아가는 루프**다. 하나의 도구 실행이 끝나면 Claude Code는 결과를 관찰하고, 목표 달성 여부를 판단한 뒤, 필요하면 다음 도구를 호출한다. 이 루프가 목표가 완전히 달성될 때까지 반복된다.

### 자동 연쇄 호출

단일 요청에서 여러 도구가 자동으로 연쇄적으로 호출되는 것이 에이전틱 루프의 핵심 특성이다. 사용자가 "버그를 찾아서 고쳐줘"라고 한 번만 말하면:

```
Glob → Read → Grep → Read → Edit → Bash(테스트) → 완료
```

이 전체 체인이 사용자 개입 없이 자동으로 실행된다. 중간에 사용자가 각 단계를 지시할 필요가 없다.

### 에러 자동 복구

에이전틱 루프의 강력한 특성 중 하나는 **에러 발생 시 자동 복구를 시도**한다는 점이다. 예를 들어:

1. `Bash`로 테스트를 실행했더니 실패
2. 실패 메시지를 분석하여 원인 파악
3. `Read`로 관련 코드를 확인
4. `Edit`로 코드 수정
5. `Bash`로 테스트를 재실행하여 성공 확인

이 전 과정이 하나의 요청 안에서 자동으로 이뤄진다. Claude Code가 "테스트가 실패했으니 사용자에게 물어봐야겠다"고 판단하지 않고, 스스로 원인을 분석하고 수정을 시도한다.

### 병렬 도구 호출

독립적인 작업이 여러 개 있을 때, Claude Code는 이를 **병렬로 동시에 실행**할 수 있다. 예를 들어 여러 파일의 내용을 동시에 읽거나, 서로 관련 없는 검색을 동시에 수행한다:

```
┌─ Read("src/api.ts")
│
├─ Read("src/types.ts")     ← 3개를 동시에 실행
│
└─ Read("src/utils.ts")
```

병렬 실행은 전체 작업 시간을 크게 단축한다. 순차적으로 3개 파일을 읽으면 3번의 왕복이 필요하지만, 병렬로 읽으면 1번의 왕복으로 충분하다.

:::tip
Claude Code에게 요청할 때 "먼저 A를 하고, 그 다음 B를 해줘"처럼 순서를 지정하면 순차 실행된다. 반면 "A와 B를 해줘"처럼 요청하면 독립적인 작업은 자동으로 병렬 실행된다.
:::

---

## 도구 시스템 상세

Claude Code가 사용할 수 있는 도구는 크게 **파일 탐색/읽기**, **파일 수정**, **시스템 실행**, **에이전트**, **웹**, **작업 관리** 카테고리로 나뉜다. 각 도구의 역할과 주요 파라미터를 상세히 살펴보자.

### 파일 탐색/읽기 도구

#### Read - 파일 읽기

`Read`는 로컬 파일 시스템에서 파일을 읽는 도구다. 단순한 텍스트 파일뿐 아니라 이미지, PDF, Jupyter 노트북까지 지원한다.

| 파라미터 | 설명 | 예시 |
|----------|------|------|
| `file_path` | 읽을 파일의 절대 경로 (필수) | `/home/user/project/src/app.ts` |
| `offset` | 읽기 시작할 라인 번호 | `100` (100번째 줄부터) |
| `limit` | 읽을 라인 수 | `50` (50줄만) |
| `pages` | PDF 페이지 범위 | `"1-5"` |

주요 특성:
- 기본적으로 파일의 처음 2000줄을 읽는다
- 결과는 `cat -n` 형식으로 라인 번호가 포함된다
- 이미지 파일을 읽으면 시각적으로 내용을 인식한다 (멀티모달)
- PDF는 최대 20페이지까지 한 번에 읽을 수 있다
- 대용량 파일은 `offset`과 `limit`으로 필요한 부분만 읽어야 한다

```json
{
  "tool": "Read",
  "file_path": "/home/user/project/src/components/Header.tsx",
  "offset": 50,
  "limit": 30
}
```

#### Glob - 파일 패턴 매칭

`Glob`은 글로브 패턴으로 파일을 검색하는 도구다. 프로젝트 내에서 특정 확장자나 이름 패턴의 파일을 빠르게 찾을 때 사용한다.

| 파라미터 | 설명 | 예시 |
|----------|------|------|
| `pattern` | 글로브 패턴 (필수) | `**/*.tsx` |
| `path` | 검색 시작 디렉토리 | `/home/user/project/src` |

사용 예시:

```json
// 모든 TypeScript 컴포넌트 파일 찾기
{ "pattern": "**/*.tsx", "path": "/home/user/project/src" }

// 특정 이름 패턴의 파일 찾기
{ "pattern": "**/test_*.py" }

// 설정 파일 찾기
{ "pattern": "**/{tsconfig,jest.config,vite.config}.*" }
```

결과는 수정 시간 기준으로 정렬되어 반환된다. 최근 수정된 파일이 먼저 나오므로 활발히 작업 중인 파일을 빠르게 파악할 수 있다.

#### Grep - 코드 내용 검색

`Grep`은 ripgrep 기반의 강력한 코드 검색 도구다. 정규식을 지원하며, 파일 내용을 검색할 때 `Glob`보다 훨씬 세밀한 제어가 가능하다.

| 파라미터 | 설명 | 예시 |
|----------|------|------|
| `pattern` | 정규식 패턴 (필수) | `function\s+\w+` |
| `path` | 검색 경로 | `/home/user/project/src` |
| `glob` | 파일 필터 | `"*.ts"` |
| `type` | 파일 타입 | `"py"`, `"js"`, `"rust"` |
| `output_mode` | 출력 모드 | `"content"`, `"files_with_matches"`, `"count"` |
| `-A`, `-B`, `-C` | 전후 컨텍스트 줄 수 | `-C: 3` (전후 3줄) |
| `-i` | 대소문자 무시 | `true` |
| `multiline` | 여러 줄 매칭 | `true` |

세 가지 출력 모드:
- `files_with_matches` (기본): 매칭된 파일 경로만 반환
- `content`: 매칭된 줄과 주변 컨텍스트를 반환
- `count`: 파일별 매칭 횟수를 반환

```json
// 특정 함수가 호출되는 모든 위치 찾기
{
  "pattern": "useAuth\\(",
  "type": "tsx",
  "output_mode": "content",
  "-C": 2
}

// Python 파일에서 클래스 정의 찾기
{
  "pattern": "class\\s+\\w+Model",
  "glob": "*.py",
  "output_mode": "files_with_matches"
}
```

:::tip
`Grep`은 기본적으로 결과를 250줄로 제한한다. 더 많은 결과가 필요하면 `head_limit` 파라미터를 조정하고, 결과가 너무 많으면 `glob`이나 `type`으로 검색 범위를 좁혀야 한다.
:::

---

### 파일 수정 도구

#### Edit - 정확한 문자열 치환

`Edit`는 파일 내용을 수정하는 핵심 도구다. 전체 파일을 덮어쓰는 것이 아니라, **정확한 문자열 매칭으로 특정 부분만 치환**한다.

| 파라미터 | 설명 | 예시 |
|----------|------|------|
| `file_path` | 수정할 파일 경로 (필수) | `/home/user/project/src/app.ts` |
| `old_string` | 대체할 기존 문자열 (필수) | `const x = 1;` |
| `new_string` | 새로운 문자열 (필수) | `const x = 2;` |
| `replace_all` | 모든 매칭 치환 여부 | `false` (기본) |

핵심 규칙:
- `old_string`이 파일 내에서 **유일해야** 한다. 중복되면 에러가 발생한다.
- 중복 시에는 더 많은 주변 컨텍스트를 포함하여 유일하게 만들거나, `replace_all: true`를 사용한다.
- 파일의 들여쓰기(탭/스페이스)를 정확히 맞춰야 한다.
- `Read`로 파일을 먼저 읽지 않으면 `Edit`이 실패한다.

```json
{
  "tool": "Edit",
  "file_path": "/home/user/project/src/utils.ts",
  "old_string": "export function calculateTotal(items) {\n  return items.reduce((sum, item) => sum + item.price, 0);\n}",
  "new_string": "export function calculateTotal(items) {\n  return items.reduce((sum, item) => sum + item.price * item.quantity, 0);\n}"
}
```

`replace_all` 옵션은 변수명 변경처럼 파일 전체에서 같은 문자열을 일괄 치환할 때 유용하다:

```json
{
  "tool": "Edit",
  "file_path": "/home/user/project/src/app.ts",
  "old_string": "oldVariableName",
  "new_string": "newVariableName",
  "replace_all": true
}
```

#### Write - 새 파일 생성 또는 전체 덮어쓰기

`Write`는 파일을 새로 생성하거나 기존 파일의 전체 내용을 교체할 때 사용한다.

| 파라미터 | 설명 |
|----------|------|
| `file_path` | 파일의 절대 경로 (필수) |
| `content` | 파일에 쓸 내용 (필수) |

주요 특성:
- 기존 파일이 있으면 **전체를 덮어쓴다**
- 기존 파일을 수정할 때는 `Edit`이 더 적절하다 (diff만 전송하므로 효율적)
- 새 파일 생성 시 주로 사용한다

:::warning
`Write`로 기존 파일을 수정하면 전체 내용을 다시 전송해야 하므로 토큰 사용량이 증가한다. 기존 파일의 일부만 수정할 때는 반드시 `Edit`을 사용하자.
:::

---

### 시스템 실행 도구

#### Bash - 셸 명령 실행

`Bash`는 Claude Code에서 가장 다재다능한 도구다. 빌드, 테스트, Git 작업, 패키지 관리 등 셸에서 할 수 있는 모든 작업을 수행한다.

| 파라미터 | 설명 | 예시 |
|----------|------|------|
| `command` | 실행할 셸 명령 (필수) | `npm test` |
| `description` | 명령 설명 | `"단위 테스트 실행"` |
| `timeout` | 타임아웃(ms) | `300000` (5분) |
| `run_in_background` | 백그라운드 실행 | `true` |

주요 특성:
- 기본 타임아웃은 **2분** (120,000ms), 최대 **10분** (600,000ms)
- 작업 디렉토리는 호출 간에 유지되지 않는다 (매번 초기화)
- `run_in_background: true`로 장시간 작업을 백그라운드에서 실행 가능
- 여러 명령을 `&&`로 연결하여 순차 실행 가능

자주 사용되는 명령 예시:

```bash
# 빌드
npm run build

# 테스트
pytest tests/ -v

# Git 작업
git status && git diff --staged

# 의존성 설치
npm install express

# 서비스 상태 확인
docker compose ps
```

:::warning
`Bash`는 시스템에 직접 접근하므로 가장 강력하면서도 위험한 도구다. `rm -rf /`, `git push --force` 같은 파괴적 명령이 실행될 수 있으므로 권한 설정이 중요하다. 자세한 내용은 아래 권한 시스템 섹션에서 다룬다.
:::

---

### 에이전트 도구

#### Agent - 서브에이전트 생성

`Agent`는 독립적인 서브에이전트를 생성하여 특화된 작업을 수행하게 하는 도구다. 메인 에이전트의 컨텍스트를 오염시키지 않으면서 복잡한 탐색이나 분석을 위임할 수 있다.

| 파라미터 | 설명 | 예시 |
|----------|------|------|
| `prompt` | 서브에이전트에게 전달할 작업 지시 | `"src 디렉토리의 모든 API 엔드포인트를 분석해"` |
| `isolation` | 격리 모드 | `"worktree"` |

서브에이전트 활용 시나리오:
- **탐색**: 대규모 코드베이스에서 특정 패턴을 조사
- **분석**: 복잡한 의존성 트리를 추적
- **계획**: 리팩토링 계획을 수립
- **병렬 작업**: 여러 독립적인 분석을 동시에 수행

`isolation: "worktree"` 옵션을 사용하면 Git worktree를 활용한 격리된 환경에서 작업한다. 이 모드에서는 서브에이전트의 파일 수정이 메인 작업 디렉토리에 영향을 주지 않는다.

```json
{
  "tool": "Agent",
  "prompt": "이 프로젝트에서 순환 의존성이 있는지 분석하고, 있다면 어떤 모듈 간에 발생하는지 목록으로 정리해줘",
  "isolation": "worktree"
}
```

:::info
서브에이전트는 메인 에이전트와 동일한 도구(Read, Grep, Bash 등)를 사용할 수 있지만, 독립적인 컨텍스트 윈도우를 가진다. 따라서 메인 에이전트의 컨텍스트를 소비하지 않는다는 큰 장점이 있다.
:::

---

### 웹 도구

#### WebSearch - 웹 검색

최신 정보나 외부 레퍼런스가 필요할 때 웹 검색을 수행한다.

```json
{
  "tool": "WebSearch",
  "query": "React 19 useOptimistic hook usage"
}
```

#### WebFetch - URL 콘텐츠 가져오기

특정 URL에서 콘텐츠를 가져올 때 사용한다. 문서, API 레퍼런스, 이슈 페이지 등을 직접 읽을 수 있다.

```json
{
  "tool": "WebFetch",
  "url": "https://docs.python.org/3/library/asyncio.html"
}
```

---

### 작업 관리 도구

#### TaskCreate, TaskUpdate, TaskList

장기 실행 작업이나 복잡한 멀티스텝 작업을 관리하는 도구다.

| 도구 | 역할 |
|------|------|
| `TaskCreate` | 새로운 작업(Task) 생성, 서브에이전트에 위임 |
| `TaskUpdate` | 작업 상태 업데이트 (진행 중, 완료, 실패) |
| `TaskList` | 현재 진행 중인 작업 목록 조회 |

이 도구들은 주로 복잡한 리팩토링이나 대규모 코드 변환처럼 여러 서브에이전트가 병렬로 작업해야 할 때 사용된다.

---

### 도구 시스템 요약

전체 도구를 카테고리별로 정리하면 다음과 같다:

| 카테고리 | 도구 | 핵심 역할 |
|----------|------|-----------|
| 탐색/읽기 | `Read` | 파일 읽기 (텍스트, 이미지, PDF) |
| 탐색/읽기 | `Glob` | 파일 이름/경로 패턴 검색 |
| 탐색/읽기 | `Grep` | 파일 내용 검색 (ripgrep) |
| 수정 | `Edit` | 문자열 치환으로 파일 수정 |
| 수정 | `Write` | 새 파일 생성 / 전체 덮어쓰기 |
| 실행 | `Bash` | 셸 명령 실행 |
| 에이전트 | `Agent` | 서브에이전트 생성/위임 |
| 웹 | `WebSearch` | 웹 검색 |
| 웹 | `WebFetch` | URL 콘텐츠 가져오기 |
| 작업 관리 | `TaskCreate` | 작업 생성 |
| 작업 관리 | `TaskUpdate` | 작업 상태 업데이트 |
| 작업 관리 | `TaskList` | 작업 목록 조회 |

---

## 권한 시스템

Claude Code는 강력한 도구들을 제공하는 만큼, **권한 시스템**으로 안전성을 확보한다. 도구별로 자동 허용, 사용자 확인 요청, 완전 차단을 세밀하게 제어할 수 있다.

### 기본 동작

기본적으로 Claude Code는 위험도에 따라 도구 실행 방식이 다르다:

| 위험도 | 도구 예시 | 기본 동작 |
|--------|-----------|-----------|
| 낮음 | `Read`, `Glob`, `Grep` | 자동 허용 |
| 중간 | `Edit`, `Write` | 사용자 확인 요청 |
| 높음 | `Bash` | 사용자 확인 요청 |

파일을 읽는 것은 시스템에 영향을 주지 않으므로 자동 허용되지만, 파일을 수정하거나 셸 명령을 실행하는 것은 사용자의 확인을 받는다.

### settings.json으로 권한 설정

`.claude/settings.json` 파일에서 도구별 허용/차단 규칙을 정의할 수 있다:

```json
{
  "permissions": {
    "allow": [
      "Edit",
      "Write",
      "Bash(npm test)",
      "Bash(npm run build)",
      "Bash(git status)",
      "Bash(git diff *)",
      "Bash(git log *)"
    ],
    "deny": [
      "Bash(rm -rf *)",
      "Bash(git push --force *)",
      "Bash(git reset --hard *)"
    ]
  }
}
```

### 허용 규칙 작성법

허용/차단 규칙은 세 가지 형태로 작성할 수 있다:

**1. 도구 전체 허용/차단**

```json
"allow": ["Edit", "Write"]
```

`Edit`과 `Write` 도구의 모든 사용을 자동 허용한다.

**2. Bash 명령 패턴 매칭**

```json
"allow": [
  "Bash(npm test)",
  "Bash(npm run *)",
  "Bash(git status)"
]
```

`Bash` 도구 중 특정 명령 패턴만 자동 허용한다. `*` 와일드카드를 사용할 수 있다.

**3. 파일 경로 제한**

```json
"allow": [
  "Edit:src/**/*.ts",
  "Write:src/**/*.ts"
]
```

`src` 디렉토리 내의 TypeScript 파일만 수정을 허용한다. 프로젝트 설정 파일이나 빌드 파일이 실수로 수정되는 것을 방지한다.

### 설정 파일 계층 구조

권한 설정은 여러 레벨에서 정의할 수 있고, 하위 레벨이 우선한다:

```
~/.claude/settings.json          ← 전역 설정 (모든 프로젝트)
~/project/.claude/settings.json  ← 프로젝트 설정
```

전역 설정에서 기본적인 안전 규칙(위험한 명령 차단)을 정의하고, 프로젝트별로 특화된 허용 규칙을 추가하는 것이 권장 패턴이다.

### Yolo 모드

개발 중 빠른 반복이 필요할 때는 **Yolo 모드**로 모든 권한 확인을 건너뛸 수 있다:

```bash
claude --dangerously-skip-permissions
```

:::danger
Yolo 모드는 모든 도구 실행이 사용자 확인 없이 자동으로 진행된다. 테스트 환경이나 격리된 컨테이너에서만 사용해야 한다. 프로덕션 환경에서는 절대 사용하지 말 것.
:::

### 실전 권한 설정 예시

일반적인 웹 프로젝트에서 권장하는 권한 설정:

```json
{
  "permissions": {
    "allow": [
      "Edit",
      "Write",
      "Bash(npm test *)",
      "Bash(npm run *)",
      "Bash(npx *)",
      "Bash(git status)",
      "Bash(git diff *)",
      "Bash(git log *)",
      "Bash(git add *)",
      "Bash(git commit *)",
      "Bash(ls *)",
      "Bash(cat *)",
      "Bash(pwd)",
      "Bash(which *)",
      "Bash(node *)",
      "Bash(python *)"
    ],
    "deny": [
      "Bash(rm -rf *)",
      "Bash(git push --force *)",
      "Bash(git reset --hard *)",
      "Bash(git clean -f *)",
      "Bash(curl * | bash)",
      "Bash(wget * | bash)"
    ]
  }
}
```

이 설정은:
- 파일 수정과 일반적인 개발 명령은 자동 허용
- 파괴적인 Git 명령과 위험한 셸 패턴은 차단
- `git push`(force 제외)나 Docker 명령 등은 기본 동작(사용자 확인)을 유지

---

## 컨텍스트 관리

Claude Code는 대규모 코드베이스에서 작업하므로 **컨텍스트 윈도우**(한 번에 처리할 수 있는 토큰 수) 관리가 매우 중요하다. 컨텍스트가 가득 차면 이전 정보가 사라지고, 작업 품질이 저하된다.

### 컨텍스트 윈도우와 자동 압축

Claude Code는 대화가 길어지면 **자동으로 컨텍스트를 압축**한다. 이전 도구 호출의 상세 결과는 요약되고, 핵심 정보만 유지된다.

자동 압축 과정:
1. 컨텍스트 사용량이 임계값(약 80-90%)에 도달
2. 이전 대화와 도구 결과를 자동으로 요약
3. 핵심 정보(현재 작업, 파일 경로, 중요한 발견)는 유지
4. 상세한 파일 내용과 중간 결과는 압축

### /compact 명령으로 수동 압축

자동 압축을 기다리지 않고, 수동으로 컨텍스트를 압축할 수 있다:

```
> /compact
```

커스텀 지시사항과 함께 압축할 수도 있다:

```
> /compact 현재 작업 중인 버그 수정 내용만 유지해줘
```

이렇게 하면 압축 과정에서 특정 정보를 우선적으로 보존한다.

### 토큰 사용량 최적화 전략

효율적인 컨텍스트 관리를 위한 실전 팁:

**1. 구체적으로 요청하기**

```
// 비효율적 - 전체 프로젝트를 탐색
> 이 프로젝트에서 버그를 찾아줘

// 효율적 - 범위를 명확히 지정
> src/components/PostList.tsx에서 무한 스크롤이 동작하지 않는 원인을 찾아줘
```

**2. 파일 부분 읽기 활용**

Claude Code가 대용량 파일을 읽을 때 `offset`과 `limit`을 사용하면 필요한 부분만 컨텍스트에 로드된다. "500번째 줄 근처를 봐줘"처럼 지정하면 불필요한 코드로 컨텍스트가 낭비되지 않는다.

**3. 서브에이전트 활용**

복잡한 탐색 작업은 서브에이전트에 위임하면 메인 컨텍스트가 보존된다. 서브에이전트의 결과 요약만 메인 컨텍스트에 반영되므로 효율적이다.

**4. 적절한 시점에 새 세션 시작**

하나의 세션에서 너무 많은 작업을 하면 컨텍스트 효율이 떨어진다. 작업 단위가 바뀌면 새 세션을 시작하는 것이 좋다.

**5. `/cost` 명령으로 비용 모니터링**

```
> /cost
```

현재 세션의 토큰 사용량과 예상 비용을 확인할 수 있다. 비용이 급격히 증가하면 `/compact`를 실행하거나 새 세션을 시작한다.

:::tip
장기간 작업할 때는 중간중간 `/compact`를 실행하는 습관을 들이자. 특히 여러 파일을 읽은 후나, 큰 테스트 출력이 나온 후에 실행하면 효과적이다.
:::

---

## 실전 예시: 도구 연쇄 동작

에이전틱 루프와 도구 시스템이 실제로 어떻게 협력하는지, "테스트 실패 수정" 시나리오를 단계별로 살펴보자.

### 시나리오: 테스트 실패 수정

사용자가 다음과 같이 요청한다:

```
> npm test가 실패해. 원인을 찾아서 고쳐줘
```

#### 1단계: Bash로 테스트 실행 - 실패 확인

```json
{
  "tool": "Bash",
  "command": "npm test 2>&1",
  "description": "테스트 실행하여 실패 내용 확인"
}
```

```output
FAIL  src/utils/__tests__/formatDate.test.ts
  ● formatDate › should format ISO date to Korean format

    expect(received).toBe(expected)

    Expected: "2024년 3월 15일"
    Received: "2024-03-15"

      12 |   it('should format ISO date to Korean format', () => {
      13 |     const result = formatDate('2024-03-15T00:00:00Z');
    > 14 |     expect(result).toBe('2024년 3월 15일');
      15 |   });

Tests: 1 failed, 23 passed, 24 total
```

Claude Code는 이 결과를 관찰하고, `formatDate` 함수가 날짜를 한국어 형식으로 포맷하지 못하고 있음을 파악한다.

#### 2단계: Read로 실패한 테스트 파일 읽기

```json
{
  "tool": "Read",
  "file_path": "/home/user/project/src/utils/__tests__/formatDate.test.ts"
}
```

테스트 파일을 읽어 테스트가 기대하는 동작을 정확히 파악한다.

#### 3단계: Grep으로 관련 소스 코드 검색

```json
{
  "tool": "Grep",
  "pattern": "export.*function formatDate",
  "type": "ts",
  "output_mode": "content",
  "-C": 3
}
```

```output
/home/user/project/src/utils/formatDate.ts
5-
6:export function formatDate(isoString: string): string {
7-  const date = new Date(isoString);
8-  return date.toISOString().split('T')[0];
9-}
```

`formatDate` 함수가 ISO 형식을 그대로 반환하고 있음을 발견한다.

#### 4단계: Read로 소스 코드 전체 확인

```json
{
  "tool": "Read",
  "file_path": "/home/user/project/src/utils/formatDate.ts"
}
```

파일 전체를 읽어 다른 의존성이나 import 관계를 파악한다.

#### 5단계: Edit로 버그 수정

```json
{
  "tool": "Edit",
  "file_path": "/home/user/project/src/utils/formatDate.ts",
  "old_string": "export function formatDate(isoString: string): string {\n  const date = new Date(isoString);\n  return date.toISOString().split('T')[0];\n}",
  "new_string": "export function formatDate(isoString: string): string {\n  const date = new Date(isoString);\n  const year = date.getFullYear();\n  const month = date.getMonth() + 1;\n  const day = date.getDate();\n  return `${year}년 ${month}월 ${day}일`;\n}"
}
```

#### 6단계: Bash로 테스트 재실행 - 성공 확인

```json
{
  "tool": "Bash",
  "command": "npm test 2>&1",
  "description": "수정 후 테스트 재실행"
}
```

```output
PASS  src/utils/__tests__/formatDate.test.ts
  formatDate
    ✓ should format ISO date to Korean format (3ms)

Tests: 24 passed, 24 total
```

테스트가 통과하면 Claude Code는 사용자에게 수정 내용을 요약하여 보고한다.

### 도구 호출 흐름 시각화

전체 과정의 도구 호출 흐름을 시각화하면:

```
[사용자 요청] "npm test가 실패해. 원인을 찾아서 고쳐줘"
     │
     ▼
[Bash] npm test 2>&1
     │ → 실패: formatDate 테스트
     ▼
[Read] formatDate.test.ts
     │ → 테스트 기대값 파악
     ▼
[Grep] "export.*function formatDate"
     │ → 소스 파일 위치 발견
     ▼
[Read] formatDate.ts
     │ → 현재 구현 확인
     ▼
[Edit] formatDate.ts (버그 수정)
     │ → ISO → 한국어 포맷 변환
     ▼
[Bash] npm test 2>&1
     │ → 성공: 24 passed
     ▼
[사용자에게 결과 보고]
```

이 6단계 과정 전체가 **사용자의 한 번의 요청**으로 자동 수행되었다. 사용자는 중간에 어떤 개입도 하지 않았다.

### 더 복잡한 시나리오: 파일 생성 + 테스트 + 커밋

실제 개발에서는 더 긴 도구 체인이 만들어지기도 한다:

```
[사용자] "API에 페이지네이션 기능을 추가하고 테스트까지 작성해줘"

Grep(기존 API 패턴 파악)
  → Read(라우터 파일)
  → Read(컨트롤러 파일)
  → Edit(컨트롤러에 페이지네이션 로직 추가)
  → Edit(라우터에 쿼리 파라미터 추가)
  → Write(새 테스트 파일 생성)
  → Bash(npm test - 실패)
  → Read(에러 메시지 분석)
  → Edit(타입 오류 수정)
  → Bash(npm test - 성공)
  → Bash(git add .)
  → Bash(git commit -m "feat: API 페이지네이션 추가")
```

이처럼 10개 이상의 도구 호출이 하나의 요청에서 연쇄적으로 실행될 수 있다.

---

## 정리

| 항목 | 내용 |
|------|------|
| 에이전틱 루프 | 계획 - 실행 - 관찰 - 반복의 자율적 순환 구조 |
| 도구 수 | 12개+ (Read, Glob, Grep, Edit, Write, Bash, Agent, WebSearch, WebFetch, Task 등) |
| 파일 탐색 | `Glob`(이름 패턴) + `Grep`(내용 검색) + `Read`(파일 읽기) |
| 파일 수정 | `Edit`(부분 치환) + `Write`(전체 생성) |
| 셸 실행 | `Bash` - 빌드, 테스트, Git 등 모든 셸 작업 |
| 서브에이전트 | `Agent` - 독립 컨텍스트에서 탐색/분석 위임 |
| 권한 제어 | `.claude/settings.json`의 allow/deny 규칙 |
| 컨텍스트 관리 | 자동 압축 + `/compact` 수동 압축 |
| 병렬 실행 | 독립적인 도구 호출을 동시에 실행하여 속도 향상 |
| 에러 복구 | 실패 시 자동으로 원인 분석 - 수정 - 재실행 |

다음 글 [[claude-code-guide-03-advanced|Claude Code 고급 활용]]에서는 MCP 서버 연동과 서브에이전트 활용법을 다룬다.
