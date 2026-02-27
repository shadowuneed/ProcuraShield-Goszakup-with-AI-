"""
ProcuraShield — Celery задачи
"""

from app.workers.celery_app import celery_app
import structlog

logger = structlog.get_logger()


@celery_app.task(name="app.workers.tasks.analyze_procurement")
def analyze_procurement_task(procurement_id: str):
    """Задача анализа одной закупки"""
    import asyncio
    from app.services.analysis_service import AnalysisService
    from app.core.database import async_session
    from app.models import Procurement
    from sqlalchemy import select

    async def _run():
        async with async_session() as db:
            result = await db.execute(
                select(Procurement).where(Procurement.id == procurement_id)
            )
            procurement = result.scalar_one_or_none()
            if procurement and procurement.raw_text:
                service = AnalysisService()
                await service.full_analysis(procurement, db)
                await db.commit()
                logger.info("Celery: анализ завершён", procurement_id=procurement_id)

    asyncio.run(_run())


@celery_app.task(name="app.workers.tasks.parse_new_tenders")
def parse_new_tenders():
    """Периодический парсинг новых тендеров из ЕИС"""
    logger.info("Запуск парсинга новых тендеров")
    # Здесь интеграция с ЕИС API


@celery_app.task(name="app.workers.tasks.recalculate_risk_scores")
def recalculate_risk_scores():
    """Пересчёт риск-скоров с учётом новых данных"""
    logger.info("Запуск пересчёта риск-скоров")        
