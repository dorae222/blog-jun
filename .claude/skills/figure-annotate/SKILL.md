---
name: figure-annotate
description: Claude Code 멀티모달 figure 분석 + 캡션 개선
allowed-tools: Bash(python *), Read
---
Claude Code multimodal figure annotation:

1. 대상 PNG 확인:
   ls backend/media/figures/outputs/

2. Claude Code가 Read 도구로 PNG 직접 분석:
   Read backend/media/figures/outputs/[slug]/[slug]_fig_1.png
   → 분석 후 적절한 한국어 캡션 작성

3. 자동화 스크립트 (대규모):
   python pipeline/useful/annotate_figures.py --slug [slug]
   python pipeline/useful/annotate_figures.py --all --dry-run
   python pipeline/useful/annotate_figures.py --all

4. 출처 표기 추가:
   python pipeline/useful/add_figure_attribution.py --papers --dry-run
   python pipeline/useful/add_figure_attribution.py --all

5. import --update로 DB 반영
