# Gemini CLI 핵심 기능: 도구 시스템과 확장

:::info
이 글은 **Gemini CLI Guide** 시리즈의 두 번째 글이다. 시리즈 전체 목차:
1. [[gemini-cli-guide-01-setup|설치와 기본 사용법]]
2. **핵심 기능: 도구 시스템과 확장** (현재 글)
3. [[gemini-cli-guide-03-advanced|고급 활용: Google 생태계 통합]]
4. [[gemini-cli-guide-04-workflow|실전: 프로젝트 적용 사례]]
:::

Gemini CLI의 진정한 힘은 **빌트인 도구 시스템**에 있다. 단순히 텍스트를 생성하는 것이 아니라, 파일을 읽고 쓰고, 셸 명령을 실행하고, 웹을 검색하며, 코드베이스를 분석하는 **에이전틱 루프**를 통해 복잡한 작업을 자율적으로 수행한다. 이 글에서는 Gemini CLI의 12가지 빌트인 도구, 에이전틱 동작 원리, Extensions 시스템, 샌드박스, Hooks까지 핵심 기능을 상세히 분석한다.

---

## 1. 에이전틱 루프 동작 원리

Gemini CLI는 **ReAct(Reason and Act)** 패턴을 기반으로 동작한다. 사용자의 요청을 받으면 다음과 같은 루프를 반복한다.

```
사용자 입력
    ↓
[Reason] 현재 상황 분석, 다음 행동 결정
    ↓
[Act] 도구 호출 (파일 읽기, 코드 수정, 명령 실행 등)
    ↓
[Observe] 도구 실행 결과 관찰
    ↓
[Reason] 결과를 바탕으로 다음 단계 결정
    ↓
  ... (반복) ...
    ↓
최종 응답 출력
```

### 구체적인 예시

"테스트가 실패하는 원인을 찾아서 수정해줘"라고 요청하면 Gemini CLI는 다음과 같이 동작한다.

1. **Reason**: 먼저 테스트를 실행해서 어떤 테스트가 실패하는지 확인해야 한다
2. **Act**: `run_shell_command` - `npm test` 실행
3. **Observe**: 테스트 결과에서 `UserService.test.ts`의 3개 테스트 실패 확인
4. **Reason**: 실패하는 테스트 파일을 읽어서 어떤 테스트인지 파악해야 한다
5. **Act**: `read_file` - `UserService.test.ts` 읽기
6. **Observe**: mock 데이터와 실제 API 응답 형식 불일치 발견
7. **Reason**: 소스 코드의 타입 정의를 확인해야 한다
8. **Act**: `read_file` - `UserService.ts` 읽기
9. **Observe**: 타입이 최근 변경된 것을 확인
10. **Reason**: 테스트의 mock 데이터를 새로운 타입에 맞게 수정해야 한다
11. **Act**: `replace` - 테스트 파일의 mock 데이터 수정
12. **Act**: `run_shell_command` - `npm test` 재실행하여 수정 확인
13. **Observe**: 모든 테스트 통과
14. **최종 응답**: 수정 내용과 원인 설명

이 전체 과정이 사용자의 단 한 번의 요청으로 자동 수행된다.

### Plan Mode

Gemini CLI v0.34.0부터 기본으로 활성화된 **Plan Mode**는 읽기 전용 모드로, 에이전트가 코드베이스를 읽고 변경 계획을 먼저 제안한 후 사용자의 승인을 받아야 실제 수정을 진행한다. 이를 통해 의도하지 않은 변경을 방지할 수 있다.

---

## 2. 빌트인 도구 상세 분석

Gemini CLI는 다양한 빌트인 도구를 제공한다. `/tools` 명령으로 현재 활성화된 도구 목록을 확인할 수 있다.

### 파일 시스템 도구

#### read_file - 파일 읽기

단일 파일의 내용을 읽는다. 절대 경로를 사용한다.

```
도구: read_file
입력: { "path": "/Users/dev/project/src/index.ts" }
```

