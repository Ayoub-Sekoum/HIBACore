# Task 10.08: Makefile for dev stack
.PHONY: dev-up dev-down test lint

dev-up:
	docker-compose up --build -d

dev-down:
	docker-compose down

test:
	cd backend && pytest

lint:
	cd backend && ruff check .
