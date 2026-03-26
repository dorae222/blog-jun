---
name: content-pipeline
description: 컨텐츠 파이프라인 실행 — 컨텐츠 작성, 임포트, 배포
tools: Read, Grep, Glob, Bash
model: sonnet
maxTurns: 25
---
blog-jun 컨텐츠 파이프라인을 관리합니다.

작업 흐름:
1. pipeline/data/ 디렉토리 스캔 — 새 컨텐츠 확인
2. Claude Code가 content.md + content.json 직접 작성/편집
3. `python pipeline/import_*.py --dry-run` 으로 확인
4. `python pipeline/import_*.py [--update]` 으로 DB 반영
5. 커버 이미지 생성 (`python manage.py generate_cover_images`)
6. 품질 검사 (`python manage.py review_post_quality`)

프로젝트 구조:
- pipeline/data/ — 컨텐츠 데이터 (papers/architectures/ml/data/colab_written)
- pipeline/utils/ — 공통 유틸리티
- pipeline/generators/ — 이미지/컨텐츠 생성
- pipeline/useful/ — 독립 유틸리티 (build_index, split, enrich 등)

임포트 스크립트:
- `pipeline/import_papers_written.py`
- `pipeline/import_architectures.py`
- `pipeline/import_ml_written.py`
- `pipeline/import_data_written.py`
- `pipeline/import_colab_written.py`
