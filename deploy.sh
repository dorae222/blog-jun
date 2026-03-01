#!/usr/bin/env bash
# 수동 배포 스크립트 — 서버에서 직접 빌드
# 사용법: ./deploy.sh
#
# 사전 조건:
#   - ~/.ssh/config에 hj-remote / blog-server 등록
#   - 서버 /opt/blog-jun에 git remote 연결

set -euo pipefail

JUMP_HOST="hj-remote"
REMOTE_HOST="blog-server"
REMOTE_DIR="/opt/blog-jun"
COMPOSE_FILE="docker-compose.prod.yml"

echo "▶ 1/3  서버에서 코드 pull + 이미지 빌드"
ssh -J "${JUMP_HOST}" "${REMOTE_HOST}" bash <<REMOTE
set -euo pipefail
cd ${REMOTE_DIR}

echo "  git pull..."
git pull origin main

echo "  이미지 빌드..."
docker compose -f ${COMPOSE_FILE} build --no-cache

echo "  DB / Redis 기동..."
docker compose -f ${COMPOSE_FILE} up -d db redis

echo "  DB 준비 대기..."
for i in \$(seq 1 30); do
  docker compose -f ${COMPOSE_FILE} exec -T db pg_isready -U \${DB_USER:-blog_user} && break
  sleep 2
done

echo "  마이그레이션..."
docker compose -f ${COMPOSE_FILE} run --rm backend python manage.py migrate --noinput

echo "  전체 서비스 재시작..."
docker compose -f ${COMPOSE_FILE} up -d

echo "  이미지 정리..."
docker image prune -f
REMOTE

echo "▶ 2/3  헬스체크 대기..."
for i in $(seq 1 12); do
  if curl -sf https://blog.dorae222.com/api/health/ > /dev/null 2>&1; then
    echo "  ✓ 헬스체크 통과 (시도 $i)"
    break
  fi
  echo "  헬스체크 실패 $i/12, 재시도..."
  sleep 5
done

echo "▶ 3/3  렌더링 검증"
if curl -sf https://blog.dorae222.com/api/health/ > /dev/null; then
  echo "✓ 배포 완료 — https://blog.dorae222.com"
else
  echo "✗ 사이트 응답 없음, 로그 확인:"
  echo "  ssh -J ${JUMP_HOST} ${REMOTE_HOST} 'cd ${REMOTE_DIR} && docker compose -f ${COMPOSE_FILE} logs --tail=50'"
  exit 1
fi
