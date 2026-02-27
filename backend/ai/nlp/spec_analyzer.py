"""
ProcuraShield — NLP-анализатор тендерных спецификаций
Главный модуль AI-анализа документации.

7 детекторов аномалий:
1. Гиперспецифичные технические требования
2. Нестандартные сертификаты
3. Нереалистичные сроки
4. Географические ограничения
5. Аномальный опыт
6. Копипаста из коммерческих предложений
7. Семантическая схожесть с выигранными тендерами
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()


@dataclass
class AnomalyResult:
    """Результат обнаружения аномалии"""
    type: str
    severity: float
    title: str
    description: str
    evidence: Optional[Dict[str, Any]] = None
    location: Optional[str] = None
    suggested_action: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "evidence": self.evidence,
            "location": self.location,
            "suggested_action": self.suggested_action,
        }


class SpecificationAnalyzer:
    """
    NLP-анализатор тендерных спецификаций.
    Применяет 7 детекторов аномалий для выявления признаков
    «заточки под поставщика».
    """

    def __init__(self):
        # Паттерны для детекторов (regex — для скорости на MVP)
        self._init_patterns()

    def _init_patterns(self):
        """Инициализация паттернов для всех детекторов"""

        # === ДЕТЕКТОР 1: Гиперспецифичные требования ===
        # Конкретные модели, артикулы, бренды
        self.brand_patterns = [
            r'\b(Intel\s+Core\s+i[3579]-\d{4,5}[A-Z]*)',
            r'\b(AMD\s+Ryzen\s+\d\s+\d{4}[A-Z]*)',
            r'\b(NVIDIA\s+(?:GeForce|Quadro|Tesla)\s+[A-Z\d\s]+)',
            r'\b(Samsung\s+Galaxy\s+[A-Z]\d{1,2})',
            r'\b(iPhone\s+\d{1,2}\s*(?:Pro|Max|Plus)?)',
            r'\b(HP\s+(?:EliteBook|ProBook|ZBook)\s+\d{3,4})',
            r'\b(Dell\s+(?:Latitude|Precision|OptiPlex)\s+\d{4})',
            r'\b(Lenovo\s+(?:ThinkPad|ThinkCentre)\s+[A-Z]\d{2,3})',
            r'\b(Cisco\s+(?:Catalyst|ASR|ISR)\s+\d{4})',
            r'\b(Huawei\s+\w+\s+\d{2,4})',
        ]

        # Артикулы — точные номера моделей
        self.article_patterns = [
            r'\b[A-Z]{2,5}-?\d{3,10}[A-Z]{0,3}\b',  # Артикулы типа ABC-12345
            r'\b\d{3,}-[A-Z]{2,}-\d{2,}\b',           # 123-AB-45
            r'\bpart\s*(?:number|#|№)\s*[:.]?\s*\w+',
            r'\bарт(?:икул)?[\s.:]*\w{3,}',
        ]

        # === ДЕТЕКТОР 2: Нестандартные сертификаты ===
        self.rare_cert_patterns = [
            r'сертификат\s+(?:соответствия\s+)?(?:№|номер)\s*[\w-]+',
            r'(?:ISO|ГОСТ|ТУ)\s*\d{4,}[-:]\d{2,}[-:]\d{2,}',
            r'лицензи[яию]\s+(?:№|номер)\s*[\w-]+',
            r'допуск\s+(?:СРО|саморегулируемой)',
            r'аттестат\s+аккредитации',
            r'свидетельство\s+о\s+(?:регистрации|допуске)',
        ]

        # Специфичные сертификаты (могут быть у 1-2 компаний)
        self.exclusive_cert_keywords = [
            'единственный сертифицированный',
            'эксклюзивный партнёр',
            'авторизованный дилер',
            'единственный поставщик',
            'официальный представитель',
        ]

        # === ДЕТЕКТОР 3: Нереалистичные сроки ===
        self.deadline_patterns = [
            (r'(?:срок\s+(?:поставки|выполнения|исполнения))\s*[-:—]?\s*(\d+)\s*(?:календарн(?:ых|ых)|рабоч(?:их|ий))?\s*дн(?:ей|я)',
             'days'),
            (r'(?:в\s+течение|не\s+позднее)\s+(\d+)\s*дн(?:ей|я)',
             'days'),
            (r'(?:срок)\s*[-:—]?\s*(\d+)\s*час(?:ов|а)',
             'hours'),
        ]

        # Минимальные разумные сроки по категориям
        self.min_reasonable_days = {
            'компьютер': 14,
            'сервер': 21,
            'оборудование': 21,
            'строительство': 60,
            'монтаж': 30,
            'проектирование': 30,
            'разработка': 45,
            'поставка': 10,
            'ремонт': 14,
            'мебель': 21,
            'транспорт': 30,
            'медицинское': 30,
            'программное обеспечение': 14,
        }

        # === ДЕТЕКТОР 4: Географические ограничения ===
        self.geo_restriction_patterns = [
            r'(?:офис|представительство|филиал|склад)\s+(?:в\s+(?:городе|г\.)\s+)([\w-]+)',
            r'(?:расположен(?:ие|ный)|находиться)\s+(?:в\s+)?(?:г\.|городе)\s+([\w-]+)',
            r'близость\s+(?:к\s+)?(?:месту|объекту|заказчику)',
            r'(?:в\s+радиусе|не\s+далее)\s+(\d+)\s*км',
            r'(?:только|исключительно)\s+(?:из|в)\s+(?:г\.|города)\s+',
            r'наличие\s+(?:офиса|склада|представительства)\s+(?:в|на\s+территории)',
        ]

        # === ДЕТЕКТОР 5: Аномальный опыт ===
        self.experience_patterns = [
            r'опыт\s+(?:поставки|выполнения|оказания)\s+(?:именно\s+)?(?:данного|аналогичного|такого\s+же)',
            r'(?:опыт|стаж)\s+(?:работы\s+)?(?:не\s+менее|от)\s+(\d+)\s*лет',
            r'(?:выполнение|исполнение)\s+(?:не\s+менее|от)\s+(\d+)\s+(?:аналогичных\s+)?контрактов',
            r'(?:опыт\s+работы|сотрудничества)\s+(?:с|именно\s+с)\s+(?:данным\s+)?заказчиком',
            r'наличие\s+(?:положительных\s+)?(?:отзывов|рекомендаций)\s+(?:от\s+)?(?:данного\s+)?заказчика',
            r'ранее\s+(?:поставлял|выполнял|оказывал)',
        ]

        # === ДЕТЕКТОР 6: Копипаста из КП ===
        self.commercial_proposal_markers = [
            r'(?:коммерческое\s+предложение|КП)\s+(?:от|№)',
            r'(?:прайс[-\s]?лист|каталог)\s+(?:компании|ООО|АО|ТОО)',
            r'наша\s+компания\s+(?:предлагает|готова)',
            r'с\s+уважением',
            r'(?:директор|менеджер)\s+(?:по\s+продажам)',
            r'(?:скидка|спецпредложение|акция)',
        ]

    def analyze(self, text: str) -> List[Dict[str, Any]]:
        """
        Главный метод анализа текста.
        Возвращает список обнаруженных аномалий.
        """
        if not text or len(text.strip()) < 50:
            return []

        anomalies = []

        # Запускаем все детекторы
        anomalies.extend(self._detect_hyperspecific(text))
        anomalies.extend(self._detect_rare_certificates(text))
        anomalies.extend(self._detect_unrealistic_deadlines(text))
        anomalies.extend(self._detect_geo_restrictions(text))
        anomalies.extend(self._detect_anomalous_experience(text))
        anomalies.extend(self._detect_commercial_copy(text))
        anomalies.extend(self._detect_restrictive_language(text))

        logger.info(f"NLP-анализ: обнаружено {len(anomalies)} аномалий")
        return [a.to_dict() for a in anomalies]

    def _detect_hyperspecific(self, text: str) -> List[AnomalyResult]:
        """
        ДЕТЕКТОР 1: Гиперспецифичные технические требования.
        Выявляет указание конкретных брендов, моделей, артикулов
        вместо функциональных характеристик.
        """
        anomalies = []

        # Поиск конкретных брендов и моделей
        brand_matches = []
        for pattern in self.brand_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            brand_matches.extend(matches)

        if brand_matches:
            severity = min(90.0, 50.0 + len(brand_matches) * 10)
            anomalies.append(AnomalyResult(
                type="hyperspecific_requirements",
                severity=severity,
                title="Указание конкретных брендов и моделей",
                description=(
                    f"В тендерной документации обнаружены ссылки на конкретные бренды/модели: "
                    f"{', '.join(brand_matches[:5])}. "
                    f"Это может ограничивать конкуренцию, исключая аналогичную продукцию "
                    f"других производителей."
                ),
                evidence={"brands_found": brand_matches[:10], "count": len(brand_matches)},
                suggested_action=(
                    "Рекомендуется заменить указание конкретных моделей на функциональные "
                    "характеристики (например, 'процессор с тактовой частотой не менее X ГГц' "
                    "вместо конкретной модели) или добавить формулировку 'или эквивалент'."
                ),
            ))

        # Поиск артикулов (точные номера)
        article_matches = []
        for pattern in self.article_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            article_matches.extend(matches)

        # Фильтруем ложные срабатывания (даты, телефоны)
        article_matches = [
            m for m in article_matches
            if not re.match(r'^\d{2}[./-]\d{2}[./-]\d{2,4}$', m)
            and len(m) >= 5
        ]

        if len(article_matches) > 2:
            anomalies.append(AnomalyResult(
                type="hyperspecific_requirements",
                severity=70.0,
                title="Множественные артикулы в спецификации",
                description=(
                    f"Обнаружено {len(article_matches)} артикулов/номеров моделей. "
                    f"Указание точных артикулов существенно ограничивает круг поставщиков."
                ),
                evidence={"articles": article_matches[:10]},
                suggested_action="Заменить артикулы на описание функциональных характеристик.",
            ))

        return anomalies

    def _detect_rare_certificates(self, text: str) -> List[AnomalyResult]:
        """
        ДЕТЕКТОР 2: Нестандартные / редкие сертификаты.
        Выявляет требования сертификатов, которые могут быть
        только у одной или очень ограниченного круга компаний.
        """
        anomalies = []

        # Поиск эксклюзивных формулировок
        for keyword in self.exclusive_cert_keywords:
            if keyword.lower() in text.lower():
                anomalies.append(AnomalyResult(
                    type="nonstandard_certificates",
                    severity=85.0,
                    title="Требование эксклюзивного статуса",
                    description=(
                        f"Обнаружено требование '{keyword}'. "
                        f"Такое требование может быть выполнимо только одной компанией, "
                        f"что является признаком ограничения конкуренции."
                    ),
                    evidence={"keyword": keyword},
                    suggested_action=(
                        "Убрать требование эксклюзивного статуса. Допустить участие "
                        "любых компаний, способных выполнить технические требования."
                    ),
                ))

        # Подсчёт количества сертификатов
        cert_count = 0
        for pattern in self.rare_cert_patterns:
            cert_count += len(re.findall(pattern, text, re.IGNORECASE))

        if cert_count > 5:
            anomalies.append(AnomalyResult(
                type="nonstandard_certificates",
                severity=60.0,
                title="Избыточное количество сертификатов",
                description=(
                    f"Требуется {cert_count} различных сертификатов/лицензий. "
                    f"Избыточные требования к наличию сертификатов могут ограничивать "
                    f"конкуренцию."
                ),
                evidence={"cert_count": cert_count},
                suggested_action="Оставить только объективно необходимые сертификаты.",
            ))

        return anomalies

    def _detect_unrealistic_deadlines(self, text: str) -> List[AnomalyResult]:
        """
        ДЕТЕКТОР 3: Нереалистичные сроки.
        Сравнивает указанные сроки с разумными минимумами по категориям.
        """
        anomalies = []
        text_lower = text.lower()

        for pattern, unit in self.deadline_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                try:
                    value = int(match)
                except (ValueError, TypeError):
                    continue

                # Конвертируем в дни
                days = value if unit == 'days' else value / 24

                if days <= 3:
                    # Критически короткий срок
                    anomalies.append(AnomalyResult(
                        type="unrealistic_deadlines",
                        severity=90.0,
                        title="Критически короткий срок исполнения",
                        description=(
                            f"Установлен срок исполнения {value} {unit}. "
                            f"Это нереалистично короткий срок, который может выполнить "
                            f"только заранее подготовленный поставщик."
                        ),
                        evidence={"deadline_value": value, "unit": unit, "days": days},
                        suggested_action="Установить разумный срок исполнения согласно рыночным нормам.",
                    ))
                elif days <= 7:
                    # Проверяем по категории
                    for category, min_days in self.min_reasonable_days.items():
                        if category in text_lower and days < min_days:
                            anomalies.append(AnomalyResult(
                                type="unrealistic_deadlines",
                                severity=75.0,
                                title=f"Сжатый срок для категории '{category}'",
                                description=(
                                    f"Срок {value} дней для категории '{category}' "
                                    f"значительно ниже рекомендуемого минимума ({min_days} дней)."
                                ),
                                evidence={
                                    "deadline_days": value,
                                    "category": category,
                                    "min_reasonable": min_days
                                },
                                suggested_action=f"Увеличить срок минимум до {min_days} дней.",
                            ))
                            break

        return anomalies

    def _detect_geo_restrictions(self, text: str) -> List[AnomalyResult]:
        """
        ДЕТЕКТОР 4: Географические ограничения.
        Выявляет необоснованные требования к локации поставщика.
        """
        anomalies = []

        for pattern in self.geo_restriction_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                location = matches[0] if isinstance(matches[0], str) else str(matches[0])
                anomalies.append(AnomalyResult(
                    type="geographic_restrictions",
                    severity=65.0,
                    title="Географическое ограничение для участников",
                    description=(
                        f"Обнаружено требование географической привязки: '{location}'. "
                        f"Требование наличия офиса/склада в конкретном городе без объективного "
                        f"обоснования ограничивает конкуренцию."
                    ),
                    evidence={"location": location, "pattern": pattern[:50]},
                    suggested_action=(
                        "Убрать требование наличия офиса в конкретном городе или "
                        "обосновать его производственной необходимостью."
                    ),
                ))

        return anomalies

    def _detect_anomalous_experience(self, text: str) -> List[AnomalyResult]:
        """
        ДЕТЕКТОР 5: Аномальные требования к опыту.
        Выявляет требования опыта работы именно с данным заказчиком
        или нереалистичные требования к стажу.
        """
        anomalies = []
        text_lower = text.lower()

        for pattern in self.experience_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                detail = matches[0] if matches else ""

                # Проверяем на требование опыта с конкретным заказчиком
                if 'заказчик' in pattern or 'данн' in pattern:
                    anomalies.append(AnomalyResult(
                        type="anomalous_experience",
                        severity=85.0,
                        title="Требование опыта с конкретным заказчиком",
                        description=(
                            "Обнаружено требование предыдущего опыта работы именно с данным заказчиком. "
                            "Это прямое ограничение конкуренции — новые поставщики не смогут участвовать."
                        ),
                        evidence={"pattern_matched": pattern[:80]},
                        suggested_action="Заменить на требование аналогичного опыта без привязки к заказчику.",
                    ))
                elif detail:
                    try:
                        years = int(detail)
                        if years > 10:
                            anomalies.append(AnomalyResult(
                                type="anomalous_experience",
                                severity=60.0,
                                title="Завышенное требование к опыту",
                                description=(
                                    f"Требуется опыт не менее {years} лет. "
                                    f"Такое требование чрезмерно ограничивает круг участников."
                                ),
                                evidence={"required_years": years},
                                suggested_action="Снизить требование к опыту до разумного уровня (3-5 лет).",
                            ))
                    except ValueError:
                        pass

        return anomalies

    def _detect_commercial_copy(self, text: str) -> List[AnomalyResult]:
        """
        ДЕТЕКТОР 6: Копипаста из коммерческих предложений.
        Выявляет признаки того, что ТЗ было скопировано
        из коммерческого предложения конкретного поставщика.
        """
        anomalies = []
        markers_found = []

        for pattern in self.commercial_proposal_markers:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                markers_found.extend(matches)

        if len(markers_found) >= 2:
            anomalies.append(AnomalyResult(
                type="commercial_proposal_copy",
                severity=80.0,
                title="Признаки копирования из коммерческого предложения",
                description=(
                    f"Обнаружены {len(markers_found)} маркеров коммерческого предложения в тексте ТЗ. "
                    f"Техническое задание, скопированное из КП одного поставщика, "
                    f"создаёт неконкурентные условия."
                ),
                evidence={"markers": markers_found[:5]},
                suggested_action="Переписать ТЗ с нейтральными формулировками.",
            ))

        return anomalies

    def _detect_restrictive_language(self, text: str) -> List[AnomalyResult]:
        """
        Дополнительный детектор: ограничительные формулировки.
        Выявляет языковые конструкции, характерные для «заточки».
        """
        anomalies = []
        text_lower = text.lower()

        restrictive_phrases = [
            ('только', 'Использование слова "только" ограничивает выбор'),
            ('исключительно', 'Слово "исключительно" исключает альтернативы'),
            ('единственный', '"Единственный" указывает на отсутствие альтернатив'),
            ('не допускается замена', 'Запрет замены ограничивает конкуренцию'),
            ('без эквивалента', 'Запрет эквивалентов ограничивает конкуренцию'),
            ('конкретной марки', '"Конкретной марки" — явное ограничение'),
            ('определённого производителя', 'Привязка к производителю'),
        ]

        found = []
        for phrase, desc in restrictive_phrases:
            count = text_lower.count(phrase)
            if count > 0:
                found.append({"phrase": phrase, "count": count, "note": desc})

        if len(found) >= 2:
            anomalies.append(AnomalyResult(
                type="hyperspecific_requirements",
                severity=55.0,
                title="Ограничительные формулировки в ТЗ",
                description=(
                    f"Обнаружены {len(found)} типов ограничительных формулировок: "
                    f"{', '.join([f['phrase'] for f in found])}. "
                    f"Такие формулировки могут свидетельствовать о заточке ТЗ."
                ),
                evidence={"phrases": found},
                suggested_action="Заменить ограничительные формулировки на нейтральные.",
            ))

        return anomalies
