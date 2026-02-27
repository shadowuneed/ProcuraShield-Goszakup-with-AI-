-- ============================================================
-- ProcuraShield — Инициализация базы данных
-- Полная SQL-схема с индексами, партиционированием и FTS
-- ============================================================

-- Расширения
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "timescaledb" CASCADE;

-- ============================================================
-- ENUM типы
-- ============================================================
CREATE TYPE user_role AS ENUM ('admin', 'analyst', 'investigator', 'public');
CREATE TYPE risk_level AS ENUM ('green', 'yellow', 'orange', 'red');
CREATE TYPE procurement_status AS ENUM ('draft', 'published', 'active', 'evaluation', 'completed', 'cancelled');
CREATE TYPE anomaly_type AS ENUM (
    'hyperspecific_requirements',
    'nonstandard_certificates',
    'unrealistic_deadlines',
    'geographic_restrictions',
    'anomalous_experience',
    'commercial_proposal_copy',
    'semantic_similarity',
    'bid_suppression',
    'bid_rotation',
    'market_allocation',
    'cover_bidding',
    'price_anomaly',
    'shell_company',
    'procurement_splitting',
    'subcontract_chain',
    'stylometric_match'
);
CREATE TYPE alert_status AS ENUM ('new', 'viewed', 'investigating', 'resolved', 'dismissed');
CREATE TYPE evidence_status AS ENUM ('collected', 'verified', 'frozen', 'submitted');

-- ============================================================
-- Таблица: users — Пользователи системы
-- ============================================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role user_role NOT NULL DEFAULT 'public',
    organization VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- ============================================================
-- Таблица: procurements — Государственные закупки
-- ============================================================
CREATE TABLE procurements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(100) UNIQUE,              -- ID из ЕИС
    registry_number VARCHAR(50),                   -- Реестровый номер
    title TEXT NOT NULL,
    description TEXT,
    customer_name VARCHAR(500) NOT NULL,            -- Наименование заказчика
    customer_inn VARCHAR(12),                       -- ИНН заказчика
    customer_kpp VARCHAR(9),
    customer_region VARCHAR(100),
    procurement_method VARCHAR(100),                -- Способ закупки
    category VARCHAR(255),                          -- Категория товаров/услуг
    okpd2_code VARCHAR(20),                         -- Код ОКПД2
    initial_price DECIMAL(18, 2),                   -- Начальная (максимальная) цена
    currency VARCHAR(3) DEFAULT 'KZT',
    publication_date TIMESTAMPTZ,
    submission_deadline TIMESTAMPTZ,
    auction_date TIMESTAMPTZ,
    contract_deadline TIMESTAMPTZ,
    status procurement_status DEFAULT 'published',
    document_hash VARCHAR(66),                      -- Хеш оригинала в блокчейне
    blockchain_tx_hash VARCHAR(66),                 -- Транзакция регистрации
    ipfs_hash VARCHAR(100),                         -- IPFS CID документов
    raw_text TEXT,                                  -- Извлечённый текст документации
    specifications JSONB,                           -- Структурированные ТЗ
    metadata JSONB,                                 -- Дополнительные данные
    source_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Индексы для производительности
CREATE INDEX idx_procurements_customer_inn ON procurements(customer_inn);
CREATE INDEX idx_procurements_status ON procurements(status);
CREATE INDEX idx_procurements_publication_date ON procurements(publication_date DESC);
CREATE INDEX idx_procurements_category ON procurements(category);
CREATE INDEX idx_procurements_region ON procurements(customer_region);
CREATE INDEX idx_procurements_okpd2 ON procurements(okpd2_code);
CREATE INDEX idx_procurements_price ON procurements(initial_price);

-- Full-text search
ALTER TABLE procurements ADD COLUMN search_vector tsvector;
CREATE INDEX idx_procurements_fts ON procurements USING GIN(search_vector);

CREATE OR REPLACE FUNCTION procurements_search_trigger() RETURNS trigger AS $$
BEGIN
    NEW.search_vector := to_tsvector('russian', COALESCE(NEW.title, '') || ' ' || COALESCE(NEW.description, '') || ' ' || COALESCE(NEW.raw_text, ''));
    RETURN NEW;
