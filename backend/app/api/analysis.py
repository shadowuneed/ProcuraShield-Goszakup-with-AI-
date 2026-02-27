"""
ProcuraShield — API: AI-Анализ тендеров
Запуск NLP-анализа, скоринга, получение результатов
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.core.database import get_db
from app.core.security import get_current_user, require_analyst
from app.models import Procurement, RiskAssessment, Anomaly
from app.schemas import (
    AnalysisResultResponse, RiskAssessmentResponse,
    AnomalyResponse, ProcurementResponse
)
from app.services.analysis_service import AnalysisService

logger = structlog.get_logger()
router = APIRouter()


@router.post("/analyze/{procurement_id}", response_model=AnalysisResultResponse)
async def analyze_procurement(
    procurement_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_analyst),
):
    """
    Запустить полный AI-анализ тендерной документации.

    Этапы анализа:
    1. NLP-анализ текста на аномалии в ТЗ
    2. Проверка на гиперспецифичные требования
    3. Анализ сроков и ограничений
    4. Стилометрический анализ
    5. Risk Scoring (ML-модель)
    6. Генерация текстового объяснения
    """
    # Получаем закупку
    result = await db.execute(select(Procurement).where(Procurement.id == procurement_id))
    procurement = result.scalar_one_or_none()
    if not procurement:
        raise HTTPException(status_code=404, detail="Закупка не найдена")

    if not procurement.raw_text:
        raise HTTPException(status_code=400, detail="Отсутствует текст документации для анализа")

    # Запускаем анализ
    service = AnalysisService()
    analysis_result = await service.full_analysis(procurement, db)

    logger.info(
        "Анализ завершён",
        procurement_id=str(procurement_id),
        risk_score=analysis_result["risk_assessment"].overall_score,
        anomalies_found=len(analysis_result["anomalies"])
    )

    return AnalysisResultResponse(
        procurement=ProcurementResponse.model_validate(procurement),
        risk_assessment=RiskAssessmentResponse.model_validate(analysis_result["risk_assessment"]),
        anomalies=[AnomalyResponse.model_validate(a) for a in analysis_result["anomalies"]],
        graph_data=analysis_result.get("graph_data")
    )


@router.get("/results/{procurement_id}", response_model=AnalysisResultResponse)
async def get_analysis_results(
    procurement_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Получить результаты анализа тендера"""
    # Закупка
    result = await db.execute(select(Procurement).where(Procurement.id == procurement_id))
    procurement = result.scalar_one_or_none()
    if not procurement:
        raise HTTPException(status_code=404, detail="Закупка не найдена")

    # Risk Assessment
    ra_result = await db.execute(
        select(RiskAssessment)
        .where(RiskAssessment.procurement_id == procurement_id)
        .order_by(RiskAssessment.created_at.desc())
    )
    risk_assessment = ra_result.scalar_one_or_none()
    if not risk_assessment:
        raise HTTPException(status_code=404, detail="Анализ ещё не проводился")

    # Anomalies
    anomalies_result = await db.execute(
        select(Anomaly).where(Anomaly.procurement_id == procurement_id)
    )
    anomalies = anomalies_result.scalars().all()

    return AnalysisResultResponse(
        procurement=ProcurementResponse.model_validate(procurement),
        risk_assessment=RiskAssessmentResponse.model_validate(risk_assessment),
        anomalies=[AnomalyResponse.model_validate(a) for a in anomalies],
    )


@router.get("/anomalies/{procurement_id}", response_model=list[AnomalyResponse])
async def get_anomalies(
    procurement_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Получить список аномалий для закупки"""
    result = await db.execute(
        select(Anomaly)
        .where(Anomaly.procurement_id == procurement_id)
        .order_by(Anomaly.severity.desc())
    )
    anomalies = result.scalars().all()
    return [AnomalyResponse.model_validate(a) for a in anomalies]


@router.post("/batch-analyze")
async def batch_analyze(
    procurement_ids: list[UUID],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_analyst),
):
    """Запустить анализ для нескольких закупок (async через Celery)"""
    # В production это отправляется в Celery
    for pid in procurement_ids:
        background_tasks.add_task(_run_analysis_task, pid)

    return {
        "message": f"Анализ запущен для {len(procurement_ids)} закупок",
        "procurement_ids": [str(pid) for pid in procurement_ids],
        "status": "processing"
    }


async def _run_analysis_task(procurement_id: UUID):
    """Фоновая задача анализа"""
    from app.core.database import async_session
    async with async_session() as db:
        result = await db.execute(select(Procurement).where(Procurement.id == procurement_id))
        procurement = result.scalar_one_or_none()
        if procurement and procurement.raw_text:
            service = AnalysisService()
            await service.full_analysis(procurement, db)
            await db.commit()
