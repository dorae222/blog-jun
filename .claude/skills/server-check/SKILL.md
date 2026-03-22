---
name: server-check
description: blog-server 상태 점검 (Docker, 디스크, 서비스)
allowed-tools: Bash(ssh *), Bash(curl *)
---
blog-server 종합 상태 점검:

1. 서비스 상태: ssh -J hj-remote blog-server 'docker compose -f /opt/blog-jun/docker-compose.prod.yml ps'
2. 디스크: ssh -J hj-remote blog-server 'df -h /'
3. 컨테이너 로그: ssh -J hj-remote blog-server 'docker compose -f /opt/blog-jun/docker-compose.prod.yml logs --tail=20 backend'
4. 헬스체크: curl -s https://blog.dorae222.com/api/health/
5. 미디어 파일 수: ssh -J hj-remote blog-server 'find /opt/blog-jun/media/covers/ -name "*.png" | wc -l'
