# Gemini CLI 고급 활용: Google 생태계 통합

:::info
이 글은 **Gemini CLI Guide** 시리즈의 세 번째 글이다. 시리즈 전체 목차:
1. [[gemini-cli-guide-01-setup|설치와 기본 사용법]]
2. [[gemini-cli-guide-02-core|핵심 기능: 도구 시스템과 확장]]
3. **고급 활용: Google 생태계 통합** (현재 글)
4. [[gemini-cli-guide-04-workflow|실전: 프로젝트 적용 사례]]
:::

Gemini CLI의 차별화된 강점은 **Google 생태계와의 긴밀한 통합**이다. Vertex AI, Google Cloud, Google Search, Google Workspace까지 - Google의 방대한 인프라를 터미널에서 직접 활용할 수 있다. 이 글에서는 Google Cloud 연동, MCP 서버 설정, 커스텀 Extension 개발, 멀티모달 활용, 고급 프롬프팅 기법, 세션 관리까지 고급 기능을 깊이 있게 다룬다.

---

## 1. Google Cloud / Vertex AI 연동

### Vertex AI란

Vertex AI는 Google Cloud의 통합 AI 플랫폼이다. Gemini CLI를 Vertex AI에 연결하면 다음과 같은 이점이 있다.

| 이점 | 설명 |
|------|------|
| **보안** | VPC 내부 통신, IAM 기반 접근 제어 |
| **규정 준수** | 데이터 주권, 감사 로그 |
| **확장성** | 엔터프라이즈 수준의 요청 한도 |
| **통합** | BigQuery, Cloud Storage, Cloud Run 등과 연계 |

### Vertex AI 인증 설정

#### ADC (Application Default Credentials) 방식

가장 일반적인 방법이다. gcloud CLI로 인증한다.

```bash
# gcloud CLI 설치 확인
gcloud --version

# 인증 수행
gcloud auth application-default login

# 프로젝트와 리전 설정
export GOOGLE_CLOUD_PROJECT="my-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"
```

인증이 완료되면 Gemini CLI가 자동으로 Vertex AI를 통해 모델에 접근한다.

#### 서비스 계정 방식 (CI/CD용)

비대화형 환경에서는 서비스 계정 JSON 키를 사용한다.

```bash
# 1. Google Cloud Console에서 서비스 계정 생성
# 2. "Vertex AI User" 역할 부여
# 3. JSON 키 다운로드

# 환경 변수로 키 파일 지정
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
export GOOGLE_CLOUD_PROJECT="my-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"
```

:::warning
서비스 계정 JSON 키는 강력한 권한을 가진다. Git에 커밋하지 말고, 안전한 비밀 관리 시스템(Secret Manager, Vault 등)에 보관하자.
:::

#### Workload Identity Federation (권장)

클라우드 환경에서는 JSON 키 대신 **Workload Identity Federation**을 사용하는 것이 보안상 더 안전하다. GitHub Actions 등 외부 ID 제공자와 연합하여 키 파일 없이 인증할 수 있다.

```yaml
# GitHub Actions에서 Workload Identity Federation 사용 예
- name: Authenticate to Google Cloud
  uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: 'projects/123/locations/global/workloadIdentityPools/my-pool/providers/my-provider'
    service_account: 'gemini-ci@my-project.iam.gserviceaccount.com'
```

### Google Cloud Shell 통합

Google Cloud Shell에는 Gemini CLI가 **사전 설치**되어 있다. Cloud Shell을 열면 별도 설치 없이 바로 사용할 수 있다.

```bash
# Cloud Shell에서 바로 사용
$ gemini
gemini> Cloud Run 서비스를 배포할 Dockerfile을 만들어줘
```

Cloud Shell은 이미 Google Cloud 인증이 완료된 상태이므로 별도 인증 과정이 필요 없다.

---

## 2. Google Search 통합

Gemini CLI는 **Google Search Grounding** 기능을 내장하고 있다. 모델이 자체 학습 데이터만으로 답변하기 어려운 경우 자동으로 Google 검색을 수행하여 최신 정보를 가져온다.

### 자동 검색 활용

```bash
gemini> React 19.1의 새로운 기능은 뭐야?
```

모델이 학습 데이터에 없는 최신 정보라고 판단하면 `google_web_search` 도구를 자동 호출한다. 검색 결과가 컨텍스트에 통합되어 정확한 답변이 생성된다.

### 명시적 검색 요청

```bash
gemini> 웹에서 검색해서 Next.js 15와 Remix 3의 성능 벤치마크를 비교해줘
```

