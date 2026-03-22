---
paths:
  - "backend/**/*.py"
---
# Django Backend Rules

- Django 5 + DRF 사용, Python 3.12
- 설정: config/settings/{base,dev,prod}.py 분리
- 모델 변경 시 makemigrations 실행 필수
- Serializer에서 검증, View는 얇게 유지
- QuerySet 사용 시 N+1 쿼리 주의 (select_related/prefetch_related)
- 민감 정보는 환경변수로 (django-environ)
- Post.objects는 PostManager (published(), with_cover(), by_category())
- ImageUrlMixin으로 URL 빌딩 공통화
- operations 앱의 OperationLog로 중요 작업 기록
