---
name: scrape-arxiv
description: arXiv 논문에서 figure/table HTML 크롤링
allowed-tools: Bash(python *), Read, Glob, WebFetch
---

ar5iv HTML에서 논문 figure를 크롤링합니다.

## 원리

ar5iv.labs.arxiv.org는 arXiv 논문의 HTML 렌더링을 제공합니다.
PDF에서 벡터 그래픽으로 누락된 figure도 HTML에서는 PNG로 정상 노출됩니다.

## 사용법

```bash
# 단일 논문
python pipeline/scrape_arxiv_figures.py --slug <slug>

# Figure 0인 논문만 (30개 대상)
python pipeline/scrape_arxiv_figures.py --missing-only

# 전체 재크롤링
python pipeline/scrape_arxiv_figures.py --all

# 테이블도 추출
python pipeline/scrape_arxiv_figures.py --slug <slug> --tables
```

## Figure 통합 (크롤링 후)

```bash
# 단일 논문 figure를 content.json에 통합
python -m pipeline.generators.figure_integrator --slug <slug>

# 전체 논문
python -m pipeline.generators.figure_integrator --all

# 변경 없이 확인만
python -m pipeline.generators.figure_integrator --dry-run --all
```

## 출력 경로

- 크롤링 원본: `pipeline/data/papers_written/{slug}/figures/fig_{idx}.png`
- 메타데이터: `pipeline/data/papers_written/{slug}/figures/metadata.json`
- Django media: `media/figures/papers/{slug}/fig_{idx}.png`
- DB 모델: `PostImage(image_type='paper_figure')`

## Figure 0인 논문 (30개)

albert, bart, bert, bloom, chinchilla, deepseek-v2, deit, electra, elmo, ernie,
gated-deltanet, gla, llama, lora, mamba, mt5, olmo, qwen2, react, reflexion,
retnet, roberta, self-consistency, siglip, switch-transformer, t5, toolformer,
ul2, whisper, xlstm

## Rate Limit

arXiv 정책 준수: 요청 간 3초 간격.
