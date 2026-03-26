# blog-jun

Personal tech blog: Django 5 + DRF backend, React 19 + Vite + Tailwind CSS frontend.

## Project Structure
- `backend/` — Django DRF API (config/settings split: base/dev/prod)
  - `blog/` — 포스트, 카테고리, 태그, 시리즈, 커버 이미지
  - `accounts/` — JWT 인증
  - `operations/` — 운영 로그 (API 요청, 관리 명령어, 세션 기록)
- `frontend/` — React SPA with Framer Motion animations
- `pipeline/` — 데이터 처리 파이프라인
  - `data/` — 컨텐츠 데이터 (아래 "컨텐츠 데이터 구조" 참조)
  - `useful/` — 독립 유틸리티 스크립트 (split, build_index, improvement_plan 등)
  - `importers/` — 컨텐츠 임포트 (papers, architectures, ml, colab, data)
  - `generators/` — 이미지/컨텐츠 생성 (cover_templates, arch_figures, paper_svgs)
  - `preprocessing/` — Notion→Markdown 전처리 (scanner, preprocessor, html_parser)
- `content/` — 소스 컨텐츠 (cloud, llm, agent 등 10개 도메인)
- `e2e/` — Playwright E2E 테스트
- `lxd/` — LXD container provisioning scripts

## Commands
- `make dev` — Start dev environment (docker compose)
- `make migrate` — Run Django migrations
- `make seed` — Seed post templates
- `make deploy` / `./deploy.sh` — 수동 배포 (서버에서 직접 빌드)
- `python manage.py generate_cover_images` — 커버 이미지 생성/재생성
- `python manage.py seed_cloud_categories` — Cloud 카테고리 시딩 (AWS 10개 서브카테고리)
- `python manage.py reclassify_cloud_posts` — Cloud 포스트 서브카테고리 재분류
- `python manage.py fix_content --fix=emoji` — 이모지 제거
- `python manage.py assign_series` — 시리즈 할당
- `python manage.py review_post_quality` — 품질 검사

## 컨텐츠 데이터 구조

### 디렉토리 레이아웃 (pipeline/data/)
```
pipeline/data/
├── blog-jun-content.json          ← 중앙 인덱스 (621개 엔트리)
├── papers_written/                 ← 논문 리뷰 (201개)
│   └── {slug}/
│       ├── content.md              ← 마크다운 본문 (편집 대상)
│       ├── content.json            ← 메타데이터 (title, tags, arxiv_url 등)
│       ├── figures/                ← 이미지 파일
│       │   ├── *.png
│       │   └── metadata.json       ← ar5iv 크롤링 figure 메타데이터
│       └── figure_reference.json   ← 영문 캡션 (있는 경우)
├── architectures_written/          ← 아키텍처 (182개)
│   └── {slug}/
│       ├── content.md
│       ├── content.json
│       ├── entry.json              ← ArchitectureEntry 모델 데이터
│       └── figures/
├── cloud_written/                  ← 클라우드/AWS (166개)
├── ml_written/                     ← 머신러닝 (51개)
├── data_written/                   ← 데이터 엔지니어링 (13개)
└── colab_written/                  ← 튜토리얼 (8개)
```

### blog-jun-content.json 중앙 인덱스
- 621개 전체 컨텐츠의 메타데이터 + improvement_plan
- 섹션: `papers`, `architectures`, `cloud`, `ml`, `data`, `colab`
- papers는 상세 (figures items, improvement_plan.figure_insertions 포함)
- 비-papers는 경량 (slug, title, sections, improvement_plan 요약만)
- 재생성: `python3 pipeline/useful/build_content_index.py`

### 컨텐츠 개선 워크플로우
1. `blog-jun-content.json`에서 `improvement_plan.priority` 순으로 대상 선택
2. Claude Code가 content.md + figures를 직접 검토 (멀티모달)
3. 개선된 content.md 작성 (figure 삽입 + 텍스트 품질 개선)
4. `improvement_plan.status` → `"completed"` 업데이트
5. import 스크립트 `--update` 실행 → Django DB 반영
6. 배포