대용량 파일도 처리 가능하며, 바이너리 파일은 자동으로 인식하여 메타데이터만 반환한다.

#### read_many_files - 다중 파일 읽기

여러 파일이나 디렉토리의 내용을 한 번에 읽는다. glob 패턴도 지원한다.

```
도구: read_many_files
입력: { "paths": ["src/**/*.ts", "package.json", "tsconfig.json"] }
```

코드베이스를 빠르게 파악할 때 유용하다. 디렉토리를 지정하면 해당 디렉토리의 파일 목록을 반환한다.

#### write_file - 파일 쓰기

새 파일을 생성하거나 기존 파일의 전체 내용을 덮어쓴다.

```
도구: write_file
입력: { "path": "/Users/dev/project/src/utils/helper.ts", "content": "..." }
```

:::warning
`write_file`은 파일 전체를 덮어쓰므로, 기존 파일의 일부만 수정할 때는 `replace` 도구를 사용하는 것이 안전하다.
:::

#### replace - 파일 편집 (부분 수정)

파일의 특정 부분만 찾아서 교체한다. 정밀한 코드 수정에 적합하다.

```
도구: replace
입력: {
  "path": "/Users/dev/project/src/auth.ts",
  "old_string": "const TOKEN_EXPIRY = 3600;",
  "new_string": "const TOKEN_EXPIRY = 7200; // 2시간으로 변경"
}
```

`replace`는 `old_string`이 파일에서 유일하게 매치되어야 한다. 여러 곳을 수정할 때는 충분한 컨텍스트를 포함시켜 고유성을 확보해야 한다.

#### glob - 파일 검색 (패턴)

glob 패턴으로 파일을 검색한다.

```
도구: glob
입력: { "pattern": "src/**/*.test.ts" }
```

특정 확장자의 파일을 찾거나, 프로젝트 구조를 파악할 때 사용한다.

#### search_file_content - 텍스트 검색

파일 내용에서 텍스트 패턴을 검색한다. grep과 유사한 기능이다.

```
도구: search_file_content
입력: { "pattern": "TODO|FIXME", "path": "src/" }
```

정규표현식을 지원하며, 코드베이스에서 특정 패턴이나 함수 사용처를 찾을 때 유용하다.

#### list_directory - 디렉토리 탐색

디렉토리의 내용(파일/폴더 목록)을 나열한다.

```
도구: list_directory
입력: { "path": "/Users/dev/project/src" }
```

### 시스템 도구

#### run_shell_command - 셸 명령 실행

임의의 셸 명령을 실행한다. 가장 강력하지만 가장 위험한 도구이기도 하다.

```
도구: run_shell_command
입력: { "command": "npm test -- --coverage" }
```

기본 승인 모드에서는 매번 사용자의 확인을 요청한다. 샌드박스가 활성화된 경우 격리된 환경에서 실행된다.

:::tip
`run_shell_command`는 빌드, 테스트, lint, 패키지 설치 등 다양한 용도로 활용된다. YOLO 모드 사용시 반드시 샌드박스와 함께 사용하자.
:::

### 웹 도구

#### google_web_search - 웹 검색

Google 검색을 수행하여 최신 정보를 가져온다.

```
도구: google_web_search
입력: { "query": "React 19 new features 2025" }
```

모델의 학습 데이터에 포함되지 않은 최신 정보가 필요할 때 자동으로 호출된다. Google Search Grounding 기능을 통해 검색 결과를 컨텍스트에 통합한다.

#### web_fetch - 웹 페이지 가져오기

특정 URL의 내용을 가져온다.

```
도구: web_fetch
입력: { "url": "https://api.example.com/docs" }
```

문서 페이지, API 레퍼런스, README 등의 내용을 직접 가져올 때 사용한다.

### 에이전트/메모리 도구

#### codebase_investigator - 코드베이스 분석 에이전트

