#!/usr/bin/env bash
# 수동 배포 스크립트
# 사용법: ./deploy.sh
#
# 사전 조건:
#   - Docker Hub 로그인: docker login
#   - SSH 설정: ~/.ssh/config에 hj-remote / blog-server 등록

set -euo pipefail

DOCKER_USER="dorae222"
BACKEND_IMAGE="${DOCKER_USER}/blog-backend"
FRONTEND_IMAGE="${DOCKER_USER}/blog-frontend"
JUMP_HOST="hj-remote"
REMOTE_HOST="blog-server"
REMOTE_DIR="/opt/blog-jun"
COMPOSE_FILE="docker-compose.prod.yml"

echo "▶ 1/4  Docker 이미지 빌드"
docker build -t "${BACKEND_IMAGE}:latest"  ./backend
docker build -t "${FRONTEND_IMAGE}:latest" ./frontend

echo "▶ 2/4  Docker Hub push"
docker push "${BACKEND_IMAGE}:latest"
docker push "${FRONTEND_IMAGE}:latest"

echo "▶ 3/4  서버 배포 (ProxyJump: ${JUMP_HOST} → ${REMOTE_HOST})"
ssh -J "${JUMP_HOST}" "${REMOTE_HOST}" bash <<REMOTE
set -euo pipefail
cd ${REMOTE_DIR}

echo "  이미지 pull..."
docker compose -f ${COMPOSE_FILE} pull

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

echo "  헬스체크..."
for i in \$(seq 1 10); do
  if curl -sf http://localhost/api/health/ > /dev/null 2>&1; then
    echo "  ✓ 헬스체크 통과 (시도 \$i)"
    break
  fi
  echo "  헬스체크 실패 \$i/10, 재시도..."
  sleep 5
done

curl -sf http://localhost/api/health/ || echo "WARNING: 헬스체크 최종 실패"

echo "  이미지 정리..."
docker image prune -f
REMOTE

echo "▶ 4/4  렌더링 검증"
sleep 3
if curl -sf https://blog.dorae222.com/api/health/ > /dev/null; then
  echo "✓ 배포 완료 — https://blog.dorae222.com"
else
  echo "✗ 사이트 응답 없음, 로그 확인: make prod-logs"
  exit 1
fi
