"""
ProcuraShield — API: Управление закупками
CRUD операции и поиск по тендерам
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
import structlog

from app.core.database import get_db
from app.core.security import get_current_user, require_analyst, require_admin
from app.models import Procurement
from app.schemas import ProcurementCreate, ProcurementResponse, ProcurementListResponse

logger = structlog.get_logger()
router = APIRouter()


@router.get("/", response_model=ProcurementListResponse)
async def list_procurements(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    region: Optional[str] = None,
    category: Optional[str] = None,
    risk_level: Optional[str] = None,
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    sort_by: str = Query("publication_date", pattern=r"^(publication_date|initial_price|title)$"),
    sort_order: str = Query("desc", pattern=r"^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    """Список закупок с фильтрацией, пагинацией и FTS-поиском"""
    query = select(Procurement)

    # Фильтры
    if region:
        query = query.where(Procurement.customer_region == region)
    if category:
        query = query.where(Procurement.category == category)
    if status_filter:
        query = query.where(Procurement.status == status_filter)
    if min_price is not None:
        query = query.where(Procurement.initial_price >= min_price)
    if max_price is not None:
        query = query.where(Procurement.initial_price <= max_price)

    # Full-text search
    if search:
        query = query.where(
            text("search_vector @@ plainto_tsquery('russian', :search)").bindparams(search=search)
        )

    # Общее количество
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Сортировка
    sort_column = getattr(Procurement, sort_by, Procurement.publication_date)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Пагинация
    offset = (page - 1) * size
    query = query.offset(offset).limit(size)

    result = await db.execute(query)
    items = result.scalars().all()

    return ProcurementListResponse(
        items=[ProcurementResponse.model_validate(p) for p in items],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{procurement_id}", response_model=ProcurementResponse)
async def get_procurement(
    procurement_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Получить закупку по ID"""
    result = await db.execute(select(Procurement).where(Procurement.id == procurement_id))
    procurement = result.scalar_one_or_none()
    if not procurement:
        raise HTTPException(status_code=404, detail="Закупка не найдена")
    return ProcurementResponse.model_validate(procurement)


@router.post("/", response_model=ProcurementResponse, status_code=status.HTTP_201_CREATED)
async def create_procurement(
    data: ProcurementCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_analyst),
):
    """Создать новую закупку (ручной ввод)"""
    procurement = Procurement(**data.model_dump())
    db.add(procurement)
    await db.flush()
    logger.info("Закупка создана", id=str(procurement.id), title=procurement.title)
    return ProcurementResponse.model_validate(procurement)


@router.post("/upload", response_model=ProcurementResponse)
async def upload_procurement_document(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    customer_name: Optional[str] = "Не указан",
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_analyst),
):
    """Загрузка тендерного документа (PDF/DOCX/XML) для анализа"""
    # Проверяем тип файла
    allowed_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/xml", "text/xml",
        "application/msword",
    ]

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый тип файла: {file.content_type}. Допустимые: PDF, DOCX, XML"
        )

    # Читаем содержимое файла
    content = await file.read()

    # Извлекаем текст из документа
    raw_text = await _extract_text(content, file.content_type)

    # Создаём запись закупки
    procurement = Procurement(
        title=title or file.filename or "Без названия",
        customer_name=customer_name,
        raw_text=raw_text,
        status="published",
    )
    db.add(procurement)
    await db.flush()

    logger.info("Документ загружен", id=str(procurement.id), filename=file.filename)
    return ProcurementResponse.model_validate(procurement)


async def _extract_text(content: bytes, content_type: str) -> str:
    """Извлечение текста из документа"""
    import io

    if "pdf" in content_type:
        from PyPDF2 import PdfReader
        reader = PdfReader(io.BytesIO(content))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.strip()

    elif "wordprocessingml" in content_type or "msword" in content_type:
        from docx import Document
        doc = Document(io.BytesIO(content))
        text = "\n".join([p.text for p in doc.paragraphs])
        return text.strip()

    elif "xml" in content_type:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content, "lxml-xml")
        return soup.get_text(separator="\n").strip()

    return content.decode("utf-8", errors="ignore")


@router.delete("/{procurement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_procurement(
    procurement_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Удалить закупку (только admin)"""
    result = await db.execute(select(Procurement).where(Procurement.id == procurement_id))
    procurement = result.scalar_one_or_none()
    if not procurement:
        raise HTTPException(status_code=404, detail="Закупка не найдена")

    await db.delete(procurement)
    logger.info("Закупка удалена", id=str(procurement_id))
