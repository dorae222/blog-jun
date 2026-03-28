# Codex CLI 핵심 기능: 샌드박스와 코드 생성

:::info
이 글은 **Codex CLI Guide** 시리즈의 두 번째 글이다. 시리즈 전체 목차:
1. [[codex-guide-01-setup|설치와 기본 사용법]]
2. **핵심 기능: 샌드박스와 코드 생성** (현재 글)
3. [[codex-guide-03-advanced|고급 활용: 자동화와 CI 통합]]
4. [[codex-guide-04-workflow|실전: 레거시 마이그레이션]]
:::

이전 글에서 Codex CLI의 설치와 기본 사용법을 다뤘다. 이번 글에서는 Codex CLI의 핵심 기술인 **플랫폼 네이티브 샌드박스**와 **에이전틱 코드 생성** 메커니즘을 심층적으로 분석한다.

---

## 1. 플랫폼 네이티브 샌드박스 심층 분석

Codex CLI가 다른 AI 코딩 도구와 차별화되는 가장 큰 기술적 특징은 **OS 수준의 네이티브 샌드박스**다. 컨테이너나 VM 기반 격리가 아니라, 운영체제 커널이 직접 제한을 강제하는 방식이다. 이로 인해 오버헤드가 극히 적으면서도 탈출이 매우 어렵다.

### 왜 네이티브 샌드박스인가

| 격리 방식 | 시작 오버헤드 | 메모리 오버헤드 | 보안 수준 | Codex CLI |
|-----------|-------------|---------------|----------|-----------|
| Docker 컨테이너 | ~500ms | ~50MB | 높음 | - |
| VM (Firecracker 등) | ~125ms | ~128MB | 매우 높음 | - |
| OS 네이티브 샌드박스 | ~1ms 미만 | ~0 | 높음 | 사용 |

네이티브 샌드박스는 커널이 시스템 콜 수준에서 제한을 걸기 때문에, Codex CLI가 시스템 콜을 보기도 전에 커널이 차단한다. 별도의 데몬이나 런타임이 필요하지 않다.

---

### 1.1 macOS: Seatbelt (sandbox-exec)

macOS에서 Codex CLI는 Apple의 **Seatbelt** 프레임워크를 사용한다. `sandbox-exec`를 통해 SBPL(Sandbox Profile Language) 스크립트를 동적으로 생성하고 적용한다.

#### Seatbelt 동작 원리

Seatbelt은 **기본 거부(deny-by-default)** 정책을 사용한다. 명시적으로 허용하지 않은 모든 시스템 콜은 차단된다.

```text
(version 1)
(deny default)

;; 기본 시스템 동작 허용
(allow process-exec)
(allow process-fork)

;; 읽기 전용 모드: 파일 읽기만 허용
(allow file-read*)

;; workspace-write 모드: 작업 디렉터리 쓰기 허용
(allow file-write*
  (subpath "/Users/dev/my-project"))

;; 네트워크 차단 (suggest, auto-edit 모드)
(deny network*)
```

#### 모드별 Seatbelt 권한

| 권한 | suggest (read-only) | auto-edit (workspace-write) | full-auto (가능한 설정) |
|------|--------------------|-----------------------------|----------------------|
| 파일 읽기 | 전체 허용 | 전체 허용 | 전체 허용 |
| 파일 쓰기 | 차단 | 작업 디렉터리만 | 작업 디렉터리만 |
| 네트워크 | 차단 | 차단 | 설정에 따라 허용 |
| 프로세스 실행 | 제한적 | 제한적 | 허용 |

#### Seatbelt 테스트

Codex CLI는 샌드박스 동작을 직접 테스트할 수 있는 디버그 명령을 제공한다.

```bash
# Seatbelt 샌드박스 내에서 명령 실행 테스트
codex debug seatbelt -- ls /tmp

# 또는 별칭 사용
codex sandbox seatbelt -- cat /etc/passwd
```

이 명령은 실제 Codex 에이전트를 실행하지 않고, 지정한 명령만 샌드박스 내에서 실행하여 어떤 작업이 허용되고 차단되는지 확인할 수 있다.

---

### 1.2 Linux: Bubblewrap + Landlock + Seccomp

Linux에서 Codex CLI는 세 가지 커널 보안 메커니즘을 결합한다.

