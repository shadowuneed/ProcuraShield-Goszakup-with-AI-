"""
ProcuraShield — Стилометрический анализ
Определение, один ли человек писал документацию заказчика и КП победителя.
Использует статистические характеристики текста.
"""

import re
import math
from typing import List, Dict, Any, Optional
from collections import Counter
import structlog

logger = structlog.get_logger()


class StylometryAnalyzer:
    """
    Стилометрический анализ текста.
    Извлекает «отпечаток стиля» автора по:
    - Средней длине предложений
    - Распределению длин слов
    - Частоте служебных слов
    - Использованию пунктуации
    - Лексическому богатству
    - Паттернам форматирования
    """

    def __init__(self):
        # Русские служебные слова для стилометрии
        self.function_words = [
            'и', 'в', 'не', 'на', 'с', 'что', 'а', 'по', 'но', 'для',
            'к', 'от', 'из', 'за', 'о', 'же', 'или', 'при', 'до', 'как',
            'то', 'это', 'ни', 'бы', 'ли', 'так', 'ещё', 'уже', 'да',
            'вот', 'тоже', 'также', 'который', 'однако', 'между', 'через',
            'после', 'перед', 'может', 'будет', 'быть', 'был', 'была',
            'должен', 'должна', 'должно', 'необходимо', 'следует',
        ]

    def analyze(self, text: str) -> List[Dict[str, Any]]:
        """
        Основной анализ текста.
        Если текст содержит разнородные стилевые маркеры —
        возможна вставка из внешнего документа (КП).
        """
        if not text or len(text) < 200:
            return []

        anomalies = []

        # Разбиваем текст на секции (параграфы)
        sections = self._split_into_sections(text)
        if len(sections) < 3:
            return []

        # Вычисляем стилометрический вектор для каждой секции
        vectors = [self._compute_style_vector(s) for s in sections if len(s) > 100]
        if len(vectors) < 3:
            return []

        # Ищем аномальные секции (сильно отличающиеся по стилю)
        outliers = self._find_style_outliers(vectors, sections)

        if outliers:
            anomalies.append({
                "type": "stylometric_match",
                "severity": 65.0,
                "title": "Стилевая неоднородность документа",
                "description": (
                    f"Стилометрический анализ выявил {len(outliers)} секций документа "
                    f"с существенно отличающимся стилем написания. Это может указывать "
                    f"на вставку текста из коммерческого предложения поставщика."
                ),
                "evidence": {
                    "outlier_sections": [o["section_preview"] for o in outliers],
                    "style_deviation": [o["deviation"] for o in outliers],
                },
                "suggested_action": "Проверить указанные секции на совпадение с КП поставщиков.",
            })

        return anomalies

    def _split_into_sections(self, text: str) -> List[str]:
        """Разбивка текста на смысловые секции"""
        # По двойным переносам строк или нумерованным разделам
        sections = re.split(r'\n\s*\n|\n\d+[.)]\s+', text)
        return [s.strip() for s in sections if len(s.strip()) > 50]

    def _compute_style_vector(self, text: str) -> Dict[str, float]:
        """
        Вычисление стилометрического вектора текста.
        Включает 12 метрик стиля.
        """
        words = re.findall(r'[а-яёa-z]+', text.lower())
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

        if not words or not sentences:
            return {}

        word_lengths = [len(w) for w in words]
        sent_lengths = [len(re.findall(r'\S+', s)) for s in sentences]

        # Частоты служебных слов
        word_freq = Counter(words)
        total_words = len(words)
        func_word_freq = {
            w: word_freq.get(w, 0) / total_words
            for w in self.function_words
        }

        return {
            # Длина слов
            "avg_word_length": sum(word_lengths) / len(word_lengths),
            "word_length_std": self._std(word_lengths),

            # Длина предложений
            "avg_sent_length": sum(sent_lengths) / max(len(sent_lengths), 1),
            "sent_length_std": self._std(sent_lengths),

            # Лексическое богатство (TTR)
            "type_token_ratio": len(set(words)) / max(total_words, 1),

            # Hapax legomena (слова, встречающиеся 1 раз)
            "hapax_ratio": sum(1 for w, c in word_freq.items() if c == 1) / max(total_words, 1),

            # Пунктуация
            "comma_rate": text.count(',') / max(total_words, 1),
            "semicolon_rate": text.count(';') / max(total_words, 1),
            "dash_rate": (text.count('—') + text.count('-')) / max(total_words, 1),

            # Служебные слова (топ-10 по важности)
            "func_и": func_word_freq.get('и', 0),
            "func_в": func_word_freq.get('в', 0),
            "func_не": func_word_freq.get('не', 0),
        }

    def _find_style_outliers(
        self,
        vectors: List[Dict[str, float]],
        sections: List[str]
    ) -> List[Dict[str, Any]]:
        """Поиск секций с аномальным стилем"""
        if len(vectors) < 3:
            return []

        outliers = []

        # Вычисляем центроид (средний вектор)
        keys = [k for k in vectors[0].keys() if vectors[0][k] is not None]
        centroid = {}
        for key in keys:
            values = [v.get(key, 0) for v in vectors]
            centroid[key] = sum(values) / len(values)

        # Вычисляем расстояние каждой секции от центроида
        distances = []
        for i, vec in enumerate(vectors):
            dist = self._euclidean_distance(vec, centroid, keys)
            distances.append(dist)

        # Находим выбросы (> 1.5 * IQR)
        if not distances:
            return []

        sorted_d = sorted(distances)
        q1 = sorted_d[len(sorted_d) // 4]
        q3 = sorted_d[3 * len(sorted_d) // 4]
        iqr = q3 - q1
        threshold = q3 + 1.5 * iqr

        for i, dist in enumerate(distances):
            if dist > threshold and i < len(sections):
                outliers.append({
                    "section_index": i,
                    "section_preview": sections[i][:150] + "...",
                    "deviation": round(dist, 4),
                })

        return outliers

    @staticmethod
    def _std(values: List[float]) -> float:
        """Стандартное отклонение"""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)

    @staticmethod
    def _euclidean_distance(vec1: dict, vec2: dict, keys: list) -> float:
        """Евклидово расстояние между двумя векторами"""
        total = 0.0
        for key in keys:
            v1 = vec1.get(key, 0) or 0
            v2 = vec2.get(key, 0) or 0
            total += (v1 - v2) ** 2
        return math.sqrt(total)


def compare_documents(doc1: str, doc2: str) -> Dict[str, Any]:
    """
    Сравнение стилей двух документов.
    Используется для сравнения ТЗ заказчика с КП поставщика.
    """
    analyzer = StylometryAnalyzer()
    vec1 = analyzer._compute_style_vector(doc1)
    vec2 = analyzer._compute_style_vector(doc2)

    if not vec1 or not vec2:
        return {"similarity": 0.0, "conclusion": "Недостаточно текста для анализа"}

    keys = list(set(vec1.keys()) & set(vec2.keys()))
    distance = analyzer._euclidean_distance(vec1, vec2, keys)

    # Нормализуем в similarity (0-1, где 1 = идентично)
    similarity = max(0, 1. - distance / 5.0)

    conclusion = "Стили существенно различаются"
    if similarity > 0.85:
        conclusion = "ВЫСОКАЯ вероятность единого авторства"
    elif similarity > 0.65:
        conclusion = "Умеренная схожесть стилей"

    return {
        "similarity": round(similarity, 4),
        "distance": round(distance, 4),
        "conclusion": conclusion,
        "details": {
            "doc1_metrics": vec1,
            "doc2_metrics": vec2,
        }
    }
