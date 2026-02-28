#!/bin/bash
# DB 백업 스크립트 — pg_dump + gzip, 30일 보존
set -euo pipefail

BACKUP_DIR="/opt/blog-jun/backups"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/blog_jun_${TIMESTAMP}.sql.gz"

mkdir -p "${BACKUP_DIR}"

# Docker Compose 환경에서 실행
docker compose -f /opt/blog-jun/docker-compose.prod.yml exec -T db \
    pg_dump -U "${DB_USER:-blog_user}" "${DB_NAME:-blog_jun}" \
    | gzip > "${BACKUP_FILE}"

# 백업 파일 크기 확인
SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
echo "[$(date)] Backup created: ${BACKUP_FILE} (${SIZE})"

# 오래된 백업 정리
DELETED=$(find "${BACKUP_DIR}" -name "*.sql.gz" -mtime +${RETENTION_DAYS} -delete -print | wc -l)
if [ "${DELETED}" -gt 0 ]; then
    echo "[$(date)] Cleaned up ${DELETED} backup(s) older than ${RETENTION_DAYS} days"
fi
