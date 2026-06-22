"""
Smoke tests for forecast, recommendations, and NILM model-card endpoints.

These verify route registration, auth protection, and basic response shape
without requiring real household data or a running MongoDB instance.
"""

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.db.mongodb import get_db
from app.main import app


MISSING_HOUSEHOLD_ID = "000000000000000000000000"


class FakeCollection:
    async def find_one(self, query):
        return None


class FakeDb:
    households = FakeCollection()


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = lambda: FakeDb()
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    token = create_access_token("user-123", "demo@example.com")
    return {"Authorization": f"Bearer {token}"}


class TestForecastEndpoint:
    def test_missing_household_returns_error(self, client, auth_headers):
        response = client.get(
            f"/api/v1/forecast/{MISSING_HOUSEHOLD_ID}",
            headers=auth_headers,
        )

        assert response.status_code == 404, response.text

    def test_requires_auth(self, client):
        response = client.get(f"/api/v1/forecast/{MISSING_HOUSEHOLD_ID}")

        assert response.status_code in (401, 403)


class TestRecommendationsEndpoint:
    def test_missing_household_returns_error(self, client, auth_headers):
        response = client.get(
            f"/api/v1/recommendations/{MISSING_HOUSEHOLD_ID}",
            headers=auth_headers,
        )

        assert response.status_code == 404, response.text

    def test_requires_auth(self, client):
        response = client.get(f"/api/v1/recommendations/{MISSING_HOUSEHOLD_ID}")

        assert response.status_code in (401, 403)


class TestNilmModelCard:
    def test_model_card_returns_200(self, client, auth_headers):
        response = client.get("/api/v1/nilm/model-card", headers=auth_headers)

        assert response.status_code == 200, response.text
        assert response.json()["version"] == "nilm_v1"

    def test_model_card_requires_auth(self, client):
        response = client.get("/api/v1/nilm/model-card")

        assert response.status_code in (401, 403)

    def test_shap_endpoint_exists(self, client, auth_headers):
        response = client.get("/api/v1/nilm/shap", headers=auth_headers)

        assert response.status_code == 200, response.text
        assert "feature_importance" in response.json()

    def test_data_validation_endpoint_exists(self, client, auth_headers):
        response = client.get("/api/v1/nilm/data-validation", headers=auth_headers)

        assert response.status_code in (200, 404), response.text
        if response.status_code == 200:
            assert "adf_statistic" in response.json()

    def test_data_validation_requires_auth(self, client):
        response = client.get("/api/v1/nilm/data-validation")

        assert response.status_code in (401, 403)