#### Landlock LSM (Linux 5.13+)

Landlock은 Linux 커널에 내장된 **능력 기반(capability-based) 파일시스템 접근 제어** 프레임워크다. 비특권 프로세스가 스스로의 파일시스템 접근 권한을 제한할 수 있다.

```rust
// Codex CLI 내부의 Landlock 설정 (개념적 구조)
// 실제 구현은 codex-rs/sandbox 크레이트에 있다

let ruleset = Ruleset::new()
    .handle_access(AccessFs::ReadFile | AccessFs::ReadDir)?
    // workspace-write 모드: 작업 디렉터리만 쓰기 허용
    .add_rule(PathBeneath::new(
        work_dir_fd,
        AccessFs::WriteFile | AccessFs::MakeReg,
    ))?
    .restrict_self()?;
```

Landlock의 핵심은 **계층적 제한**이다. 한 번 적용된 제한은 하위 프로세스에도 전파되며, 제한을 완화할 수 없다.

#### Bubblewrap (bwrap)

Bubblewrap은 Linux 네임스페이스를 활용한 경량 샌드박스 도구다. Codex CLI에서는 다음 네임스페이스를 사용한다:

| 네임스페이스 | 역할 |
|------------|------|
| Mount | 파일시스템 격리, 필요한 경로만 바인드 마운트 |
| PID | 프로세스 격리, 호스트 프로세스 접근 차단 |
| Network | 네트워크 격리 (모드에 따라) |
| User | 비특권 네임스페이스 생성 |

```bash
# Codex가 내부적으로 구성하는 bwrap 명령 (개념적)
bwrap \
  --ro-bind /usr /usr \
  --ro-bind /lib /lib \
  --ro-bind /etc/resolv.conf /etc/resolv.conf \
  --bind /home/dev/project /home/dev/project \
  --unshare-net \    # 네트워크 격리 (suggest/auto-edit)
  --unshare-pid \    # PID 격리
  --dev /dev \
  -- /bin/bash -c "실행할 명령"
```

#### Seccomp-BPF

Seccomp(Secure Computing Mode)은 시스템 콜 필터링을 제공한다. Codex CLI는 BPF(Berkeley Packet Filter) 프로그램을 사용하여 허용되는 시스템 콜을 제한한다.

```text
# Codex의 Seccomp 필터 (개념적)
# 네트워크 관련 시스템 콜 차단
SCMP_ACT_ERRNO(EPERM) connect
SCMP_ACT_ERRNO(EPERM) bind
SCMP_ACT_ERRNO(EPERM) sendto
SCMP_ACT_ERRNO(EPERM) recvfrom

# AF_UNIX (로컬 소켓)만 허용
SCMP_ACT_ALLOW socket(AF_UNIX)
```

네트워크 시스템 콜(`connect`, `bind`, `sendto` 등)은 차단하되, 로컬 유닉스 소켓(`AF_UNIX`)은 허용하여 Codex CLI와 에이전트 프로세스 간 통신이 가능하도록 한다.

#### Linux 샌드박스 테스트

```bash
# Landlock 샌드박스 테스트
codex debug landlock -- ls /tmp

# 또는 별칭
codex sandbox landlock -- touch /etc/test-file
# 결과: Permission denied (Landlock이 차단)
```

---

### 1.3 샌드박스 모드 설정

config.toml에서 샌드박스 모드를 명시적으로 설정할 수 있다.

```toml
# ~/.codex/config.toml

# 전역 샌드박스 모드
sandbox_mode = "workspace-write"

# workspace-write 모드의 세부 설정
[sandbox_workspace_write]
# 네트워크 접근 허용 여부
network_access = false
```

사용 가능한 샌드박스 모드:

| 모드 | 파일 읽기 | 파일 쓰기 | 네트워크 | 용도 |
|------|----------|----------|---------|------|
| `read-only` | 전체 | 차단 | 차단 | 코드 분석, 질의 |
| `workspace-write` | 전체 | CWD만 | 설정 가능 | 일반 개발 (기본) |
| `danger-full-access` | 전체 | 전체 | 허용 | 주의 필요 |

:::warning
`danger-full-access`는 이름에서 알 수 있듯 위험한 설정이다. 에이전트가 시스템 전체에 접근할 수 있으므로, 반드시 신뢰할 수 있는 환경에서만 사용한다.
:::

