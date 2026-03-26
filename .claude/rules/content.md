---
paths:
  - "pipeline/data/**/*.md"
  - "pipeline/data/**/*.json"
---
# 컨텐츠 작성 규칙

## 포스트 타입별 요구사항

### paper_review
- 구조: 개요 → 배경 → 핵심 아이디어 → 방법론 → 실험 → 한계 → 결론
- content.json 필수: slug, title, title_ko, tags, category_slug, summary, arxiv_url, venue, paper_year, paper_authors
- Figure: 핵심 3~5개 선별 (아키텍처, 실험 결과, 핵심 개념도)
- 최소 2500단어

### tutorial
- 구조: 소개 → 개념 설명 → 단계별 구현 → 결과 → 정리
- content.json 필수: slug, title, title_ko, tags, category_slug, summary
- 코드 블록 + 실행 결과 포함
- 최소 2000단어

### article
- 구조: 자유 (주제에 맞게)
- content.json 필수: slug, title, title_ko, tags, category_slug, summary
- 최소 1500단어

## Figure 형식 표준
```markdown
![한국어 alt text](figures/filename.png)

*Figure N: 한국어 캡션. (Author, Year)*
```

## MarkdownRenderer 지원 기능
- Callout: `:::info`, `:::warning`, `:::tip`, `:::danger`
- KaTeX 수식: `$inline$`, `$$block$$`
- Wiki-link: `[[slug]]` → 내부 포스트 링크
- 코드 블록: syntax highlighting + 복사 버튼
- Output 블록: ` ```output ` (실행 결과 표시)
- BookmarkEmbed: URL을 카드형 임베드로 변환
- Figure zoom: 이미지 클릭 시 확대
- **Mermaid 사용 지양** — 텍스트 설명 또는 figure 이미지 사용

## 품질 기준
- 분야/카테고리별로 품질 기준이 다름
- 각 컨텐츠 작성 시 사용자 피드백 필수
- 초안 → 피드백 → 수정 → 승인 사이클
