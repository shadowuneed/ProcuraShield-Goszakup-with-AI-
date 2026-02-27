"""
ProcuraShield — Главное приложение FastAPI
Антикоррупционная платформа для анализа государственных закупок
"""

import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings
from app.api import auth, procurements, analysis, graph, blockchain, whistleblower, dashboard, alerts
from app.middleware.security import (
    SecurityHeadersMiddleware,
    AuditLogMiddleware,
    RateLimitMiddleware,
    RequestSanitizer,
)

# Настройка логирования
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл приложения"""
    logger.info("🛡️ ProcuraShield запускается...", environment=settings.ENVIRONMENT)
    yield
    logger.info("🛡️ ProcuraShield остановлен")


# Создание приложения
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
    ## 🛡️ ProcuraShield API
    
    Интеллектуальная антикоррупционная платформа для анализа государственных закупок.
    
    ### Возможности:
    - **Анализ тендеров** — NLP-анализ технических спецификаций
    - **Risk Scoring** — многофакторная оценка риска (0-100)
    - **Граф связей** — выявление аффилированности через GNN
    - **Блокчейн аудит** — неизменяемое хранение доказательств
    - **Anti-Collusion** — выявление картельных сговоров
    - **AML** — противодействие отмыванию денег
    
    ### Роли:
    - `public` — просмотр публичных данных
    - `analyst` — анализ и оценка тендеров
    - `investigator` — расследование и доказательства
    - `admin` — полный доступ
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Безопасность — OWASP заголовки, аудит, rate-limit, санитизация
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(AuditLogMiddleware)
app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)
app.add_middleware(RequestSanitizer)

# Prometheus метрики
Instrumentator().instrument(app).expose(app)

# Подключение роутеров
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Авторизация"])
app.include_router(procurements.router, prefix=f"{settings.API_V1_PREFIX}/procurements", tags=["Закупки"])
app.include_router(analysis.router, prefix=f"{settings.API_V1_PREFIX}/analysis", tags=["AI-Анализ"])
app.include_router(graph.router, prefix=f"{settings.API_V1_PREFIX}/graph", tags=["Граф связей"])
app.include_router(blockchain.router, prefix=f"{settings.API_V1_PREFIX}/blockchain", tags=["Блокчейн"])
app.include_router(whistleblower.router, prefix=f"{settings.API_V1_PREFIX}/whistleblower", tags=["Анонимные жалобы"])
app.include_router(dashboard.router, prefix=f"{settings.API_V1_PREFIX}/dashboard", tags=["Дашборд"])
app.include_router(alerts.router, prefix=f"{settings.API_V1_PREFIX}/alerts", tags=["Алерты"])


@app.get("/", tags=["Система"])
async def root():
    """Корневой эндпоинт — информация о системе"""
    return {
        "name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "status": "operational",
        "description": "Антикоррупционная платформа для анализа госзакупок"
    }


@app.get("/health", tags=["Система"])
async def health_check():
    """Проверка здоровья сервиса"""
    return {"status": "healthy", "service": "procurashield-backend"}