### 유틸리티 스크립트 (pipeline/useful/)
| 스크립트 | 역할 |
|----------|------|
| `split_content_json.py` | content.json → content.md 분리 (전체 카테고리) |
| `build_content_index.py` | blog-jun-content.json 재생성 |
| `generate_improvement_plans.py` | papers별 improvement_plan 생성 |
| `enrich_figure_metadata.py` | ar5iv 크롤링으로 figure 메타데이터 보강 |
| `insert_figures.py` | content.md에 figure 마크다운 삽입 |

### Import 스크립트
| 스크립트 | 대상 | `--update` |
|----------|------|------------|
| `import_papers_written.py` | papers → Post(paper_review) | ✓ |
| `import_architectures.py` | architectures → ArchitectureEntry + Post | ✓ |
| `import_ml_written.py` | ml → Post(article) | ✓ |
| `import_data_written.py` | data → Post(article) | ✓ |
| `import_colab_written.py` | colab → Post(tutorial) | ✓ |

## Architecture
- Backend: Django 5 + DRF + Gunicorn + PostgreSQL (pgvector) + Redis
- Frontend: React 19 + Vite + Tailwind CSS v4 + Framer Motion
- Auth: JWT (simplejwt)
- Deploy: Docker Compose + Cloudflare Tunnel
- Pipeline: content.md 편집 → import --update → deploy

## Key Files
- Models: `backend/blog/models.py` (Post, Category, Tag, Series + PostManager)
- Managers: `backend/blog/managers.py` (PostQuerySet: published, with_cover, by_category)
- Mixins: `backend/blog/mixins.py` (ImageUrlMixin)
- API: `backend/blog/views.py`, `backend/blog/urls.py`
- Operations: `backend/operations/` (OperationLog, SessionLog, RequestLoggingMiddleware)
- Frontend entry: `frontend/src/App.jsx`
- Cover templates: `pipeline/cover_templates.py` (`pipeline/generators/cover_templates.py`)
- SVG utils: `pipeline/svg_utils.py` (`pipeline/utils/svg_utils.py`)

## Category Structure

### Cloud (10.Cloud) — 13개 서브카테고리
Docker, LXD, DevOps + AWS 10개 도메인:
aws-compute, aws-storage, aws-database, aws-networking, aws-security,
aws-analytics, aws-ai-ml, aws-devtools, aws-management, aws-integration

### AI/ML (20.AI) — 7개 서브카테고리
llm, ssm, diffusion, vision, multimodal, agent, technique

### ML (40.ML) — 12개 서브카테고리
fundamentals, math-foundations, preprocessing, supervised-regression/classification,
ensemble, unsupervised, model-evaluation, causal-inference, advanced-algorithms,
applications, mlops

## Deployment
- Live: https://blog.dorae222.com
- Infra: LXD container `blog-server` (10.10.10.30) on hj-remote
- Tunnel: Cloudflare Tunnel `blog-jun` (079ef309)
- Docker: docker-compose.prod.yml (db, redis, backend, frontend) — build: 지시자 사용
- 배포: `./deploy.sh` — SSH ProxyJump(hj-remote → blog-server) + git pull + docker compose build
- **Git LFS**: pipeline/data/ 하위 PNG/SVG/PDF는 LFS 관리. push 후 반드시 `git lfs push origin main --all` 실행

## ML Sandbox
- LXD container `ml-sandbox` (10.10.10.32) on hj-remote
- 용도: ML 코드 격리 실행 (matplotlib, scikit-learn 시각화)
- 스펙: 4 CPU, 16GB RAM, Ubuntu 24.04
- 접속: `ssh ml-sandbox` (ProxyJump hj-remote)
- Python 3.12 + numpy, scipy, scikit-learn, pandas, matplotlib, seaborn
- 작업 디렉토리: /workspace

