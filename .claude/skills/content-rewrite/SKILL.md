---
name: content-rewrite
description: 컨텐츠 품질 개선 — Claude Code 직접 편집
allowed-tools: Bash(python *), Read, Edit, Write, Grep, Glob
---
컨텐츠 품질 개선 워크플로우 (Claude Code 직접 작성):

1. 대상 선별:
   - `blog-jun-content.json`의 `improvement_plan.priority` 참조
   - 또는 `python manage.py review_post_quality`로 품질 검사

2. 현재 컨텐츠 확인:
   - `pipeline/data/{type}_written/{slug}/content.md` 읽기
   - `pipeline/data/{type}_written/{slug}/figures/` 확인 (멀티모달)

3. content.md 직접 편집:
   - Claude Code가 Read → 분석 → Edit/Write로 개선
   - Figure 삽입: `![한국어 alt](figures/file.png)` + `*Figure N: 캡션. (Author, Year)*`
   - 품질 기준은 분야/카테고리별로 다름 — 사용자 피드백 필수

4. 메타데이터 업데이트 (필요 시):
   - `content.json`의 tags, summary, category_slug 수정

5. DB 반영:
   - `python pipeline/import_{type}_written.py --update`
   - 서버 반영: deploy 스킬 사용
