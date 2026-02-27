"""
ProcuraShield — Pydantic-схемы для валидации данных
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator


# ===== Auth Schemas =====

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=255)
    role: str = Field(default="public")
    organization: Optional[str] = None


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    organization: Optional[str]
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


# ===== Procurement Schemas =====

class ProcurementCreate(BaseModel):
    title: str = Field(..., min_length=5)
    description: Optional[str] = None
    customer_name: str = Field(..., min_length=2)
    customer_inn: Optional[str] = Field(None, pattern=r"^\d{10,12}$")
    customer_region: Optional[str] = None
    procurement_method: Optional[str] = None
    category: Optional[str] = None
    okpd2_code: Optional[str] = None
    initial_price: Optional[float] = Field(None, ge=0)
    currency: str = "KZT"
    publication_date: Optional[datetime] = None
    submission_deadline: Optional[datetime] = None
    source_url: Optional[str] = None


class ProcurementResponse(BaseModel):
    id: UUID
    external_id: Optional[str]
    registry_number: Optional[str]
    title: str
    description: Optional[str]
    customer_name: str
    customer_inn: Optional[str]
    customer_region: Optional[str]
    procurement_method: Optional[str]
    category: Optional[str]
    initial_price: Optional[float]
    currency: str
    publication_date: Optional[datetime]
    submission_deadline: Optional[datetime]
    status: str
    document_hash: Optional[str]
    blockchain_tx_hash: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ProcurementListResponse(BaseModel):
    items: List[ProcurementResponse]
    total: int
    page: int
    size: int


class ProcurementAnalysisRequest(BaseModel):
    """Запрос на анализ тендера"""
    procurement_id: Optional[UUID] = None
    raw_text: Optional[str] = None
    # Файл передаётся через multipart/form-data


# ===== Risk Assessment Schemas =====

class RiskAssessmentResponse(BaseModel):
    id: UUID
    procurement_id: UUID
    overall_score: float
    risk_level: str
    confidence: float
    specification_score: float
    competition_score: float
    pricing_score: float
    supplier_score: float
    timing_score: float
    historical_score: float
    network_score: float
    explanation_text: Optional[str]
    shap_values: Optional[Dict[str, Any]]
    model_version: Optional[str]
    blockchain_tx_hash: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AnomalyResponse(BaseModel):
    id: UUID
    procurement_id: UUID
    anomaly_type: str
    severity: float
    title: str
    description: str
    evidence: Optional[Dict[str, Any]]
    location_in_document: Optional[str]
    suggested_action: Optional[str]
    is_confirmed: bool
    false_positive: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AnalysisResultResponse(BaseModel):
    """Полный результат анализа"""
    procurement: ProcurementResponse
    risk_assessment: RiskAssessmentResponse
    anomalies: List[AnomalyResponse]
    graph_data: Optional[Dict[str, Any]] = None


# ===== Supplier Schemas =====

class SupplierResponse(BaseModel):
    id: UUID
    name: str
    inn: Optional[str]
    legal_address: Optional[str]
    registration_date: Optional[datetime]
    authorized_capital: Optional[float]
    ceo_name: Optional[str]
    is_shell_company: bool
    risk_score: float
    sanctions_listed: bool
    pep_associated: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ===== Alert Schemas =====

class AlertResponse(BaseModel):
    id: UUID
    procurement_id: Optional[UUID]
    alert_type: str
    title: str
    message: str
    severity: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ===== Whistleblower Schemas =====

class WhistleblowerSubmit(BaseModel):
    encrypted_content: str = Field(..., min_length=10)
    encrypted_contact: Optional[str] = None
    procurement_id: Optional[UUID] = None
    category: Optional[str] = None


class WhistleblowerResponse(BaseModel):
    tracking_id: str
    status: str
    message: str = "Ваша жалоба принята и будет рассмотрена"


class WhistleblowerStatusResponse(BaseModel):
    tracking_id: str
    status: str
    response_encrypted: Optional[str] = None
    created_at: datetime


# ===== Graph Schemas =====

class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # 'supplier', 'person', 'procurement'
    risk_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class GraphEdge(BaseModel):
    source: str
    target: str
    type: str  # 'ceo_of', 'founder_of', 'won', 'bid_in', etc
    strength: float = 1.0


class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    communities: Optional[List[Dict[str, Any]]] = None


# ===== Complaint Schemas =====

class ComplaintGenerateRequest(BaseModel):
    procurement_id: UUID
    complaint_type: str = Field(..., pattern=r"^(fas|prosecutor|regulator)$")
    additional_info: Optional[str] = None


class ComplaintResponse(BaseModel):
    id: UUID
    procurement_id: UUID
    complaint_type: str
    generated_text: str
    status: str
    created_at: datetime


# ===== Stats/Dashboard =====

class DashboardStats(BaseModel):
    total_procurements: int
    analyzed_today: int
    high_risk_count: int
    total_anomalies: int
    avg_risk_score: float
    regional_stats: List[Dict[str, Any]]
    risk_distribution: Dict[str, int]
    top_risky: List[ProcurementResponse]
    trend_data: List[Dict[str, Any]]
