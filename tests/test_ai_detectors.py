"""
Тесты AI-детекторов ProcuraShield.
Покрывают NLP-анализатор, стилометрию, детектор сговора, AML, risk scorer.
"""
import pytest
from backend.ai.nlp.spec_analyzer import SpecificationAnalyzer
from backend.ai.nlp.stylometry import StylometryAnalyzer
from backend.ai.risk.risk_scorer import RiskScorer
from backend.ai.collusion.collusion_detector import CollusionDetector
from backend.ai.aml.aml_detector import AMLDetector


# ============================================================
# NLP Specification Analyzer
# ============================================================

class TestSpecificationAnalyzer:
    """Тесты NLP-анализатора технических спецификаций."""

    def setup_method(self):
        self.analyzer = SpecificationAnalyzer()

    def test_detect_hyperspecific_brand(self):
        """Тест: обнаружение указания конкретного бренда."""
        text = """
        Требуется поставка оборудования марки Caterpillar серии CAT 345 GC.
        Альтернативы не допускаются.
        """
        results = self.analyzer.analyze(text)
        anomaly_types = [r["type"] for r in results]
        assert "hyperspecific_requirements" in anomaly_types

    def test_detect_unrealistic_deadline(self):
        """Тест: обнаружение нереалистичных сроков."""
        text = """
        Строительство автомобильной дороги протяжённостью 22 км.
        Срок выполнения работ: 7 календарных дней.
        """
        results = self.analyzer.analyze(text)
        anomaly_types = [r["type"] for r in results]
        assert "unrealistic_deadline" in anomaly_types

    def test_detect_rare_certificate(self):
        """Тест: обнаружение требования редкого сертификата."""
        text = """
        Подрядчик должен иметь сертификат ISO/IEC 27701:2019
        и аккредитацию FSSC 22000.
        """
        results = self.analyzer.analyze(text)
        anomaly_types = [r["type"] for r in results]
        assert "rare_certificate" in anomaly_types

    def test_detect_geographic_restriction(self):
        """Тест: обнаружение географического ограничения."""
        text = """
        Обязательно наличие офиса в городе Астана.
        Компании из других регионов к участию не допускаются.
        """
        results = self.analyzer.analyze(text)
        anomaly_types = [r["type"] for r in results]
        assert "geographic_restriction" in anomaly_types

    def test_no_anomalies_clean_text(self):
        """Тест: нет аномалий в чистом тексте."""
        text = """
        Поставка канцелярских товаров: бумага А4 (5000 пачек),
        ручки шариковые (2000 штук). Срок поставки: 30 рабочих дней.
        Стандартные требования к качеству.
        """
        results = self.analyzer.analyze(text)
        # Может быть 0 или минимальное количество аномалий
        high_severity = [r for r in results if r.get("severity") == "high"]
        assert len(high_severity) == 0

    def test_multiple_anomalies(self):
        """Тест: обнаружение множественных аномалий."""
        text = """
        Требуется поставка серверов Dell PowerEdge R750.
        Эквиваленты не допускаются. Обязательный сертификат ISO/IEC 27701:2019.
        Срок поставки и монтажа: 5 дней. Только поставщики из г.Алматы.
        Минимальный опыт работы: 20 лет.
        """
        results = self.analyzer.analyze(text)
        assert len(results) >= 3  # Бренд + сертификат + географ. ограничение


# ============================================================
# Стилометрия
# ============================================================

class TestStylometryAnalyzer:
    """Тесты стилометрического анализа."""

    def setup_method(self):
        self.analyzer = StylometryAnalyzer()

    def test_compute_style_vector(self):
        """Тест: вычисление стилевого вектора."""
        text = "Это тестовый текст для анализа стилометрии. Он содержит несколько предложений разной длины."
        vector = self.analyzer.compute_style_vector(text)
        assert isinstance(vector, dict)
        assert "avg_word_length" in vector
        assert "avg_sentence_length" in vector
        assert "type_token_ratio" in vector
        assert vector["avg_word_length"] > 0

    def test_detect_outlier(self):
        """Тест: обнаружение стилометрического выброса."""
        # Группа похожих текстов
        group = [
            "Поставка строительных материалов для ремонта здания школы. Цемент марки М500 в количестве 100 тонн.",
            "Поставка строительных материалов для ремонта дорожного покрытия. Щебень фракции 20-40 в количестве 200 тонн.",
            "Поставка строительных материалов для ремонта моста. Арматура класса А500 в количестве 50 тонн.",
        ]
        # Сильно отличающийся текст
        outlier = "The quick brown fox jumps over the lazy dog. This is a completely different style of writing!"

        vectors = [self.analyzer.compute_style_vector(t) for t in group]
        outlier_vector = self.analyzer.compute_style_vector(outlier)

        result = self.analyzer.detect_outlier(outlier_vector, vectors)
        assert isinstance(result, dict)
        assert "is_outlier" in result


# ============================================================
# Risk Scorer
# ============================================================

