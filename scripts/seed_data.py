"""
Скрипт генерации демо-данных для ProcuraShield.
Создаёт 10 синтетических тендеров с различными уровнями риска.
"""
import asyncio
import hashlib
import random
from datetime import datetime, timedelta

import asyncpg

# Настройки подключения
DB_URL = "postgresql://procurashield:procurashield_pass@localhost:5432/procurashield"


DEMO_ORGANIZATIONS = [
    "АО «КазАвтоЖол»",
    "Управление здравоохранения г.Алматы",
    "Акимат Караганды",
    "МЦР РК",
    "Акимат Шымкента",
    "МОН РК",
    "Акимат Астаны",
    "КГП «Водоканал»",
    "ТОО «СпецСтройМонтаж»",
    "Акимат Атырау",
]

DEMO_TENDERS = [
    {
        "number": "ГЗ-2024-001234",
        "title": "Строительство автомобильной дороги Астана-Щучинск, участок 45-67 км",
        "description": """Техническая спецификация: Требуется поставка и монтаж оборудования
        марки Caterpillar серии CAT 345 GC. Альтернативы не допускаются.
        Подрядчик должен иметь сертификат ISO/IEC 27701:2019.
        Срок выполнения: 15 календарных дней.
        Обязательно наличие офиса в городе Астана.""",
        "organization": "АО «КазАвтоЖол»",
        "amount": 2_450_000_000,
        "region": "Астана",
    },
    {
        "number": "ГЗ-2024-001235",
        "title": "Поставка медицинского оборудования для городских поликлиник",
        "description": """Требуется поставка аппаратов МРТ марки Siemens MAGNETOM Sola 1.5T.
        Эквиваленты NOT допустимы. Поставщик обязан иметь опыт работы не менее 15 лет.
        Обязательна регистрация в г.Алматы. Срок: 10 рабочих дней.""",
        "organization": "Управление здравоохранения г.Алматы",
        "amount": 890_000_000,
        "region": "Алматы",
    },
    {
        "number": "ГЗ-2024-001236",
        "title": "Капитальный ремонт средней школы №45 г.Караганды",
        "description": """Капремонт здания школы. Площадь 4500 кв.м.
        Требуется опыт аналогичных работ от 10 лет. Только компании
        зарегистрированные в Карагандинской области.""",
        "organization": "Акимат Караганды",
        "amount": 345_000_000,
        "region": "Караганда",
    },
    {
        "number": "ГЗ-2024-001237",
        "title": "Закупка программного обеспечения для ГИС «Электронное правительство»",
        "description": """Внедрение ERP-системы SAP S/4HANA. Подрядчик должен быть
        сертифицированным партнёром SAP уровня Gold. Требуется сертификат
        ISO 9001:2015, ISO 27001:2013, ISO/IEC 27701:2019.
        Срок внедрения: 20 рабочих дней.""",
        "organization": "МЦР РК",
        "amount": 567_000_000,
        "region": "Астана",
    },
    {
        "number": "ГЗ-2024-001238",
        "title": "Благоустройство центрального парка Независимости г.Шымкент",
        "description": """Благоустройство территории парка площадью 12 га.
        Работы включают укладку тротуарной плитки, озеленение,
        установку освещения. Стандартные требования.""",
        "organization": "Акимат Шымкента",
        "amount": 234_000_000,
        "region": "Шымкент",
    },
    {
        "number": "ГЗ-2024-001239",
        "title": "Поставка канцелярских товаров для нужд МОН РК",
        "description": """Поставка бумаги А4 (5000 пачек), ручек шариковых (2000 шт),
        папок-регистраторов (1000 шт). Стандартные канцтовары.""",
        "organization": "МОН РК",
        "amount": 15_000_000,
        "region": "Астана",
    },
    {
        "number": "ГЗ-2024-001240",
        "title": "Реконструкция водоочистных сооружений г.Атырау",
        "description": """Реконструкция с заменой фильтровального оборудования.
        Только оборудование производства SUEZ Water Technologies.
        Обязательно присутствие на территории Атырауской области.
        Минимальный штат — 200 сотрудников.""",
        "organization": "Акимат Атырау",
        "amount": 1_780_000_000,
        "region": "Атырау",
    },
    {
        "number": "ГЗ-2024-001241",
        "title": "Поставка школьного питания на 2024-2025 учебный год",
        "description": """Обеспечение горячим питанием учащихся 120 школ города.
        Требования согласно СанПиН. Стандартный конкурс.""",
        "organization": "Акимат Астаны",
        "amount": 2_100_000_000,
        "region": "Астана",
    },
    {
        "number": "ГЗ-2024-001242",
        "title": "Строительство ливневой канализации, 3-й микрорайон",
        "description": """Прокладка ливневых коллекторов общей длиной 12 км.
        Использовать только трубы диаметром 1200мм производства Hakan Plastik (Турция).
        Срок: 30 календарных дней. Субподряд запрещён.""",
        "organization": "КГП «Водоканал»",
        "amount": 456_000_000,
        "region": "Караганда",
    },
    {
        "number": "ГЗ-2024-001243",
        "title": "Техническое обслуживание системы видеонаблюдения",
        "description": """ТО системы видеонаблюдения (450 камер).
        Стандартные работы: чистка, настройка, замена неисправных.
        Годовой контракт.""",
        "organization": "Акимат Шымкента",
        "amount": 45_000_000,
        "region": "Шымкент",
    },
]

