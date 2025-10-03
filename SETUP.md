# Setup Instructions

## Quick Start (5 minutes)

### 1. Prerequisites
- Docker and Docker Compose installed
- At least one LLM API key (OpenAI or Anthropic)

### 2. Setup Steps

```bash
# 1. Clone the repository
git clone <repository-url>
cd air-analytics-platform

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 3. Start all services
docker-compose up -d

# 4. Wait for services to be ready (about 30 seconds)
docker-compose logs -f backend

# 5. Run database migrations
docker-compose exec backend alembic upgrade head

# 6. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
```

## Detailed Setup

### Environment Configuration

Edit `.env` file with your settings:

```env
# Required: At least one LLM API key
OPENAI_API_KEY=sk-your-openai-key-here
# OR
ANTHROPIC_API_KEY=your-anthropic-key-here

# Optional: Database settings (defaults are fine for development)
POSTGRES_DB=air_analytics
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password

# Security (change in production)
SECRET_KEY=your-super-secret-key-change-in-production
```

### Service Health Check

```bash
# Check all services are running
docker-compose ps

# Check backend health
curl http://localhost:8000/health

# Check database connection
docker-compose exec postgres psql -U postgres -d air_analytics -c "SELECT 1;"

# Check Redis
docker-compose exec redis redis-cli ping
```

### First Database Connection

1. Open http://localhost:3000
2. Go to "Databases" page
3. Click "Add Database"
4. Fill in test database details:
   - Alias: `test-db`
   - Type: `postgres`
   - Host: `postgres` (if connecting from within Docker)
   - Port: `5432`
   - Database: `air_analytics`
   - Username: `postgres`
   - Password: `password`
5. Click "Create"
6. Click the "Import" button to index the schema

### Test the Chat Feature

1. Go to "Chat" page
2. Select your database from dropdown
3. Ask: "What tables are available?"
4. Try: "Show me the structure of vector_documents table"

## Troubleshooting

### Common Issues

**Backend not starting:**
```bash
# Check logs
docker-compose logs backend

# Common fixes:
# 1. Wait for database to be ready
# 2. Check API keys in .env
# 3. Restart services
docker-compose restart backend
```

**Database connection issues:**
```bash
# Check PostgreSQL is running
docker-compose logs postgres

# Verify pgvector extension
docker-compose exec postgres psql -U postgres -d air_analytics -c "SELECT * FROM pg_extension WHERE extname='vector';"
```

**Frontend not loading:**
```bash
# Check frontend logs
docker-compose logs frontend

# Rebuild if needed
docker-compose build frontend
docker-compose up -d frontend
```

**Import jobs failing:**
```bash
# Check worker logs
docker-compose logs worker

# Restart worker
docker-compose restart worker
```

### Performance Issues

**Slow vector search:**
```sql
-- Connect to database and check indexes
docker-compose exec postgres psql -U postgres -d air_analytics

-- Check vector index exists
\d vector_documents

-- Recreate index if needed
DROP INDEX IF EXISTS idx_vector_documents_embedding;
CREATE INDEX idx_vector_documents_embedding
ON vector_documents
USING ivfflat (embedding vector_l2_ops)
WITH (lists = 100);
```

**Memory issues:**
```yaml
# Add to docker-compose.yml under services
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
  postgres:
    deploy:
      resources:
        limits:
          memory: 1G
```

### Development Setup

**Backend development:**
```bash
# Run backend locally
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with database settings

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

**Frontend development:**
```bash
# Run frontend locally
cd frontend
npm install
npm run dev
```

## Production Deployment

### Minimal Production Setup

1. **Secure Environment**
   ```bash
   # Create production environment
   cp .env.example .env.prod

   # Update with secure values:
   # - Strong SECRET_KEY
   # - Production database credentials
   # - Real API keys
   # - CORS origins for your domain
   ```

2. **Production Compose**
   ```yaml
   # docker-compose.prod.yml
   version: '3.8'
   services:
     postgres:
       restart: unless-stopped
       volumes:
         - /var/lib/postgresql/data:/var/lib/postgresql/data

     backend:
       restart: unless-stopped
       environment:
         - DEBUG=false

     frontend:
       restart: unless-stopped
       command: npm run build && npm run start
   ```

3. **Deploy**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Security Checklist

- [ ] Change all default passwords
- [ ] Use strong SECRET_KEY
- [ ] Configure HTTPS/SSL
- [ ] Set up firewall rules
- [ ] Enable database encryption in transit
- [ ] Configure backup strategy
- [ ] Set up monitoring and alerting

## Advanced Configuration

### Custom LLM Models

```python
# backend/app/core/config.py
class Settings(BaseSettings):
    # Custom OpenAI endpoint
    OPENAI_API_BASE: str = "https://api.openai.com/v1"

    # Custom model names
    LLM_MODEL: str = "gpt-4"
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
```

### Database Connection Pooling

```python
# backend/app/core/database.py
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,           # Number of connections to maintain
    max_overflow=10,        # Additional connections when needed
    pool_pre_ping=True,     # Validate connections
    pool_recycle=300,       # Recycle connections every 5 minutes
)
```

### Vector Search Tuning

```sql
-- For large datasets, tune the IVFFlat index
DROP INDEX idx_vector_documents_embedding;
CREATE INDEX idx_vector_documents_embedding
ON vector_documents
USING ivfflat (embedding vector_l2_ops)
WITH (lists = 1000);  -- Increase for larger datasets

-- Set query parameters
SET ivfflat.probes = 10;  -- Number of lists to search
```

### Monitoring Setup

```yaml
# Add to docker-compose.yml
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

## Need Help?

- 📖 Check the main [README.md](./README.md) for detailed documentation
- 🐛 Report issues on GitHub Issues
- 💬 Ask questions in GitHub Discussions
- 📊 Check API documentation at http://localhost:8000/docs