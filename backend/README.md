# IDKit Backend API

FastAPI-based backend for the IDKit AI-powered creator platform.

## Features

- User authentication and authorization (JWT)
- Social media integration
- AI content generation
- Creator analytics
- Monetization tools

## Quick Start

```bash
# Install dependencies
pip install -e .

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Environment Variables

See `.env.example` for required configuration.

## API Documentation

- Swagger UI: `/docs`
- ReDoc: `/redoc`
