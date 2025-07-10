.PHONY: help install setup dev prod test clean docker-up docker-down migrate

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make setup      - Setup development environment"
	@echo "  make dev        - Run in development mode"
	@echo "  make prod       - Run in production mode"
	@echo "  make test       - Run tests"
	@echo "  make clean      - Clean up temporary files"
	@echo "  make docker-up  - Start Docker services"
	@echo "  make docker-down - Stop Docker services"
	@echo "  make migrate    - Run database migrations"

install:
	cd backend && python3 -m venv venv
	cd backend && ./venv/bin/pip install --upgrade pip
	cd backend && ./venv/bin/pip install -r requirements.txt
	cd backend && ./venv/bin/pip install -r requirements-dev.txt
	cd frontend && npm install

setup: install
	cp .env.example .env
	@echo "Environment setup complete. Edit .env file with your configuration."

dev:
	cd backend && ./run.sh

prod:
	cd backend && ENVIRONMENT=production ./run.sh

test:
	cd backend && ./venv/bin/pytest tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

migrate:
	cd backend && ./venv/bin/alembic upgrade head