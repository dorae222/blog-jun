---
paths:
  - "pipeline/**/*.py"
---
# Pipeline Rules

- pipeline/utils/의 공통 유틸리티 활용 (batch_client, post_factory, image_utils)
- SVG 생성 시 viewBox="0 0 1792 1024" (16:9)
- 한글 폰트 스택: FONT_TITLE, FONT_BODY, FONT_MONO (cover_templates.py)
- cairosvg 사용 시 시스템 폰트 의존 — Docker에서 fontconfig 설정 필요
- Batch API는 utils/batch_client.py의 BatchAPIClient 사용
