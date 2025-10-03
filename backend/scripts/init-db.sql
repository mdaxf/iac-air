-- Initialize PostgreSQL database with pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create a test user (optional for development)
-- CREATE USER air_user WITH PASSWORD 'air_password';
-- GRANT ALL PRIVILEGES ON DATABASE air_analytics TO air_user;