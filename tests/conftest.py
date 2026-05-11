from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth.hashers import make_password
from rest_framework.test import APIClient

from better_life_backend.db.models import Exercise
from better_life_backend.db.models import Recipe
from better_life_backend.db.models import UserAccount
from better_life_backend.db.models import UserHealthProfile
from better_life_backend.db.models import UserProfile


@pytest.fixture
def user(db):
    return UserAccount.objects.create(
        email="test@example.com",
        password_hash=make_password("testpass123"),
    )


@pytest.fixture
def user_with_profile(db, user):
    from better_life_backend.db.models import BodyMetrics

    UserProfile.objects.create(
        user=user,
        first_name="Test",
        last_name="User",
        gender="male",
        date_of_birth=date(1990, 6, 15),
        activity_level="moderately_active",
        main_goal="maintain",
        fitness_level="intermediate",
        training_days_per_week=3,
        workout_duration_minutes=60,
        training_location="gym",
        dietary_preference="omnivore",
        meals_per_day=3,
        created_by=user,
        updated_by=user,
    )
    UserHealthProfile.objects.create(user=user, created_by=user, updated_by=user)
    BodyMetrics.objects.create(
        user=user,
        weight=Decimal("75.0"),
        height=Decimal("178.0"),
        created_by=user,
        updated_by=user,
    )
    return user


@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def auth_client_with_profile(user_with_profile):
    client = APIClient()
    client.force_authenticate(user=user_with_profile)
    return client


@pytest.fixture
def recipe(db, user):
    return Recipe.objects.create(
        name="Oats with berries",
        meal_type="breakfast",
        kcal=350,
        protein_g=Decimal("12.0"),
        carbs_g=Decimal("55.0"),
        fat_g=Decimal("8.0"),
        fiber_g=Decimal("6.0"),
        is_vegan=True,
        is_vegetarian=True,
        created_by=user,
        updated_by=user,
    )


@pytest.fixture
def lunch_recipe(db, user):
    return Recipe.objects.create(
        name="Grilled chicken salad",
        meal_type="lunch",
        kcal=480,
        protein_g=Decimal("42.0"),
        carbs_g=Decimal("20.0"),
        fat_g=Decimal("18.0"),
        fiber_g=Decimal("5.0"),
        created_by=user,
        updated_by=user,
    )


@pytest.fixture
def dinner_recipe(db, user):
    return Recipe.objects.create(
        name="Salmon with vegetables",
        meal_type="dinner",
        kcal=520,
        protein_g=Decimal("45.0"),
        carbs_g=Decimal("25.0"),
        fat_g=Decimal("20.0"),
        fiber_g=Decimal("7.0"),
        created_by=user,
        updated_by=user,
    )


@pytest.fixture
def exercise(db, user):
    return Exercise.objects.create(
        name="Push-up",
        muscle_group="chest",
        exercise_type="reps",
        default_sets=3,
        default_reps=12,
        rest_seconds=60,
        difficulty="beginner",
        equipment="none",
        created_by=user,
        updated_by=user,
    )