END
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_procurements_search
    BEFORE INSERT OR UPDATE ON procurements
    FOR EACH ROW EXECUTE FUNCTION procurements_search_trigger();

-- ============================================================
-- Таблица: suppliers — Поставщики
-- ============================================================
CREATE TABLE suppliers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(500) NOT NULL,
    inn VARCHAR(12) UNIQUE,
    kpp VARCHAR(9),
    ogrn VARCHAR(15),
    legal_address TEXT,
    actual_address TEXT,
    registration_date DATE,
    authorized_capital DECIMAL(18, 2),
    phone VARCHAR(50),
    email VARCHAR(255),
    website VARCHAR(500),
    ceo_name VARCHAR(255),
    ceo_inn VARCHAR(12),
    founder_names JSONB,                            -- Список учредителей
    okved_codes JSONB,                              -- Коды ОКВЭД
    employee_count INTEGER,
    annual_revenue DECIMAL(18, 2),
    is_shell_company BOOLEAN DEFAULT false,         -- Признак компании-однодневки
    risk_score DECIMAL(5, 2) DEFAULT 0,
    sanctions_listed BOOLEAN DEFAULT false,
    pep_associated BOOLEAN DEFAULT false,           -- Связь с PEP
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_suppliers_inn ON suppliers(inn);
CREATE INDEX idx_suppliers_name ON suppliers USING GIN(name gin_trgm_ops);
CREATE INDEX idx_suppliers_risk ON suppliers(risk_score DESC);
CREATE INDEX idx_suppliers_shell ON suppliers(is_shell_company) WHERE is_shell_company = true;

-- ============================================================
-- Таблица: persons — Физические лица (директора, учредители)
-- ============================================================
CREATE TABLE persons (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name VARCHAR(255) NOT NULL,
    inn VARCHAR(12),
    passport_hash VARCHAR(66),                      -- Хеш паспортных данных
    birth_date DATE,
    phone VARCHAR(50),
    email VARCHAR(255),
    address TEXT,
    is_pep BOOLEAN DEFAULT false,                   -- Politically Exposed Person
    sanctions_listed BOOLEAN DEFAULT false,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_persons_inn ON persons(inn);
CREATE INDEX idx_persons_name ON persons USING GIN(full_name gin_trgm_ops);

-- ============================================================
-- Таблица: connections — Связи между сущностями (граф)
-- ============================================================
CREATE TABLE connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_type VARCHAR(50) NOT NULL,               -- 'supplier', 'person', 'procurement'
    source_id UUID NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    target_id UUID NOT NULL,
    connection_type VARCHAR(100) NOT NULL,           -- 'ceo_of', 'founder_of', 'same_address', 'bid_in', 'won', 'subcontractor', 'affiliated'
    strength DECIMAL(3, 2) DEFAULT 1.0,             -- Сила связи (0-1)
    evidence TEXT,                                   -- Доказательство связи
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB,

    CONSTRAINT uq_connection UNIQUE(source_type, source_id, target_type, target_id, connection_type)
);

CREATE INDEX idx_connections_source ON connections(source_type, source_id);
CREATE INDEX idx_connections_target ON connections(target_type, target_id);
CREATE INDEX idx_connections_type ON connections(connection_type);

