# 🛡️ ProcuraShield — Интеллектуальная антикоррупционная платформа

## Executive Summary

**ProcuraShield** — это AI-powered платформа для автоматического выявления коррупции, картельных сговоров и манипуляций в государственных закупках. Платформа использует NLP, граф-нейронные сети, блокчейн и поведенческий анализ для обеспечения прозрачности и честной конкуренции.


<div align="center">

# 🛡️ ProcuraShield

### Интеллектуальная антикоррупционная платформа для государственных закупок

**AI + Graph Neural Networks + Blockchain**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Solidity](https://img.shields.io/badge/Solidity-0.8-363636?style=for-the-badge&logo=solidity&logoColor=white)](https://soliditylang.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

[![Stars](https://img.shields.io/github/stars/shadowuneed/ProcuraShield-Goszakup-with-AI-?style=social)](https://github.com/shadowuneed/ProcuraShield-Goszakup-with-AI-/stargazers)
[![Forks](https://img.shields.io/github/forks/shadowuneed/ProcuraShield-Goszakup-with-AI-?style=social)](https://github.com/shadowuneed/ProcuraShield-Goszakup-with-AI-/network/members)

</div>

---

## 🎯 О проекте

**ProcuraShield** — AI-powered платформа для автоматического выявления коррупции, картельных сговоров и манипуляций в государственных закупках.

Платформа объединяет:
- **NLP** — анализ технических спецификаций на «заточку» под конкретного поставщика
- **Graph Neural Networks** — выявление скрытых аффилированностей и картелей
- **Risk Scoring** — многофакторная оценка риска каждой закупки (0–100)
- **Blockchain** — неизменяемый аудит доказательств (Ethereum + IPFS)
- **AML-анализ** — детектирование отмывания денег через госзакупки

> Цель: сделать государственные закупки прозрачными, конкурентными и защищёнными от манипуляций.

---

## ✨ Ключевые возможности

| Модуль | Что делает |
|--------|------------|
| 🔍 **AI-анализ тендеров** | Автоматически находит дискриминационные требования в ТЗ |
| 📊 **Risk Scoring** | Выдаёт оценку риска 0–100 с объяснением |
| 🕸️ **Граф связей** | GNN выявляет аффилированность и картельные схемы |
| ⛓️ **Блокчейн-аудит** | Хеширование документов в Ethereum + IPFS |
| 💰 **AML-детектор** | Находит подозрительные финансовые потоки |
| 🔔 **Real-time алерты** | Мгновенные уведомления о высокорисковых тендерах |
| 📝 **Автожалоба** | Формирование жалобы в ФАС / прокуратуру одной кнопкой |
| 🕵️ **Whistleblower Portal** | Анонимный портал для информаторов |

---

## 🏗️ Архитектура

```text
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js 14 + TypeScript)           │
│     Dashboard  │  Анализ тендера  │  Граф связей  │  Portal     │
└──────────────────────────────┬──────────────────────────────────┘
                               │ REST / WebSocket
┌──────────────────────────────▼──────────────────────────────────┐
│                    API GATEWAY (FastAPI)                        │
│         Auth │ Rate Limiting │ CORS │ Validation                │
└───┬──────────┬──────────┬──────────┬───────────┬────────────────┘
    │          │          │          │           │
┌───▼───┐ ┌───▼───┐ ┌───▼───┐ ┌───▼───┐  ┌───▼────────┐
│ NLP   │ │ Graph │ │ Risk  │ │ AML   │  │ Blockchain │
│Engine │ │Analysr│ │Scorer │ │Detect │  │   Layer    │
└───┬───┘ └───┬───┘ └───┬───┘ └───┬───┘  └───┬────────┘
    │         │         │         │           │
┌───▼─────────▼─────────▼─────────▼───┐  ┌───▼────────┐
│  PostgreSQL + Redis + TimescaleDB   │  │ Ethereum   │
│  Celery + Kafka                     │  │ IPFS       │
└─────────────────────────────────────┘  └────────────┘

### Ключевые возможности

- 🔍 **AI-анализ тендеров** — автоматическое выявление "заточки под поставщика" в технических спецификациях
- 📊 **Risk Scoring** — многофакторная оценка риска каждой закупки (0-100)
- 🕸️ **Граф связей** — выявление аффилированности и картельных сговоров через GNN
- ⛓️ **Блокчейн-аудит** — неизменяемое хранение доказательств в Ethereum + IPFS
- 💰 **AML-анализ** — выявление отмывания денег через госзакупки
- 🔔 **Real-time алерты** — мгновенные уведомления о подозрительных тендерах
- 📝 **Автоматическая жалоба** — формирование жалобы в ФАС/прокуратуру одной кнопкой

### Архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js 14 + TS)                   │
│  Dashboard │ Анализ тендера │ Граф связей │ Whistleblower Portal│
└──────────────────────────┬──────────────────────────────────────┘
                           │ REST / WebSocket
┌──────────────────────────▼──────────────────────────────────────┐
│                    API GATEWAY (FastAPI)                         │
│  Auth │ Rate Limiting │ CORS │ Request Validation               │
└───┬──────────┬──────────┬──────────┬───────────┬────────────────┘
    │          │          │          │           │
┌───▼───┐ ┌───▼───┐ ┌───▼───┐ ┌───▼───┐  ┌───▼────────┐
│ NLP   │ │ Graph │ │ Risk  │ │ AML   │  │ Blockchain │
│Engine │ │Analysr│ │Scorer │ │Detect │  │   Layer    │
└───┬───┘ └───┬───┘ └───┬───┘ └───┬───┘  └───┬────────┘
    │         │         │         │           │
┌───▼─────────▼─────────▼─────────▼───┐  ┌───▼────────┐
│  PostgreSQL + Redis + TimescaleDB   │  │ Ethereum   │
│  Celery + Kafka                     │  │ IPFS       │
└─────────────────────────────────────┘  └────────────┘
```

## 🚀 Быстрый старт (5 минут)

### Предварительные требования
- Docker & Docker Compose
- Node.js 18+ (для фронтенда)
- Python 3.11+ (для бэкенда)
- Git

### Запуск через Docker Compose

```bash
git clone <repo-url> procurashield
cd procurashield

# Скопировать и настроить конфигурацию
cp .env.example .env

# Запустить все сервисы
docker-compose up -d

# Применить миграции БД
docker-compose exec backend alembic upgrade head

# Загрузить демо-данные
docker-compose exec backend python -m scripts.seed_data
```

Откройте:
- **Frontend**: http://localhost:3100
- **API Docs**: http://localhost:8100/docs
- **Grafana**: http://localhost:3101

### Локальная разработка

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8100

# Frontend
cd frontend
npm install
npm run dev
```

### Демо-аккаунты

| Роль | Email | Пароль |
|------|-------|--------|
| Admin | admin@procurashield.kz | admin123! |
| Analyst | analyst@procurashield.kz | analyst123! |
| Investigator | investigator@procurashield.kz | invest123! |

## 📁 Структура проекта

```
goszakup/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Конфигурация, безопасность
│   │   ├── models/         # SQLAlchemy модели
│   │   ├── schemas/        # Pydantic схемы
│   │   ├── services/       # Бизнес-логика
│   │   └── workers/        # Celery задачи
│   ├── ai/                 # AI/ML модули
│   │   ├── nlp/            # NLP анализ тендеров
│   │   ├── graph/          # Граф-анализ связей
│   │   ├── risk/           # Risk scoring
│   │   ├── collusion/      # Anti-collusion детектор
│   │   └── aml/            # AML анализ
│   ├── blockchain/         # Web3 интеграция
│   ├── integrations/       # Внешние API
│   └── tests/              # Тесты
├── frontend/               # Next.js 14 frontend
│   ├── src/
│   │   ├── app/            # App Router
│   │   ├── components/     # React компоненты
│   │   ├── lib/            # Утилиты
│   │   └── types/          # TypeScript типы
│   └── public/
├── contracts/              # Solidity смарт-контракты
├── docker/                 # Docker конфиги
├── k8s/                    # Kubernetes манифесты
├── scripts/                # Утилитарные скрипты
└── docs/                   # Документация
```

## 🏗️ Roadmap

### MVP (Хакатон — 48 часов)
- [x] NLP-анализ тендерных спецификаций
- [x] Risk Scoring (базовый)
- [x] Блокчейн хеширование документов
- [x] Dashboard с картой рисков
- [x] API для загрузки и анализа тендеров

### v1.0 (3 месяца)
- [ ] Граф-анализ связей с GNN
- [ ] Anti-collusion detection
- [ ] Интеграция с ЕИС/ФНС
- [ ] Telegram-бот для алертов
- [ ] Whistleblower portal с PGP

### v2.0 (6 месяцев)
- [ ] Предиктивный анализ победителей
- [ ] NFT-сертификат чистой закупки
- [ ] Zero-knowledge proofs
- [ ] Международная адаптация (Узбекистан, Кыргызстан)
- [ ] Мобильное приложение

## 🏆 Почему это революционно

1. **Единственная платформа** с полным AI+Blockchain пайплайном для госзакупок
2. **Объяснимый AI** — каждое решение объясняется простым языком
3. **Децентрализация** — невозможно подделать результаты анализа
4. **7 типов детекторов** аномалий в тендерных спецификациях
5. **Граф-нейронные сети** для выявления скрытых связей
6. **Автоматическая жалоба** в ФАС одним кликом
7. **Стилометрия** — определение авторства документов

## 📜 Лицензия

MIT License — свободное использование для государственных нужд.
