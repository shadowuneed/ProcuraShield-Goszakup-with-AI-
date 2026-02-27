"""
Middleware безопасности ProcuraShield.
OWASP Top-10 protection, аудит-логирование, rate limiting.
"""
import time
import logging
import hashlib
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Добавление заголовков безопасности (OWASP)."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # OWASP Secure Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' ws: wss:;"
        )

        return response


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Логирование всех действий пользователей для аудита."""

    # Эндпоинты, которые нужно логировать
    AUDIT_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Получить информацию о пользователе из JWT
        user_info = self._extract_user(request)

        response = await call_next(request)

        duration = time.time() - start_time

        # Логируем модифицирующие запросы
        if request.method in self.AUDIT_METHODS:
            log_entry = {
                "timestamp": time.time(),
                "method": request.method,
                "path": request.url.path,
                "user": user_info,
                "ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", ""),
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
            }
            logger.info(f"AUDIT: {log_entry}")

        # Добавить заголовок с временем обработки
        response.headers["X-Process-Time"] = str(round(duration * 1000, 2))

        return response

    @staticmethod
    def _extract_user(request: Request) -> str:
        """Извлечь информацию о пользователе из заголовка Authorization."""
        auth = request.headers.get("authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
            # Хешируем токен для лога (не записываем сам токен)
            return f"user:{hashlib.sha256(token.encode()).hexdigest()[:12]}"
        return "anonymous"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Простой rate limiter на основе IP-адреса."""

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Очистка старых записей
        if client_ip in self.requests:
            self.requests[client_ip] = [
                t for t in self.requests[client_ip]
                if now - t < self.window
            ]
        else:
            self.requests[client_ip] = []

        # Проверка лимита
        if len(self.requests[client_ip]) >= self.max_requests:
            return Response(
                content='{"detail": "Too many requests"}',
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": str(self.window)},
            )

        self.requests[client_ip].append(now)
        return await call_next(request)


class RequestSanitizer(BaseHTTPMiddleware):
    """Санитизация входящих запросов (XSS/SQL injection protection)."""

    DANGEROUS_PATTERNS = [
        "<script", "javascript:", "onerror=", "onload=",
        "'; DROP TABLE", "1=1", "UNION SELECT",
        "../", "..\\",
    ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Проверка query-параметров
        query_string = str(request.url.query).lower()
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern.lower() in query_string:
                logger.warning(
                    f"SECURITY: Подозрительный запрос от {request.client.host}: {query_string[:100]}"
                )
                return Response(
                    content='{"detail": "Forbidden - suspicious input detected"}',
                    status_code=403,
                    media_type="application/json",
                )

        return await call_next(request)
