---
name: db-query
description: Django ORM으로 블로그 데이터 조회
allowed-tools: Bash(python *), Bash(ssh *)
---
Django shell을 통해 데이터를 조회합니다.

로컬: cd backend && python manage.py shell -c "QUERY"
서버: ssh -J hj-remote blog-server 'cd /opt/blog-jun && docker compose -f docker-compose.prod.yml run --rm backend python manage.py shell -c "QUERY"'

자주 쓰는 쿼리:
- 카테고리별 포스트 수: Post.objects.values('category__name').annotate(count=Count('id'))
- 커버 없는 포스트: Post.objects.without_cover().count()
- 최근 포스트: Post.objects.order_by('-created_at')[:10].values('title', 'category__name', 'status')
- Published 포스트: Post.objects.published().count()