DEMO_SUPPLIERS = [
    {"bin": "120540004567", "name": 'ТОО "СтройИнвест KZ"', "director": "Иванов Иван Иванович", "address": "г.Астана, ул.Кенесары 40", "phone": "+7-717-255-1234", "employees": 150, "capital": 50_000_000, "founded": "2012-05-15"},
    {"bin": "150340008901", "name": 'ТОО "МегаСтрой"', "director": "Иванов Пётр Иванович", "address": "г.Астана, ул.Кенесары 40", "phone": "+7-717-255-1235", "employees": 12, "capital": 1_000_000, "founded": "2023-09-01"},
    {"bin": "090140001234", "name": 'ТОО "АльфаТрейд"', "director": "Петров Сергей Николаевич", "address": "г.Алматы, ул.Абая 150", "phone": "+7-727-123-4567", "employees": 85, "capital": 30_000_000, "founded": "2009-01-20"},
    {"bin": "180640005678", "name": 'ТОО "БетаСервис"', "director": "Сидоров Алексей Дмитриевич", "address": "г.Караганда, ул.Бухар-Жырау 25", "phone": "+7-721-345-6789", "employees": 45, "capital": 15_000_000, "founded": "2018-06-10"},
    {"bin": "200140009999", "name": 'ТОО "ГаммаТех"', "director": "Козлов Дмитрий Петрович", "address": "г.Астана, ул.Туран 55", "phone": "+7-717-100-0001", "employees": 5, "capital": 500_000, "founded": "2023-11-20"},
]


async def seed_database():
    """Заполнить БД демо-данными."""
    conn = await asyncpg.connect(DB_URL)

    try:
        print("🔹 Создание поставщиков...")
        for s in DEMO_SUPPLIERS:
            await conn.execute(
                """
                INSERT INTO suppliers (bin_iin, name, address, phone, director_name,
                                       registration_date, employee_count, authorized_capital)
                VALUES ($1, $2, $3, $4, $5, $6::date, $7, $8)
                ON CONFLICT (bin_iin) DO NOTHING
                """,
                s["bin"], s["name"], s["address"], s["phone"], s["director"],
                s["founded"], s["employees"], s["capital"],
            )

        print("🔹 Создание закупок...")
        for t in DEMO_TENDERS:
            doc_hash = hashlib.sha256(t["description"].encode()).hexdigest()
            published = datetime.now() - timedelta(days=random.randint(1, 30))

            proc_id = await conn.fetchval(
                """
                INSERT INTO procurements (number, title, description, organization,
                                         amount, currency, region, status,
                                         document_hash, published_at)
                VALUES ($1, $2, $3, $4, $5, 'KZT', $6, 'active', $7, $8)
                RETURNING id
                """,
                t["number"], t["title"], t["description"], t["organization"],
                t["amount"], t["region"], doc_hash, published,
            )

            # Создание заявок (бидов)
            num_bids = random.randint(2, 5)
            supplier_indices = random.sample(range(len(DEMO_SUPPLIERS)), min(num_bids, len(DEMO_SUPPLIERS)))

            for idx, si in enumerate(supplier_indices):
                supplier = DEMO_SUPPLIERS[si]
                # Цена: базовая +/- 10%
                price = t["amount"] * random.uniform(0.85, 1.05)
                is_winner = idx == 0

                await conn.execute(
                    """
                    INSERT INTO bids (procurement_id, supplier_bin, price, is_winner)
                    VALUES ($1, $2, $3, $4)
                    """,
                    proc_id, supplier["bin"], price, is_winner,
                )

            print(f"  ✓ {t['number']}: {t['title'][:50]}... ({num_bids} заявок)")

        print("🔹 Создание алертов...")
        alerts = [
            ("Обнаружен картельный сговор", "Три компании подали одинаковые заявки с ценами в пределах 1%", "critical", "collusion"),
            ("Гиперспецифичная спецификация", "Указан конкретный бренд Caterpillar без допуска аналогов", "high", "spec_anomaly"),
            ("Аффилированные участники", "Директора двух компаний-участников зарегистрированы по одному адресу", "high", "affiliation"),
            ("Дробление платежей", "7 платежей за 24 часа на общую сумму 15 млн тенге", "medium", "aml"),
            ("Нереалистичные сроки", "Срок 15 дней для строительства автодороги", "medium", "deadline"),
            ("Компания-однодневка", "Победитель зарегистрирован 2 месяца назад, уставный капитал минимальный", "high", "shell_company"),
        ]

        proc_ids = await conn.fetch("SELECT id FROM procurements ORDER BY id LIMIT 10")
        for i, (title, desc, severity, atype) in enumerate(alerts):
            pid = proc_ids[i % len(proc_ids)]["id"]
            await conn.execute(
                """
                INSERT INTO alerts (procurement_id, title, description, severity, alert_type, status)
                VALUES ($1, $2, $3, $4, $5, 'new')
                """,
                pid, title, desc, severity, atype,
            )

        print("\n✅ Демо-данные успешно загружены!")
        print(f"   Поставщиков: {len(DEMO_SUPPLIERS)}")
        print(f"   Тендеров: {len(DEMO_TENDERS)}")
        print(f"   Алертов: {len(alerts)}")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(seed_database())
