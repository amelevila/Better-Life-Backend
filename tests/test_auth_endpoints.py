import pytest
from django.contrib.auth.hashers import make_password
from rest_framework.test import APIClient

from better_life_backend.db.models import UserAccount

TOKEN_URL = "/auth/token/"
TOKEN_REFRESH_URL = "/auth/token/refresh/"
ME_URL = "/users/me/"


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
def inactive_user(db):
    return UserAccount.objects.create(
        email="inactive@example.com",
        password_hash=make_password("password123"),
        is_active=False,
    )


@pytest.fixture
def tokens(client, user):
    response = client.post(TOKEN_URL, {"email": user.email, "password": "password123"})
    return response.data


class TestTokenObtain:
    def test_returns_access_and_refresh_tokens(self, client, user):
        response = client.post(
            TOKEN_URL, {"email": user.email, "password": "password123"}
        )
        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data

    def test_tokens_are_jwt_format(self, client, user):
        response = client.post(
            TOKEN_URL, {"email": user.email, "password": "password123"}
        )
        assert response.data["access"].count(".") == 2
        assert response.data["refresh"].count(".") == 2

    def test_rejects_wrong_password(self, client, user):
        response = client.post(
            TOKEN_URL, {"email": user.email, "password": "wrongpassword"}
        )
        assert response.status_code == 400

    def test_rejects_nonexistent_email(self, client, db):
        response = client.post(
            TOKEN_URL, {"email": "nobody@example.com", "password": "password123"}
        )
        assert response.status_code == 400

    def test_rejects_inactive_user(self, client, inactive_user):
        response = client.post(
            TOKEN_URL,
            {"email": inactive_user.email, "password": "password123"},
        )
        assert response.status_code == 400

    def test_rejects_missing_password(self, client, user):
        response = client.post(TOKEN_URL, {"email": user.email})
        assert response.status_code == 400

    def test_rejects_missing_email(self, client, db):
        response = client.post(TOKEN_URL, {"password": "password123"})
        assert response.status_code == 400

    def test_rejects_empty_body(self, client, db):
        response = client.post(TOKEN_URL, {})
        assert response.status_code == 400

    def test_does_not_expose_password_hash(self, client, user):
        response = client.post(
            TOKEN_URL, {"email": user.email, "password": "password123"}
        )
        assert "password_hash" not in response.data
        assert "password" not in response.data


class TestTokenRefresh:
    def test_returns_new_access_token(self, client, tokens):
        response = client.post(TOKEN_REFRESH_URL, {"refresh": tokens["refresh"]})
        assert response.status_code == 200
        assert "access" in response.data

    def test_new_access_token_is_different(self, client, tokens):
        response = client.post(TOKEN_REFRESH_URL, {"refresh": tokens["refresh"]})
        assert response.data["access"] != tokens["access"]

    def test_rejects_invalid_refresh_token(self, client, db):
        response = client.post(TOKEN_REFRESH_URL, {"refresh": "not.a.token"})
        assert response.status_code == 400

    def test_rejects_access_token_as_refresh(self, client, tokens):
        response = client.post(TOKEN_REFRESH_URL, {"refresh": tokens["access"]})
        assert response.status_code == 400

    def test_rejects_missing_refresh_token(self, client, db):
        response = client.post(TOKEN_REFRESH_URL, {})
        assert response.status_code == 400


class TestJWTAuthentication:
    def test_access_token_authenticates_request(self, client, user, tokens):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        response = client.get(ME_URL)
        assert response.status_code == 200
        assert response.data["email"] == user.email

    def test_refreshed_token_authenticates_request(self, client, user, tokens):
        refresh_response = client.post(
            TOKEN_REFRESH_URL, {"refresh": tokens["refresh"]}
        )
        new_access = refresh_response.data["access"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {new_access}")
        response = client.get(ME_URL)
        assert response.status_code == 200
        assert response.data["email"] == user.email

    def test_rejects_tampered_token(self, client, tokens, db):
        tampered = tokens["access"][:-10] + "tampered123"
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {tampered}")
        response = client.get(ME_URL)
        assert response.status_code == 401

    def test_rejects_random_string_as_token(self, client, db):
        client.credentials(HTTP_AUTHORIZATION="Bearer notavalidtoken")
        response = client.get(ME_URL)
        assert response.status_code == 401

    def test_rejects_missing_token(self, client, db):
        response = client.get(ME_URL)
        assert response.status_code == 401

    def test_rejects_token_for_deleted_user(self, client, user, tokens, db):
        user.delete()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        response = client.get(ME_URL)
        assert response.status_code == 401

    def test_rejects_token_for_deactivated_user(self, client, user, tokens, db):
        user.is_active = False
        user.save()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        response = client.get(ME_URL)
        assert response.status_code == 401
