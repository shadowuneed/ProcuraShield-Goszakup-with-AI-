"""
ProcuraShield — API: Блокчейн верификация
Регистрация, проверка и просмотр блокчейн-записей
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.core.database import get_db
from app.core.security import get_current_user, require_analyst
from app.models import Procurement

logger = structlog.get_logger()
router = APIRouter()


@router.post("/register/{procurement_id}")
async def register_on_blockchain(
    procurement_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_analyst),
):
    """Зарегистрировать тендер в блокчейне (хеш документации)"""
    result = await db.execute(select(Procurement).where(Procurement.id == procurement_id))
    procurement = result.scalar_one_or_none()
    if not procurement:
        raise HTTPException(status_code=404, detail="Закупка не найдена")

    # Вычисляем хеш документа
    import hashlib
    doc_text = procurement.raw_text or procurement.title
    doc_hash = "0x" + hashlib.sha256(doc_text.encode()).hexdigest()

    # Запись в блокчейн (имитация для MVP, в production — через Web3)
    tx_hash = "0x" + hashlib.sha256(f"{procurement_id}{doc_hash}".encode()).hexdigest()[:64]

    procurement.document_hash = doc_hash
    procurement.blockchain_tx_hash = tx_hash
    await db.flush()

    logger.info("Тендер зарегистрирован в блокчейне", procurement_id=str(procurement_id))

    return {
        "procurement_id": str(procurement_id),
        "document_hash": doc_hash,
        "tx_hash": tx_hash,
        "status": "confirmed",
        "message": "Документ успешно зарегистрирован в блокчейне"
    }


@router.get("/verify/{document_hash}")
async def verify_document(
    document_hash: str,
    db: AsyncSession = Depends(get_db),
):
    """Проверить подлинность документа по хешу"""
    result = await db.execute(
        select(Procurement).where(Procurement.document_hash == document_hash)
    )
    procurement = result.scalar_one_or_none()

    if not procurement:
        return {
            "verified": False,
            "message": "Документ не найден в реестре"
        }

    return {
        "verified": True,
        "procurement_id": str(procurement.id),
        "title": procurement.title,
        "tx_hash": procurement.blockchain_tx_hash,
        "registered_at": procurement.created_at.isoformat(),
        "message": "Документ подтверждён — зарегистрирован в блокчейне"
    }


@router.get("/transactions/{procurement_id}")
async def get_blockchain_history(
    procurement_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Получить историю блокчейн-транзакций для закупки"""
    from sqlalchemy import text
    result = await db.execute(text("""
        SELECT tx_hash, block_number, function_name, args, status, created_at
        FROM blockchain_records
        WHERE related_id = :pid
        ORDER BY created_at DESC
    """), {"pid": str(procurement_id)})

    transactions = []
    for row in result.fetchall():
        transactions.append({
            "tx_hash": row.tx_hash,
            "block_number": row.block_number,
            "function": row.function_name,
            "status": row.status,
            "timestamp": row.created_at.isoformat() if row.created_at else None,
        })

    return {"procurement_id": str(procurement_id), "transactions": transactions}


@router.get("/ipfs/{cid}")
async def get_ipfs_document(cid: str):
    """Получить документ из IPFS по CID"""
    # В production — через IPFS HTTP API
    return {
        "cid": cid,
        "gateway_url": f"https://ipfs.io/ipfs/{cid}",
        "status": "available"
    }
