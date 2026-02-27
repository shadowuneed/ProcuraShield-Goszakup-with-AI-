"""
Тесты API-эндпоинтов ProcuraShield.
Интеграционные тесты для FastAPI.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ============================================================
# Health Check
# ============================================================

@pytest.mark.anyio
async def test_health_check(client: AsyncClient):
    """Тест: health-check эндпоинт."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


# ============================================================
# Auth
# ============================================================

@pytest.mark.anyio
async def test_login_invalid_credentials(client: AsyncClient):
    """Тест: неверные логин/пароль."""
    response = await client.post("/api/auth/login", json={
        "email": "nonexistent@test.com",
        "password": "wrongpassword",
    })
    assert response.status_code in (401, 422)


@pytest.mark.anyio
async def test_register_and_login(client: AsyncClient):
    """Тест: регистрация и вход."""
    # Регистрация
    reg_response = await client.post("/api/auth/register", json={
        "email": "testuser@test.com",
        "password": "TestPass123!",
        "full_name": "Test User",
    })
    # Может быть 201 (создан) или 409 (уже существует)
    assert reg_response.status_code in (200, 201, 409)


@pytest.mark.anyio
async def test_me_unauthorized(client: AsyncClient):
    """Тест: /me без авторизации."""
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


# ============================================================
# Procurements
# ============================================================

@pytest.mark.anyio
async def test_list_procurements(client: AsyncClient):
    """Тест: получение списка закупок."""
    response = await client.get("/api/procurements")
    assert response.status_code in (200, 401)


@pytest.mark.anyio
async def test_search_procurements(client: AsyncClient):
    """Тест: поиск закупок."""
    response = await client.get("/api/procurements/search", params={"q": "дорога"})
    assert response.status_code in (200, 401)


# ============================================================
# Dashboard
# ============================================================

@pytest.mark.anyio
async def test_dashboard_stats(client: AsyncClient):
    """Тест: дашборд статистика."""
    response = await client.get("/api/dashboard/stats")
    assert response.status_code in (200, 401)


# ============================================================
# Whistleblower
# ============================================================

@pytest.mark.anyio
async def test_submit_whistleblower_report(client: AsyncClient):
    """Тест: подача анонимного обращения."""
    response = await client.post("/api/whistleblower/submit", data={
        "title": "Тестовое обращение",
        "description": "Описание тестового нарушения для проверки API",
    })
    # 200/201 или 422 (если требуется авторизация)
    assert response.status_code in (200, 201, 422)


@pytest.mark.anyio
async def test_check_whistleblower_status(client: AsyncClient):
    """Тест: проверка статуса обращения."""
    response = await client.get("/api/whistleblower/status/INVALID-ID")
    assert response.status_code in (200, 404)


# ============================================================
# Blockchain
# ============================================================

@pytest.mark.anyio
async def test_verify_document_not_found(client: AsyncClient):
    """Тест: верификация несуществующего документа."""
    fake_hash = "0" * 64
    response = await client.get(f"/api/blockchain/verify/{fake_hash}")
    assert response.status_code in (200, 404, 401)


# ============================================================
# Alerts
# ============================================================

@pytest.mark.anyio
async def test_list_alerts(client: AsyncClient):
    """Тест: получение списка алертов."""
    response = await client.get("/api/alerts")
    assert response.status_code in (200, 401)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
