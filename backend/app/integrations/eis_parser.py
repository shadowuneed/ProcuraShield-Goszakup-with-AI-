"""
Парсер данных из ЕИС (Единая информационная система) / ГосЗакупки РК.
Поддержка XML/JSON форматов API, параллельная обработка.
"""
import asyncio
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional
from xml.etree import ElementTree

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class EISParser:
    """Парсер данных из ЕИС / goszakup.gov.kz API."""

    BASE_URL = "https://ows.goszakup.gov.kz/v3"  # API госзакупок РК
    EIS_BASE_URL = "https://zakupki.gov.ru/epz/order/extendedsearch/results.html"

    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or settings.EIS_API_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    async def fetch_recent_tenders(
        self, days: int = 1, limit: int = 100
    ) -> list[dict]:
        """
        Получить недавние тендеры за последние N дней.

        Args:
            days: Количество дней назад
            limit: Максимальное количество записей

        Returns:
            Список словарей с данными тендеров
        """
        date_from = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        date_to = datetime.utcnow().strftime("%Y-%m-%d")

        params = {
            "limit": limit,
            "start_date": date_from,
            "end_date": date_to,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/trd/buy",
                    headers=self.headers,
                    params=params,
                )
                response.raise_for_status()
                data = response.json()

                tenders = []
                for item in data.get("items", []):
                    tender = self._normalize_tender(item)
                    if tender:
                        tenders.append(tender)

                logger.info(f"Получено {len(tenders)} тендеров за {days} дней")
                return tenders

            except httpx.HTTPError as e:
                logger.error(f"Ошибка получения тендеров: {e}")
                return []

    async def fetch_tender_details(self, tender_id: str) -> Optional[dict]:
        """Получить детали конкретного тендера."""
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/trd/buy/{tender_id}",
                    headers=self.headers,
                )
                response.raise_for_status()
                return self._normalize_tender(response.json())
            except httpx.HTTPError as e:
                logger.error(f"Ошибка получения тендера {tender_id}: {e}")
                return None

    async def fetch_supplier_info(self, bin_iin: str) -> Optional[dict]:
        """
        Получить информацию о поставщике по БИН/ИИН.
        """
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/subject/biin/{bin_iin}",
                    headers=self.headers,
                )
                response.raise_for_status()
                data = response.json()

                return {
                    "bin_iin": data.get("bin", bin_iin),
                    "name": data.get("name_ru", ""),
                    "registration_date": data.get("regdate"),
                    "status": data.get("status"),
                    "address": data.get("address_ru"),
                    "phone": data.get("phone"),
                    "head_name": data.get("fio"),
                    "activity_type": data.get("oked", {}).get("name_ru", ""),
                }
            except httpx.HTTPError as e:
                logger.error(f"Ошибка поиска поставщика {bin_iin}: {e}")
                return None

    async def fetch_bids(self, tender_id: str) -> list[dict]:
        """Получить заявки по тендеру."""
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/trd/buy/{tender_id}/lots",
                    headers=self.headers,
                )
                response.raise_for_status()
                lots_data = response.json()

                bids = []
                for lot in lots_data.get("items", []):
                    for app in lot.get("applications", []):
                        bids.append({
                            "tender_id": tender_id,
                            "lot_id": str(lot.get("id")),
                            "supplier_bin": app.get("supplier_biin", ""),
                            "supplier_name": app.get("supplier_name_ru", ""),
                            "price": float(app.get("price", 0)),
                            "status": app.get("status", ""),
                        })

                return bids
            except httpx.HTTPError as e:
                logger.error(f"Ошибка получения заявок {tender_id}: {e}")
                return []

    def parse_xml_tender(self, xml_content: str) -> Optional[dict]:
        """
        Парсинг тендера из XML-формата (ЕИС РФ).
        """
        try:
            root = ElementTree.fromstring(xml_content)
            ns = {"ns": root.tag.split("}")[0].strip("{") if "}" in root.tag else ""}

            def find_text(path: str) -> str:
                elem = root.find(path, ns) if ns.get("ns") else root.find(path)
                return elem.text if elem is not None and elem.text else ""

            return {
                "number": find_text(".//purchaseNumber") or find_text(".//regNum"),
                "title": find_text(".//purchaseObjectInfo") or find_text(".//name"),
                "organization": find_text(".//fullName") or find_text(".//orgName"),
                "amount": float(find_text(".//maxPrice") or find_text(".//sum") or "0"),
                "currency": find_text(".//currency//code") or "KZT",
                "description": find_text(".//purchaseObjectInfo"),
                "region": find_text(".//region"),
                "deadline": find_text(".//endDateTime") or find_text(".//applEndDate"),
                "published_at": find_text(".//publishDTInEIS") or find_text(".//startDate"),
                "source": "EIS_XML",
            }
        except ElementTree.ParseError as e:
            logger.error(f"Ошибка парсинга XML: {e}")
            return None

    def _normalize_tender(self, raw: dict) -> Optional[dict]:
        """Нормализация данных тендера из различных API."""
        try:
            amount_str = raw.get("total_sum", raw.get("sum", raw.get("price", "0")))
            amount = float(amount_str) if amount_str else 0

            return {
                "number": raw.get("number_anno", raw.get("id", "")),
                "title": raw.get("name_ru", raw.get("title", "")),
                "organization": raw.get("org_name_ru", raw.get("orgName", "")),
                "amount": amount,
                "currency": raw.get("currency", "KZT"),
                "description": raw.get("description_ru", raw.get("description", "")),
                "region": raw.get("region", ""),
                "category": raw.get("trd_type", raw.get("category", "")),
                "method": raw.get("buy_type", raw.get("method", "")),
                "iin_bin": raw.get("bin", raw.get("inn", "")),
                "status": raw.get("status", "active"),
                "deadline": raw.get("end_date", ""),
                "published_at": raw.get("start_date", raw.get("publish_date", "")),
                "source": "goszakup_api",
                "document_hash": hashlib.sha256(
                    str(raw).encode()
                ).hexdigest(),
            }
        except Exception as e:
            logger.error(f"Ошибка нормализации тендера: {e}")
            return None


# Singleton
eis_parser = EISParser()