대규모 코드베이스를 체계적으로 분석하는 서브 에이전트다. 단순 파일 읽기보다 깊은 수준의 분석을 수행한다.

```
도구: codebase_investigator
입력: { "query": "인증 흐름에서 JWT 토큰이 어떻게 검증되는지 추적해줘" }
```

#### save_memory - 메모리 저장

중요한 정보를 영구 메모리에 저장한다. 세션 간에 유지된다.

```
도구: save_memory
입력: { "content": "이 프로젝트는 PostgreSQL 15를 사용하며, 마이그레이션은 Alembic으로 관리한다" }
```

저장된 메모리는 `~/.gemini/memory/` 디렉토리에 저장되며, 이후 세션에서 자동으로 로드된다.

#### write_todos - 할 일 관리

작업 목록을 생성하고 관리한다.

```
도구: write_todos
입력: { "todos": ["API 엔드포인트 구현", "유닛 테스트 작성", "문서 업데이트"] }
```

### 도구 전체 요약

| 카테고리 | 도구 이름 | 기능 |
|----------|-----------|------|
| 파일 읽기 | `read_file` | 단일 파일 읽기 |
| 파일 읽기 | `read_many_files` | 다중 파일/디렉토리 읽기 |
| 파일 쓰기 | `write_file` | 파일 생성/덮어쓰기 |
| 파일 편집 | `replace` | 파일 부분 수정 |
| 검색 | `glob` | 파일명 패턴 검색 |
| 검색 | `search_file_content` | 파일 내용 텍스트 검색 |
| 디렉토리 | `list_directory` | 디렉토리 목록 |
| 시스템 | `run_shell_command` | 셸 명령 실행 |
| 웹 | `google_web_search` | Google 검색 |
| 웹 | `web_fetch` | URL 내용 가져오기 |
| 에이전트 | `codebase_investigator` | 코드베이스 심층 분석 |
| 메모리 | `save_memory` | 영구 메모리 저장 |
| 관리 | `write_todos` | 할 일 목록 관리 |

---

## 3. Extensions 시스템 (MCP 기반)

Gemini CLI의 Extensions 시스템은 **MCP(Model Context Protocol)** 를 기반으로 한다. 빌트인 도구로 부족한 기능을 외부 MCP 서버를 연결하여 확장할 수 있다.

### Extensions란

Extension은 MCP 서버와 추가 컨텍스트 파일을 패키징한 단위다. 각 Extension은 다음을 포함할 수 있다.

- MCP 서버 설정 (도구 추가)
- 컨텍스트 파일 (추가 지시사항)
- 도구 제외 목록 (특정 도구 비활성화)

### Extension 구조

Extension은 `gemini-extension.json` 파일을 포함하는 디렉토리다.

```json
{
  "name": "my-custom-extension",
  "version": "1.0.0",
  "mcpServers": {
    "my-server": {
      "command": "node",
      "args": ["./server.js"]
    }
  },
  "contextFileName": "GEMINI.md",
  "excludeTools": ["run_shell_command"]
}
```

| 필드 | 설명 |
|------|------|
| `name` | Extension 이름 |
| `version` | 버전 |
| `mcpServers` | MCP 서버 설정 (복수 가능) |
| `contextFileName` | 추가 컨텍스트 파일명 |
| `excludeTools` | 비활성화할 도구 목록 |

### Extension 설치와 관리

```bash
# GitHub에서 Extension 설치
gemini extensions install https://github.com/example/my-extension

# 로컬 경로에서 설치
gemini extensions install /path/to/local/extension

# 설치된 Extension 목록 확인
gemini extensions list

# Extension 제거
gemini extensions uninstall my-extension
```

### settings.json에서 MCP 서버 직접 설정

Extension 없이 MCP 서버를 직접 연결할 수도 있다. `~/.gemini/settings.json` 또는 프로젝트의 `.gemini/settings.json`에 추가한다.

```json
{
  "mcpServers": {
    "github": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
        "ghcr.io/github/github-mcp-server"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "$GITHUB_MCP_PAT"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/docs"]
    }
  }
}
```

