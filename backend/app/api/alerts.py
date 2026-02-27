"""
ProcuraShield — API: Алерты и уведомления
Управление алертами, WebSocket real-time обновления
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import structlog
import json

from app.core.database import get_db
from app.core.security import get_current_user, require_analyst
from app.models import Alert
from app.schemas import AlertResponse

logger = structlog.get_logger()
router = APIRouter()

# WebSocket менеджер для real-time уведомлений
class ConnectionManager:
    """Менеджер WebSocket-соединений"""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket подключён", total=len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Отправить сообщение всем подключённым клиентам"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


ws_manager = ConnectionManager()


@router.get("/", response_model=list[AlertResponse])
async def list_alerts(
    status: Optional[str] = Query(None, pattern=r"^(new|viewed|investigating|resolved|dismissed)$"),
    severity: Optional[str] = Query(None, pattern=r"^(green|yellow|orange|red)$"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Список алертов с фильтрацией"""
    query = select(Alert).order_by(Alert.created_at.desc())

    if status:
        query = query.where(Alert.status == status)
    if severity:
        query = query.where(Alert.severity == severity)

    offset = (page - 1) * size
    query = query.offset(offset).limit(size)

    result = await db.execute(query)
    alerts = result.scalars().all()

    return [AlertResponse.model_validate(a) for a in alerts]


@router.patch("/{alert_id}/status")
async def update_alert_status(
    alert_id: UUID,
    new_status: str = Query(..., pattern=r"^(viewed|investigating|resolved|dismissed)$"),
    resolution_notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_analyst),
):
    """Обновить статус алерта"""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Алерт не найден")

    alert.status = new_status
    if resolution_notes:
        alert.resolution_notes = resolution_notes

    return {"message": "Статус обновлён", "new_status": new_status}


@router.websocket("/ws")
async def websocket_alerts(websocket: WebSocket):
    """WebSocket для real-time алертов"""
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Обработка команд от клиента
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
