---
name: content-rewrite
description: Batch API 기반 컨텐츠 재작성 (품질 개선)
allowed-tools: Bash(python *), Read
---
Batch API 기반 컨텐츠 재작성:

1. 대상 선별 (quality-check 결과 활용):
   python manage.py review_post_quality

2. 재작성 준비:
   python pipeline/batch_rewrite.py --slugs slug1,slug2 --prepare

3. Batch API 실행:
   python pipeline/batch_rewrite.py --process

4. 결과 확인:
   python pipeline/batch_rewrite.py --review

5. 승인 후 import:
   python pipeline/batch_rewrite_import.py

개선 포인트:
- papers_written (57개): architecture figure 삽입, arXiv 링크 인라인, 실험 결과 표 표준화
- ml_written (51개): figure 캡션 개선, 의존성 명시, HuggingFace 예제 추가
- architectures_written (192개): inline figure + 논문 링크, 모델 스펙 카드 통일
