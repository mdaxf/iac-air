# Docker Deployment Guide

This guide explains how to deploy the AI Data Analytics Platform v1.0 using Docker and Docker Compose.

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- At least 4GB RAM available for containers
- OpenAI or Anthropic API key

## Quick Start (Development)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd air
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

3. **Start the services**
   ```bash
   docker-compose up -d
   ```

4. **Initialize the database**
   ```bash
   docker exec -it air_backend python scripts/init_db_v1.py
   ```

5. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Production Deployment

1. **Configure production environment**
   ```bash
   cp .env.example .env
   # Edit .env with production values
   # IMPORTANT: Generate secure SECRET_KEY using:
   # openssl rand -hex 32
   ```

2. **Build and start production services**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Initialize the database**
   ```bash
   docker exec -it air_backend python scripts/init_db_v1.py
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

## Environment Variables

### Required Variables

```env
# Database
POSTGRES_PASSWORD=your_secure_password

# LLM API Keys (at least one)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Security
SECRET_KEY=<generate-using-openssl-rand-hex-32>
```

### Optional Variables

```env
# Ports
POSTGRES_PORT=5432
BACKEND_PORT=8000
FRONTEND_PORT=5173  # dev or 3000 for prod

# Environment
ENVIRONMENT=development  # or production
```

## Docker Compose Files

### docker-compose.yml (Development)
- Hot-reload enabled for both frontend and backend
- Volume mounts for local development
- Vite dev server on port 5173
- Single worker backend process

### docker-compose.prod.yml (Production)
- Optimized production builds
- Multi-stage Docker builds
- 4 backend workers for better performance
- Static file serving for frontend
- No volume mounts (built into image)

## Services

### PostgreSQL (pgvector/pgvector:pg16)
- PostgreSQL 16 with pgvector extension
- Data persistence via Docker volume
- Health checks enabled
- Default port: 5432

### Backend (Python 3.11)
- FastAPI application
- Async SQLAlchemy 2.0
- Uvicorn ASGI server
- Health endpoint: `/health`
- API docs: `/docs`

### Frontend (Node 20)
- React + Vite application
- Development: Vite dev server
- Production: Optimized static build served with `serve`

## Container Management

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### Restart services
```bash
# All services
docker-compose restart

# Specific service
docker-compose restart backend
```

### Stop services
```bash
# Stop and remove containers
docker-compose down

# Stop, remove containers and volumes (WARNING: deletes data!)
docker-compose down -v
```

### Execute commands in containers
```bash
# Backend shell
docker exec -it air_backend bash

# Run database migrations
docker exec -it air_backend alembic upgrade head

# PostgreSQL shell
docker exec -it air_postgres psql -U postgres -d air_analytics
```

## Health Checks

All services have health checks configured:

- **PostgreSQL**: `pg_isready` every 10s
- **Backend**: HTTP GET `/health` every 30s
- **Frontend**: HTTP GET `/` every 30s (production only)

View health status:
```bash
docker-compose ps
```

## Volume Management

### Persistent Volumes

- `postgres_data`: PostgreSQL database files
- `backend_logs`: Application logs

### Backup Database

```bash
# Create backup
docker exec air_postgres pg_dump -U postgres air_analytics > backup.sql

# Restore backup
docker exec -i air_postgres psql -U postgres air_analytics < backup.sql
```

### Clear Volumes

```bash
# WARNING: This deletes all data!
docker-compose down -v
```

## Troubleshooting

### Container won't start

Check logs:
```bash
docker-compose logs <service-name>
```

### Database connection errors

1. Check PostgreSQL is healthy:
   ```bash
   docker-compose ps postgres
   ```

2. Verify environment variables:
   ```bash
   docker exec air_backend env | grep POSTGRES
   ```

### Frontend can't connect to backend

1. Check backend is healthy:
   ```bash
   curl http://localhost:8000/health
   ```

2. Verify VITE_API_URL in frontend container:
   ```bash
   docker exec air_frontend env | grep VITE
   ```

### Permission errors

Reset permissions:
```bash
docker-compose down
sudo chown -R $USER:$USER .
docker-compose up -d
```

### Port conflicts

Change ports in `.env`:
```env
POSTGRES_PORT=5433
BACKEND_PORT=8001
FRONTEND_PORT=5174
```

## Performance Tuning

### Production Backend

Adjust worker count in `docker-compose.prod.yml`:
```yaml
command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Recommended: `workers = (2 × CPU cores) + 1`

### Database Connection Pool

Edit `backend/app/core/database.py`:
```python
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,        # Adjust based on load
    max_overflow=10,     # Additional connections
    pool_pre_ping=True
)
```

## Security Considerations

1. **Change default passwords** in production
2. **Generate secure SECRET_KEY**: `openssl rand -hex 32`
3. **Use environment-specific .env files**
4. **Don't commit .env files** to version control
5. **Use Docker secrets** for sensitive data in production
6. **Enable HTTPS** with reverse proxy (nginx/traefik)
7. **Restrict PostgreSQL port** to internal network only

## Monitoring

### Resource Usage

```bash
# Real-time stats
docker stats

# Specific container
docker stats air_backend
```

### Application Logs

Logs are stored in Docker volume `backend_logs`:
```bash
docker exec air_backend ls -la /app/logs
docker exec air_backend cat /app/logs/debug.log
```

## Updates and Maintenance

### Rebuild after code changes

```bash
# Development
docker-compose up -d --build

# Production
docker-compose -f docker-compose.prod.yml up -d --build
```

### Update base images

```bash
docker-compose pull
docker-compose up -d
```

## Next Steps

After deployment:

1. Access the frontend at http://localhost:5173 (dev) or http://localhost:3000 (prod)
2. Create database connections via UI
3. Import schemas and generate embeddings
4. Start chatting with your data!