---

## 2. 핵심 도구 체계

Codex CLI 에이전트는 **도구(tools)**를 통해 외부 세계와 상호작용한다. 핵심 도구는 크게 **셸 실행**과 **파일 조작** 두 축으로 나뉜다.

### 2.1 도구 목록

| 도구 | 설명 | 용도 |
|------|------|------|
| `shell` | 셸 명령 실행 | 빌드, 테스트, Git 등 |
| `read_file` | 파일 내용 읽기 | 코드 분석, 설정 확인 |
| `write_file` | 파일 생성/덮어쓰기 | 새 파일 생성 |
| `apply_patch` | Diff 기반 파일 수정 | 기존 파일 수정 |
| `list_dir` | 디렉터리 목록 조회 | 프로젝트 구조 탐색 |
| `text_search` | 텍스트 검색 (grep/rg) | 코드 검색 |

### 2.2 shell 도구

`shell`은 가장 강력한 도구다. 에이전트가 임의의 셸 명령을 실행할 수 있다.

```bash
# 에이전트가 내부적으로 호출하는 예시
shell: npm test
shell: git diff HEAD~1
shell: grep -r "TODO" src/
shell: python -m pytest tests/ -v
```

`suggest` 모드에서는 모든 셸 명령에 사용자 승인이 필요하다. `full-auto` 모드에서는 자동 실행된다. 어떤 모드에서든 셸 명령은 샌드박스 내에서 실행되므로, 샌드박스 정책에 의해 파일 접근과 네트워크가 제한된다.

### 2.3 apply_patch 도구

`apply_patch`는 Codex CLI에서 파일 수정의 핵심 메커니즘이다. 전체 파일을 덮어쓰는 대신, **통합 diff(unified diff)** 형식의 패치를 생성하여 최소한의 변경만 적용한다.

```diff
--- a/src/utils/parser.ts
+++ b/src/utils/parser.ts
@@ -15,7 +15,10 @@
 export function parseConfig(raw: string): Config {
-  const data = JSON.parse(raw);
-  return data as Config;
+  try {
+    const data = JSON.parse(raw);
+    return validateConfig(data);
+  } catch (error) {
+    throw new ConfigParseError(`Invalid config: ${error.message}`);
+  }
 }
```

이 접근법의 장점:

- **최소 변경**: 전체 파일 재작성 대신 필요한 부분만 수정
- **리뷰 용이**: diff 형식이므로 변경 사항을 즉시 파악 가능
- **충돌 감소**: 파일의 다른 부분은 건드리지 않으므로 Git 충돌 위험 감소
- **토큰 절약**: 전체 파일을 출력하지 않으므로 출력 토큰 비용 절감

:::tip
OpenAI는 `apply_patch`의 정확한 구현을 사용할 것을 강력히 권장한다. 모델이 이 diff 형식에 맞게 훈련되어 있기 때문이다. Responses API에서 `apply_patch`를 네이티브 도구로 지원하므로, API를 직접 사용할 때도 같은 메커니즘을 활용할 수 있다.
:::

### 2.4 read_file과 text_search

에이전트는 코드를 이해하기 위해 파일을 읽고 검색한다. 중요한 점은 Codex CLI가 **전체 프로젝트를 미리 로드하지 않는다**는 것이다.

```bash
# 에이전트의 전형적인 탐색 패턴
list_dir: src/            # 디렉터리 구조 파악
read_file: src/index.ts   # 진입점 확인
text_search: "parseConfig" # 함수 사용처 검색
read_file: src/utils/parser.ts  # 관련 파일 읽기
```

이 "필요할 때 읽기(lazy loading)" 방식은 컨텍스트 윈도우를 효율적으로 사용한다. 대규모 프로젝트에서도 관련 파일만 읽으므로, 토큰 한계에 빨리 도달하지 않는다.

---

## 3. 에이전틱 루프 동작

Codex CLI는 **ReAct(Reasoning + Acting) 패턴**의 단일 에이전트 루프로 동작한다. 이 루프는 모델이 최종 답변을 생성할 때까지 반복된다.

### 3.1 ReAct 루프 구조

