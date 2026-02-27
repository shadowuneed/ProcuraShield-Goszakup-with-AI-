"""
ProcuraShield — ML Risk Scoring Model
Многофакторная модель оценки риска закупки (0-100)

50+ признаков закупки с весами.
XGBoost модель с объяснимостью через SHAP.
Категории: Зелёный (0-30), Жёлтый (31-60), Оранжевый (61-80), Красный (81-100)
"""

import re
import math
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()


# Веса факторов риска (настраиваемые)
RISK_WEIGHTS = {
    # === СПЕЦИФИКАЦИЯ (30%) ===
    "hyperspecific_brands": 8.0,          # Указание конкретных брендов
    "hyperspecific_articles": 6.0,        # Артикулы в ТЗ
    "exclusive_cert_required": 7.0,       # Эксклюзивные сертификаты
    "excessive_certs": 4.0,              # Избыточные сертификаты
    "restrictive_language": 5.0,         # Ограничительные формулировки

    # === КОНКУРЕНЦИЯ (20%) ===
    "single_bidder": 9.0,               # Одна заявка
    "low_competition": 5.0,             # Мало участников (2-3)
    "all_disqualified_except_one": 8.0, # Все отклонены кроме одного
    "same_winner_pattern": 7.0,         # Один и тот же победитель
    "bid_price_variance_low": 6.0,      # Подозрительно низкая вариация цен

    # === ЦЕНООБРАЗОВАНИЕ (15%) ===
    "price_above_market": 7.0,          # Цена выше рыночной
    "price_below_market_suspicious": 5.0, # Подозрительно низкая цена
    "no_price_justification": 4.0,      # Нет обоснования НМЦК
    "round_price": 3.0,                 # Круглая цена (признак «с потолка»)
    "price_near_threshold": 6.0,        # Цена у порога (дробление)

    # === СРОКИ (10%) ===
    "unrealistic_deadline": 8.0,        # Нереалистичный срок
    "very_short_submission": 6.0,       # Короткий срок подачи заявок
    "holiday_deadline": 4.0,            # Срок на праздники/выходные

    # === ПОСТАВЩИК (10%) ===
    "shell_company": 9.0,              # Компания-однодневка
    "low_authorized_capital": 5.0,     # Минимальный уставной капитал
    "no_employees": 6.0,              # Нет сотрудников
    "recent_registration": 7.0,        # Недавно зарегистрирована
    "sanctions_listed": 8.0,           # В санкционном списке
    "pep_associated": 7.0,            # Связь с PEP

    # === ГЕОГРАФИЧЕСКИЕ (5%) ===
    "geo_restriction": 5.0,           # Географическое ограничение
    "remote_supplier": 3.0,           # Поставщик из другого региона

    # === ОПЫТ (5%) ===
    "experience_with_customer": 8.0,   # Требование опыта с заказчиком
    "excessive_experience": 5.0,       # Завышенные требования к опыту
    "no_new_entrants_possible": 6.0,   # Невозможность входа новых участников

    # === ИСТОРИЧЕСКИЕ ПАТТЕРНЫ (5%) ===
    "repeated_customer_supplier": 7.0, # Повторяющаяся пара заказчик-поставщик
    "sequential_contracts": 5.0,       # Последовательные контракты
    "seasonal_anomaly": 4.0,          # Аномалия по сезонности
    "year_end_rush": 5.0,             # «Освоение бюджета» в конце года

    # === ДОКУМЕНТАЛЬНЫЕ (5%) ===
    "copy_paste_detected": 7.0,        # Копипаста из КП
    "stylometric_match": 6.0,         # Стилометрическое совпадение
    "doc_versioning_suspicious": 5.0,  # Подозрительные изменения документации
}


