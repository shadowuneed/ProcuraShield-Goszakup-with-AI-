"""
ProcuraShield — API: Анонимные жалобы (Whistleblower Portal)
Приём, шифрование и отслеживание анонимных обращений
"""

import secrets
import hashlib
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.core.database import get_db
from app.models import WhistleblowerReport
from app.schemas import WhistleblowerSubmit, WhistleblowerResponse, WhistleblowerStatusResponse

logger = structlog.get_logger()
router = APIRouter()


@router.post("/submit", response_model=WhistleblowerResponse)
async def submit_report(
    data: WhistleblowerSubmit,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Подать анонимную жалобу.

    Данные шифруются на клиенте (PGP) перед отправкой.
    IP-адрес хешируется — мы НЕ храним реальный IP.
    Возвращается анонимный tracking_id для отслеживания.
    """
    # Генерируем уникальный tracking ID
    tracking_id = "PS-" + secrets.token_hex(8).upper()

    # Хешируем IP (не храним реальный)
    client_ip = request.client.host if request.client else "unknown"
    ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()

    # Создаём запись
    report = WhistleblowerReport(
        tracking_id=tracking_id,
        encrypted_content=data.encrypted_content,
        encrypted_contact=data.encrypted_contact,
        procurement_id=data.procurement_id,
        category=data.category,
        ip_hash=ip_hash,
    )
    db.add(report)
    await db.flush()

    logger.info("Анонимная жалоба принята", tracking_id=tracking_id)

    return WhistleblowerResponse(
        tracking_id=tracking_id,
        status="new",
        message="Ваша жалоба принята и будет рассмотрена. Сохраните tracking_id для отслеживания статуса."
    )


@router.get("/status/{tracking_id}", response_model=WhistleblowerStatusResponse)
async def check_report_status(
    tracking_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Проверить статус жалобы по tracking_id (анонимно)"""
    result = await db.execute(
        select(WhistleblowerReport).where(WhistleblowerReport.tracking_id == tracking_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Жалоба не найдена. Проверьте tracking_id.")

    return WhistleblowerStatusResponse(
        tracking_id=report.tracking_id,
        status=report.status,
        response_encrypted=report.response_encrypted,
        created_at=report.created_at,
    )