```text
사용자 입력
    |
    v
[Think] - 현재 상태를 분석하고 다음 행동을 결정
    |
    v
[Tool Call] - 도구를 호출 (shell, read_file, apply_patch 등)
    |
    v
[Observe] - 도구 실행 결과를 관찰
    |
    v
[반복] - 목표 달성까지 Think -> Tool Call -> Observe 반복
    |
    v
[최종 답변] - 더 이상 도구 호출이 필요 없으면 결과 보고
```

### 3.2 실제 에이전틱 루프 예시

사용자가 "테스트가 실패하는 버그를 찾아서 수정해줘"라고 요청했을 때:

```text
[Think] 먼저 테스트를 실행하여 어떤 테스트가 실패하는지 확인해야 한다.

[Tool: shell] npm test
[Observe] FAIL src/__tests__/parser.test.ts
  - parseConfig should handle empty input (AssertionError)

[Think] parser.test.ts의 실패 테스트를 확인하고, parseConfig 함수를 분석해야 한다.

[Tool: read_file] src/__tests__/parser.test.ts
[Observe] (테스트 코드 내용)

[Tool: read_file] src/utils/parser.ts
[Observe] (파서 코드 - 빈 입력 처리 누락 발견)

[Think] parseConfig에 빈 문자열 입력 시 예외 처리가 없다.
        빈 입력 검증을 추가하겠다.

[Tool: apply_patch] src/utils/parser.ts
  (빈 입력 검증 코드 추가하는 diff)

[Think] 수정을 적용했다. 테스트가 통과하는지 확인하겠다.

[Tool: shell] npm test
[Observe] PASS src/__tests__/parser.test.ts (all tests passed)

[최종 답변] parseConfig 함수에 빈 입력 검증을 추가하여
           실패하던 테스트를 수정했습니다. 변경 사항: ...
```

### 3.3 셸 우선(Shell-First) 전략

Codex CLI의 독특한 점은 **셸 우선** 접근법이다. 전용 도구가 있더라도 셸 명령을 적극 활용한다.

```bash
# 파일 읽기: read_file 대신 cat도 사용
shell: cat src/config.ts

# 검색: text_search 대신 grep/rg도 사용
shell: rg "TODO|FIXME" --type ts

# Git 작업: 셸을 통해 직접 실행
shell: git log --oneline -10
shell: git diff HEAD~1 --stat
```

이 전략의 이유는 셸이 가장 **범용적인 인터페이스**이기 때문이다. 빌드 도구, 테스트 프레임워크, 린터, 패키지 매니저 등 모든 개발 도구를 셸을 통해 호출할 수 있다. 파일 수정만은 `apply_patch`를 통해 구조화된 형식으로 처리하여 안전성을 확보한다.

---

## 4. codex-mini-latest 모델 특성

Codex CLI의 기본 모델인 **codex-mini-latest**는 코딩 작업에 특화된 경량 모델이다.

### 4.1 모델 특성

| 특성 | 설명 |
|------|------|
| 최적화 대상 | 코드 생성, 수정, 분석 |
| 응답 속도 | 빠름 (경량 모델) |
| apply_patch 정확도 | 높음 (해당 형식에 맞게 훈련) |
| 컨텍스트 윈도우 | 코딩 작업에 충분한 크기 |
| 가격 | $1.50/$6.00 per 1M tokens (입력/출력) |

### 4.2 모델별 적합한 작업

```toml
# config.toml에서 작업별 프로필 설정 예시

[profiles.quick]
# 빠른 코드 수정, 간단한 리팩토링
model = "codex-mini-latest"

[profiles.complex]
# 복잡한 아키텍처 설계, 대규모 리팩토링
model = "o4-mini"

[profiles.review]
# 코드 리뷰, 보안 분석
model = "gpt-4.1"
```

codex-mini-latest는 다음 작업에서 특히 뛰어나다:

- 단일 함수/클래스 수정
- 테스트 코드 생성
- 린트 에러 수정
- 간단한 리팩토링 (변수명 변경, 함수 추출 등)
- diff 기반 코드 패치 생성

반면, 전체 시스템 아키텍처를 설계하거나 복잡한 알고리즘을 구현할 때는 o4-mini나 GPT-4.1 같은 더 강력한 모델을 사용하는 것이 좋다.

---

## 5. 멀티턴 대화와 승인 흐름

### 5.1 대화형 세션의 흐름

