---
name: quality-check
description: 포스트 품질 검사 + 개선 제안
allowed-tools: Bash(python *), Read, Grep, Glob
---
1. python manage.py review_post_quality [--category CAT] 실행
2. quality_score < 5.0 포스트 목록 출력
3. 커버 이미지 없는 포스트 목록 출력
4. 각 저품질 포스트에 대한 개선 방향 제안