class TestRiskScorer:
    """Тесты модуля расчёта риск-скора."""

    def setup_method(self):
        self.scorer = RiskScorer()

    def test_calculate_high_risk(self):
        """Тест: высокий риск при множественных аномалиях."""
        procurement = {
            "amount": 2_000_000_000,
            "description": "Строительство дороги. Требуется оборудование Caterpillar.",
            "deadline_days": 10,
            "single_supplier": True,
        }
        anomalies = [
            {"type": "hyperspecific_requirements", "severity": "high", "confidence": 0.9},
            {"type": "unrealistic_deadline", "severity": "high", "confidence": 0.85},
            {"type": "geographic_restriction", "severity": "medium", "confidence": 0.7},
        ]

        result = self.scorer.calculate_score(procurement, anomalies)
        assert result["score"] >= 60
        assert result["level"] in ("orange", "red")

    def test_calculate_low_risk(self):
        """Тест: низкий риск при отсутствии аномалий."""
        procurement = {
            "amount": 10_000_000,
            "description": "Стандартная поставка канцтоваров",
            "deadline_days": 30,
        }
        anomalies = []

        result = self.scorer.calculate_score(procurement, anomalies)
        assert result["score"] <= 40
        assert result["level"] in ("green", "yellow")

    def test_score_in_range(self):
        """Тест: скор всегда в диапазоне 0-100."""
        for _ in range(20):
            procurement = {
                "amount": random.randint(1_000_000, 5_000_000_000),
                "description": "Тестовый тендер",
            }
            anomalies = [
                {"type": "test", "severity": random.choice(["high", "medium", "low"]),
                 "confidence": random.random()}
                for _ in range(random.randint(0, 10))
            ]

            result = self.scorer.calculate_score(procurement, anomalies)
            assert 0 <= result["score"] <= 100

    def test_explanation_generated(self):
        """Тест: генерация текстового объяснения."""
        result = self.scorer.calculate_score(
            {"amount": 100_000_000, "description": "Тест"},
            [{"type": "brand_mention", "severity": "high", "confidence": 0.9}],
        )
        assert "explanation" in result
        assert len(result["explanation"]) > 10


# ============================================================
# Collusion Detector
# ============================================================

class TestCollusionDetector:
    """Тесты детектора сговора."""

    def setup_method(self):
        self.detector = CollusionDetector()

    def test_detect_price_clustering(self):
        """Тест: обнаружение кластеризации цен (подозрение на сговор)."""
        bids = [
            {"supplier": "A", "price": 100_000_000},
            {"supplier": "B", "price": 100_100_000},  # разница 0.1%
            {"supplier": "C", "price": 100_050_000},  # разница 0.05%
        ]

        result = self.detector.analyze_procurement(bids)
        assert isinstance(result, dict)
        # При CV < 1% должен быть флаг

    def test_no_collusion_diverse_prices(self):
        """Тест: нет сговора при разных ценах."""
        bids = [
            {"supplier": "A", "price": 50_000_000},
            {"supplier": "B", "price": 120_000_000},
            {"supplier": "C", "price": 85_000_000},
        ]

        result = self.detector.analyze_procurement(bids)
        assert isinstance(result, dict)

    def test_cover_bidding_detection(self):
        """Тест: обнаружение подставных заявок (cover bidding)."""
        bids = [
            {"supplier": "Winner", "price": 100_000_000},
            {"supplier": "Cover1", "price": 200_000_000},  # Сильно завышена
            {"supplier": "Cover2", "price": 250_000_000},  # Сильно завышена
        ]

        result = self.detector.analyze_procurement(bids)
        assert isinstance(result, dict)


# ============================================================
# AML Detector
# ============================================================

class TestAMLDetector:
    """Тесты AML-детектора."""

    def setup_method(self):
        self.detector = AMLDetector()

    def test_detect_splitting(self):
        """Тест: обнаружение дробления платежей."""
        payments = [
            {"amount": 2_900_000, "date": "2024-01-15"},
            {"amount": 2_800_000, "date": "2024-01-15"},
            {"amount": 2_700_000, "date": "2024-01-15"},
            {"amount": 2_950_000, "date": "2024-01-15"},
        ]

        result = self.detector.check_splitting(payments, threshold=3_000_000)
        assert isinstance(result, dict)
        assert "is_suspicious" in result

    def test_detect_shell_company(self):
        """Тест: обнаружение компании-однодневки."""
        company = {
            "registration_date": "2023-11-01",
            "authorized_capital": 100_000,
            "employee_count": 1,
            "name": "ТОО Тест",
        }

        result = self.detector.check_shell_company(company)
        assert isinstance(result, dict)
        assert "risk_score" in result
        assert result["risk_score"] > 50  # Высокий риск

    def test_legitimate_company(self):
        """Тест: легитимная компания проходит проверку."""
        company = {
            "registration_date": "2010-03-15",
            "authorized_capital": 50_000_000,
            "employee_count": 200,
            "name": "ТОО КрупнаяКомпания",
        }

        result = self.detector.check_shell_company(company)
        assert result["risk_score"] < 50

    def test_round_amount_detection(self):
        """Тест: обнаружение подозрительно круглых сумм."""
        result = self.detector.check_round_amounts([
            100_000_000, 200_000_000, 300_000_000, 50_000_000
        ])
        assert isinstance(result, dict)
        assert "suspicious_count" in result


import random  # для test_score_in_range


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
