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
