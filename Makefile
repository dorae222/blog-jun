.PHONY: dev up down migrate seed shell deploy cover import-cloud reclassify lint

# === Development ===
dev:
	docker compose up --build

up:
	docker compose up -d

down:
	docker compose down

migrate:
	docker compose exec backend python manage.py migrate

seed:
	docker compose exec backend python manage.py seed_templates

shell:
	docker compose exec backend python manage.py shell

createsuperuser:
	docker compose exec backend python manage.py createsuperuser

# === Production ===
prod-up:
	docker compose -f docker-compose.prod.yml up -d

prod-down:
	docker compose -f docker-compose.prod.yml down

prod-migrate:
	docker compose -f docker-compose.prod.yml exec backend python manage.py migrate

prod-logs:
	docker compose -f docker-compose.prod.yml logs -f

deploy:
	./deploy.sh

# === Content Management ===
cover:
	docker compose -f docker-compose.prod.yml run --rm backend \
	  python manage.py generate_cover_images

import-cloud:
	docker compose -f docker-compose.prod.yml run --rm backend \
	  python manage.py import_cloud_content

reclassify:
	docker compose -f docker-compose.prod.yml run --rm backend \
	  python manage.py reclassify_cloud_posts

seed-categories:
	docker compose -f docker-compose.prod.yml run --rm backend \
	  python manage.py seed_cloud_categories && \
	docker compose -f docker-compose.prod.yml run --rm backend \
	  python manage.py seed_ai_categories && \
	docker compose -f docker-compose.prod.yml run --rm backend \
	  python manage.py seed_ml_categories

# === Quality ===
lint:
	cd backend && python -m py_compile blog/views.py blog/models.py blog/serializers.py
	cd frontend && npx eslint src/ --max-warnings 0
