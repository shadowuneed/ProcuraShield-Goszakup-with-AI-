"""
ProcuraShield — Celery Worker
Асинхронная обработка задач анализа
"""

from celery import Celery
from app.core.config import settings

# Создаём Celery приложение
celery_app = Celery(
    "procurashield",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Almaty",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        # Периодический парсинг новых тендеров из ЕИС
        "parse-new-tenders": {
            "task": "app.workers.tasks.parse_new_tenders",
            "schedule": 3600.0,  # Каждый час
        },
        # Пересчёт риск-скоров
        "recalculate-risk-scores": {
            "task": "app.workers.tasks.recalculate_risk_scores",
            "schedule": 86400.0,  # Каждый день
        },
    },
)
