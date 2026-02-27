"""
Нагрузочные тесты ProcuraShield (Locust).
Цель: 1000 RPS на основные эндпоинты.
"""
from locust import HttpUser, task, between


class ProcuraShieldUser(HttpUser):
    """Имитация пользователя ProcuraShield."""

    wait_time = between(0.1, 0.5)
    host = "http://localhost:8000"

    def on_start(self):
        """Аутентификация при старте."""
        response = self.client.post("/api/auth/login", json={
            "email": "analyst@procurashield.kz",
            "password": "analyst123!",
        })
        if response.status_code == 200:
            token = response.json().get("access_token", "")
            self.client.headers["Authorization"] = f"Bearer {token}"

    @task(5)
    def dashboard(self):
        """Тест дашборда (наиболее частый запрос)."""
        self.client.get("/api/dashboard/stats")

    @task(3)
    def list_procurements(self):
        """Тест списка закупок."""
        self.client.get("/api/procurements?limit=20")

    @task(2)
    def search_procurements(self):
        """Поиск закупок."""
        self.client.get("/api/procurements/search?q=строительство")

    @task(2)
    def list_alerts(self):
        """Получение алертов."""
        self.client.get("/api/alerts?limit=10")

    @task(1)
    def analyze_procurement(self):
        """Запуск анализа (тяжёлый запрос)."""
        self.client.post("/api/analysis/analyze/1")

    @task(1)
    def verify_blockchain(self):
        """Верификация блокчейн."""
        self.client.get("/api/blockchain/verify/" + "a" * 64)

    @task(1)
    def health_check(self):
        """Health check."""
        self.client.get("/health")