"웹에서 검색해서"와 같은 지시를 포함하면 모델이 더 적극적으로 검색을 활용한다.

### web_fetch와의 조합

검색 결과에서 특정 페이지의 상세 내용이 필요하면 `web_fetch`를 함께 활용한다.

```bash
gemini> Google Cloud의 최신 가격 정책을 https://cloud.google.com/pricing 에서 확인하고 요약해줘
```

---

## 3. MCP 서버 연동

MCP(Model Context Protocol)는 AI 에이전트가 외부 시스템과 상호작용하기 위한 표준 프로토콜이다. Gemini CLI는 MCP를 완전히 지원하며, 다양한 MCP 서버를 연결하여 기능을 확장할 수 있다.

### MCP 서버 설정 구조

`settings.json`의 `mcpServers` 블록에 서버를 정의한다.

```json
{
  "mcpServers": {
    "server-name": {
      "command": "실행할 명령",
      "args": ["인자1", "인자2"],
      "env": {
        "ENV_VAR": "값"
      },
      "timeout": 30000
    }
  }
}
```

### 실전 MCP 서버 설정 예시

#### GitHub MCP 서버

GitHub 이슈, PR, 코드 검색 등을 AI가 직접 수행할 수 있다.

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
    }
  }
}
```

설정 후 사용 예시:

```bash
gemini> GitHub에서 이 레포지토리의 열린 이슈 중 버그 라벨이 있는 것을 찾아줘
gemini> PR #42의 변경사항을 리뷰하고 코멘트를 달아줘
```

#### PostgreSQL MCP 서버

데이터베이스 스키마 조회, 쿼리 실행 등이 가능하다.

```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": [
        "-y", "@modelcontextprotocol/server-postgres",
        "postgresql://user:password@localhost:5432/mydb"
      ]
    }
  }
}
```

#### Slack MCP 서버

Slack 채널 메시지 확인, 전송 등이 가능하다.

```json
{
  "mcpServers": {
    "slack": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-slack"],
      "env": {
        "SLACK_BOT_TOKEN": "$SLACK_BOT_TOKEN"
      }
    }
  }
}
```

#### Google Cloud MCP 서버 (원격)

Google Cloud 서비스와 연동하는 원격 MCP 서버를 설정할 수 있다.

```json
{
  "mcpServers": {
    "bigquery": {
      "httpUrl": "https://mcp-bigquery-abc123.run.app/v1",
      "authProviderType": "google_credentials",
      "oauth": {
        "scopes": ["https://www.googleapis.com/auth/bigquery"]
      },
      "timeout": 30000,
      "headers": {
        "x-goog-user-project": "my-project-id"
      }
    }
  }
}
```

### 주요 MCP 서버 목록

| MCP 서버 | 용도 | 설치 방법 |
|----------|------|-----------|
| GitHub | 이슈, PR, 코드 검색 | Docker 이미지 |
| PostgreSQL | DB 스키마, 쿼리 | npx |
| Filesystem | 추가 파일시스템 접근 | npx |
| Slack | 메시지 읽기/쓰기 | npx |
| Google Cloud | BigQuery, Cloud Run 등 | 원격 HTTP |
| Brave Search | 웹 검색 (대안) | npx |
| Puppeteer | 브라우저 자동화 | npx |

:::tip
MCP 서버 생태계는 빠르게 성장 중이다. [MCP 공식 사이트](https://modelcontextprotocol.io)에서 최신 서버 목록을 확인할 수 있다.
:::

---

## 4. 커스텀 Extension 개발

기존 MCP 서버로 해결되지 않는 요구사항이 있다면 직접 Extension을 개발할 수 있다.

### Extension 개발 절차

#### 1단계: 디렉토리 구조 생성

```bash
mkdir my-extension
cd my-extension
```

#### 2단계: MCP 서버 구현

Node.js로 간단한 MCP 서버를 구현하는 예시다.

```javascript
// server.js
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';

const server = new Server(
  { name: 'my-custom-server', version: '1.0.0' },
  { capabilities: { tools: {} } }
);

// 커스텀 도구 정의
server.setRequestHandler('tools/list', async () => ({
  tools: [
    {
      name: 'get_deploy_status',
      description: '현재 배포 상태를 확인한다',
      inputSchema: {
        type: 'object',
        properties: {
          environment: {
            type: 'string',
            description: '환경 (dev, staging, prod)',
            enum: ['dev', 'staging', 'prod']
          }
        },
        required: ['environment']
      }
    }
  ]
}));

