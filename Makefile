.PHONY: dev up down migrate seed shell

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

prod-up:
	docker compose -f docker-compose.prod.yml up -d

prod-down:
	docker compose -f docker-compose.prod.yml down

prod-migrate:
	docker compose -f docker-compose.prod.yml exec backend python manage.py migrate

prod-logs:
	docker compose -f docker-compose.prod.yml logs -f
