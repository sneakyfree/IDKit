# IDKit Makefile
# Common commands for development and deployment

.PHONY: help install dev dev-tools dev-gpu build test lint format clean deploy

# Default target
help:
	@echo "IDKit Development Commands"
	@echo ""
	@echo "Development:"
	@echo "  make install      - Install all dependencies"
	@echo "  make dev          - Start development environment"
	@echo "  make dev-tools    - Start development with extra tools (pgAdmin, Redis Commander)"
	@echo "  make dev-gpu      - Start development with GPU workers"
	@echo "  make down         - Stop all containers"
	@echo "  make logs         - View container logs"
	@echo "  make shell        - Open shell in API container"
	@echo ""
	@echo "Database:"
	@echo "  make db-migrate   - Run database migrations"
	@echo "  make db-upgrade   - Apply pending migrations"
	@echo "  make db-downgrade - Rollback last migration"
	@echo "  make db-reset     - Reset database (WARNING: deletes all data)"
	@echo ""
	@echo "Testing:"
	@echo "  make test         - Run all tests"
	@echo "  make test-unit    - Run unit tests"
	@echo "  make test-int     - Run integration tests"
	@echo "  make test-cov     - Run tests with coverage"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"
	@echo "  make typecheck    - Run type checking"
	@echo ""
	@echo "Build & Deploy:"
	@echo "  make build        - Build Docker images"
	@echo "  make push         - Push images to registry"
	@echo "  make deploy       - Deploy to Kubernetes"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean        - Remove build artifacts"
	@echo "  make clean-docker - Remove Docker containers and volumes"

# =============================================================================
# Development
# =============================================================================

install:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Installing GPU worker dependencies..."
	cd gpu-workers && pip install -r requirements.base.txt

dev:
	docker-compose up -d
	@echo ""
	@echo "IDKit is running!"
	@echo "  API:      http://localhost:8000"
	@echo "  Frontend: http://localhost:3000"
	@echo "  MinIO:    http://localhost:9001"
	@echo ""

dev-tools:
	docker-compose --profile dev-tools up -d
	@echo ""
	@echo "IDKit is running with dev tools!"
	@echo "  API:             http://localhost:8000"
	@echo "  Frontend:        http://localhost:3000"
	@echo "  MinIO:           http://localhost:9001"
	@echo "  pgAdmin:         http://localhost:5050"
	@echo "  Redis Commander: http://localhost:8081"
	@echo "  Flower:          http://localhost:5555"
	@echo "  Mailhog:         http://localhost:8025"
	@echo ""

dev-gpu:
	docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up -d
	@echo ""
	@echo "IDKit is running with GPU workers!"
	@echo ""

down:
	docker-compose --profile dev-tools down

logs:
	docker-compose logs -f

logs-api:
	docker-compose logs -f api

logs-worker:
	docker-compose logs -f celery-worker

shell:
	docker-compose exec api bash

shell-db:
	docker-compose exec postgres psql -U idkit -d idkit

# =============================================================================
# Database
# =============================================================================

db-migrate:
	docker-compose exec api alembic revision --autogenerate -m "$(msg)"

db-upgrade:
	docker-compose exec api alembic upgrade head

db-downgrade:
	docker-compose exec api alembic downgrade -1

db-reset:
	@echo "WARNING: This will delete all data!"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ]
	docker-compose down -v
	docker-compose up -d postgres redis minio minio-init
	sleep 5
	docker-compose up -d api
	docker-compose exec api alembic upgrade head

# =============================================================================
# Testing
# =============================================================================

test:
	docker-compose exec api pytest tests/ -v

test-unit:
	docker-compose exec api pytest tests/unit/ -v

test-int:
	docker-compose exec api pytest tests/integration/ -v

test-cov:
	docker-compose exec api pytest tests/ -v --cov=app --cov-report=html

# =============================================================================
# Code Quality
# =============================================================================

lint:
	@echo "Linting backend..."
	cd backend && ruff check .
	@echo "Linting frontend..."
	cd frontend && npm run lint

format:
	@echo "Formatting backend..."
	cd backend && ruff format .
	cd backend && ruff check --fix .
	@echo "Formatting frontend..."
	cd frontend && npm run format

typecheck:
	@echo "Type checking backend..."
	cd backend && mypy app/
	@echo "Type checking frontend..."
	cd frontend && npm run typecheck

# =============================================================================
# Build & Deploy
# =============================================================================

VERSION ?= latest
REGISTRY ?= idkit

build:
	@echo "Building API image..."
	docker build -t $(REGISTRY)/api:$(VERSION) ./backend
	@echo "Building Frontend image..."
	docker build -t $(REGISTRY)/frontend:$(VERSION) ./frontend
	@echo "Building GPU worker images..."
	docker build -t $(REGISTRY)/gpu-worker-avatar:$(VERSION) -f gpu-workers/Dockerfile.avatar ./gpu-workers
	docker build -t $(REGISTRY)/gpu-worker-voice:$(VERSION) -f gpu-workers/Dockerfile.voice ./gpu-workers
	docker build -t $(REGISTRY)/gpu-worker-llm:$(VERSION) -f gpu-workers/Dockerfile.llm ./gpu-workers

push:
	docker push $(REGISTRY)/api:$(VERSION)
	docker push $(REGISTRY)/frontend:$(VERSION)
	docker push $(REGISTRY)/gpu-worker-avatar:$(VERSION)
	docker push $(REGISTRY)/gpu-worker-voice:$(VERSION)
	docker push $(REGISTRY)/gpu-worker-llm:$(VERSION)

deploy:
	kubectl apply -k infrastructure/kubernetes/

deploy-staging:
	kubectl apply -k infrastructure/kubernetes/overlays/staging/

deploy-prod:
	kubectl apply -k infrastructure/kubernetes/overlays/production/

# =============================================================================
# Cleanup
# =============================================================================

clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .next -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

clean-docker:
	docker-compose --profile dev-tools down -v --rmi local
	docker system prune -f
