"""
ProcuraShield — Конфигурация приложения
Загрузка настроек из переменных окружения
"""

from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Настройки приложения"""

    # Основные
    PROJECT_NAME: str = "ProcuraShield"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "procurashield-super-secret-key-change-in-production"
    API_V1_PREFIX: str = "/api/v1"

    # Сервер
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # База данных
    DATABASE_URL: str = "postgresql+asyncpg://procurashield:procurashield_db_pass_2024@localhost:5432/procurashield"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # JWT
    JWT_SECRET_KEY: str = "jwt-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Blockchain
    ETHEREUM_RPC_URL: str = "http://localhost:8545"
    ETHEREUM_CHAIN_ID: int = 1337
    ETHEREUM_PRIVATE_KEY: str = "0x4f3edf983ac636a65a842ce7c78d9aa706d3b113bce9c46f30d7d21715b23b1d"
    IPFS_API_URL: str = "http://localhost:5001"
    IPFS_GATEWAY_URL: str = "http://localhost:8080"

    # AI/ML
    NLP_MODEL_NAME: str = "ai-forever/ruBert-base"
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    MODEL_CACHE_DIR: str = "./models/cache"

    # Интеграции
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_ALERT_CHAT_ID: Optional[str] = None
    SENDGRID_API_KEY: Optional[str] = None
    EMAIL_FROM: str = "alerts@procurashield.kz"

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:80"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