// 도구 실행 핸들러
server.setRequestHandler('tools/call', async (request) => {
  if (request.params.name === 'get_deploy_status') {
    const env = request.params.arguments.environment;
    // 실제 배포 상태 조회 로직
    const status = await checkDeployStatus(env);
    return {
      content: [{ type: 'text', text: JSON.stringify(status) }]
    };
  }
});

async function checkDeployStatus(env) {
  // 실제로는 CI/CD API를 호출
  return {
    environment: env,
    version: '2.1.0',
    status: 'healthy',
    lastDeployed: new Date().toISOString()
  };
}

const transport = new StdioServerTransport();
await server.connect(transport);
```

#### 3단계: gemini-extension.json 작성

```json
{
  "name": "deploy-status",
  "version": "1.0.0",
  "mcpServers": {
    "deploy": {
      "command": "node",
      "args": ["server.js"]
    }
  },
  "contextFileName": "DEPLOY.md"
}
```

#### 4단계: 컨텍스트 파일 작성 (선택)

```markdown
# 배포 상태 도구

이 Extension은 배포 상태를 확인하는 도구를 제공한다.
- `get_deploy_status` 도구를 사용하여 dev, staging, prod 환경의 배포 상태를 확인할 수 있다
- 배포 관련 질문을 받으면 이 도구를 먼저 호출하여 현재 상태를 파악하라
```

#### 5단계: 설치 및 테스트

```bash
# 로컬 Extension 설치
gemini extensions install /path/to/my-extension

# 테스트
gemini -i "prod 환경의 배포 상태를 확인해줘"
```

### Go로 MCP 서버 구현

Google은 Go로 MCP 서버를 구현하는 방법도 공식적으로 지원한다.

```go
// main.go
package main

import (
    "context"
    "encoding/json"
    "fmt"
    "os"

    "github.com/mark3labs/mcp-go/mcp"
    "github.com/mark3labs/mcp-go/server"
)

func main() {
    s := server.NewMCPServer(
        "deploy-status",
        "1.0.0",
    )

    tool := mcp.NewTool("get_deploy_status",
        mcp.WithDescription("현재 배포 상태를 확인한다"),
        mcp.WithString("environment",
            mcp.Required(),
            mcp.Description("환경 (dev, staging, prod)"),
        ),
    )

    s.AddTool(tool, func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
        env := req.Params.Arguments["environment"].(string)
        result := fmt.Sprintf(`{"environment": "%s", "status": "healthy"}`, env)
        return mcp.NewToolResultText(result), nil
    })

    if err := server.ServeStdio(s); err != nil {
        fmt.Fprintf(os.Stderr, "Error: %v\n", err)
        os.Exit(1)
    }
}
```

---

## 5. 멀티모달 지원

Gemini 모델은 네이티브 멀티모달 모델이다. Gemini CLI에서도 텍스트 이외의 입력을 활용할 수 있다.

### 이미지 입력

```bash
# 이미지 파일을 컨텍스트로 제공
gemini> @screenshot.png 이 UI의 레이아웃 문제를 분석하고 CSS 수정안을 제시해줘

# 에러 스크린샷 분석
gemini> @error-screen.jpg 이 에러 화면의 원인을 파악해줘
```

### 활용 시나리오

| 시나리오 | 설명 |
|----------|------|
| **UI 디버깅** | 스크린샷에서 레이아웃 문제 파악 |
| **에러 분석** | 에러 화면 이미지로 원인 추적 |
| **디자인 구현** | 디자인 목업을 코드로 변환 |
| **다이어그램 이해** | 아키텍처 다이어그램 분석 |
| **문서 추출** | 이미지 속 텍스트/코드 추출 |

### Gemini의 멀티모달 처리 능력

Gemini 모델은 프롬프트당 최대 3,600개의 이미지를 처리할 수 있으며, 비디오의 경우 90분 길이까지 지원한다. `media_resolution` 파라미터로 이미지/비디오 프레임당 할당되는 토큰 수를 제어할 수 있다.

:::tip
이미지를 포함하면 토큰 소비가 증가한다. 꼭 필요한 이미지만 전달하고, 가능하면 관련 부분만 크롭하여 전달하는 것이 효율적이다.
:::

---

## 6. 고급 프롬프팅 기법

### 구조화된 지시

복잡한 작업은 단계별로 구조화하여 지시하면 더 정확한 결과를 얻는다.

```bash
gemini> 다음 작업을 순서대로 수행해줘:
1. src/api/ 디렉토리의 모든 엔드포인트를 분석
2. 각 엔드포인트의 에러 핸들링 패턴을 확인
3. 일관되지 않은 에러 핸들링을 찾아서 표로 정리
4. 통일된 에러 핸들링 패턴을 제안하고 적용
```

### GEMINI.md를 활용한 페르소나 설정

프로젝트의 GEMINI.md에 상세한 페르소나와 규칙을 정의하면 일관된 품질의 코드를 생성할 수 있다.

```markdown
# 코드 리뷰어 페르소나