Codex CLI의 대화형 모드에서는 여러 턴에 걸친 작업이 가능하다. 각 턴에서 에이전트는 도구를 호출하고, 사용자는 승인 여부를 결정한다.

```text
[사용자] 이 프로젝트의 TypeScript 에러를 모두 수정해줘

[Codex] 먼저 TypeScript 컴파일 에러를 확인하겠습니다.
        > shell: npx tsc --noEmit
        [y/n/e]? y

[Codex] 3개의 타입 에러를 발견했습니다:
        1. src/api/handler.ts:15 - Type 'string' is not assignable...
        2. src/utils/format.ts:8 - Property 'name' does not exist...
        3. src/types/index.ts:22 - Missing return type...

        handler.ts부터 수정하겠습니다.
        [apply_patch: src/api/handler.ts]
        (diff 표시)
        [y/n/e]? y

[Codex] 다음으로 format.ts를 수정합니다.
        [apply_patch: src/utils/format.ts]
        (diff 표시)
        [y/n/e]? y

[Codex] 마지막으로 types/index.ts를 수정합니다.
        [apply_patch: src/types/index.ts]
        (diff 표시)
        [y/n/e]? y

[Codex] 모든 수정이 완료되었습니다. 확인을 위해 다시 컴파일하겠습니다.
        > shell: npx tsc --noEmit
        [y/n/e]? y

[Codex] 컴파일 성공! 모든 타입 에러가 수정되었습니다.
```

### 5.2 승인 옵션

도구 호출 시 사용자에게 제공되는 선택지:

| 옵션 | 키 | 설명 |
|------|---|------|
| 승인 | `y` | 도구 호출 실행 |
| 거부 | `n` | 도구 호출 거부, 에이전트에게 다른 방법 요청 |
| 편집 | `e` | 도구 호출 내용을 수정한 후 실행 |
| 항상 승인 | `a` | 현재 세션에서 동일 유형의 도구 호출을 자동 승인 |

`e` 옵션은 에이전트가 제안한 코드 수정을 직접 편집할 수 있게 해준다. apply_patch의 diff를 열어서 원하는 부분만 수정한 후 적용할 수 있다.

### 5.3 컨텍스트 관리

긴 세션에서는 컨텍스트 윈도우 한계에 도달할 수 있다. Codex CLI는 이를 **컨텍스트 압축(context compaction)**으로 처리한다.

```text
[시스템] 컨텍스트 윈도우 한계에 근접했습니다.
        세션을 자동으로 요약합니다.

[요약] 이전 대화에서 수행한 작업:
       - TypeScript 에러 3개 수정 완료
       - handler.ts, format.ts, types/index.ts 수정
       - 컴파일 성공 확인

[계속] 다음 작업을 지시해주세요.
```

중단된 세션을 이어서 작업하려면 `codex resume`을 사용한다.

---

## 6. Diff 기반 코드 수정 방식

### 6.1 apply_patch의 내부 동작

Codex CLI에서 파일 수정은 항상 `apply_patch` 도구를 통해 이루어진다. 모델은 통합 diff 형식의 패치를 생성하고, CLI가 이를 파싱하여 파일에 적용한다.

```diff
--- a/src/components/UserCard.tsx
+++ b/src/components/UserCard.tsx
@@ -1,6 +1,7 @@
 import React from 'react';
+import { memo } from 'react';
 import { User } from '../types';

-export function UserCard({ user }: { user: User }) {
+export const UserCard = memo(function UserCard({ user }: { user: User }) {
   return (
     <div className="user-card">
@@ -12,4 +13,4 @@
       <span>{user.email}</span>
     </div>
   );
-}
+});
```

### 6.2 왜 전체 파일 재작성이 아닌 diff인가

전체 파일을 재작성하는 방식과 비교했을 때 diff 기반 수정의 이점은 명확하다.

| 항목 | 전체 재작성 | diff 기반 (apply_patch) |
|------|-----------|----------------------|
| 출력 토큰 | 파일 전체 크기 | 변경된 부분만 |
| 비용 | 높음 | 낮음 |
| 리뷰 | 전체 비교 필요 | 변경점 즉시 확인 |
| Git 충돌 | 높은 위험 | 낮은 위험 |
| 정확도 | 복사 실수 가능 | 정밀한 변경 |
| 대형 파일 | 비효율적 | 효율적 |

