include .env
export

SRC_DIR := src

migration:
	alembic revision --autogenerate

migrate:
	alembic upgrade head

test:
	python -m pytest tests

.PHONY: migration migrate test
