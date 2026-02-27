"""
ProcuraShield — SQLAlchemy модели
"""

import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Float, DateTime,
    ForeignKey, Enum, JSON, Numeric, Index, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.database import Base


class User(Base):
    """Пользователи системы"""
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="public")
    organization: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class Procurement(Base):
    """Государственные закупки"""
    __tablename__ = "procurements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    registry_number: Mapped[Optional[str]] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    customer_name: Mapped[str] = mapped_column(String(500), nullable=False)
    customer_inn: Mapped[Optional[str]] = mapped_column(String(12), index=True)
    customer_kpp: Mapped[Optional[str]] = mapped_column(String(9))
    customer_region: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    procurement_method: Mapped[Optional[str]] = mapped_column(String(100))
    category: Mapped[Optional[str]] = mapped_column(String(255))
    okpd2_code: Mapped[Optional[str]] = mapped_column(String(20))
    initial_price: Mapped[Optional[float]] = mapped_column(Numeric(18, 2))
    currency: Mapped[str] = mapped_column(String(3), default="KZT")
    publication_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    submission_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    auction_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    contract_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="published")
    document_hash: Mapped[Optional[str]] = mapped_column(String(66))
    blockchain_tx_hash: Mapped[Optional[str]] = mapped_column(String(66))
    ipfs_hash: Mapped[Optional[str]] = mapped_column(String(100))
    raw_text: Mapped[Optional[str]] = mapped_column(Text)
    specifications: Mapped[Optional[dict]] = mapped_column(JSONB)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB)
    source_url: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    risk_assessments = relationship("RiskAssessment", back_populates="procurement")
    anomalies = relationship("Anomaly", back_populates="procurement")
    bids = relationship("Bid", back_populates="procurement")


class Supplier(Base):
    """Поставщики"""
    __tablename__ = "suppliers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    inn: Mapped[Optional[str]] = mapped_column(String(12), unique=True)
    kpp: Mapped[Optional[str]] = mapped_column(String(9))
    ogrn: Mapped[Optional[str]] = mapped_column(String(15))
    legal_address: Mapped[Optional[str]] = mapped_column(Text)
    actual_address: Mapped[Optional[str]] = mapped_column(Text)
    registration_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    authorized_capital: Mapped[Optional[float]] = mapped_column(Numeric(18, 2))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    website: Mapped[Optional[str]] = mapped_column(String(500))
    ceo_name: Mapped[Optional[str]] = mapped_column(String(255))
    ceo_inn: Mapped[Optional[str]] = mapped_column(String(12))
    founder_names: Mapped[Optional[dict]] = mapped_column(JSONB)
    okved_codes: Mapped[Optional[dict]] = mapped_column(JSONB)
    employee_count: Mapped[Optional[int]] = mapped_column(Integer)
    annual_revenue: Mapped[Optional[float]] = mapped_column(Numeric(18, 2))
    is_shell_company: Mapped[bool] = mapped_column(Boolean, default=False)
    risk_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    sanctions_listed: Mapped[bool] = mapped_column(Boolean, default=False)
    pep_associated: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    bids = relationship("Bid", back_populates="supplier")


class Bid(Base):
    """Заявки на участие в тендере"""
    __tablename__ = "bids"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    procurement_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("procurements.id"), nullable=False)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    bid_price: Mapped[Optional[float]] = mapped_column(Numeric(18, 2))
    bid_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_winner: Mapped[bool] = mapped_column(Boolean, default=False)
    disqualified: Mapped[bool] = mapped_column(Boolean, default=False)
    disqualification_reason: Mapped[Optional[str]] = mapped_column(Text)
    rank: Mapped[Optional[int]] = mapped_column(Integer)
    score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    procurement = relationship("Procurement", back_populates="bids")
    supplier = relationship("Supplier", back_populates="bids")


class RiskAssessment(Base):
    """Оценки риска закупок"""
    __tablename__ = "risk_assessments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    procurement_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("procurements.id"), nullable=False)
    overall_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(10), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False)

    specification_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    competition_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    pricing_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    supplier_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    timing_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    historical_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    network_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0)

    feature_vector: Mapped[Optional[dict]] = mapped_column(JSONB)
    shap_values: Mapped[Optional[dict]] = mapped_column(JSONB)
    explanation_text: Mapped[Optional[str]] = mapped_column(Text)
    model_version: Mapped[Optional[str]] = mapped_column(String(50))
    blockchain_tx_hash: Mapped[Optional[str]] = mapped_column(String(66))

    analyst_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    analyst_override: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    analyst_comment: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    procurement = relationship("Procurement", back_populates="risk_assessments")
    anomalies = relationship("Anomaly", back_populates="risk_assessment")


class Anomaly(Base):
    """Обнаруженные аномалии"""
    __tablename__ = "anomalies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    procurement_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("procurements.id"), nullable=False)
    risk_assessment_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("risk_assessments.id"))
    anomaly_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[Optional[dict]] = mapped_column(JSONB)
    location_in_document: Mapped[Optional[str]] = mapped_column(Text)
    suggested_action: Mapped[Optional[str]] = mapped_column(Text)
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    confirmed_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    false_positive: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    procurement = relationship("Procurement", back_populates="anomalies")
    risk_assessment = relationship("RiskAssessment", back_populates="anomalies")


class Alert(Base):
    """Уведомления/алерты"""
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    procurement_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("procurements.id"))
    risk_assessment_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("risk_assessments.id"))
    alert_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="new")
    assigned_to: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    resolved_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text)
    notification_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    notification_channels: Mapped[Optional[dict]] = mapped_column(JSONB)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class WhistleblowerReport(Base):
    """Анонимные жалобы"""
    __tablename__ = "whistleblower_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tracking_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    encrypted_content: Mapped[str] = mapped_column(Text, nullable=False)
    encrypted_contact: Mapped[Optional[str]] = mapped_column(Text)
    procurement_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("procurements.id"))
    category: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="new")
    assigned_to: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    priority: Mapped[int] = mapped_column(Integer, default=0)
    response_encrypted: Mapped[Optional[str]] = mapped_column(Text)
    ip_hash: Mapped[Optional[str]] = mapped_column(String(66))
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    """Аудит-лог действий пользователей"""
    __tablename__ = "audit_log"
    __table_args__ = {"implicit_returning": False}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[Optional[str]] = mapped_column(String(100))
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    request_method: Mapped[Optional[str]] = mapped_column(String(10))
    request_path: Mapped[Optional[str]] = mapped_column(Text)
    request_body: Mapped[Optional[dict]] = mapped_column(JSONB)
    response_status: Mapped[Optional[int]] = mapped_column(Integer)
    details: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, primary_key=True)