당신은 시니어 백엔드 엔지니어로서 코드를 리뷰한다.

## 리뷰 기준
- 보안: SQL 인젝션, XSS, CSRF 등 보안 취약점 확인
- 성능: N+1 쿼리, 불필요한 메모리 할당, 복잡도 분석
- 가독성: 함수/변수 네이밍, 주석, 코드 구조
- 테스트: 테스트 커버리지, 엣지 케이스 처리

## 출력 형식
| 파일:라인 | 심각도 | 카테고리 | 설명 | 제안 |
```

### 컨텍스트 윈도우 활용 전략

Gemini CLI는 100만 토큰의 컨텍스트 윈도우를 제공하지만, 효율적으로 활용해야 한다.

```bash
# 비효율적: 모든 파일을 한번에 읽으려 함
gemini> 프로젝트의 모든 .ts 파일을 읽고 분석해줘

# 효율적: 단계적으로 접근
gemini> 먼저 프로젝트 구조를 파악하고, 핵심 모듈만 분석해줘
```

### @ 구문으로 파일 참조

대화 중 특정 파일을 명시적으로 참조할 수 있다.

```bash
gemini> @src/config/database.ts 와 @src/config/redis.ts 를 비교해서
       설정 패턴을 통일해줘
```

### 멀티턴 대화 전략

복잡한 작업은 한 번에 모든 것을 요청하기보다 단계별로 대화를 이어가는 것이 효과적이다.

```bash
# 1단계: 분석
gemini> 이 프로젝트의 인증 시스템 아키텍처를 분석해줘

# 2단계: 문제 파악 (이전 분석 결과가 컨텍스트에 유지됨)
gemini> 방금 분석한 인증 시스템에서 보안 취약점이 있는지 확인해줘

# 3단계: 수정 (이전 대화의 맥락을 모두 활용)
gemini> 발견된 취약점을 수정해줘. JWT 리프레시 토큰 로직을 개선하고 테스트도 추가해줘
```

---

## 7. 메모리와 세션 관리

### 영구 메모리

Gemini CLI의 `save_memory` 도구는 중요한 정보를 세션 간에 유지한다.

```bash
gemini> 이 프로젝트에서 데이터베이스 마이그레이션은 항상 Alembic을 사용한다고 기억해줘
# save_memory 도구가 호출되어 ~/.gemini/memory/에 저장
```

저장된 메모리는 이후 세션에서 자동으로 로드된다. `/memory show`로 현재 메모리 내용을 확인할 수 있다.

```bash
gemini> /memory show
# 저장된 모든 메모리 항목 표시
```

### 세션 저장과 복원

대화 세션을 저장하고 나중에 이어서 작업할 수 있다.

```bash
# 현재 세션 저장
gemini> /chat save auth-refactor

# 다음에 저장된 세션 불러오기
gemini> /chat load auth-refactor

# 또는 명령줄에서 마지막 세션 복원
gemini --resume
gemini -r
```

### 세션 저장 위치

세션은 프로젝트별로 관리된다.

```text
~/.gemini/tmp/<project_hash>/chats/
```

- 프로젝트 디렉토리를 변경하면 해당 프로젝트의 세션 히스토리로 전환
- 기본 보관 기간은 30일
- `/chat export`로 마크다운이나 JSON으로 내보내기 가능

### 대화 분기 (Conversational Branching)

`Esc`를 두 번 누르면 이전 대화 지점으로 되돌아가서 다른 방향으로 대화를 분기할 수 있다. 이는 여러 접근 방식을 실험할 때 유용하다.

```bash
# 접근 방식 A 시도
gemini> Redis를 사용해서 세션 관리를 구현해줘
# ... 결과 확인 ...

# Esc 두 번 -> 이전 지점으로 되돌리기
# 접근 방식 B 시도
gemini> JWT를 사용해서 세션 관리를 구현해줘
```

---

## 8. 커스텀 명령어

자주 사용하는 프롬프트를 커스텀 명령어로 등록하면 반복 작업을 줄일 수 있다.

### 커스텀 명령어 생성

TOML 형식의 파일을 생성한다.

```toml
# ~/.gemini/commands/review.toml
[command]
name = "review"
description = "현재 Git diff를 코드 리뷰"

