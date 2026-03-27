# Pipeline Scripts

블로그 컨텐츠 데이터 처리 파이프라인.

## 주요 흐름

```
Obsidian 노트 / arXiv 논문
        ↓
scanner → preprocessor → content.md 직접 편집 (Claude Code)
        ↓                        ↓
   content/ (원본)      pipeline/data/ (결과)
                              ↓
                       각 importer → Django DB
```

## 디렉토리 구조

| 디렉토리 | 역할 |
|---------|------|
| `utils/` | 공통 유틸 (svg_utils, post_factory, text_utils, image_utils) |
| `importers/` | 컨텐츠 → Django DB (papers, architectures, ml, colab, data, cloud) |
| `generators/` | 이미지/컨텐츠 생성 (cover_templates, arch_figures, paper_svgs, ml_outputs) |
| `preprocessing/` | Notion → Markdown 전처리 (scanner, preprocessor, html_parser) |
| `useful/` | 독립 유틸리티 (embedding, figure 분석, PDF 임포트 등) |
| `data/` | 처리된 컨텐츠 JSON (ml_written, papers_written, architectures_written 등) |

## 스크립트별 역할

### Importers (pipeline/data/ → Django DB)

| 스크립트 | 역할 | 실행 예시 |
|---------|------|---------|
| `import_ml_written.py` | ML 포스트 임포트/업데이트 | `--dry-run`, `--update`, `--reset` |
| `import_papers_written.py` | 논문 리뷰 임포트 | `--dry-run`, `--force-images` |
| `import_architectures.py` | 아키텍처 엔트리 임포트 | `--dry-run` |
| `import_colab_written.py` | Colab 노트북 임포트 | `--dry-run` |
| `import_data_written.py` | 데이터 포스트 임포트 | `--dry-run` |

### Generators

| 스크립트 | 역할 | 실행 예시 |
|---------|------|---------|
| `generators/ml_outputs.py` | ML 코드 실행 + figure 생성 | `--slug [slug] --execute`, `--all --execute` |
| `generators/cover_templates.py` | SVG 커버 이미지 템플릿 | Django management command로 실행 |
| `generators/arch_figures.py` | 아키텍처 다이어그램 생성 | `--slug [slug]` |
| `generators/paper_svgs.py` | 논문 리뷰 SVG 생성 | `--slug [slug]` |
| `generators/figure_integrator.py` | Figure를 content에 통합 | `--slug [slug]` |

### Useful (독립 유틸리티)

| 스크립트 | 역할 |
|---------|------|
| `useful/annotate_figures.py` | Claude API로 ML figure 캡션 개선 |
| `useful/add_figure_attribution.py` | Figure 출처 표기 추가 (papers/architectures) |
| `useful/embedding_generator.py` | RAG용 포스트 임베딩 생성 |
| `useful/build_post_links.py` | PostLink 자동 생성 |
| `useful/extract_paper_figures.py` | 논문 PDF에서 figure 추출 |

## ml-sandbox 실행 가이드

ML 코드는 격리된 LXD 컨테이너에서 실행합니다.

```bash
# 1. 접속
ssh ml-sandbox  # ProxyJump hj-remote

# 2. 작업 디렉토리
cd /workspace

# 3. 스크립트 동기화 (로컬에서)
rsync -avz pipeline/ ml-sandbox:/workspace/pipeline/

# 4. 실행
python3 -m pipeline.generators.ml_outputs --all --execute

# 5. 결과 회수 (로컬에서)
rsync -avz ml-sandbox:/workspace/pipeline/data/ml_written/ pipeline/data/ml_written/
rsync -avz ml-sandbox:/workspace/backend/media/figures/outputs/ backend/media/figures/outputs/
```

### GPU 모델 실행 기준 (RTX 3090 24GB)

| 모델 유형 | VRAM 요구 | 실행 가능 |
|---------|---------|---------|
| sklearn, numpy, pandas | CPU | ✅ |
| BERT-base, GPT-2, T5-base | ~1.5-3GB | ✅ |
| LLaMA 7B, Mistral 7B | ~14GB fp16 | ✅ |
| LLaMA 13B | int8 ~13GB | ✅ |
| LLaMA 30B | int4 ~15GB | ✅ |
| LLaMA 65B+ | > 24GB | ❌ API 대체 |

## 코드 블록 분류 (ml_outputs.py)

| 타입 | 설명 | 처리 |
|------|------|------|
| `execute_figure` | matplotlib/seaborn 시각화 | 실행 → PNG 저장 |
| `execute_print` | print/display 출력 | 실행 → stdout 캡처 |
| `precompute` | 표준 데이터셋 + 메트릭 | 실행 시도, 실패 시 검색 대체 |
| `hf_gpu` | HuggingFace 경량 모델 | GPU fp16 실행 |
| `hf_quantized` | HuggingFace 대규모 모델 | int4/int8 quantization |
| `hf_api` | 초대규모 모델 (65B+) | 스킵 + API 호출 주석 |
| `no_output` | import/setup | namespace에 실행만 |

## data/ 디렉토리

`pipeline/data/`는 컨텐츠 소스 데이터를 보관.
바이너리 파일(PNG/SVG/PDF)은 Git LFS로, 텍스트 파일(JSON/MD)은 일반 git으로 추적.
중간 산출물(preprocessed/ 등)은 .gitignore에서 제외.
