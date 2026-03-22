# Pipeline

Obsidian Vault → Django DB 데이터 처리 파이프라인.

## 데이터 흐름

```
Obsidian Vault → scanner → preprocessor → batch API → import → Django DB
```

## 패키지 구조

- `utils/` — 공통 유틸리티 (Batch API 클라이언트, ORM 헬퍼, SVG, 이미지, 텍스트)
- `importers/` — 컨텐츠 임포트 (papers, architectures, ml, cloud, colab, data)
- `generators/` — 이미지/컨텐츠 생성 (커버 SVG, 아키텍처 figure, 논문 SVG)
- `batch/` — OpenAI Batch API 파이프라인 (prepare, process, import)
- `preprocessing/` — Notion→Markdown 전처리 (scanner, preprocessor, html_parser)
- `useful/` — 독립 유틸리티 스크립트 (1회성이지만 참고 가치)

## 주요 명령어

```bash
# 전처리
python -m pipeline.preprocessing.scanner --vault-path /path/to/vault
python -m pipeline.preprocessing.preprocessor --input-dir data/scanned/

# Batch API
python -m pipeline.batch.prepare --input data/preprocessed/
python -m pipeline.batch.process --input data/batch_input.jsonl
python -m pipeline.batch.import_results --input data/batch_output.jsonl

# 임포트
python pipeline/importers/papers.py --data-dir data/papers_written/
python pipeline/importers/architectures.py --data-dir data/architectures_written/
python pipeline/importers/ml.py --data-dir data/ml_written/

# 커버 이미지 (Django management command)
python manage.py generate_cover_images [--category CAT] [--strategy paper_cover|category_gradient]
```

## data/ 디렉토리

`pipeline/data/`는 컨텐츠 소스 데이터를 보관.
바이너리 파일(PNG/SVG/PDF)은 Git LFS로, 텍스트 파일(JSON/MD)은 일반 git으로 추적.
중간 산출물(batch_*.jsonl, preprocessed/ 등)은 .gitignore에서 제외.
