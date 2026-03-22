---
name: cover-gen
description: 커버 이미지 생성/재생성 (로컬 또는 서버)
allowed-tools: Bash(python *), Bash(ssh *), Read, Glob
---
커버 이미지를 생성합니다.

로컬 실행:
  python manage.py generate_cover_images [--category CAT] [--strategy paper_cover|category_gradient] [--force] [--dry-run] [--slug SLUG]

서버 실행:
  ssh -J hj-remote blog-server 'cd /opt/blog-jun && docker compose -f docker-compose.prod.yml run --rm backend python manage.py generate_cover_images [옵션]'

먼저 --dry-run으로 대상을 확인한 후 실행하세요.
