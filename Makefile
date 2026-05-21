.PHONY: up down build logs api chat worker portal widget shell-api shell-worker migrate

up:
	docker compose up -d --build

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f --tail=200

api:
	docker compose up -d api

chat:
	docker compose up -d chat-server

worker:
	docker compose up -d worker

portal:
	docker compose up -d portal

widget:
	docker compose up -d widget

shell-api:
	docker compose exec api /usr/local/bin/docker-entrypoint.sh shell

shell-worker:
	docker compose exec worker /usr/local/bin/docker-entrypoint.sh shell

migrate:
	docker compose exec api alembic upgrade head
