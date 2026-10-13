.PHONY: up down logs migrate revision delete

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	docker compose run --rm migrate

revision:
	@test -n "$(MESSAGE)" || (echo 'Usage: make revision MESSAGE="description"' >&2; exit 1)
	docker compose run --rm --volume "$(CURDIR)/migrations:/app/migrations" migrate alembic revision --autogenerate -m "$(MESSAGE)"

delete:
	docker compose down -v
