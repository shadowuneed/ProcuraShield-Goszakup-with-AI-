"""
ProcuraShield — Детектор картельных сговоров
Поведенческий анализ торгов (Anti-Collusion Detection)

Выявление:
- Bid suppression (подавление конкуренции)
- Bid rotation (ротация победителей)
- Market allocation (разделение рынка)
- Cover bidding (фиктивные заявки)
"""

import math
from typing import List, Dict, Any, Optional
from collections import defaultdict, Counter
import structlog

logger = structlog.get_logger()


class CollusionDetector:
    """
    Детектор картельных сговоров.
    Анализирует паттерны участия и побед в тендерах.
    """

    def __init__(self):
        # Пороговые значения для детекции
        self.rotation_threshold = 0.7       # Доля поочерёдных побед
        self.cv_threshold = 0.05            # Порог коэффициента вариации цен
        self.win_rate_threshold = 0.8       # Подозрительная win rate
        self.allocation_threshold = 0.9     # Порог разделения рынка

    def analyze_procurement(self, procurement) -> List[Dict[str, Any]]:
        """
        Анализ закупки на признаки сговора.
        Использует данные о заявках и исторические данные.
        """
        anomalies = []
        bids = getattr(procurement, 'bids', None) or []

        if len(bids) < 2:
            return anomalies

        # 1. Анализ ценового поведения
        price_anomalies = self._analyze_bid_prices(bids, procurement)
        anomalies.extend(price_anomalies)

        # 2. Cover bidding
        cover_anomalies = self._detect_cover_bidding(bids, procurement)
        anomalies.extend(cover_anomalies)

        return anomalies

    def analyze_historical(
        self,
        bids_history: List[Dict[str, Any]],
        category: Optional[str] = None,
        region: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Анализ исторических данных для выявления:
        - Bid rotation
        - Market allocation
        - Bid suppression
        """
        anomalies = []

        if len(bids_history) < 5:
            return anomalies

        # 1. Bid Rotation — поочерёдные победы
        rotation_result = self._detect_bid_rotation(bids_history)
        if rotation_result:
            anomalies.extend(rotation_result)

        # 2. Market Allocation — разделение рынка
        allocation_result = self._detect_market_allocation(bids_history)
        if allocation_result:
            anomalies.extend(allocation_result)

        # 3. Bid Suppression — подавление конкуренции
        suppression_result = self._detect_bid_suppression(bids_history)
        if suppression_result:
            anomalies.extend(suppression_result)

        return anomalies

    def _analyze_bid_prices(
        self,
        bids: list,
        procurement
    ) -> List[Dict[str, Any]]:
        """
        Анализ ценового поведения участников.
        Низкий коэффициент вариации цен = признак сговора.
        """
        anomalies = []
        prices = []

        for bid in bids:
            price = getattr(bid, 'bid_price', None)
            if price and float(price) > 0:
                prices.append(float(price))

        if len(prices) < 2:
            return anomalies

        # Коэффициент вариации
        mean_price = sum(prices) / len(prices)
        variance = sum((p - mean_price) ** 2 for p in prices) / len(prices)
        std_dev = math.sqrt(variance)
        cv = std_dev / mean_price if mean_price > 0 else 0

        if cv < self.cv_threshold and len(prices) >= 3:
            anomalies.append({
                "type": "cover_bidding",
                "severity": 75.0,
                "title": "Подозрительно близкие цены участников",
                "description": (
                    f"Коэффициент вариации цен заявок составляет {cv:.4f} "
                    f"(порог: {self.cv_threshold}). Средняя цена: {mean_price:,.0f}. "
                    f"Такое совпадение цен может указывать на ценовой сговор."
                ),
                "evidence": {
                    "prices": prices,
                    "cv": round(cv, 4),
                    "mean": round(mean_price, 2),
                    "std_dev": round(std_dev, 2),
                },
                "suggested_action": "Проверить участников на аффилированность.",
            })

        # Проверяем, есть ли заведомо завышенные заявки
        initial_price = float(procurement.initial_price or 0)
        if initial_price > 0:
            close_to_max = [p for p in prices if p > 0.95 * initial_price]
            if len(close_to_max) >= len(prices) - 1 and len(prices) >= 3:
                anomalies.append({
                    "type": "bid_suppression",
                    "severity": 80.0,
                    "title": "Заведомо завышенные заявки (Bid Suppression)",
                    "description": (
                        f"{len(close_to_max)} из {len(prices)} заявок поданы "
                        f"с ценой выше 95% от НМЦК. Это может указывать на "
                        f"координированную подачу «заведомо проигрышных» заявок."
                    ),
                    "evidence": {
                        "prices_close_to_max": close_to_max,
                        "initial_price": initial_price,
                    },
                    "suggested_action": "Расследовать связи между участниками.",
                })

        return anomalies

    def _detect_cover_bidding(
        self,
        bids: list,
        procurement
    ) -> List[Dict[str, Any]]:
        """
        Cover Bidding: подача заведомо проигрышных заявок для видимости конкуренции.
        Признаки: заявка с незначительно более высокой ценой, заявка с условиями заведомого отказа.
        """
        anomalies = []

        initial_price = float(procurement.initial_price or 0)
        if initial_price <= 0 or len(bids) < 3:
            return anomalies

        winner_price = None
        other_prices = []
        disqualified_count = 0

        for bid in bids:
            if getattr(bid, 'is_winner', False):
                winner_price = float(getattr(bid, 'bid_price', 0) or 0)
            else:
                price = float(getattr(bid, 'bid_price', 0) or 0)
                if price > 0:
                    other_prices.append(price)
            if getattr(bid, 'disqualified', False):
                disqualified_count += 1

        # Если есть победитель и другие цены минимально выше
        if winner_price and other_prices:
            margins = [(p - winner_price) / winner_price for p in other_prices if p >= winner_price]
            small_margins = [m for m in margins if 0 < m < 0.03]  # Менее 3% разница

            if len(small_margins) > 0 and len(small_margins) >= len(margins) * 0.5:
                anomalies.append({
                    "type": "cover_bidding",
                    "severity": 70.0,
                    "title": "Признаки Cover Bidding",
                    "description": (
                        f"Цены проигравших участников минимально выше цены победителя "
                        f"(разница менее 3%). Это характерный признак cover bidding — "
                        f"подачи заведомо проигрышных заявок для создания видимости конкуренции."
                    ),
                    "evidence": {
                        "winner_price": winner_price,
                        "other_prices": other_prices,
                        "margins": [round(m * 100, 2) for m in margins],
                    },
                    "suggested_action": "Проверить участников на общих директоров/учредителей.",
                })

        return anomalies

    def _detect_bid_rotation(
        self,
        bids_history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Bid Rotation: поочерёдные победы компаний в тендерах одной категории.
        Выявляет паттерн A→B→A→B→A...
        """
        anomalies = []

        # Группируем по категории/заказчику
        by_customer = defaultdict(list)
        for bid in bids_history:
            if bid.get("is_winner"):
                key = bid.get("customer_inn", "unknown")
                by_customer[key].append(bid.get("supplier_inn", ""))

        for customer, winners in by_customer.items():
            if len(winners) < 4:
                continue

            # Проверяем паттерн ротации
            unique_winners = list(set(winners))
            if 2 <= len(unique_winners) <= 3:
                # Считаем количество «переключений»
                switches = sum(1 for i in range(1, len(winners)) if winners[i] != winners[i - 1])
                switch_rate = switches / (len(winners) - 1)

                if switch_rate > self.rotation_threshold:
                    anomalies.append({
                        "type": "bid_rotation",
                        "severity": 85.0,
                        "title": "Обнаружен паттерн ротации победителей (Bid Rotation)",
                        "description": (
                            f"У заказчика {customer} выявлен паттерн поочерёдных побед: "
                            f"{len(unique_winners)} компании чередуются как победители "
                            f"({switch_rate:.0%} переключений). "
                            f"Это классический признак картельного сговора."
                        ),
                        "evidence": {
                            "customer": customer,
                            "winner_sequence": winners[:10],
                            "unique_winners": unique_winners,
                            "switch_rate": round(switch_rate, 2),
                        },
                        "suggested_action": "Провести расследование возможного картеля.",
                    })

        return anomalies

    def _detect_market_allocation(
        self,
        bids_history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Market Allocation: разделение рынка по регионам или категориям.
        Каждая компания побеждает только в «своём» регионе/категории.
        """
        anomalies = []

        # Группируем победы по поставщикам
        wins_by_supplier = defaultdict(lambda: defaultdict(int))
        for bid in bids_history:
            if bid.get("is_winner"):
                supplier = bid.get("supplier_inn", "")
                region = bid.get("region", "unknown")
                wins_by_supplier[supplier][region] += 1

        # Проверяем, концентрируются ли победы в одном регионе
        for supplier, regions in wins_by_supplier.items():
            total_wins = sum(regions.values())
            if total_wins < 3:
                continue

            max_region_wins = max(regions.values())
            concentration = max_region_wins / total_wins

            if concentration > self.allocation_threshold:
                main_region = max(regions, key=regions.get)
                anomalies.append({
                    "type": "market_allocation",
                    "severity": 70.0,
                    "title": "Признаки разделения рынка (Market Allocation)",
                    "description": (
                        f"Поставщик {supplier} побеждает преимущественно в одном регионе "
                        f"({main_region}): {concentration:.0%} побед. "
                        f"Это может указывать на разделение рынка между участниками картеля."
                    ),
                    "evidence": {
                        "supplier": supplier,
                        "region_distribution": dict(regions),
                        "concentration": round(concentration, 2),
                    },
                    "suggested_action": "Проверить, есть ли аналогичный паттерн у других поставщиков.",
                })

        return anomalies

    def _detect_bid_suppression(
        self,
        bids_history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Bid Suppression: намеренный отказ от участия для обеспечения победы «назначенного» участника.
        Проверяем, систематически ли компании НЕ участвуют в тендерах друг друга.
        """
        anomalies = []

        # Строим матрицу совместного участия
        procurement_participants = defaultdict(set)
        for bid in bids_history:
            proc_id = bid.get("procurement_id", "")
            supplier = bid.get("supplier_inn", "")
            procurement_participants[proc_id].add(supplier)

        # Подсчёт количества совместных участий пар
        all_suppliers = set()
        for participants in procurement_participants.values():
            all_suppliers.update(participants)

        pair_cooccurrence = Counter()
        pair_total = Counter()

        suppliers_list = list(all_suppliers)
        for i, s1 in enumerate(suppliers_list):
            for s2 in suppliers_list[i + 1:]:
                for proc_id, participants in procurement_participants.items():
                    if s1 in participants or s2 in participants:
                        pair_total[(s1, s2)] += 1
                    if s1 in participants and s2 in participants:
                        pair_cooccurrence[(s1, s2)] += 1

        # Пары, которые НИКОГДА не участвуют вместе
        for pair, total in pair_total.items():
            if total >= 5 and pair_cooccurrence.get(pair, 0) == 0:
                anomalies.append({
                    "type": "bid_suppression",
                    "severity": 65.0,
                    "title": "Подозрение на Bid Suppression",
                    "description": (
                        f"Компании {pair[0]} и {pair[1]} никогда не участвуют "
                        f"в одних тендерах (0 из {total} возможных). "
                        f"Это может указывать на координированный отказ от участия."
                    ),
                    "evidence": {
                        "supplier_1": pair[0],
                        "supplier_2": pair[1],
                        "total_opportunities": total,
                        "cooccurrences": 0,
                    },
                    "suggested_action": "Проверить аффилированность компаний.",
                })

        return anomalies
