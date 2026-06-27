include .env
export

SRC_DIR := src

migration:
	alembic revision --autogenerate

migrate:
	alembic upgrade head

test:
	PYTHONPATH=src uv run -m pytest tests

.PHONY: migration migrate test