### 원격 MCP 서버 (HTTP)

로컬 프로세스뿐만 아니라 HTTP 기반의 원격 MCP 서버도 연결할 수 있다.

```json
{
  "mcpServers": {
    "cloud-tools": {
      "httpUrl": "https://mcp.example.com/v1",
      "authProviderType": "google_credentials",
      "oauth": {
        "scopes": ["https://www.googleapis.com/auth/cloud-platform"]
      },
      "timeout": 30000,
      "headers": {
        "x-goog-user-project": "my-project-id"
      }
    }
  }
}
```

### 환경 변수 보안

MCP 서버에 환경 변수를 전달할 때 보안에 주의해야 한다.

:::warning
`env` 속성에 명시적으로 선언된 변수만 MCP 서버에 전달된다. 이는 의도하지 않은 환경 변수 노출을 방지하기 위한 보안 설계다. 사용자가 명시적으로 설정한 변수만 신뢰하는 원칙을 따른다.
:::

---

## 4. 샌드박스 프로필

Gemini CLI는 AI가 실행하는 명령의 위험성을 최소화하기 위해 **샌드박스** 기능을 제공한다.

### macOS Seatbelt 샌드박스

macOS에서는 기본적으로 **Seatbelt** (sandbox-exec) 기반 샌드박스가 활성화된다.

| 프로필 | 설명 |
|--------|------|
| `permissive-open` | 기본값. 프로젝트 폴더 내 쓰기 허용, 나머지는 읽기 전용 |
| `strict` | 엄격한 프로필. 기본적으로 모든 작업을 거부 |

```json
{
  "sandbox": {
    "enabled": true,
    "type": "seatbelt",
    "profile": "permissive-open"
  }
}
```

커스텀 프로필을 만들 수도 있다. `.gemini/sandbox-macos-custom.sb` 파일을 생성하면 된다.

### 컨테이너 기반 샌드박스 (Docker/Podman)

완전한 프로세스 격리가 필요하면 Docker/Podman 기반 샌드박스를 사용한다.

```json
{
  "sandbox": {
    "enabled": true,
    "type": "docker"
  }
}
```

컨테이너 샌드박스의 특징은 다음과 같다.

- `--rm` 옵션으로 자동 정리 (사용 후 컨테이너 삭제)
- `--init` 옵션으로 좀비 프로세스 방지
- 프로젝트 디렉토리만 마운트하여 격리

### 커스텀 Dockerfile

프로젝트별 샌드박스 환경을 구성하려면 `.gemini/sandbox.Dockerfile`을 생성한다.

```dockerfile
# .gemini/sandbox.Dockerfile
FROM gcr.io/gemini-cli/sandbox-base:latest

# 프로젝트에 필요한 도구 설치
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    postgresql-client

# Python 의존성 설치
COPY requirements.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt
```

### 샌드박스 비교

| 방식 | 격리 수준 | 성능 | 설정 복잡도 | 적합한 환경 |
|------|-----------|------|------------|------------|
| Seatbelt (permissive) | 중간 | 빠름 | 낮음 | macOS 일반 개발 |
| Seatbelt (strict) | 높음 | 빠름 | 중간 | macOS 보안 중시 |
| Docker | 매우 높음 | 중간 | 중간 | 크로스 플랫폼, CI/CD |
| Podman | 매우 높음 | 중간 | 중간 | 루트리스 컨테이너 |
| 없음 (none) | 없음 | 최고 | 없음 | 신뢰할 수 있는 환경만 |

---

## 5. Hooks 시스템

Hooks는 Gemini CLI의 에이전틱 루프 중 특정 시점에 사용자 정의 스크립트를 실행할 수 있는 시스템이다. 소스 코드를 수정하지 않고도 CLI의 동작을 커스터마이징할 수 있다.

### Hook 이벤트 종류

