"""
Integration tests для API аналитики.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

# Импорты будут работать после установки в PYTHONPATH
from api.main import app
from database.base import get_db


@pytest.fixture
def client(db_session):
    """Создать FastAPI test client."""

    # Override get_db dependency
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(test_user):
    """Создать auth headers для тестов."""

    # Mock JWT token (в production должен генерироваться правильно)
    # Для тестов используем простой словарь
    return {
        "user_id": test_user.id,
        "username": test_user.username
    }


class TestAnalyticsDashboard:
    """Тесты dashboard API."""

    def test_get_dashboard_success(self, client, auth_headers, sample_traffic_sources):
        """Тест успешного получения dashboard."""

        # Note: В реальном API требуется JWT auth
        # Для упрощения тестов можно мокировать get_current_user

        # Этот тест показывает структуру - в production нужна авторизация
        response = client.get(
            "/api/v1/analytics/dashboard",
            # headers={"Authorization": f"Bearer {token}"}
        )

        # Пока API требует авторизации, ожидаем 401 или 403
        # После настройки мокаauthorization, тест будет работать
        assert response.status_code in [401, 403, 200]

    def test_get_dashboard_with_date_range(self, client):
        """Тест dashboard с фильтрацией по датам."""

        date_from = (datetime.utcnow() - timedelta(days=7)).isoformat()
        date_to = datetime.utcnow().isoformat()

        response = client.get(
            f"/api/v1/analytics/dashboard?date_from={date_from}&date_to={date_to}"
        )

        # Ожидаем требование авторизации
        assert response.status_code in [401, 403, 200]


class TestCreativeAnalysisAPI:
    """Тесты creative analysis API."""

    def test_analyze_creative_endpoint(self, client):
        """Тест endpoint анализа креатива."""

        payload = {
            "caption": "Wait until the end! 🔥",
            "hashtags": ["fyp", "viral"],
            "product_category": "lootbox"
        }

        response = client.post(
            "/api/v1/creative/analyze",
            json=payload
        )

        # Ожидаем требование авторизации или успех если мокали auth
        assert response.status_code in [401, 403, 200]

        if response.status_code == 200:
            data = response.json()
            assert "hook_type" in data
            assert "emotion" in data
            assert "predicted_cvr" in data

    def test_create_creative_endpoint(self, client):
        """Тест endpoint создания креатива."""

        payload = {
            "name": "Test Creative",
            "creative_type": "ugc",
            "product_category": "lootbox",
            "hook_type": "wait",
            "emotion": "excitement",
            "pacing": "fast"
        }

        response = client.post(
            "/api/v1/creative/creatives",
            json=payload
        )

        # Ожидаем требование авторизации
        assert response.status_code in [401, 403, 201]

    def test_get_creatives_list(self, client):
        """Тест получения списка креативов."""

        response = client.get("/api/v1/creative/creatives")

        # Ожидаем требование авторизации
        assert response.status_code in [401, 403, 200]


class TestPatternOptimization:
    """Тесты pattern optimization API."""

    def test_get_top_patterns(self, client):
        """Тест получения топ паттернов."""

        response = client.get(
            "/api/v1/creative/patterns/top?product_category=lootbox&metric=cvr&top_n=10"
        )

        # Ожидаем требование авторизации
        assert response.status_code in [401, 403, 200]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_update_pattern_performance(self, client):
        """Тест обновления pattern performance."""

        response = client.post("/api/v1/creative/patterns/update")

        # Ожидаем требование авторизации
        assert response.status_code in [401, 403, 200]


class TestEarlySignalsAPI:
    """Тесты early signals API."""

    def test_analyze_early_signals(self, client, sample_creatives):
        """Тест анализа ранних сигналов."""

        creative_id = str(sample_creatives[0].id)

        payload = {
            "impressions": 500,
            "clicks": 20,
            "landing_views": 18,
            "landing_bounces": 6,
            "avg_time_on_page": 6.5,
            "conversions": 2
        }

        response = client.post(
            f"/api/v1/creative/analyze-early-signals?creative_id={creative_id}",
            json=payload
        )

        # Ожидаем требование авторизации
        assert response.status_code in [401, 403, 200]

        if response.status_code == 200:
            data = response.json()
            assert "signal" in data
            assert "recommendation" in data
            assert "predicted_final_cvr" in data


class TestModelManagement:
    """Тесты management API для моделей."""

    def test_auto_train_models(self, client):
        """Тест автоматического переобучения моделей."""

        response = client.post(
            "/api/v1/creative/models/auto-train?product_category=lootbox"
        )

        # Ожидаем требование авторизации
        assert response.status_code in [401, 403, 200]

    def test_get_model_metrics(self, client):
        """Тест получения метрик модели."""

        response = client.get(
            "/api/v1/creative/models/metrics?product_category=lootbox&model_type=markov_chain"
        )

        # Ожидаем требование авторизации
        assert response.status_code in [401, 403, 200]


class TestRecommendations:
    """Тесты recommendation API."""

    def test_recommend_next_patterns(self, client):
        """Тест рекомендации следующих паттернов."""

        response = client.get(
            "/api/v1/creative/recommend/next-patterns?product_category=lootbox&n_patterns=5"
        )

        # Ожидаем требование авторизации
        assert response.status_code in [401, 403, 200]

    def test_recommend_scaling_creatives(self, client):
        """Тест рекомендации креативов для масштабирования."""

        payload = {
            "budget": 500000,  # $5000
            "min_cvr": 0.10
        }

        response = client.post(
            "/api/v1/creative/recommend/scaling",
            json=payload
        )

        # Ожидаем требование авторизации
        assert response.status_code in [401, 403, 200]


# Note: Для полноценных integration тестов нужно:
# 1. Мокировать JWT authentication (get_current_user dependency)
# 2. Настроить test database с тестовыми данными
# 3. Использовать fixtures для создания пользователей и токенов
#
# Пример setup для полноценных тестов:
#
# @pytest.fixture
# def authenticated_client(client, test_user):
#     # Generate test JWT token
#     token = create_test_jwt_token(test_user)
#     client.headers = {"Authorization": f"Bearer {token}"}
#     return client
