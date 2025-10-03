# AI Data Analytics Platform

A comprehensive AI-powered data analytics platform that enables natural language queries across multiple enterprise data sources using vector search and large language models.

## 🏗️ Architecture

- **Backend**: Python FastAPI with PostgreSQL + pgvector for vector storage
- **Frontend**: React with TypeScript and Tailwind CSS
- **Database**: PostgreSQL with pgvector extension for vector similarity search
- **Queue**: Redis with Celery for background job processing
- **LLM Integration**: OpenAI GPT-4 and Anthropic Claude support
- **Deployment**: Docker Compose for local development and production

## 🎯 Features

### Core Capabilities
- 🤖 **Natural Language Queries**: Ask questions about your data in plain English
- 🔍 **Vector Search**: AI-powered semantic search across database schemas and documentation
- 📊 **Multi-Database Support**: Connect to PostgreSQL, MySQL, SQL Server, and Oracle
- 📈 **Intelligent Visualizations**: Automatic chart generation based on query results
- 🔐 **SQL Safety**: Built-in query validation and read-only execution
- 📱 **Modern UI**: Responsive React interface with real-time chat

### Enterprise Features
- 🏢 **Multi-Tenant Support**: Isolated data access by tenant
- 🔑 **RBAC**: Role-based access control and permissions
- 📋 **Audit Logging**: Complete query and access audit trail
- 🔄 **Schema Import**: Automated database schema introspection and documentation
- 📤 **Export Options**: CSV, Excel, and PDF export capabilities
- ⚡ **Performance**: Optimized vector search with pgvector indexing

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- At least one LLM API key (OpenAI or Anthropic)

### 1. Clone and Setup
```bash
git clone <repository-url>
cd air-analytics-platform

# Copy environment file and configure
cp .env.example .env
# Edit .env with your API keys
```

### 2. Configure Environment
Edit `.env` file with your API keys:
```env
OPENAI_API_KEY=your-openai-api-key-here
# OR
ANTHROPIC_API_KEY=your-anthropic-api-key-here
```

### 3. Start Services
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### 4. Initialize Database
```bash
# Run database migrations
docker-compose exec backend alembic upgrade head
```

### 5. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📖 Usage Guide

### Adding Database Connections

1. Navigate to **Databases** page
2. Click **Add Database**
3. Fill in connection details:
   - **Alias**: Unique identifier (e.g., "production-db")
   - **Type**: Database type (PostgreSQL, MySQL, etc.)
   - **Connection**: Host, port, database name, credentials
   - **Schemas**: Whitelist/blacklist patterns
   - **Domain**: Business domain (MES, ERP, CRM, etc.)

### Schema Import and Indexing

1. After adding a database, click the **Import** button
2. The system will:
   - Introspect database schema
   - Generate human-readable documentation
   - Create vector embeddings for semantic search
   - Store everything in the vector database

### Chatting with Your Data

1. Go to **Chat** page
2. Select a database from the dropdown
3. Start a new conversation
4. Ask questions like:
   - "Show me sales by region for last quarter"
   - "What are our top customers by revenue?"
   - "Find production issues from last week"

### Understanding Results

Each AI response includes:
- **Narrative**: Human-readable explanation
- **Visualization**: Automatic charts when appropriate
- **Data Table**: Tabular results with pagination
- **SQL Query**: Generated SQL (expandable)
- **Provenance**: Source tables and database information

## 🛠️ Development

### Backend Development

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## 🏗️ Project Structure

```
air-analytics-platform/
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core configuration
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   └── services/       # Business logic
│   ├── migrations/         # Alembic migrations
│   ├── scripts/           # Utility scripts
│   └── tests/             # Test suite
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API clients
│   │   ├── hooks/         # Custom React hooks
│   │   └── types/         # TypeScript types
│   └── public/            # Static assets
├── docker-compose.yml     # Development environment
└── README.md             # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for GPT models | Required |
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude | Alternative to OpenAI |
| `POSTGRES_*` | Database connection settings | See .env.example |
| `REDIS_URL` | Redis connection for Celery | redis://localhost:6379/0 |
| `SECRET_KEY` | Security key for JWT tokens | Change in production |

### Database Support

| Database | Status | Notes |
|----------|--------|-------|
| PostgreSQL | ✅ Full | Native support with asyncpg |
| MySQL | ✅ Full | Requires mysql-connector-python |
| SQL Server | ✅ Full | Requires pyodbc and drivers |
| Oracle | ✅ Full | Requires cx_Oracle |

### LLM Models

| Provider | Models | Features |
|----------|--------|----------|
| OpenAI | GPT-4, GPT-3.5 | SQL generation, embeddings |
| Anthropic | Claude 3 | SQL generation |
| Local | Planned | On-premises deployment |

## 📊 Performance Tuning

### Vector Search Optimization

```sql
-- Create HNSW index for better performance (if available)
CREATE INDEX idx_vector_hnsw
ON vector_documents
USING hnsw (embedding vector_l2_ops)
WITH (m = 16, ef_construction = 64);

-- Partition large tables by tenant
CREATE TABLE vector_documents_tenant1
PARTITION OF vector_documents
FOR VALUES IN ('tenant1');
```

### Database Connection Pooling

Configure connection pooling in production:
```python
# In backend/app/core/database.py
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=300
)
```

## 🔒 Security

### Production Security Checklist

- [ ] Change default passwords and secret keys
- [ ] Use HTTPS with valid certificates
- [ ] Configure CORS for production domains
- [ ] Set up proper firewall rules
- [ ] Enable database connection encryption
- [ ] Configure rate limiting
- [ ] Set up monitoring and alerting
- [ ] Regular security updates

### Data Privacy

- All SQL queries are logged for audit purposes
- PII detection and masking (configurable)
- Option to use local LLMs for sensitive data
- Database connections use encrypted passwords
- Support for vault-based credential storage

## 🚀 Deployment

### Production Deployment

1. **Prepare Environment**
   ```bash
   # Create production environment file
   cp .env.example .env.prod
   # Configure with production values
   ```

2. **Deploy with Docker**
   ```bash
   # Build and deploy
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Initialize Database**
   ```bash
   # Run migrations
   docker-compose exec backend alembic upgrade head
   ```

4. **Configure Monitoring**
   - Set up health check endpoints
   - Configure log aggregation
   - Monitor vector search performance

### Scaling Considerations

- **Horizontal Scaling**: Multiple backend replicas behind load balancer
- **Database**: Read replicas for heavy analytical queries
- **Vector Storage**: Partition by tenant for large deployments
- **Workers**: Scale Celery workers based on import job volume

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests and documentation
5. Submit a pull request

### Development Guidelines

- Follow Python PEP 8 style guide
- Use TypeScript for frontend development
- Write tests for new features
- Update documentation for API changes
- Follow conventional commit messages

## 📝 License

This project is licensed under the MIT License. See LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the GitHub Issues
- Review the API documentation at `/docs`
- Check system health at `/health`

## 🗺️ Roadmap

### Version 1.1
- [ ] Advanced visualization options
- [ ] Scheduled reports and alerts
- [ ] Advanced RBAC with field-level permissions
- [ ] Multi-language support

### Version 1.2
- [ ] Real-time streaming data support
- [ ] Advanced analytics and ML insights
- [ ] Custom dashboard builder
- [ ] API rate limiting and quotas

### Version 2.0
- [ ] Plugin system for custom connectors
- [ ] Advanced query optimization
- [ ] Distributed vector search
- [ ] Enterprise SSO integration