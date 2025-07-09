.PHONY: help install run test lint format migrate docker-up docker-down clean init-db seed-db test-rls

help:
	@echo "Available commands:"
	@echo "  make install     - Install dependencies"
	@echo "  make run         - Run the development server"
	@echo "  make test        - Run tests"
	@echo "  make lint        - Run linting"
	@echo "  make format      - Format code"
	@echo "  make migrate     - Run database migrations"
	@echo "  make init-db     - Initialize database with RLS and seed data"
	@echo "  make seed-db     - Seed database with enhanced data"
	@echo "  make test-rls    - Test Row Level Security"
	@echo "  make docker-up   - Start Docker containers"
	@echo "  make docker-down - Stop Docker containers"
	@echo "  make clean       - Clean up generated files"

install:
	pip install -r requirements.txt

run:
	python main.py

test:
	pytest

test-cov:
	pytest --cov=. --cov-report=html --cov-report=term

lint:
	flake8 .
	mypy .

format:
	black .
	isort .

migrate:
	alembic upgrade head

migration:
	@read -p "Enter migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

init-db:
	@echo "Initializing database with RLS and seed data..."
	python scripts/init_database_with_rls.py

seed-db:
	@echo "Seeding database with enhanced data..."
	python scripts/seed_data_enhanced.py

test-rls:
	@echo "Testing Row Level Security..."
	python scripts/test_rls.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +