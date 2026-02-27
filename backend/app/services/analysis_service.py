"""
ProcuraShield — Сервис полного анализа тендера
Оркестрирует все AI-модули и формирует итоговую оценку
"""

from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.models import Procurement, RiskAssessment, Anomaly

logger = structlog.get_logger()


class AnalysisService:
    """
    Сервис оркестрации AI-анализа.
    Последовательно запускает все детекторы и формирует итоговый результат.
    """

    def __init__(self):
        from ai.nlp.spec_analyzer import SpecificationAnalyzer
        from ai.nlp.stylometry import StylometryAnalyzer
        from ai.risk.risk_scorer import RiskScorer
        from ai.collusion.collusion_detector import CollusionDetector
        from ai.aml.aml_detector import AMLDetector

        self.spec_analyzer = SpecificationAnalyzer()
        self.stylometry = StylometryAnalyzer()
        self.risk_scorer = RiskScorer()
        self.collusion_detector = CollusionDetector()
        self.aml_detector = AMLDetector()

    async def full_analysis(
        self,
        procurement: Procurement,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Полный анализ тендера. Этапы:
        1. NLP-анализ спецификаций (7 детекторов)
        2. Стилометрический анализ
        3. Анализ на картельный сговор
        4. AML-анализ
        5. Итоговый Risk Scoring
        6. Генерация объяснения
        """
        text = procurement.raw_text or ""
        all_anomalies: List[Dict[str, Any]] = []

        # === 1. NLP-анализ спецификаций ===
        logger.info("Запуск NLP-анализа", procurement_id=str(procurement.id))
        spec_anomalies = self.spec_analyzer.analyze(text)
        all_anomalies.extend(spec_anomalies)

        # === 2. Стилометрический анализ ===
        stylometry_result = self.stylometry.analyze(text)
        if stylometry_result:
            all_anomalies.extend(stylometry_result)

        # === 3. Анализ на картельный сговор ===
        collusion_result = self.collusion_detector.analyze_procurement(procurement)
        if collusion_result:
            all_anomalies.extend(collusion_result)

        # === 4. AML-анализ ===
        aml_result = self.aml_detector.analyze(procurement)
        if aml_result:
            all_anomalies.extend(aml_result)

        # === 5. Risk Scoring ===
        features = self.risk_scorer.extract_features(procurement, all_anomalies)
        risk_result = self.risk_scorer.calculate_score(features)

        # === 6. Генерация объяснения ===
        explanation = self.risk_scorer.generate_explanation(
            risk_result["score"],
            risk_result["components"],
            all_anomalies
        )

        # === Сохраняем результаты в БД ===
        risk_assessment = RiskAssessment(
            procurement_id=procurement.id,
            overall_score=risk_result["score"],
            risk_level=risk_result["level"],
            confidence=risk_result["confidence"],
            specification_score=risk_result["components"].get("specification", 0),
            competition_score=risk_result["components"].get("competition", 0),
            pricing_score=risk_result["components"].get("pricing", 0),
            supplier_score=risk_result["components"].get("supplier", 0),
            timing_score=risk_result["components"].get("timing", 0),
            historical_score=risk_result["components"].get("historical", 0),
            network_score=risk_result["components"].get("network", 0),
            feature_vector=features,
            shap_values=risk_result.get("shap_values"),
            explanation_text=explanation,
            model_version="1.0.0",
        )
        db.add(risk_assessment)
        await db.flush()

        # Сохраняем аномалии
        saved_anomalies = []
        for anomaly_data in all_anomalies:
            anomaly = Anomaly(
                procurement_id=procurement.id,
                risk_assessment_id=risk_assessment.id,
                anomaly_type=anomaly_data["type"],
                severity=anomaly_data["severity"],
                title=anomaly_data["title"],
                description=anomaly_data["description"],
                evidence=anomaly_data.get("evidence"),
                location_in_document=anomaly_data.get("location"),
                suggested_action=anomaly_data.get("suggested_action"),
            )
            db.add(anomaly)
            saved_anomalies.append(anomaly)

        await db.flush()

        logger.info(
            "Анализ завершён",
            procurement_id=str(procurement.id),
            risk_score=risk_result["score"],
            risk_level=risk_result["level"],
            anomalies_count=len(all_anomalies)
        )

        return {
            "risk_assessment": risk_assessment,
            "anomalies": saved_anomalies,
            "features": features,
        }
