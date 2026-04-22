import pytest
from django.contrib.auth.hashers import make_password
from rest_framework.test import APIClient

from better_life_backend.db.models import BodyMetrics
from better_life_backend.db.models import UserAccount
from better_life_backend.db.models import UserProfile

USERS_URL = "/users/"
ME_URL = "/users/me/"
PROFILE_URL = "/users/me/profile/"
PROFILE_ADD_URL = "/users/me/profile/add/"
BODY_METRICS_URL = "/users/me/body-metrics/"
BODY_METRICS_ADD_URL = "/users/me/body-metrics/add/"


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user(db):
    return UserAccount.objects.create(
        email="test@example.com",
        password_hash=make_password("password123"),
        is_active=True,
    )


@pytest.fixture
def auth_client(client, user):
    user.is_authenticated = True
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def profile(db, user):
    return UserProfile.objects.create(
        user=user,
        first_name="John",
        last_name="Doe",
        phone="600000000",
    )


@pytest.fixture
def body_metric(db, user):
    return BodyMetrics.objects.create(
        user=user,
        weight="75.50",
        height="180.00",
        body_fat_pct="18.50",
    )


class TestUserCreate:
    def test_creates_user_successfully(self, client, db):
        response = client.post(
            USERS_URL, {"email": "new@example.com", "password": "strongpass1"}
        )
        assert response.status_code == 201
        assert response.data["email"] == "new@example.com"
        assert UserAccount.objects.filter(email="new@example.com").exists()

    def test_rejects_duplicate_email(self, client, user):
        response = client.post(
            USERS_URL, {"email": user.email, "password": "strongpass1"}
        )
        assert response.status_code == 400

    def test_rejects_short_password(self, client, db):
        response = client.post(
            USERS_URL, {"email": "new@example.com", "password": "123"}
        )
        assert response.status_code == 400

    def test_rejects_missing_email(self, client, db):
        response = client.post(USERS_URL, {"password": "strongpass1"})
        assert response.status_code == 400

    def test_does_not_return_password_hash(self, client, db):
        response = client.post(
            USERS_URL, {"email": "new@example.com", "password": "strongpass1"}
        )
        assert "password_hash" not in response.data
        assert "password" not in response.data


class TestMe:
    def test_returns_current_user(self, auth_client, user):
        response = auth_client.get(ME_URL)
        assert response.status_code == 200
        assert response.data["email"] == user.email
        assert response.data["id"] == str(user.id)

    def test_rejects_unauthenticated(self, client):
        response = client.get(ME_URL)
        assert response.status_code in (401, 403)


class TestUserProfile:
    def test_returns_profile(self, auth_client, profile):
        response = auth_client.get(PROFILE_URL)
        assert response.status_code == 200
        assert response.data["first_name"] == profile.first_name
        assert response.data["last_name"] == profile.last_name

    def test_returns_404_when_no_profile(self, auth_client):
        response = auth_client.get(PROFILE_URL)
        assert response.status_code == 404

    def test_rejects_unauthenticated(self, client):
        response = client.get(PROFILE_URL)
        assert response.status_code in (401, 403)


class TestUserProfileCreate:
    def test_creates_profile(self, auth_client):
        response = auth_client.post(
            PROFILE_ADD_URL,
            {"first_name": "Jane", "last_name": "Doe", "phone": "611111111"},
        )
        assert response.status_code == 201
        assert response.data["first_name"] == "Jane"

    def test_updates_existing_profile(self, auth_client, profile):
        response = auth_client.post(
            PROFILE_ADD_URL,
            {"first_name": "Updated", "last_name": "Name"},
        )
        assert response.status_code == 201
        profile.refresh_from_db()
        assert profile.first_name == "Updated"

    def test_creates_profile_with_partial_data(self, auth_client):
        response = auth_client.post(PROFILE_ADD_URL, {"first_name": "Solo"})
        assert response.status_code == 201
        assert response.data["first_name"] == "Solo"

    def test_rejects_unauthenticated(self, client):
        response = client.post(PROFILE_ADD_URL, {"first_name": "X"})
        assert response.status_code in (401, 403)


class TestBodyMetricsList:
    def test_returns_own_metrics(self, auth_client, body_metric):
        response = auth_client.get(BODY_METRICS_URL)
        assert response.status_code == 200
        assert len(response.data) == 1
        assert str(response.data[0]["id"]) == str(body_metric.id)

    def test_returns_empty_list_when_no_metrics(self, auth_client):
        response = auth_client.get(BODY_METRICS_URL)
        assert response.status_code == 200
        assert response.data == []

    def test_does_not_return_other_users_metrics(self, auth_client, db):
        other_user = UserAccount.objects.create(
            email="other@example.com",
            password_hash=make_password("password123"),
        )
        BodyMetrics.objects.create(user=other_user, weight="90.00")
        response = auth_client.get(BODY_METRICS_URL)
        assert response.status_code == 200
        assert len(response.data) == 0

    def test_rejects_unauthenticated(self, client):
        response = client.get(BODY_METRICS_URL)
        assert response.status_code in (401, 403)


class TestBodyMetricsAdd:
    def test_creates_body_metric(self, auth_client):
        response = auth_client.post(
            BODY_METRICS_ADD_URL,
            {"weight": "80.00", "height": "175.00", "body_fat_pct": "20.00"},
        )
        assert response.status_code == 201
        assert response.data["weight"] == "80.00"

    def test_creates_multiple_metrics(self, auth_client, user):
        auth_client.post(BODY_METRICS_ADD_URL, {"weight": "80.00"})
        auth_client.post(BODY_METRICS_ADD_URL, {"weight": "79.50"})
        assert BodyMetrics.objects.filter(user=user).count() == 2

    def test_creates_metric_with_partial_data(self, auth_client):
        response = auth_client.post(BODY_METRICS_ADD_URL, {"weight": "77.00"})
        assert response.status_code == 201
        assert response.data["height"] is None

    def test_rejects_unauthenticated(self, client):
        response = client.post(BODY_METRICS_ADD_URL, {"weight": "80.00"})
        assert response.status_code in (401, 403)
