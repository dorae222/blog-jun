# 리팩토링 교훈

## 한글 폰트 (cairosvg)
- `fonts-noto-cjk` 설치만으로 부족. fontconfig 별칭 설정으로 KR 변형을 명시적으로 우선 지정해야 함
- Docker multi-stage build에서 폰트는 production stage에 설치 (builder 아님)
- `fc-list :lang=ko` 으로 실제 등록된 폰트 이름 확인 필수

## Pipeline 구조
- 52개 스크립트가 flat하게 있으면 관리 불가 → 6개 패키지로 분리
- management commands는 `sys.path`로 pipeline을 import하므로, 루트 레벨 파일 유지 필요
- deprecated 스크립트는 git history에 있으므로 과감하게 삭제

## Backend
- serializer에서 반복되는 URL 빌딩 로직 → mixin으로 추출
- PostManager.published() 등 자주 쓰는 필터는 커스텀 매니저로

## 카테고리 재구조화
- 기존 aws → 10개 도메인 분할 시, 기존 카테고리의 포스트를 안전하게 이동하는 로직 필요
- TAG_TO_SUBCATEGORY 맵은 태그 추가될 때마다 유지보수 필요

## 인프라/배포 (2026-07)
- **프로덕션은 K8s** (`blog` ns, CNPG, ArgoCD). docker-compose는 레거시. 배포 대상 착각 주의 - 터널이 실제로 어느 origin을 보는지(`cloudflared config.yml`의 ingress) 먼저 확인.
- `git reset --hard origin/main` 주의: 공개 rewrite본은 CLAUDE.md/.claude 등을 제거(gitignore)했으므로, reset하면 로컬 설정이 워킹트리에서 사라짐. 백업 브랜치에서 `git checkout <backup> -- CLAUDE.md .claude` 후 `git reset`으로 복원(gitignore라 untracked 유지).
- **macOS tar → 파드 전송 시 `COPYFILE_DISABLE=1 tar ...` 필수**. 안 하면 `._` AppleDouble 파일이 함께 들어가 import가 잡파일까지 MinIO에 업로드함.
- `kubectl exec -i`로 stdin 스트리밍은 `lxc exec` 경유 시 EOF 전파 안 돼 행에 걸림. → hj-local에 kubectl 직접 두고 `kubectl cp`(파일 복사) + 파드 로컬 추출로 우회.
- 파드는 non-root(appuser) → `/app`에 못 씀. import용 파일은 `/tmp/pipeline`에 두고 `PYTHONPATH=/app`으로 Django config 찾게 실행.
- 호스트 과부하 시 sshd fork 실패로 공인 SSH가 전부 리셋됨(디스크/RAM 여유 있어도). LAN `ssh hj-local` 우회. 크래시루프 서비스(가드레일 없는 systemd Restart=always)가 만성 원인.

## 프론트 검증 (모바일/오버플로우)
- **headless Chrome 스크린샷은 SPA+framer-motion에서 신뢰 불가** (blank/애니 중간/가짜 오버플로우). 모바일 비율·수평 오버플로우 판정은 **Playwright**로. 전역 설치 위치 `/usr/local/lib/node_modules` → ESM에서 `import pw from '/usr/local/lib/node_modules/playwright/index.js'; const { chromium } = pw`. `deviceScaleFactor:2 + reducedMotion:'reduce'`로 클린 캡처, `document.documentElement.scrollWidth vs clientWidth`로 실제 오버플로우 측정(요소별 `getBoundingClientRect().right > vw`로 원인 특정).
- grid 자식이 nowrap 콘텐츠(코드블록 등)로 뷰포트를 밀어낼 때 → 그 컬럼에 `min-w-0`(grid 자식 기본 min-width:auto 해제) + 내부 `overflow-x-auto`. `pointer-events-none` aurora blob / 카드 내부 `overflow-x-auto`는 요소 rect가 vw를 넘어도 페이지 스크롤 유발 안 함(오탐 주의).
- JSX에서 텍스트–`<br>`–텍스트 사이 개행은 태그 인접 공백이 제거됨 → `hidden sm:block` br이 모바일에서 숨으면 `단어,단어`로 공백 소실. 명시적 `{' '}` 필요.
