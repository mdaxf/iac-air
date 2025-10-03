from typing import List, Union
from pydantic import AnyHttpUrl, Field, validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    PROJECT_NAME: str = "AI Data Analytics Platform"
    VERSION: str = "1.0.0"
    API_STR: str = "/api/v1"

    # Database
    #DATABASE_URL=postgresql://postgres:password@localhost:5432/air_analytics
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "air_analytics"
    POSTGRES_PORT: str = "5432"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Redis for Celery
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = ["http://localhost:3000", "http://127.0.0.1:3000"]


    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Security
    SECRET_KEY: str = "ZsLSPwKE3921GINSYsKJOeECKEosJYuqDZX7391C-qY="
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # LLM Settings
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    EMBEDDING_DIMENSION: int = 1536

    # Text2SQL Settings
    TEXT2SQL_MODEL: str = "gpt-4-turbo-preview"
    TEXT2SQL_TEMPERATURE: float = 0.1
    TEXT2SQL_MAX_TOKENS: int = 2000
    TEXT2SQL_TIMEOUT: int = 30
    TEXT2SQL_MAX_RETRIES: int = 3
    TEXT2SQL_SAMPLE_SIZE_LIMIT: int = 1000

    # Vector Search
    VECTOR_SEARCH_TOP_K: int = 10

    # Logging Configuration
    LOG_LEVEL: str = "DEBUG"
    LOG_DIR: str = "logs"
    LOG_MAX_FILE_SIZE: str = "10MB"
    LOG_BACKUP_COUNT: int = 5
    LOG_ROTATION: str = "daily"  # daily, hourly, size
    PERFORMANCE_LOG_THRESHOLD: float = 5.0  # seconds
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

    # API History Configuration
    API_HISTORY_RETENTION_DAYS: int = 30  # Days to keep API call history
    API_HISTORY_MAX_REQUEST_SIZE: int = 10000  # Max request body size to store (bytes)
    API_HISTORY_MAX_RESPONSE_SIZE: int = 10000  # Max response body size to store (bytes)
    API_HISTORY_ENABLED: bool = True  # Enable/disable API history tracking

    class Config:
        env_file = ".env"


settings = Settings()