[prompt]
template = """
다음 Git diff를 코드 리뷰해줘.
보안, 성능, 가독성 관점에서 분석하고
개선점을 표로 정리해줘.

```
{{shell "git diff --staged"}}
```
"""
```

```toml
# ~/.gemini/commands/test-gen.toml
[command]
name = "test-gen"
description = "지정된 파일의 유닛 테스트 생성"

[prompt]
template = """
{{arg "file" "테스트를 생성할 파일 경로"}} 파일을 읽고
해당 파일의 모든 공개 함수에 대한 유닛 테스트를 생성해줘.
Jest와 Testing Library를 사용하고,
엣지 케이스와 에러 케이스도 포함해줘.
"""
```

### 커스텀 명령어 사용

```bash
# 코드 리뷰 명령어 실행
gemini> /review

# 테스트 생성 명령어 실행
gemini> /test-gen src/services/UserService.ts

# 명령어 목록 갱신
gemini> /commands reload
```

### 셸 명령 인라인 실행

커스텀 명령어의 `{{shell "..."}}` 구문을 사용하면 셸 명령의 출력을 프롬프트에 동적으로 삽입할 수 있다. Git 상태, 환경 정보, 파일 내용 등을 자동으로 주입하여 컨텍스트를 풍부하게 만들 수 있다.

```toml
# 자동으로 현재 브랜치와 변경사항을 포함하는 커밋 메시지 생성
[command]
name = "commit-msg"
description = "커밋 메시지 생성"

[prompt]
template = """
현재 브랜치: {{shell "git branch --show-current"}}
변경 파일: {{shell "git diff --name-only --staged"}}
변경 내용: {{shell "git diff --staged"}}

위 변경사항에 대한 Conventional Commits 형식의 커밋 메시지를 생성해줘.
"""
```

---

## 9. 고급 설정

### settings.json 전체 구조

```json
{
  "general": {
    "defaultApprovalMode": "auto_edit",
    "theme": "dark"
  },
  "context": {
    "fileName": ["GEMINI.md", "CONTEXT.md"]
  },
  "sandbox": {
    "enabled": true,
    "type": "docker"
  },
  "checkpointing": {
    "enabled": true
  },
  "hooks": {
    "BeforeTool": [],
    "AfterTool": []
  },
  "mcpServers": {
    "github": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN", "ghcr.io/github/github-mcp-server"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "$GITHUB_MCP_PAT"
      }
    }
  }
}
```

### 설정 우선순위

설정은 다음 순서로 병합된다 (아래가 높은 우선순위):

1. 기본 설정 (CLI 내장)
2. 글로벌 사용자 설정 (`~/.gemini/settings.json`)
3. 프로젝트 설정 (`.gemini/settings.json`)
4. 명령줄 플래그 (`--yolo`, `--sandbox` 등)

프로젝트별로 다른 MCP 서버, 승인 모드, 샌드박스 설정을 적용할 수 있어 유연하게 운영할 수 있다.

### /settings 명령어

대화형 모드에서 설정을 실시간으로 변경할 수 있다.

```bash
# 설정 확인
gemini> /settings

# 승인 모드 변경
gemini> /settings set general.defaultApprovalMode yolo

# 체크포인팅 활성화
gemini> /settings set checkpointing.enabled true
```

---

## 10. 정리

이 글에서 다룬 고급 기능을 정리하면 다음과 같다.

| 기능 | 핵심 포인트 |
|------|------------|
| **Vertex AI 연동** | ADC, 서비스 계정, WIF 인증 / Cloud Shell 사전 설치 |
| **Google Search** | Search Grounding 자동 활용, web_fetch 조합 |
| **MCP 서버** | GitHub, DB, Slack 등 다양한 서버 연결 |
| **Extension 개발** | MCP SDK로 커스텀 도구 구현 (Node.js, Go) |
| **멀티모달** | 이미지 분석, UI 디버깅, 다이어그램 이해 |
| **프롬프팅** | 구조화된 지시, 페르소나 설정, 멀티턴 전략 |
| **세션 관리** | 저장/복원, 영구 메모리, 대화 분기 |
| **커스텀 명령어** | TOML 기반, 셸 명령 인라인, 동적 프롬프트 |

Gemini CLI는 Google 생태계의 강력한 서비스들과 직접 연동되며, MCP 표준을 통해 사실상 무한한 확장이 가능하다. 이러한 통합 능력이 다른 AI 코딩 에이전트와 차별화되는 핵심 강점이다.

다음 글 [[gemini-cli-guide-04-workflow|Gemini CLI 실전]]에서는 프로젝트 적용 사례와 워크플로우를 다룬다.
