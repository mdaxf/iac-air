# Database Initialization Guide

This guide explains how to initialize the database for the AI Data Analytics Platform v1.0.

## Overview

The project now uses a consolidated v1.0 schema instead of incremental migrations. This simplifies deployment and ensures consistent database state.

## Prerequisites

1. PostgreSQL 12+ with pgvector extension support
2. Python 3.8+
3. All backend dependencies installed (`pip install -r requirements.txt`)

## Option 1: Initialize Fresh Database (Recommended)

Use the initialization script to create all tables from scratch:

```bash
cd backend
python scripts/init_db_v1.py
```

This script will:
1. Check if database has existing tables
2. Prompt for confirmation if tables exist
3. Drop all existing tables (if confirmed)
4. Create PostgreSQL extensions (vector, uuid-ossp)
5. Create all tables from SQLAlchemy models
6. Mark database as v1.0 in alembic_version table

### Interactive Prompts

If the database already has tables, you'll see:

```
Database already contains tables!
Do you want to drop all existing tables and reinitialize? (yes/no):
```

Type `yes` to proceed with reinitialization, or `no` to cancel.

## Option 2: Using Alembic Migrations

If you prefer using Alembic for migration management:

```bash
cd backend

# Initialize to v1.0 (for fresh database)
alembic upgrade v1.0

# Or upgrade to head (same as v1.0 for now)
alembic upgrade head
```

## Database Schema v1.0

The v1.0 schema includes all tables:

### Core Tables
- `users` - User accounts and authentication
- `database_connections` - Connected data sources
- `query_history` - Historical queries and results
- `api_call_history` - API request logging

### Conversation & Reports
- `conversations` - Chat conversation sessions
- `messages` - Individual chat messages
- `reports` - Report definitions
- `report_versions` - Report versioning
- `report_components` - Report widgets/components
- `report_layouts` - Report layout configurations
- `report_parameters` - Report parameter definitions
- `report_parameter_values` - User-specific parameter values

### Vector & Semantic Layer
- `vector_documents` - Document embeddings for RAG
- `vector_table_metadata` - Database table metadata with embeddings
- `vector_column_metadata` - Database column metadata with embeddings
- `vector_relationship_metadata` - Table relationship metadata
- `business_entities` - Business entity mappings
- `business_metrics` - Business metric definitions
- `concept_mappings` - Business-to-technical term mappings
- `query_templates` - Reusable query templates

### File Management
- `uploaded_files` - User-uploaded documentation files
- `import_jobs` - Schema import job tracking
- `vector_regeneration_jobs` - Embedding regeneration job tracking

## PostgreSQL Extensions

The database uses these extensions:

- **vector** - pgvector for semantic search
- **uuid-ossp** - UUID generation

These are automatically created by the initialization script.

## Verification

After initialization, verify the database:

```bash
# Connect to PostgreSQL
psql -U your_username -d your_database

# List all tables
\dt

# Check alembic version
SELECT * FROM alembic_version;
```

You should see `v1.0` as the version_num.

## Configuration

Ensure your `.env` file has the correct database URL:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
```

## Troubleshooting

### Permission Issues

If you get permission errors:
```bash
# Grant create extension permission
GRANT CREATE ON DATABASE your_database TO your_user;
```

### Connection Issues

Check if PostgreSQL is running:
```bash
# Windows
powershell -Command "Get-Service postgresql*"

# Linux/Mac
systemctl status postgresql
```

### pgvector Extension Missing

Install pgvector extension:
```bash
# Ubuntu/Debian
sudo apt install postgresql-16-pgvector

# Mac
brew install pgvector

# Windows - download from https://github.com/pgvector/pgvector
```

## Migration from Previous Versions

If you have data in an older database version:

1. **Backup your data first!**
   ```bash
   pg_dump -U user -d database > backup.sql
   ```

2. Run the initialization script (it will prompt before dropping tables)

3. If needed, restore specific data from backup

## Next Steps

After database initialization:

1. Start the backend server:
   ```bash
   uvicorn app.main:app --reload
   ```

2. Access the frontend and create database connections

3. Import database schemas via the UI

4. Generate embeddings for semantic search

## Version History

- **v1.0** (2025-10-02) - Initial consolidated schema with all features
  - User management
  - Database connections
  - Query history and API logging
  - Conversations and chat
  - Reports with versioning
  - Vector embeddings and semantic layer
  - Business entity/metric mappings
  - File upload and job tracking
