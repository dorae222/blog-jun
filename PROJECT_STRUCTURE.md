# Project Structure

## 디렉토리 트리

```
blog-jun/
├── backend/                # Django 5 + DRF API
│   ├── accounts/           # 사용자 인증 (JWT)
│   ├── blog/               # 블로그 핵심 앱
│   │   ├── management/     # 커스텀 관리 명령어
│   │   └── migrations/     # DB 마이그레이션
│   ├── chatbot/            # RAG 챗봇 (pgvector + OpenAI SSE)
│   ├── config/             # Django 설정
│   │   └── settings/       # base / dev / prod 분리
│   ├── bin/                # 유틸리티 스크립트
│   └── media/              # 업로드 파일 (git 미추적)
├── frontend/               # React 19 + Vite + Tailwind CSS v4
│   ├── public/             # 정적 에셋
│   ├── src/
│   │   ├── api/            # API 호출 함수
│   │   ├── components/
│   │   │   ├── architecture/  # 아키텍처 갤러리 컴포넌트
│   │   │   ├── blog/       # 블로그 관련 (MarkdownRenderer, PaperSummaryBox)
│   │   │   ├── chatbot/    # 챗봇 UI
│   │   │   ├── common/     # 공통 컴포넌트
│   │   │   ├── editor/     # 에디터 (EditorToolbar, NotionEditor, SlashCommand)
│   │   │   ├── effects/    # 시각 효과 (ParticleBackground, TiltCard, GradientCursor)
│   │   │   ├── icons/      # 아이콘 컴포넌트
│   │   │   ├── layout/     # Header, Footer 등
│   │   │   └── portfolio/  # 포트폴리오 섹션
│   │   ├── data/           # 정적 데이터
│   │   ├── hooks/          # 커스텀 React 훅
│   │   ├── pages/          # 페이지 컴포넌트
│   │   └── utils/          # 유틸리티 함수
│   └── nginx.conf          # 프로덕션 Nginx 설정
├── pipeline/               # 데이터 처리 파이프라인
│   ├── data/               # 전처리 데이터 (git 미추적)
│   ├── archive/            # 아카이브 스크립트 (git 미추적)
│   └── backup_*/           # 로컬 백업 (git 미추적)
├── e2e/                    # Playwright E2E 테스트
│   ├── screenshots/        # 테스트 스크린샷
│   └── test-results/       # 테스트 결과 (git 미추적)
├── lxd/                    # LXD 컨테이너 프로비저닝 스크립트
├── docs/                   # 문서
├── tasks/                  # 작업 관리
├── docker-compose.prod.yml # 프로덕션 Docker Compose
├── deploy.sh               # 배포 스크립트
└── Makefile                # 개발 명령어 단축
```

## 핵심 파일 매핑

### 백엔드 (Django)

| 파일 | 역할 |
|------|------|
| `backend/blog/models.py` | Post, Category, Tag, Series, PostTemplate, ArchitectureEntry, ArchitectureConcept |
| `backend/blog/views.py` | REST API 뷰셋 (PostViewSet 등) |
| `backend/blog/serializers.py` | DRF 시리얼라이저 |
| `backend/blog/urls.py` | API URL 라우팅 |
| `backend/blog/admin.py` | Django Admin 설정 |
| `backend/chatbot/views.py` | RAG 챗봇 (pgvector + OpenAI SSE 스트리밍) |
| `backend/config/settings/base.py` | 공통 Django 설정 |
| `backend/config/settings/prod.py` | 프로덕션 설정 |
| `backend/blog/management/commands/seed_ai_categories.py` | AI 카테고리 시딩 |
| `backend/blog/management/commands/cleanup_non_cloud.py` | 비-Cloud 포스트 정리 |

### 프론트엔드 (React)

| 파일 | 역할 |
|------|------|
| `frontend/src/App.jsx` | 라우팅 + 앱 레이아웃 |
| `frontend/src/pages/PostView.jsx` | 포스트 상세 뷰 |
| `frontend/src/pages/Editor.jsx` | 포스트 에디터 |
| `frontend/src/pages/ArchitectureGallery.jsx` | 아키텍처 비교 갤러리 |
| `frontend/src/pages/PaperList.jsx` | 논문 목록 |
| `frontend/src/components/blog/MarkdownRenderer.jsx` | 마크다운 렌더링 (KaTeX + GFM) |
| `frontend/src/components/layout/Header.jsx` | 네비게이션 헤더 |
| `frontend/src/api/posts.js` | API 호출 함수 |
| `frontend/src/index.css` | 글로벌 CSS + 외부 스타일 import |

### 파이프라인

| 파일 | 역할 |
|------|------|
| `pipeline/scanner.py` | Obsidian 볼트 스캔 (마크다운 수집) |
| `pipeline/preprocessor.py` | 전처리 (메타데이터 추출, 정리) |
| `pipeline/importers/` | 컨텐츠 임포트 (papers, architectures, ml, colab, data) |
| `pipeline/generators/` | 이미지/컨텐츠 생성 (cover_templates, paper_svgs) |
| `pipeline/embedding_generator.py` | 임베딩 생성 (RAG용) |
| `pipeline/image_handler.py` | 이미지 처리 |

## 환경 변수 (.env)

| 키 | 설명 |
|----|------|
| `DJANGO_SECRET_KEY` | Django 시크릿 키 |
| `DB_NAME` | PostgreSQL 데이터베이스명 |
| `DB_USER` | PostgreSQL 사용자명 |
| `DB_PASSWORD` | PostgreSQL 비밀번호 |
| `ALLOWED_HOSTS` | Django 허용 호스트 (e.g. blog.dorae222.com) |
| `CORS_ALLOWED_ORIGINS` | CORS 허용 출처 |
| `OPENAI_API_KEY` | OpenAI API 키 (파이프라인 + 챗봇) |
| `LLM_BASE_URL` | (선택) 자체 LLM 엔드포인트 |
| `LLM_MODEL` | (선택) 자체 LLM 모델명 |
| `IMAGE_TAG` | Docker 이미지 태그 (기본: latest) |
