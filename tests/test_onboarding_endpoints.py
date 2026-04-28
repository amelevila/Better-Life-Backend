import pytest
from django.contrib.auth.hashers import make_password
from rest_framework.test import APIClient

from better_life_backend.db.models import UserAccount
from better_life_backend.db.models import UserHealthProfile
from better_life_backend.db.models import UserProfile

PROFILE_ADD_URL = "/users/me/profile/add/"
PROFILE_URL = "/users/me/profile/"
HEALTH_PROFILE_URL = "/users/me/health-profile/"
HEALTH_PROFILE_ADD_URL = "/users/me/health-profile/add/"


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user(db):
    return UserAccount.objects.create(
        email="wizard@example.com",
        password_hash=make_password("password123"),
        is_active=True,
    )


@pytest.fixture
def auth_client(client, user):
    client.force_authenticate(user=user)
    return client


class TestUserProfileFitnessFields:
    def test_creates_profile_with_fitness_fields(self, auth_client):
        response = auth_client.post(
            PROFILE_ADD_URL,
            {
                "first_name": "Ana",
                "main_goal": "lose_weight",
                "activity_level": "moderately_active",
                "fitness_level": "beginner",
                "training_days_per_week": 3,
                "workout_duration_minutes": 45,
                "training_location": "gym",
            },
        )
        assert response.status_code == 201
        assert response.data["main_goal"] == "lose_weight"
        assert response.data["activity_level"] == "moderately_active"
        assert response.data["fitness_level"] == "beginner"
        assert response.data["training_days_per_week"] == 3
        assert response.data["training_location"] == "gym"

    def test_creates_profile_with_nutrition_fields(self, auth_client):
        response = auth_client.post(
            PROFILE_ADD_URL,
            {
                "dietary_preference": "vegetarian",
                "meals_per_day": 4,
                "food_allergies": "nuts, shellfish",
            },
        )
        assert response.status_code == 201
        assert response.data["dietary_preference"] == "vegetarian"
        assert response.data["meals_per_day"] == 4
        assert response.data["food_allergies"] == "nuts, shellfish"

    def test_creates_profile_with_onboarding_completed(self, auth_client):
        response = auth_client.post(
            PROFILE_ADD_URL,
            {"onboarding_completed": True},
        )
        assert response.status_code == 201
        assert response.data["onboarding_completed"] is True

    def test_rejects_invalid_main_goal(self, auth_client):
        response = auth_client.post(
            PROFILE_ADD_URL,
            {"main_goal": "invalid_goal"},
        )
        assert response.status_code == 400

    def test_rejects_invalid_activity_level(self, auth_client):
        response = auth_client.post(
            PROFILE_ADD_URL,
            {"activity_level": "super_active"},
        )
        assert response.status_code == 400

    def test_rejects_invalid_dietary_preference(self, auth_client):
        response = auth_client.post(
            PROFILE_ADD_URL,
            {"dietary_preference": "carnivore"},
        )
        assert response.status_code == 400

    def test_profile_returns_new_fields(self, auth_client, user):
        UserProfile.objects.create(
            user=user,
            main_goal="gain_muscle",
            fitness_level="intermediate",
            dietary_preference="vegan",
            onboarding_completed=True,
        )
        response = auth_client.get(PROFILE_URL)
        assert response.status_code == 200
        assert response.data["main_goal"] == "gain_muscle"
        assert response.data["fitness_level"] == "intermediate"
        assert response.data["dietary_preference"] == "vegan"
        assert response.data["onboarding_completed"] is True


class TestUserHealthProfile:
    def test_creates_health_profile(self, auth_client):
        response = auth_client.post(
            HEALTH_PROFILE_ADD_URL,
            {
                "diabetes": "none",
                "hypertension": False,
                "heart_condition": False,
                "celiac_disease": False,
                "lactose_intolerance": True,
            },
        )
        assert response.status_code == 201
        assert response.data["diabetes"] == "none"
        assert response.data["lactose_intolerance"] is True

    def test_creates_health_profile_with_text_fields(self, auth_client):
        response = auth_client.post(
            HEALTH_PROFILE_ADD_URL,
            {
                "injuries": "lower back pain",
                "medications": "ibuprofen",
                "other_conditions": "asthma",
            },
        )
        assert response.status_code == 201
        assert response.data["injuries"] == "lower back pain"
        assert response.data["medications"] == "ibuprofen"
        assert response.data["other_conditions"] == "asthma"

    def test_creates_health_profile_with_diabetes_type(self, auth_client):
        response = auth_client.post(
            HEALTH_PROFILE_ADD_URL,
            {"diabetes": "type2", "hypertension": True},
        )
        assert response.status_code == 201
        assert response.data["diabetes"] == "type2"
        assert response.data["hypertension"] is True

    def test_updates_existing_health_profile(self, auth_client, user):
        UserHealthProfile.objects.create(user=user, diabetes="none")
        response = auth_client.post(
            HEALTH_PROFILE_ADD_URL,
            {"diabetes": "type1"},
        )
        assert response.status_code == 201
        assert response.data["diabetes"] == "type1"
        assert UserHealthProfile.objects.filter(user=user).count() == 1

    def test_returns_health_profile(self, auth_client, user):
        UserHealthProfile.objects.create(
            user=user,
            diabetes="prediabetes",
            celiac_disease=True,
        )
        response = auth_client.get(HEALTH_PROFILE_URL)
        assert response.status_code == 200
        assert response.data["diabetes"] == "prediabetes"
        assert response.data["celiac_disease"] is True

    def test_returns_404_when_no_health_profile(self, auth_client):
        response = auth_client.get(HEALTH_PROFILE_URL)
        assert response.status_code == 404

    def test_rejects_invalid_diabetes_value(self, auth_client):
        response = auth_client.post(
            HEALTH_PROFILE_ADD_URL,
            {"diabetes": "type3"},
        )
        assert response.status_code == 400

    def test_rejects_unauthenticated_get(self, client):
        response = client.get(HEALTH_PROFILE_URL)
        assert response.status_code in (401, 403)

    def test_rejects_unauthenticated_post(self, client):
        response = client.post(HEALTH_PROFILE_ADD_URL, {"diabetes": "none"})
        assert response.status_code in (401, 403)
