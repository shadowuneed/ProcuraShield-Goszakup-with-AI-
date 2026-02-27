"""
ProcuraShield — API: Дашборд
Статистика, тренды, региональный анализ
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
import structlog

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Procurement, RiskAssessment, Anomaly, Alert
from app.schemas import DashboardStats, ProcurementResponse

logger = structlog.get_logger()
router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
):
    """Основная статистика для дашборда"""
    # Общее количество закупок
    total_result = await db.execute(select(func.count(Procurement.id)))
    total_procurements = total_result.scalar() or 0

    # Анализировано сегодня
    analyzed_result = await db.execute(text("""
        SELECT COUNT(*) FROM risk_assessments 
        WHERE created_at >= CURRENT_DATE
    """))
    analyzed_today = analyzed_result.scalar() or 0

    # Высокий риск
    high_risk_result = await db.execute(
        select(func.count(RiskAssessment.id))
        .where(RiskAssessment.risk_level.in_(["red", "orange"]))
    )
    high_risk_count = high_risk_result.scalar() or 0

    # Всего аномалий
    anomaly_result = await db.execute(select(func.count(Anomaly.id)))
    total_anomalies = anomaly_result.scalar() or 0

    # Средний риск-скор
    avg_result = await db.execute(select(func.avg(RiskAssessment.overall_score)))
    avg_risk_score = float(avg_result.scalar() or 0)

    # Распределение по уровням риска
    risk_dist_result = await db.execute(text("""
        SELECT risk_level, COUNT(*) as cnt
        FROM risk_assessments
        GROUP BY risk_level
    """))
    risk_distribution = {}
    for row in risk_dist_result.fetchall():
        risk_distribution[row[0]] = row[1]

    # Статистика по регионам
    regional_result = await db.execute(text("""
        SELECT p.customer_region, COUNT(p.id), AVG(ra.overall_score)
        FROM procurements p
        LEFT JOIN risk_assessments ra ON ra.procurement_id = p.id
        WHERE p.customer_region IS NOT NULL
        GROUP BY p.customer_region
        ORDER BY AVG(ra.overall_score) DESC NULLS LAST
        LIMIT 20
    """))
    regional_stats = []
    for row in regional_result.fetchall():
        regional_stats.append({
            "region": row[0],
            "count": row[1],
            "avg_risk": float(row[2] or 0)
        })

    # Топ подозрительных
    top_result = await db.execute(
        select(Procurement)
        .join(RiskAssessment, RiskAssessment.procurement_id == Procurement.id)
        .order_by(RiskAssessment.overall_score.desc())
        .limit(10)
    )
    top_risky = [ProcurementResponse.model_validate(p) for p in top_result.scalars().all()]

    # Тренд за 30 дней
    trend_result = await db.execute(text("""
        SELECT DATE(created_at) as day, 
               COUNT(*) as count,
               AVG(overall_score) as avg_score
        FROM risk_assessments
        WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY DATE(created_at)
        ORDER BY day
    """))
    trend_data = []
    for row in trend_result.fetchall():
        trend_data.append({
            "date": row[0].isoformat(),
            "count": row[1],
            "avg_score": float(row[2] or 0)
        })

    return DashboardStats(
        total_procurements=total_procurements,
        analyzed_today=analyzed_today,
        high_risk_count=high_risk_count,
        total_anomalies=total_anomalies,
        avg_risk_score=round(avg_risk_score, 2),
        regional_stats=regional_stats,
        risk_distribution=risk_distribution,
        top_risky=top_risky,
        trend_data=trend_data,
    )
