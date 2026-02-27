"""
ProcuraShield — AML (Anti-Money Laundering) детектор
Выявление отмывания денег через государственные закупки.

Анализирует:
- Цепочки субподряда (деньги → аффилированные лица)
- Компании-однодневки
- Дробление закупок
- Сравнение цен с рыночными
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()


class AMLDetector:
    """
    Детектор отмывания денег через госзакупки.
    """

    def __init__(self):
        # Пороги для компаний-однодневок
        self.min_company_age_months = 6
        self.min_authorized_capital = 100_000  # Минимальный уставной капитал (KZT)
        self.min_employees = 3

        # Пороги для дробления
        self.splitting_thresholds = {
            "small": 100_000,       # До 100К — прямая закупка
            "medium": 3_000_000,    # До 3М — упрощённая
            "large": 10_000_000,    # До 10М — конкурс
        }

    def analyze(self, procurement) -> List[Dict[str, Any]]:
        """Полный AML-анализ закупки"""
        anomalies = []

        # 1. Анализ на дробление
        splitting = self._detect_splitting(procurement)
        if splitting:
            anomalies.extend(splitting)

        # 2. Анализ цепочек субподряда
        subcontract = self._detect_subcontract_chains(procurement)
        if subcontract:
            anomalies.extend(subcontract)

        # 3. Проверка на компании-однодневки
        shell = self._detect_shell_companies(procurement)
        if shell:
            anomalies.extend(shell)

        # 4. Ценовые аномалии
        price_anomaly = self._detect_price_anomalies(procurement)
        if price_anomaly:
            anomalies.extend(price_anomaly)

        return anomalies

    def _detect_splitting(self, procurement) -> List[Dict[str, Any]]:
        """
        Детектор дробления закупки.
        Выявляет разбиение крупной закупки на мелкие для обхода
        порогов обязательных процедур.
        """
        anomalies = []
        price = float(procurement.initial_price or 0)

        if price <= 0:
            return anomalies

        # Проверяем близость к пороговым значениям
        for level, threshold in self.splitting_thresholds.items():
            # Цена чуть ниже порога — подозрительно
            if 0.85 * threshold <= price < threshold:
                anomalies.append({
                    "type": "procurement_splitting",
                    "severity": 70.0,
                    "title": "Подозрение на дробление закупки",
                    "description": (
                        f"Цена контракта ({price:,.0f}) находится чуть ниже "
                        f"порогового значения ({threshold:,.0f}). "
                        f"Это может указывать на намеренное дробление закупки "
                        f"для обхода конкурсных процедур."
                    ),
                    "evidence": {
                        "price": price,
                        "threshold": threshold,
                        "level": level,
                        "ratio": round(price / threshold, 4),
                    },
                    "suggested_action": (
                        "Проверить, не было ли у заказчика аналогичных закупок "
                        "в недавнем прошлом (суммарно превышающих порог)."
                    ),
                })

        return anomalies

    def _detect_subcontract_chains(self, procurement) -> List[Dict[str, Any]]:
        """
        Анализ цепочек субподряда.
        Выявляет схемы, где деньги проходят через цепочку
        аффилированных компаний.
        """
        anomalies = []
        
        # ЗАГЛУШКА: В production здесь будет анализ реальных данных
        # о субподрядах из реестра контрактов
        # Логика:
        # 1. Получаем субподрядчиков из реестра
        # 2. Проверяем аффилированность с основным подрядчиком
        # 3. Если > 50% суммы уходит аффилированным — красный флаг

        return anomalies

    def _detect_shell_companies(self, procurement) -> List[Dict[str, Any]]:
        """
        Выявление компаний-однодневок.
        Признаки: возраст < 6 мес, минимальный уставной капитал,
        нет сотрудников, массовый директор/адрес.
        """
        anomalies = []

        # Анализируем поставщиков, участвующих в тендере
        bids = getattr(procurement, 'bids', None) or []

        for bid in bids:
            supplier = getattr(bid, 'supplier', None)
            if not supplier:
                continue

            flags = []
            severity = 0.0

            # Возраст компании
            reg_date = getattr(supplier, 'registration_date', None)
            if reg_date:
                age_days = (datetime.utcnow() - reg_date).days if hasattr(reg_date, 'days') else 0
                if age_days < self.min_company_age_months * 30:
                    flags.append(f"Возраст компании: {age_days} дней (< {self.min_company_age_months} мес)")
                    severity += 30

            # Уставной капитал
            capital = float(getattr(supplier, 'authorized_capital', 0) or 0)
            if 0 < capital < self.min_authorized_capital:
                flags.append(f"Уставной капитал: {capital:,.0f} (минимальный)")
                severity += 20

            # Количество сотрудников
            employees = getattr(supplier, 'employee_count', None)
            if employees is not None and employees < self.min_employees:
                flags.append(f"Сотрудников: {employees}")
                severity += 15

            # Санкционный список
            if getattr(supplier, 'sanctions_listed', False):
                flags.append("Компания в санкционном списке")
                severity += 25

            # PEP связь
            if getattr(supplier, 'pep_associated', False):
                flags.append("Связь с PEP (Politically Exposed Person)")
                severity += 20

            if severity >= 40:
                anomalies.append({
                    "type": "shell_company",
                    "severity": min(severity, 95.0),
                    "title": f"Признаки компании-однодневки: {getattr(supplier, 'name', 'N/A')}",
                    "description": (
                        f"Обнаружены признаки компании-однодневки:\n"
                        + "\n".join(f"  • {f}" for f in flags)
                    ),
                    "evidence": {
                        "supplier_name": getattr(supplier, 'name', 'N/A'),
                        "supplier_inn": getattr(supplier, 'inn', 'N/A'),
                        "flags": flags,
                    },
                    "suggested_action": "Запросить дополнительные документы у поставщика.",
                })

        return anomalies

    def _detect_price_anomalies(self, procurement) -> List[Dict[str, Any]]:
        """
        Сравнение цены контракта с рыночными ценами.
        В production — интеграция с прайс-агрегаторами.
        """
        anomalies = []
        price = float(procurement.initial_price or 0)

        if price <= 0:
            return anomalies

        # Эвристика: слишком круглые цены = «с потолка»
        if price >= 1_000_000 and price % 1_000_000 == 0:
            anomalies.append({
                "type": "price_anomaly",
                "severity": 40.0,
                "title": "Подозрительно круглая цена контракта",
                "description": (
                    f"Начальная (максимальная) цена контракта ({price:,.0f}) "
                    f"является подозрительно круглой. Это может указывать на "
                    f"отсутствие обоснования НМЦК на основе рыночных данных."
                ),
                "evidence": {"price": price},
                "suggested_action": "Запросить обоснование НМЦК.",
            })

        return anomalies
