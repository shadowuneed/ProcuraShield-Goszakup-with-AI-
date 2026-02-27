"""Модуль интеграций с внешними API."""
from app.integrations.eis_parser import eis_parser
from app.integrations.telegram_bot import telegram_bot
from app.integrations.external_apis import external_api, notification_service

__all__ = [
    "eis_parser",
    "telegram_bot",
    "external_api",
    "notification_service",
]