-- ============================================================
-- Таблица: bids — Заявки на участие в тендере
-- ============================================================
CREATE TABLE bids (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    procurement_id UUID NOT NULL REFERENCES procurements(id) ON DELETE CASCADE,
    supplier_id UUID NOT NULL REFERENCES suppliers(id),
    bid_price DECIMAL(18, 2),
    bid_date TIMESTAMPTZ,
    is_winner BOOLEAN DEFAULT false,
    disqualified BOOLEAN DEFAULT false,
    disqualification_reason TEXT,
    rank INTEGER,
    score DECIMAL(5, 2),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_bids_procurement ON bids(procurement_id);
CREATE INDEX idx_bids_supplier ON bids(supplier_id);
CREATE INDEX idx_bids_winner ON bids(is_winner) WHERE is_winner = true;

-- ============================================================
-- Таблица: risk_assessments — Оценки риска
-- ============================================================
CREATE TABLE risk_assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    procurement_id UUID NOT NULL REFERENCES procurements(id) ON DELETE CASCADE,
    overall_score DECIMAL(5, 2) NOT NULL,           -- 0-100
    risk_level risk_level NOT NULL,
    confidence DECIMAL(3, 2) NOT NULL,              -- Уверенность модели (0-1)

    -- Компоненты скоринга
    specification_score DECIMAL(5, 2) DEFAULT 0,     -- Анализ ТЗ
    competition_score DECIMAL(5, 2) DEFAULT 0,       -- Конкуренция
    pricing_score DECIMAL(5, 2) DEFAULT 0,           -- Ценовые аномалии
    supplier_score DECIMAL(5, 2) DEFAULT 0,          -- Поставщик
    timing_score DECIMAL(5, 2) DEFAULT 0,            -- Сроки
    historical_score DECIMAL(5, 2) DEFAULT 0,        -- Исторические паттерны
    network_score DECIMAL(5, 2) DEFAULT 0,           -- Сетевой анализ

    feature_vector JSONB,                            -- Вектор признаков (50+)
    shap_values JSONB,                               -- SHAP объяснения
    explanation_text TEXT,                            -- Текстовое объяснение на русском
    model_version VARCHAR(50),
    blockchain_tx_hash VARCHAR(66),                  -- Запись в блокчейн
    analyst_id UUID REFERENCES users(id),
    analyst_override DECIMAL(5, 2),                  -- Ручная корректировка
    analyst_comment TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_risk_procurement ON risk_assessments(procurement_id);
CREATE INDEX idx_risk_level ON risk_assessments(risk_level);
CREATE INDEX idx_risk_score ON risk_assessments(overall_score DESC);
CREATE INDEX idx_risk_created ON risk_assessments(created_at DESC);

-- ============================================================
-- Таблица: anomalies — Обнаруженные аномалии
-- ============================================================
CREATE TABLE anomalies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    procurement_id UUID NOT NULL REFERENCES procurements(id) ON DELETE CASCADE,
    risk_assessment_id UUID REFERENCES risk_assessments(id),
    anomaly_type anomaly_type NOT NULL,
    severity DECIMAL(5, 2) NOT NULL,                -- 0-100
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    evidence JSONB,                                  -- Доказательства (цитаты, числа)
    location_in_document TEXT,                       -- Где обнаружено в документе
    suggested_action TEXT,                           -- Рекомендуемое действие
    is_confirmed BOOLEAN DEFAULT false,
    confirmed_by UUID REFERENCES users(id),
    false_positive BOOLEAN DEFAULT false,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_anomalies_procurement ON anomalies(procurement_id);
CREATE INDEX idx_anomalies_type ON anomalies(anomaly_type);
CREATE INDEX idx_anomalies_severity ON anomalies(severity DESC);

-- ============================================================
-- Таблица: evidence — Доказательства для расследований
-- ============================================================
CREATE TABLE evidence (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    procurement_id UUID REFERENCES procurements(id),
    anomaly_id UUID REFERENCES anomalies(id),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    evidence_type VARCHAR(100),                     -- 'document', 'screenshot', 'analysis_report', 'blockchain_record'
    file_hash VARCHAR(66),                          -- SHA-256 хеш файла
    ipfs_hash VARCHAR(100),                         -- IPFS CID
    blockchain_tx_hash VARCHAR(66),                 -- Транзакция в блокчейне
    status evidence_status DEFAULT 'collected',
    is_frozen BOOLEAN DEFAULT false,                -- Заморожено для расследования
    frozen_at TIMESTAMPTZ,
    frozen_by UUID REFERENCES users(id),
    access_level INTEGER DEFAULT 0,                 -- 0 = public, 1 = analyst, 2 = investigator, 3 = admin
    collected_by UUID REFERENCES users(id),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_evidence_procurement ON evidence(procurement_id);
CREATE INDEX idx_evidence_status ON evidence(status);
CREATE INDEX idx_evidence_frozen ON evidence(is_frozen) WHERE is_frozen = true;

-- ============================================================
-- Таблица: alerts — Уведомления и алерты
-- ============================================================
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    procurement_id UUID REFERENCES procurements(id),
    risk_assessment_id UUID REFERENCES risk_assessments(id),
    alert_type VARCHAR(100) NOT NULL,               -- 'high_risk', 'new_anomaly', 'pattern_detected', 'threshold_exceeded'
    title VARCHAR(500) NOT NULL,
    message TEXT NOT NULL,
    severity risk_level NOT NULL,
    status alert_status DEFAULT 'new',
    assigned_to UUID REFERENCES users(id),
    resolved_at TIMESTAMPTZ,
    resolved_by UUID REFERENCES users(id),
    resolution_notes TEXT,
    notification_sent BOOLEAN DEFAULT false,
    notification_channels JSONB,                    -- ['email', 'telegram', 'sms']
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_alerts_status ON alerts(status);
CREATE INDEX idx_alerts_severity ON alerts(severity);
CREATE INDEX idx_alerts_assigned ON alerts(assigned_to);
CREATE INDEX idx_alerts_created ON alerts(created_at DESC);

-- ============================================================
-- Таблица: whistleblower_reports — Анонимные жалобы
-- ============================================================
CREATE TABLE whistleblower_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tracking_id VARCHAR(20) UNIQUE NOT NULL,        -- Анонимный ID для отслеживания
    encrypted_content TEXT NOT NULL,                 -- PGP-зашифрованное содержание
    encrypted_contact TEXT,                          -- Зашифрованный контакт (опционально)
    procurement_id UUID REFERENCES procurements(id),
    category VARCHAR(100),
    status alert_status DEFAULT 'new',
    assigned_to UUID REFERENCES users(id),
    priority INTEGER DEFAULT 0,
    response_encrypted TEXT,                         -- Зашифрованный ответ
    ip_hash VARCHAR(66),                            -- Хеш IP (не сам IP)
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_whistleblower_tracking ON whistleblower_reports(tracking_id);
CREATE INDEX idx_whistleblower_status ON whistleblower_reports(status);

-- ============================================================
-- Таблица: audit_log — Аудит-лог всех действий
-- ============================================================
CREATE TABLE audit_log (
    id BIGSERIAL,
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    ip_address INET,
    user_agent TEXT,
    request_method VARCHAR(10),
    request_path TEXT,
    request_body JSONB,
    response_status INTEGER,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- Партиции по месяцам (первые 12)
CREATE TABLE audit_log_2025_01 PARTITION OF audit_log FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
CREATE TABLE audit_log_2025_02 PARTITION OF audit_log FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
CREATE TABLE audit_log_2025_03 PARTITION OF audit_log FOR VALUES FROM ('2025-03-01') TO ('2025-04-01');
CREATE TABLE audit_log_2025_04 PARTITION OF audit_log FOR VALUES FROM ('2025-04-01') TO ('2025-05-01');
CREATE TABLE audit_log_2025_05 PARTITION OF audit_log FOR VALUES FROM ('2025-05-01') TO ('2025-06-01');
CREATE TABLE audit_log_2025_06 PARTITION OF audit_log FOR VALUES FROM ('2025-06-01') TO ('2025-07-01');
CREATE TABLE audit_log_2025_07 PARTITION OF audit_log FOR VALUES FROM ('2025-07-01') TO ('2025-08-01');
CREATE TABLE audit_log_2025_08 PARTITION OF audit_log FOR VALUES FROM ('2025-08-01') TO ('2025-09-01');
CREATE TABLE audit_log_2025_09 PARTITION OF audit_log FOR VALUES FROM ('2025-09-01') TO ('2025-10-01');
CREATE TABLE audit_log_2025_10 PARTITION OF audit_log FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');
CREATE TABLE audit_log_2025_11 PARTITION OF audit_log FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');
CREATE TABLE audit_log_2025_12 PARTITION OF audit_log FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');
CREATE TABLE audit_log_2026_01 PARTITION OF audit_log FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
CREATE TABLE audit_log_2026_02 PARTITION OF audit_log FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
CREATE TABLE audit_log_2026_03 PARTITION OF audit_log FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');

CREATE INDEX idx_audit_user ON audit_log(user_id, created_at DESC);
CREATE INDEX idx_audit_resource ON audit_log(resource_type, resource_id);
CREATE INDEX idx_audit_action ON audit_log(action, created_at DESC);

-- ============================================================
-- Таблица: metrics — Временные ряды метрик (TimescaleDB)
-- ============================================================
CREATE TABLE metrics (
    time TIMESTAMPTZ NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DOUBLE PRECISION NOT NULL,
    labels JSONB,
    region VARCHAR(100),
    category VARCHAR(100)
);

SELECT create_hypertable('metrics', 'time');

CREATE INDEX idx_metrics_name ON metrics(metric_name, time DESC);
CREATE INDEX idx_metrics_region ON metrics(region, time DESC);

-- ============================================================
-- Таблица: blockchain_records — Записи блокчейна
-- ============================================================
CREATE TABLE blockchain_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tx_hash VARCHAR(66) UNIQUE NOT NULL,
    block_number BIGINT,
    contract_address VARCHAR(42),
    function_name VARCHAR(100),
    args JSONB,
    related_type VARCHAR(50),                       -- 'procurement', 'risk_assessment', 'evidence'
    related_id UUID,
    gas_used BIGINT,
    status VARCHAR(20) DEFAULT 'pending',           -- 'pending', 'confirmed', 'failed'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_blockchain_tx ON blockchain_records(tx_hash);
CREATE INDEX idx_blockchain_related ON blockchain_records(related_type, related_id);

-- ============================================================
-- Таблица: complaints — Автоматические жалобы
-- ============================================================
CREATE TABLE complaints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    procurement_id UUID NOT NULL REFERENCES procurements(id),
    risk_assessment_id UUID REFERENCES risk_assessments(id),
    complaint_type VARCHAR(100),                    -- 'fas', 'prosecutor', 'regulator'
    recipient VARCHAR(255),                          -- Получатель жалобы
    generated_text TEXT NOT NULL,                    -- Текст жалобы
    anomalies_referenced UUID[],                    -- Ссылки на аномалии
    status VARCHAR(50) DEFAULT 'draft',             -- 'draft', 'ready', 'sent', 'acknowledged'
    sent_at TIMESTAMPTZ,
    response TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_complaints_procurement ON complaints(procurement_id);
CREATE INDEX idx_complaints_status ON complaints(status);

-- ============================================================
-- Представления
-- ============================================================

-- Топ подозрительных закупок
CREATE VIEW v_top_risky_procurements AS
SELECT
    p.id,
    p.title,
    p.customer_name,
    p.customer_region,
    p.initial_price,
    p.publication_date,
    ra.overall_score,
    ra.risk_level,
    ra.explanation_text,
    COUNT(a.id) AS anomaly_count
FROM procurements p
JOIN risk_assessments ra ON ra.procurement_id = p.id
LEFT JOIN anomalies a ON a.procurement_id = p.id
GROUP BY p.id, ra.id
ORDER BY ra.overall_score DESC;

-- Статистика по регионам
CREATE VIEW v_regional_stats AS
SELECT
    p.customer_region,
    COUNT(p.id) AS total_procurements,
    AVG(ra.overall_score) AS avg_risk_score,
    COUNT(CASE WHEN ra.risk_level = 'red' THEN 1 END) AS red_count,
    COUNT(CASE WHEN ra.risk_level = 'orange' THEN 1 END) AS orange_count,
    SUM(p.initial_price) AS total_value
FROM procurements p
LEFT JOIN risk_assessments ra ON ra.procurement_id = p.id
GROUP BY p.customer_region;

-- ============================================================
-- Данные по умолчанию
-- ============================================================
INSERT INTO users (email, password_hash, full_name, role, is_active, is_verified) VALUES
('admin@procurashield.kz', '$2b$12$LJ3m4ys3uz1HF0S1GA/JZOkdKhXtGVKTcUJcI4wY.kJlj4cwaVV2i', 'Администратор', 'admin', true, true),
('analyst@procurashield.kz', '$2b$12$LJ3m4ys3uz1HF0S1GA/JZOkdKhXtGVKTcUJcI4wY.kJlj4cwaVV2i', 'Аналитик', 'analyst', true, true),
('investigator@procurashield.kz', '$2b$12$LJ3m4ys3uz1HF0S1GA/JZOkdKhXtGVKTcUJcI4wY.kJlj4cwaVV2i', 'Следователь', 'investigator', true, true);