## CSS 주의사항
- Tailwind CSS v4 + `@tailwindcss/vite` 플러그인 환경에서 JSX에서 import한 CSS는 번들에 포함되지 않음
- highlight.js 등 외부 CSS는 반드시 `index.css`의 `@import`로 추가해야 함

## Git Sync
| Location | Path | Purpose |
|----------|------|---------|
| MacBook | ~/Documents/Obsidian/blog-jun/ | Development + Pipeline |
| hj-remote | ~/lxd-servers/blog-jun/ | Infra management |
| blog-server | /opt/blog-jun/ | Production |

---

## 워크플로우 설계

### 1. 기본은 계획 모드
- 사소하지 않은 모든 작업은 계획 모드로 시작 (3단계 이상이거나 구조적 결정이 필요한 경우)
- 뭔가 잘못되면 즉시 멈추고 다시 계획 세우기 — 그냥 밀어붙이지 말 것
- 계획 모드는 개발할 때만이 아니라 검증 단계에서도 활용
- 모호함을 줄이려면 처음부터 상세 스펙을 작성할 것

### 2. 서브에이전트 활용
- 메인 컨텍스트 창을 깔끔하게 유지하려면 서브에이전트를 적극적으로 활용
- 조사, 탐색, 병렬 분석은 서브에이전트에 맡길 것
- 복잡한 문제일수록 서브에이전트를 더 많이 투입
- 서브에이전트 하나당 하나의 작업만 — 집중 실행을 위해

### 3. 자기개선 루프
- 사용자에게 수정을 받을 때마다: 해당 패턴을 `tasks/lessons.md`에 기록
- 같은 실수를 반복하지 않도록 스스로 규칙을 작성
- 실수율이 낮아질 때까지 이 교훈들을 반복해서 다듬을 것
- 세션 시작 시 해당 프로젝트의 교훈 목록을 먼저 검토

### 4. 완료 전 반드시 검증
- 작동한다는 걸 증명하기 전까지 절대 작업 완료로 표시하지 말 것
- 필요한 경우 main과 변경 사항 간의 동작 차이를 비교
- 스스로에게 물어볼 것: "시니어 엔지니어가 이걸 승인할까?"
- 테스트 실행, 로그 확인, 정확성 입증

### 5. 우아함을 추구할 것 (균형 있게)
- 사소하지 않은 변경이라면: 잠깐 멈추고 "더 우아한 방법이 있지 않을까?" 자문
- 수정이 어설프게 느껴진다면: "지금 내가 아는 모든 걸 바탕으로, 우아한 해결책을 구현해"
- 단순하고 명백한 수정엔 이 과정을 생략 — 오버엔지니어링 금지
- 결과물을 내놓기 전에 스스로 검토

### 6. 자율적인 버그 수정
- 버그 리포트를 받으면: 그냥 고칠 것. 하나하나 물어보지 말 것
- 로그, 에러, 실패한 테스트를 직접 찾아서 해결
- 사용자가 컨텍스트를 전환할 필요가 없도록
- 어떻게 하라는 말 없이도 실패한 CI 테스트를 직접 가서 고칠 것

## 작업 관리

1. **계획 먼저**: 체크 가능한 항목으로 `tasks/todo.md`에 계획 작성
2. **계획 검토**: 구현 시작 전에 확인
3. **진행 상황 추적**: 진행하면서 완료 항목 표시
4. **변경 사항 설명**: 각 단계마다 상위 수준 요약 제공
5. **결과 문서화**: `tasks/todo.md`에 검토 섹션 추가
6. **교훈 기록**: 수정 후 `tasks/lessons.md` 업데이트

## 핵심 원칙

- **단순함 우선**: 모든 변경은 최대한 단순하게. 건드리는 코드는 최소화.
- **게으름 금지**: 근본 원인을 찾을 것. 임시방편 없음. 시니어 개발자 기준으로.
- **최소 영향**: 꼭 필요한 부분만 수정. 새로운 버그를 만들지 말 것.