| 이벤트 | 시점 | 매처 방식 |
|--------|------|-----------|
| `BeforeTool` | 도구 호출 전 | 정규표현식 |
| `AfterTool` | 도구 호출 후 | 정규표현식 |

`BeforeTool`은 도구가 실행되기 전에, `AfterTool`은 도구 실행 후에 트리거된다. 매처(matcher)를 사용하여 특정 도구에만 반응하도록 필터링할 수 있다.

### Hook 설정

`settings.json`의 `hooks` 객체에 정의한다.

```json
{
  "hooks": {
    "BeforeTool": [
      {
        "matcher": "run_shell_command",
        "command": ["python3", "/path/to/pre-check.py"],
        "timeout": 5000
      }
    ],
    "AfterTool": [
      {
        "matcher": "write_file|replace",
        "command": ["node", "/path/to/post-lint.js"],
        "timeout": 10000
      }
    ]
  }
}
```

### Hook 입출력 프로토콜

Gemini CLI는 stdin으로 JSON 객체를 Hook 스크립트에 전달한다.

```json
{
  "session_id": "abc123",
  "cwd": "/Users/dev/project",
  "hook_event_name": "BeforeTool",
  "tool_name": "run_shell_command",
  "tool_input": {
    "command": "rm -rf /tmp/cache"
  }
}
```

Hook 스크립트는 stdout으로 JSON 응답을 반환해야 한다. 종료 코드로 동작을 제어한다.

| 종료 코드 | 의미 |
|-----------|------|
| 0 | 정상 - 도구 실행 진행 |
| 1 | 차단 - 도구 실행 중단 |
| 2 이상 | 오류 - 경고 표시 후 진행 |

### 실용적인 Hook 예시

#### 위험한 명령 차단

```python
#!/usr/bin/env python3
# pre-check.py - 위험한 셸 명령 차단
import json
import sys

data = json.load(sys.stdin)
command = data.get("tool_input", {}).get("command", "")

# 위험한 패턴 목록
dangerous_patterns = ["rm -rf /", "DROP TABLE", "FORMAT", "mkfs"]

for pattern in dangerous_patterns:
    if pattern.lower() in command.lower():
        print(json.dumps({
            "message": f"차단됨: 위험한 명령 패턴 '{pattern}' 감지"
        }))
        sys.exit(1)  # 차단

print(json.dumps({"message": "OK"}))
sys.exit(0)  # 허용
```

#### 파일 수정 후 자동 린트

```javascript
// post-lint.js - 파일 수정 후 ESLint 실행
const { execSync } = require('child_process');
const fs = require('fs');

const data = JSON.parse(fs.readFileSync('/dev/stdin', 'utf8'));
const filePath = data.tool_input?.path;

if (filePath && filePath.endsWith('.ts')) {
  try {
    execSync(`npx eslint --fix "${filePath}"`, { stdio: 'pipe' });
    console.log(JSON.stringify({ message: `린트 완료: ${filePath}` }));
  } catch (e) {
    console.log(JSON.stringify({ message: `린트 경고: ${filePath}` }));
  }
}

process.exit(0);
```

:::tip
Hook은 동기적으로 실행된다. 즉 Hook이 완료될 때까지 Gemini CLI의 에이전틱 루프가 대기한다. 따라서 Hook 스크립트는 가능한 빨리 실행되도록 작성해야 하며, timeout을 적절히 설정하자.
:::

---

## 6. 권한 제어와 승인 모드

Gemini CLI는 도구 실행에 대한 세밀한 권한 제어를 제공한다.

### 승인 모드

| 모드 | 동작 | 설정값 |
|------|------|--------|
| **기본** | 모든 도구 호출에 사용자 승인 필요 | `default` |
| **자동 편집** | 파일 편집 도구는 자동, 나머지는 승인 | `auto_edit` |
| **YOLO** | 모든 도구 호출 자동 승인 | `yolo` |

```bash
# YOLO 모드로 시작
gemini --yolo

# 또는 대화 중 Ctrl+Y로 토글

# settings.json에서 기본값 변경
# /settings set general.defaultApprovalMode auto_edit
```