### 6.3 멀티파일 수정

하나의 작업에서 여러 파일을 수정해야 할 때, Codex는 순차적으로 각 파일에 대한 패치를 생성한다.

```text
[Think] 인터페이스 변경에 따라 3개 파일을 수정해야 한다.

[Tool: apply_patch] src/types/index.ts
--- a/src/types/index.ts
+++ b/src/types/index.ts
@@ -5,6 +5,7 @@
 export interface User {
   id: string;
   name: string;
+  avatar?: string;
 }

[Tool: apply_patch] src/components/UserCard.tsx
--- a/src/components/UserCard.tsx
+++ b/src/components/UserCard.tsx
@@ -8,6 +8,9 @@
   return (
     <div className="user-card">
+      {user.avatar && (
+        <img src={user.avatar} alt={user.name} />
+      )}
       <h3>{user.name}</h3>

[Tool: apply_patch] src/api/users.ts
--- a/src/api/users.ts
+++ b/src/api/users.ts
@@ -12,6 +12,7 @@
   return {
     id: data.id,
     name: data.name,
+    avatar: data.avatar_url,
   };
```

이처럼 타입 정의, 컴포넌트, API 레이어를 일관되게 수정하면서도, 각 파일의 변경 사항을 독립적으로 리뷰할 수 있다.

---

## 7. 실전: 샌드박스와 코드 생성 활용

### 7.1 안전한 코드 탐색

낯선 프로젝트를 처음 분석할 때, `read-only` 샌드박스가 유용하다.

```bash
codex --suggest --sandbox read-only
```

```text
> 이 프로젝트의 아키텍처를 분석하고 기술 부채를 찾아줘
```

읽기 전용 샌드박스에서는 어떤 명령도 파일을 수정하거나 네트워크에 접근할 수 없으므로, 완전히 안전하게 코드를 분석할 수 있다.

### 7.2 테스트 주도 수정

```bash
codex --auto-edit
```

```text
> src/auth/jwt.ts에 있는 토큰 검증 로직에 만료 시간 체크를 추가해줘.
  먼저 테스트를 작성하고, 테스트가 통과하도록 코드를 수정해줘.
```

auto-edit 모드에서 Codex는 테스트 파일과 소스 파일을 자동으로 수정하지만, `npm test` 실행은 사용자에게 확인을 요청한다. 이 균형이 auto-edit 모드의 핵심이다.

### 7.3 일괄 린트 수정

```bash
codex --full-auto --sandbox workspace-write \
  "ESLint 에러를 모두 수정해줘. --fix 옵션으로 자동 수정 가능한 것은 먼저 처리하고, 수동 수정이 필요한 것은 직접 고쳐줘"
```

full-auto 모드에서는 린트 실행, 파일 수정, 재검증까지 모두 자동으로 수행한다. 샌드박스가 `workspace-write`이므로 작업 디렉터리 내 파일만 수정할 수 있어 안전하다.

---

## 마무리

이 글에서 다룬 Codex CLI의 핵심 기능을 정리하면:

| 핵심 기능 | 기술적 특징 |
|----------|-----------|
| 샌드박스 (macOS) | Seatbelt - SBPL 기반 deny-by-default 정책 |
| 샌드박스 (Linux) | Bubblewrap + Landlock + Seccomp 3중 보호 |
| 코드 수정 | apply_patch - 통합 diff 기반 최소 변경 |
| 에이전틱 루프 | ReAct 패턴 - Think/Tool/Observe 반복 |
| 셸 우선 전략 | 범용 셸 + 구조화된 apply_patch 조합 |
| 컨텍스트 관리 | 지연 로딩 + 자동 압축 |

플랫폼 네이티브 샌드박스는 Codex CLI를 다른 AI 코딩 도구와 차별화하는 핵심 기술이다. OS 커널 수준에서 에이전트의 행동을 제한하므로, full-auto 모드에서도 시스템 안전성을 보장할 수 있다. apply_patch를 통한 diff 기반 수정은 토큰 효율성과 코드 리뷰 편의성을 동시에 달성한다.

다음 글 [[codex-guide-03-advanced|Codex CLI 고급 활용]]에서는 자동화와 CI 통합 방법을 다룬다.
