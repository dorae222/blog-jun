# blog-jun

Personal tech blog: Django 5 + DRF backend, React 19 + Vite + Tailwind CSS frontend.

## Project Structure
- `backend/` - Django DRF API (config/settings split: base/dev/prod)
- `frontend/` - React SPA with Framer Motion animations
- `pipeline/` - Data processing: scanner → preprocessor → batch API → import
- `lxd/` - LXD container provisioning scripts
- `.github/workflows/` - CI (PR checks) + CD (main → Docker → deploy)

## Commands
- `make dev` - Start dev environment (docker compose)
- `make migrate` - Run Django migrations
- `make seed` - Seed post templates
- `make createsuperuser` - Create admin user

## Architecture
- Backend: Django 5 + DRF + Gunicorn + PostgreSQL (pgvector) + Redis
- Frontend: React 19 + Vite + Tailwind CSS v4 + Framer Motion
- Auth: JWT (simplejwt)
- Chatbot: RAG (pgvector + OpenAI SSE streaming)
- Deploy: Docker Compose + Cloudflare Tunnel

## Key Files
- Models: `backend/blog/models.py` (Post, Category, Tag, Series, PostTemplate)
- API: `backend/blog/views.py`, `backend/blog/urls.py`
- Chatbot RAG: `backend/chatbot/views.py`
- Frontend entry: `frontend/src/App.jsx`
- Effects: `frontend/src/components/effects/` (ParticleBackground, TiltCard, GradientCursor)

## Deployment
- Live: https://blog.dorae222.com
- Infra: LXD container `blog-server` (10.10.10.30) on hj-remote
- Tunnel: Cloudflare Tunnel `blog-jun` (079ef309)
- Docker: docker-compose.prod.yml (db, redis, backend, frontend)
- CI/CD: GitHub Actions → Docker Hub → SSH deploy (ProxyJump)

## Git Sync
| Location | Path | Purpose |
|----------|------|---------|
| MacBook | ~/Documents/Obsidian/blog-jun/ | Development + Pipeline |
| hj-remote | ~/lxd-servers/blog-jun/ | Infra management |
| blog-server | /opt/blog-jun/ | Production |