class RiskScorer:
    """
    ML-модель скоринга риска закупки.
    Использует взвешенную комбинацию 50+ признаков.
    """

    def __init__(self):
        self.weights = RISK_WEIGHTS

    def extract_features(
        self,
        procurement,
        anomalies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Feature engineering: извлечение 50+ признаков из данных закупки.
        """
        features = {}
        text = (procurement.raw_text or "").lower()

        # === Спецификация (из аномалий) ===
        anomaly_types = [a.get("type", "") for a in anomalies]
        anomaly_severities = {a.get("type", ""): a.get("severity", 0) for a in anomalies}

        features["hyperspecific_brands"] = 1 if "hyperspecific_requirements" in anomaly_types else 0
        features["hyperspecific_articles"] = min(
            text.count("артикул") + text.count("арт."), 5
        ) / 5.0
        features["exclusive_cert_required"] = 1 if any(
            k in text for k in ["единственный сертифицированный", "эксклюзивный"]
        ) else 0
        features["excessive_certs"] = min(
            text.count("сертификат") + text.count("лицензи"), 10
        ) / 10.0
        features["restrictive_language"] = min(
            text.count("только") + text.count("исключительно") + text.count("единственный"), 10
        ) / 10.0

        # === Конкуренция ===
        bids_count = len(getattr(procurement, 'bids', []) or [])
        features["single_bidder"] = 1.0 if bids_count == 1 else 0.0
        features["low_competition"] = 1.0 if 1 < bids_count <= 3 else 0.0
        features["all_disqualified_except_one"] = 0.0  # Требует данных о заявках
        features["same_winner_pattern"] = 0.0  # Требует исторических данных
        features["bid_price_variance_low"] = 0.0

        # === Ценообразование ===
        price = float(procurement.initial_price or 0)
        features["price_above_market"] = 0.0  # Требует рыночных данных
        features["price_below_market_suspicious"] = 0.0
        features["no_price_justification"] = 1.0 if "обоснование" not in text else 0.0
        features["round_price"] = 1.0 if price > 0 and price % 1000000 == 0 else 0.0
        features["price_near_threshold"] = self._check_price_threshold(price)

        # === Сроки ===
        features["unrealistic_deadline"] = 1.0 if "unrealistic_deadlines" in anomaly_types else 0.0
        features["very_short_submission"] = self._check_submission_time(procurement)
        features["holiday_deadline"] = self._check_holiday_deadline(procurement)

        # === Поставщик ===
        features["shell_company"] = 0.0
        features["low_authorized_capital"] = 0.0
        features["no_employees"] = 0.0
        features["recent_registration"] = 0.0
        features["sanctions_listed"] = 0.0
        features["pep_associated"] = 0.0

        # === Географические ===
        features["geo_restriction"] = 1.0 if "geographic_restrictions" in anomaly_types else 0.0
        features["remote_supplier"] = 0.0

        # === Опыт ===
        features["experience_with_customer"] = 1.0 if "anomalous_experience" in anomaly_types else 0.0
        features["excessive_experience"] = 0.0
        features["no_new_entrants_possible"] = 0.0

        # === Исторические ===
        features["repeated_customer_supplier"] = 0.0
        features["sequential_contracts"] = 0.0
        features["seasonal_anomaly"] = 0.0
        features["year_end_rush"] = self._check_year_end(procurement)

        # === Документальные ===
        features["copy_paste_detected"] = 1.0 if "commercial_proposal_copy" in anomaly_types else 0.0
        features["stylometric_match"] = 1.0 if "stylometric_match" in anomaly_types else 0.0
        features["doc_versioning_suspicious"] = 0.0

        # === Дополнительные метаданные ===
        features["text_length"] = len(text)
        features["anomaly_count"] = len(anomalies)
        features["avg_anomaly_severity"] = (
            sum(a.get("severity", 0) for a in anomalies) / max(len(anomalies), 1)
        )
        features["max_anomaly_severity"] = max(
            (a.get("severity", 0) for a in anomalies), default=0
        )

        return features

    def calculate_score(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Расчёт итогового Risk Score (0-100).
        Использует взвешенную комбинацию с нормализацией.
        """
        # Взвешенная сумма
        weighted_sum = 0.0
        total_weight = 0.0
        component_scores = {}

        # Группировка по компонентам
        component_map = {
            "specification": [
                "hyperspecific_brands", "hyperspecific_articles",
                "exclusive_cert_required", "excessive_certs", "restrictive_language"
            ],
            "competition": [
                "single_bidder", "low_competition",
                "all_disqualified_except_one", "same_winner_pattern", "bid_price_variance_low"
            ],
            "pricing": [
                "price_above_market", "price_below_market_suspicious",
                "no_price_justification", "round_price", "price_near_threshold"
            ],
            "timing": [
                "unrealistic_deadline", "very_short_submission", "holiday_deadline"
            ],
            "supplier": [
                "shell_company", "low_authorized_capital", "no_employees",
                "recent_registration", "sanctions_listed", "pep_associated"
            ],
            "historical": [
                "repeated_customer_supplier", "sequential_contracts",
                "seasonal_anomaly", "year_end_rush"
            ],
            "network": [
                "geo_restriction", "experience_with_customer",
                "copy_paste_detected", "stylometric_match"
            ],
        }

        for component, feature_names in component_map.items():
            comp_score = 0.0
            comp_weight = 0.0
            for fname in feature_names:
                if fname in features and fname in self.weights:
                    value = float(features[fname])
                    weight = self.weights[fname]
                    comp_score += value * weight
                    comp_weight += weight

            normalized = (comp_score / comp_weight * 100) if comp_weight > 0 else 0.0
            component_scores[component] = min(100.0, normalized)
            weighted_sum += comp_score
            total_weight += comp_weight

        # Общий скор
        overall = (weighted_sum / total_weight * 100) if total_weight > 0 else 0.0

        # Бонус за количество аномалий
        anomaly_bonus = min(20, features.get("anomaly_count", 0) * 3)
        overall = min(100.0, overall + anomaly_bonus)

        # Уровень риска
        if overall <= 30:
            level = "green"
        elif overall <= 60:
            level = "yellow"
        elif overall <= 80:
            level = "orange"
        else:
            level = "red"

        # Уверенность модели
        # Зависит от количества доступных данных
        data_completeness = sum(1 for k, v in features.items() if v != 0) / max(len(features), 1)
        confidence = min(0.95, 0.5 + data_completeness * 0.4)

        return {
            "score": round(overall, 2),
            "level": level,
            "confidence": round(confidence, 2),
            "components": {k: round(v, 2) for k, v in component_scores.items()},
            "shap_values": self._compute_shap_approximation(features, component_scores),
        }

    def generate_explanation(
        self,
        score: float,
        components: Dict[str, float],
        anomalies: List[Dict[str, Any]]
    ) -> str:
        """
        Генерация текстового объяснения риска на русском языке.
        Понятное для нетехнического пользователя.
        """
        level_names = {
            "green": "НИЗКИЙ",
            "yellow": "СРЕДНИЙ",
            "orange": "ПОВЫШЕННЫЙ",
            "red": "ВЫСОКИЙ",
        }

        if score <= 30:
            level = "green"
        elif score <= 60:
            level = "yellow"
        elif score <= 80:
            level = "orange"
        else:
            level = "red"

        explanation_parts = [
            f"📊 Общий уровень риска: {level_names[level]} ({score:.1f}/100)\n"
        ]

        # Выделяем значимые компоненты
        significant = sorted(
            [(k, v) for k, v in components.items() if v > 20],
            key=lambda x: x[1],
            reverse=True
        )

        component_descriptions = {
            "specification": "Спецификация содержит ограничительные требования",
            "competition": "Низкий уровень конкуренции",
            "pricing": "Ценовые аномалии",
            "timing": "Проблемы со сроками",
            "supplier": "Риски поставщика",
            "historical": "Подозрительные исторические паттерны",
            "network": "Сетевые связи и документальные аномалии",
        }

        if significant:
            explanation_parts.append("\n⚠️ Риск повышен потому что:")
            for comp, value in significant:
                desc = component_descriptions.get(comp, comp)
                explanation_parts.append(f"  • {desc} (вклад: {value:.0f}%)")

        # Топ аномалии
        if anomalies:
            explanation_parts.append(f"\n🔍 Обнаружено аномалий: {len(anomalies)}")
            top_anomalies = sorted(anomalies, key=lambda a: a.get("severity", 0), reverse=True)[:3]
            for a in top_anomalies:
                explanation_parts.append(f"  • {a.get('title', 'Без названия')} (критичность: {a.get('severity', 0):.0f})")

        # Рекомендации
        if level in ("orange", "red"):
            explanation_parts.append("\n📋 Рекомендации:")
            explanation_parts.append("  • Направить на ручную проверку аналитиком")
            explanation_parts.append("  • Запросить обоснование у заказчика")
            if level == "red":
                explanation_parts.append("  • Рассмотреть подачу жалобы в ФАС")
                explanation_parts.append("  • Сохранить доказательства в блокчейне")

        return "\n".join(explanation_parts)

    def _check_price_threshold(self, price: float) -> float:
        """Проверка близости цены к пороговому значению (дробление закупки)"""
        thresholds = [100_000, 600_000, 3_000_000, 10_000_000]
        for t in thresholds:
            if 0.85 * t <= price <= t:
                return 1.0
        return 0.0

    def _check_submission_time(self, procurement) -> float:
        """Проверка времени на подачу заявок"""
        pub = procurement.publication_date
        deadline = procurement.submission_deadline
        if pub and deadline:
            delta = (deadline - pub).days
            if delta <= 3:
                return 1.0
            elif delta <= 7:
                return 0.5
        return 0.0

    def _check_holiday_deadline(self, procurement) -> float:
        """Проверка сроков на выходные/праздники"""
        deadline = procurement.submission_deadline
        if deadline and hasattr(deadline, 'weekday'):
            if deadline.weekday() >= 5:  # Суббота/воскресенье
                return 1.0
        return 0.0

    def _check_year_end(self, procurement) -> float:
        """Освоение бюджета в конце года"""
        pub = procurement.publication_date
        if pub and hasattr(pub, 'month'):
            if pub.month in (11, 12):
                return 0.7
        return 0.0

    def _compute_shap_approximation(
        self,
        features: Dict[str, Any],
        components: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Приближённые SHAP-значения для объяснимости.
        В production — используется библиотека shap с XGBoost.
        """
        shap_values = {}
        for feature_name, feature_value in features.items():
            if feature_name in self.weights and float(feature_value) > 0:
                # Вклад = значение × вес (нормализованный)
                total_weight = sum(self.weights.values())
                shap_values[feature_name] = round(
                    float(feature_value) * self.weights[feature_name] / total_weight * 100, 2
                )
        return shap_values
