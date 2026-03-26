---
name: deploy
description: blog-server 프로덕션 배포 (git push → SSH → docker compose build)
allowed-tools: Bash(git *), Bash(./deploy.sh), Bash(ssh *), Bash(curl *)
---
1. git status로 uncommitted 변경 확인 → 있으면 경고
2. git push origin main
3. Git LFS push: `git lfs push origin main --all` (pipeline/data/ PNG/SVG/PDF용)
4. ./deploy.sh 실행 (SSH ProxyJump: hj-remote → blog-server)
5. 배포 후 헬스체크: curl -s https://blog.dorae222.com/api/health/
6. 실패 시 docker compose logs 확인
