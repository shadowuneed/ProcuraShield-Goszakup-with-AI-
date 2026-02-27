"""
Telegram-бот для отправки алертов и уведомлений ProcuraShield.
Поддержка групповых чатов, inline-кнопок, форматирования.
"""
import asyncio
import logging
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class TelegramBot:
    """Telegram-бот для отправки уведомлений о рисках."""

    BASE_URL = "https://api.telegram.org/bot{token}"

    def __init__(self, token: Optional[str] = None, chat_id: Optional[str] = None):
        self.token = token or settings.TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or settings.TELEGRAM_CHAT_ID
        self.api_url = self.BASE_URL.format(token=self.token)

    async def send_alert(
        self,
        title: str,
        description: str,
        severity: str,
        procurement_id: Optional[str] = None,
        risk_score: Optional[int] = None,
        chat_id: Optional[str] = None,
    ) -> bool:
        """
        Отправить алерт в Telegram.

        Args:
            title: Заголовок алерта
            description: Описание
            severity: Уровень критичности (critical, high, medium, low)
            procurement_id: ID закупки
            risk_score: Risk score (0-100)
            chat_id: ID чата (по умолчанию из настроек)

        Returns:
            True если отправлено успешно
        """
        severity_emoji = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🔵",
        }

        emoji = severity_emoji.get(severity, "⚪")
        risk_bar = self._risk_bar(risk_score) if risk_score else ""

        message = (
            f"{emoji} <b>АЛЕРТ: {title}</b>\n\n"
            f"📝 {description}\n\n"
        )

        if risk_score is not None:
            message += f"⚡ <b>Risk Score:</b> {risk_score}/100\n{risk_bar}\n\n"

        if procurement_id:
            message += f"🔗 Закупка: <code>{procurement_id}</code>\n"

        message += f"📊 Серьёзность: <b>{severity.upper()}</b>\n"
        message += f"🕐 Время: {self._current_time()}"

        # Inline-кнопки
        keyboard = None
        if procurement_id:
            keyboard = {
                "inline_keyboard": [
                    [
                        {
                            "text": "📋 Подробнее",
                            "url": f"{settings.FRONTEND_URL}/procurements/{procurement_id}",
                        },
                        {
                            "text": "🔍 Анализ",
                            "url": f"{settings.FRONTEND_URL}/analysis?id={procurement_id}",
                        },
                    ]
                ]
            }

        return await self._send_message(
            chat_id or self.chat_id,
            message,
            reply_markup=keyboard,
        )

    async def send_daily_report(
        self,
        total: int,
        analyzed: int,
        high_risk: int,
        top_risky: list[dict],
        chat_id: Optional[str] = None,
    ) -> bool:
        """Отправить ежедневный отчёт."""
        message = (
            "📊 <b>Ежедневный отчёт ProcuraShield</b>\n\n"
            f"📝 Всего тендеров: <b>{total}</b>\n"
            f"🔍 Проанализировано: <b>{analyzed}</b>\n"
            f"🔴 Высокий риск: <b>{high_risk}</b>\n\n"
        )

        if top_risky:
            message += "🏆 <b>Топ-5 рискованных:</b>\n"
            for i, item in enumerate(top_risky[:5], 1):
                score = item.get("risk_score", 0)
                title = item.get("title", "N/A")[:50]
                message += f"  {i}. [{score}%] {title}\n"

        message += f"\n🕐 {self._current_time()}"

        return await self._send_message(chat_id or self.chat_id, message)

    async def send_collusion_alert(
        self,
        companies: list[str],
        pattern: str,
        procurement_id: str,
        confidence: float,
        chat_id: Optional[str] = None,
    ) -> bool:
        """Отправить алерт о сговоре."""
        companies_list = "\n".join(f"  • {c}" for c in companies)

        message = (
            "🚨 <b>ОБНАРУЖЕН СГОВОР ПОСТАВЩИКОВ</b>\n\n"
            f"🔗 Закупка: <code>{procurement_id}</code>\n\n"
            f"👥 <b>Участники:</b>\n{companies_list}\n\n"
            f"📋 <b>Паттерн:</b> {pattern}\n"
            f"📊 <b>Уверенность:</b> {confidence * 100:.0f}%\n\n"
            f"🕐 {self._current_time()}"
        )

        return await self._send_message(chat_id or self.chat_id, message)

    async def _send_message(
        self,
        chat_id: str,
        text: str,
        reply_markup: Optional[dict] = None,
    ) -> bool:
        """Отправить сообщение через Telegram API."""
        if not self.token or self.token == "your-bot-token":
            logger.warning("Telegram bot token не настроен")
            return False

        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }

        if reply_markup:
            import json
            payload["reply_markup"] = json.dumps(reply_markup)

        async with httpx.AsyncClient(timeout=10) as client:
            try:
                response = await client.post(
                    f"{self.api_url}/sendMessage",
                    data=payload,
                )
                if response.status_code == 200:
                    logger.info(f"Telegram сообщение отправлено в {chat_id}")
                    return True
                else:
                    logger.error(
                        f"Ошибка Telegram API: {response.status_code} {response.text}"
                    )
                    return False
            except httpx.HTTPError as e:
                logger.error(f"Ошибка отправки в Telegram: {e}")
                return False

    @staticmethod
    def _risk_bar(score: int) -> str:
        """Генерация визуального индикатора риска."""
        filled = score // 10
        empty = 10 - filled
        return "█" * filled + "░" * empty + f" {score}%"

    @staticmethod
    def _current_time() -> str:
        """Текущее время в формате для отчёта."""
        from datetime import datetime
        return datetime.now().strftime("%d.%m.%Y %H:%M:%S")


# Singleton
telegram_bot = TelegramBot()