### 권장 조합

| 상황 | 승인 모드 | 샌드박스 |
|------|-----------|----------|
| 민감한 프로덕션 코드 | `default` | 활성화 |
| 일반 개발 | `auto_edit` | 활성화 |
| 실험/프로토타이핑 | `yolo` | 활성화 (필수) |
| CI/CD 파이프라인 | `yolo` | Docker |

:::warning
`yolo` 모드는 편리하지만, AI가 예상치 못한 명령을 실행할 수 있다. 반드시 샌드박스와 함께 사용하거나, 신뢰할 수 있는 프로젝트에서만 사용하자.
:::

---

## 7. 컨텍스트 관리

대화가 길어지면 컨텍스트 윈도우가 커지고, 응답 품질이 저하되거나 비용이 증가할 수 있다. Gemini CLI는 이를 관리하는 여러 기능을 제공한다.

### /compress - 컨텍스트 압축

현재 대화를 요약하여 토큰을 절약한다.

```bash
gemini> /compress
# 전체 대화가 요약으로 대체됨
# 이전 맥락은 유지하면서 토큰 사용량 감소
```

### /clear - 컨텍스트 초기화

대화를 완전히 새로 시작한다.

```bash
gemini> /clear
# 또는 Ctrl+L
```

### /stats - 사용량 확인

현재 세션의 토큰 사용량과 캐시 절감 효과를 확인한다.

```bash
gemini> /stats
# 세션 지속 시간, 도구 호출 횟수, 토큰 사용량 표시
# 토큰 캐싱으로 절약된 양도 확인 가능
```

### 토큰 캐싱

API 키 인증 사용시, Gemini CLI는 자동으로 **토큰 캐싱**을 적용한다. 이전 시스템 명령과 컨텍스트를 재사용하여 후속 요청에서 처리하는 토큰 수를 줄인다. 캐싱 절감 효과는 `/stats` 명령으로 확인할 수 있다.

### 체크포인팅

Gemini CLI는 파일을 수정하기 전에 자동으로 **체크포인트**를 생성한다.

- 프로젝트의 Git 저장소와 별도의 **섀도 Git 저장소**에 스냅샷 저장
- 대화 히스토리와 도구 호출 정보도 함께 저장
- `settings.json`에서 활성화/비활성화 가능

```json
{
  "checkpointing": {
    "enabled": true
  }
}
```

체크포인팅을 통해 AI의 수정이 마음에 들지 않을 때 이전 상태로 안전하게 복원할 수 있다.

---

## 8. 정리

이 글에서 다룬 Gemini CLI 핵심 기능을 요약하면 다음과 같다.

| 기능 | 핵심 포인트 |
|------|------------|
| **에이전틱 루프** | ReAct 패턴 기반, 도구를 활용한 자율적 작업 수행 |
| **빌트인 도구** | 파일 I/O, 셸 실행, 웹 검색, 코드 분석 등 13가지 |
| **Extensions** | MCP 기반 확장, 외부 도구/서버 연동 |
| **샌드박스** | Seatbelt, Docker, Podman 기반 격리 실행 |
| **Hooks** | BeforeTool/AfterTool 이벤트에 커스텀 스크립트 실행 |
| **권한 제어** | default/auto_edit/yolo 승인 모드 |
| **컨텍스트 관리** | /compress, /clear, 토큰 캐싱, 체크포인팅 |

Gemini CLI는 단순한 코드 생성 도구가 아니라, 도구를 활용하여 복잡한 작업을 자율적으로 수행하는 에이전틱 시스템이다. Extensions과 Hooks를 통해 무한하게 확장할 수 있으며, 샌드박스와 권한 제어로 안전성도 확보할 수 있다.

다음 글 [[gemini-cli-guide-03-advanced|Gemini CLI 고급 활용]]에서는 Google 생태계와의 통합 활용법을 다룬다.
