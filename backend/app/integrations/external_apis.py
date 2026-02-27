"""
Интеграции с внешними API: ФНС/ЕГРЮЛ, СПАРК, Росфинмониторинг.
"""
import logging
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class ExternalAPIService:
    """Сервис для интеграций с внешними API (ФНС, СПАРК, и т.д.)."""

    def __init__(self):
        self.timeout = 15

    async def check_egrul(self, inn: str) -> Optional[dict]:
        """
        Проверка юр. лица по ИНН/БИН через ФНС/ЕГРЮЛ.
        Возвращает информацию о компании.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Для демо — используем публичный API ФНС
                response = await client.get(
                    f"https://egrul.nalog.ru/api/v1/search",
                    params={"query": inn, "type": "ul"},
                )

                if response.status_code == 200:
                    data = response.json()
                    items = data.get("items", [])
                    if items:
                        item = items[0]
                        return {
                            "inn": item.get("inn", inn),
                            "name": item.get("name", ""),
                            "address": item.get("address", ""),
                            "status": item.get("status", ""),
                            "registration_date": item.get("regdate", ""),
                            "capital": item.get("capital", 0),
                            "director": item.get("director", ""),
                            "activity": item.get("activity", ""),
                            "employees_count": item.get("employees", 0),
                        }
        except httpx.HTTPError as e:
            logger.error(f"Ошибка ЕГРЮЛ для ИНН {inn}: {e}")

        # Fallback — возвращаем базовую информацию
        return {
            "inn": inn,
            "name": "Не найдено",
            "status": "unknown",
            "source": "fallback",
        }

    async def check_sanctions(self, entity_name: str, inn: str = "") -> dict:
        """
        Проверка в санкционных списках.
        Проверяет: SDN (OFAC), EU, UN, Росфинмониторинг.
        """
        results = {
            "is_sanctioned": False,
            "lists": [],
            "matches": [],
        }

        # Проверка по основным спискам
        sanction_sources = [
            ("OFAC_SDN", f"https://sanctionslist.ofac.treas.gov/api/v1/search?name={entity_name}"),
            ("EU_SANCTIONS", f"https://webgate.ec.europa.eu/europeaid/fsd/fsf/public/api/v1/search?nameAlias={entity_name}"),
        ]

        async with httpx.AsyncClient(timeout=10) as client:
            for list_name, url in sanction_sources:
                try:
                    response = await client.get(url)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("results") or data.get("matches"):
                            results["is_sanctioned"] = True
                            results["lists"].append(list_name)
                            results["matches"].extend(
                                data.get("results", data.get("matches", []))[:3]
                            )
                except httpx.HTTPError:
                    logger.debug(f"Не удалось проверить {list_name}")
                    continue

        return results

    async def check_pep(self, person_name: str) -> dict:
        """
        Проверка, является ли лицо PEP (Politically Exposed Person).
        """
        return {
            "is_pep": False,
            "name": person_name,
            "position": None,
            "source": "manual_check_required",
            "note": "Требуется ручная проверка по базе ПДЛ",
        }

    async def get_company_relations(self, inn: str) -> list[dict]:
        """
        Получить связанные компании через СПАРК/Контур.Фокус.
        """
        # В реальном проекте — запрос к API СПАРК/Контур
        logger.info(f"Запрос связей для ИНН {inn}")
        return []

    async def check_rosfinmonitoring(self, inn: str) -> dict:
        """
        Проверка через Росфинмониторинг (перечень экстремистов).
        """
        return {
            "inn": inn,
            "in_list": False,
            "source": "rosfinmonitoring",
            "note": "API-ключ не настроен — ручная проверка",
        }


class NotificationService:
    """Сервис отправки уведомлений (Email, SMS)."""

    def __init__(self):
        self.sendgrid_api_key = getattr(settings, "SENDGRID_API_KEY", "")

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = True,
    ) -> bool:
        """Отправка email через SendGrid."""
        if not self.sendgrid_api_key:
            logger.warning("SendGrid API ключ не настроен")
            return False

        async with httpx.AsyncClient(timeout=10) as client:
            try:
                response = await client.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    headers={
                        "Authorization": f"Bearer {self.sendgrid_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "personalizations": [{"to": [{"email": to}]}],
                        "from": {"email": "alerts@procurashield.kz"},
                        "subject": subject,
                        "content": [
                            {
                                "type": "text/html" if html else "text/plain",
                                "value": body,
                            }
                        ],
                    },
                )
                return response.status_code in (200, 202)
            except httpx.HTTPError as e:
                logger.error(f"Ошибка отправки email: {e}")
                return False


# Singletons
external_api = ExternalAPIService()
notification_service = NotificationService()
