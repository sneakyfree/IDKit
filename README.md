# IDKit - AI-Powered Influencer Development Kit

IDKit is a comprehensive AI-powered platform for influencers to automate marketing, brand building, and content creation. Designed with **TikTok-level simplicity** - a content creator + social feed scroll experience that makes powerful AI accessible to everyone.

## Core Features

- **AI Twin/Clone Lab** - Generate realistic digital avatars with cloned voices
- **Content Generation** - AI-powered scripts, posts, and multimedia content
- **Podcast Creation Lab** - End-to-end podcast production with AI hosts
- **IDKit Social Community** - Internal social network for influencers
- **Multi-Platform Publishing** - Unified publishing to YouTube, Instagram, TikTok, Twitter, Facebook, LinkedIn

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy, Celery |
| Frontend | Next.js 14+, React, TypeScript |
| Mobile | React Native, Expo |
| Database | PostgreSQL, Redis, Elasticsearch |
| AI/ML | OpenAI, LangChain, HuggingFace |
| Infrastructure | Docker, Kubernetes, Prometheus |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/idkit.git
   cd idkit
   ```

2. **Start infrastructure services**
   ```bash
   docker-compose up -d postgres redis
   ```

3. **Set up the backend**
   ```bash
   cd backend

   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install dependencies
   pip install -e ".[dev]"

   # Copy environment file
   cp .env.example .env
   # Edit .env with your configuration

   # Run database migrations
   alembic upgrade head

   # Start the API server
   uvicorn app.main:app --reload
   ```

4. **Set up the frontend**
   ```bash
   cd frontend

   # Install dependencies
   npm install

   # Copy environment file
   cp .env.example .env.local

   # Start development server
   npm run dev
   ```

5. **Access the application**
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Frontend: http://localhost:3000

### Docker Development

For a fully containerized development environment:

```bash
# Start all services
docker-compose up -d

# With GPU workers (requires NVIDIA Docker)
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up -d
```

## Project Structure

```
idkit/
├── backend/                 # Python FastAPI Backend
│   ├── app/
│   │   ├── api/v1/         # REST API endpoints
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── services/       # Business logic
│   │   ├── adapters/       # Social platform adapters
│   │   ├── middleware/     # HTTP middleware
│   │   ├── workers/        # Celery background tasks
│   │   └── ml/             # ML model registry
│   ├── tests/              # Pytest test suite
│   └── alembic/            # Database migrations
├── frontend/               # Next.js Web Application
│   ├── src/
│   │   ├── app/            # App router pages
│   │   ├── components/     # React components
│   │   └── lib/            # Utilities & API client
├── mobile/                 # React Native Mobile App
├── gpu-workers/            # GPU Worker Docker Images
├── infrastructure/         # Kubernetes & Terraform configs
│   └── kubernetes/         # K8s manifests
└── .github/                # GitHub Actions workflows
```

## API Documentation

When running in development mode, interactive API documentation is available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check |
| `GET /metrics` | Prometheus metrics |
| `POST /api/v1/auth/login` | User authentication |
| `GET /api/v1/feed` | Personalized feed |
| `POST /api/v1/content/generate` | AI content generation |
| `POST /api/v1/twins` | Create AI twin |
| `GET /api/v1/social/accounts` | Connected social accounts |

## Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
# Application
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/idkit

# Redis
REDIS_URL=redis://localhost:6379

# JWT
JWT_SECRET_KEY=your-jwt-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# AI Providers
OPENAI_API_KEY=sk-...

# Storage
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
S3_BUCKET_NAME=idkit-media

# Social Platform OAuth (optional)
YOUTUBE_CLIENT_ID=...
YOUTUBE_CLIENT_SECRET=...
INSTAGRAM_APP_ID=...
INSTAGRAM_APP_SECRET=...
TIKTOK_CLIENT_KEY=...
TIKTOK_CLIENT_SECRET=...
```

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/api/test_health.py -v

# Run tests matching pattern
pytest -k "test_health" -v
```

### Frontend Tests

```bash
cd frontend
npm test
```

## Development

### Code Quality

The project uses several tools to maintain code quality:

**Backend:**
- `ruff` - Linting and formatting
- `mypy` - Type checking
- `pytest` - Testing

```bash
# Lint
ruff check app/

# Format
ruff format app/

# Type check
mypy app/
```

**Frontend:**
- `eslint` - Linting
- `prettier` - Formatting
- `typescript` - Type checking

```bash
npm run lint
npm run format
```

### Database Migrations

```bash
cd backend

# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

### Background Workers

Start Celery workers for background task processing:

```bash
cd backend

# Start worker
celery -A app.workers.celery_app worker --loglevel=info

# Start beat scheduler (for periodic tasks)
celery -A app.workers.celery_app beat --loglevel=info
```

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

### Prometheus Metrics

Metrics are exposed at `/metrics` in Prometheus format:

- HTTP request counts and latencies
- Database connection pool stats
- Redis connection stats
- GPU job queue metrics
- Business metrics

### Kubernetes Monitoring

The project includes pre-configured:
- Prometheus ServiceMonitor
- PrometheusRule alerts
- Grafana dashboards

## Deployment

### Kubernetes

```bash
cd infrastructure/kubernetes

# Apply all manifests
kubectl apply -f .

# Or use kustomize
kubectl apply -k .
```

### Docker Images

```bash
# Build backend
docker build -t idkit-api:latest ./backend

# Build frontend
docker build -t idkit-frontend:latest ./frontend
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Commit Convention

We use conventional commits:

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `chore:` Maintenance tasks
- `test:` Test additions/changes
- `refactor:` Code refactoring

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- [GitHub Issues](https://github.com/your-org/idkit/issues) - Bug reports and feature requests
- [Documentation](https://docs.idkit.io) - Full documentation (coming soon)
