import uuid
from datetime import date
from decimal import Decimal

import pytest
from django.db.utils import IntegrityError

from better_life_backend.db.models import BodyMetrics
from better_life_backend.db.models import UserAccount
from better_life_backend.db.models import UserProfile


@pytest.fixture
def user_account(db):
    return UserAccount.objects.create(
        email="test@example.com",
        password_hash="hashed_password_123",
    )


@pytest.fixture
def user_profile(db, user_account):
    return UserProfile.objects.create(
        user=user_account,
        first_name="John",
        last_name="Doe",
        dni="12345678A",
        phone="600000000",
        gender="male",
        date_of_birth=date(1990, 1, 15),
        profile_picture_url="https://example.com/photo.jpg",
    )


@pytest.fixture
def body_metrics(db, user_account):
    return BodyMetrics.objects.create(
        user=user_account,
        weight=Decimal("75.50"),
        height=Decimal("178.00"),
        body_fat_pct=Decimal("18.50"),
        muscle_mass_pct=Decimal("42.30"),
        visceral_fat_level=5,
        metabolic_age=28,
    )


class TestUserAccount:
    def test_create(self, user_account):
        assert UserAccount.objects.count() == 1
        assert user_account.email == "test@example.com"

    def test_default_is_active(self, user_account):
        assert user_account.is_active is True

    def test_default_is_member(self, user_account):
        assert user_account.is_member is False

    def test_id_is_uuid(self, user_account):
        assert isinstance(user_account.id, uuid.UUID)

    def test_email_is_unique(self, db, user_account):
        with pytest.raises(IntegrityError):
            UserAccount.objects.create(
                email="test@example.com",
                password_hash="another_hash",
            )

    def test_str(self, user_account):
        assert str(user_account) == "test@example.com"

    def test_created_at_is_set(self, user_account):
        assert user_account.created_at is not None

    def test_updated_at_is_set(self, user_account):
        assert user_account.updated_at is not None

    def test_deleted_at_is_null_by_default(self, user_account):
        assert user_account.deleted_at is None

    def test_audit_fields_null_by_default(self, user_account):
        assert user_account.created_by is None
        assert user_account.updated_by is None
        assert user_account.deleted_by is None


class TestUserProfile:
    def test_create(self, user_profile):
        assert UserProfile.objects.count() == 1
        assert user_profile.first_name == "John"
        assert user_profile.last_name == "Doe"

    def test_id_is_uuid(self, user_profile):
        assert isinstance(user_profile.id, uuid.UUID)

    def test_one_to_one_relation(self, user_account, user_profile):
        assert user_account.profile == user_profile

    def test_cascade_delete(self, db, user_account, user_profile):
        user_account.delete()
        assert UserProfile.objects.count() == 0

    def test_dni_is_unique(self, db, user_account, user_profile):
        second_user = UserAccount.objects.create(
            email="other@example.com",
            password_hash="hash",
        )
        with pytest.raises(IntegrityError):
            UserProfile.objects.create(
                user=second_user,
                dni="12345678A",
            )

    def test_optional_fields_are_nullable(self, db, user_account):
        profile = UserProfile.objects.create(user=user_account)
        assert profile.first_name is None
        assert profile.last_name is None
        assert profile.dni is None
        assert profile.phone is None
        assert profile.gender is None
        assert profile.date_of_birth is None
        assert profile.profile_picture_url is None

    def test_str(self, user_profile):
        assert str(user_profile) == "John Doe"


class TestBodyMetrics:
    def test_create(self, body_metrics):
        assert BodyMetrics.objects.count() == 1
        assert body_metrics.weight == Decimal("75.50")
        assert body_metrics.height == Decimal("178.00")

    def test_id_is_uuid(self, body_metrics):
        assert isinstance(body_metrics.id, uuid.UUID)

    def test_foreign_key_relation(self, user_account, body_metrics):
        assert body_metrics.user == user_account

    def test_multiple_metrics_per_user(self, db, user_account):
        BodyMetrics.objects.create(user=user_account, weight=Decimal("75.00"))
        BodyMetrics.objects.create(user=user_account, weight=Decimal("74.50"))
        assert user_account.body_metrics.count() == 2

    def test_cascade_delete(self, db, user_account, body_metrics):
        user_account.delete()
        assert BodyMetrics.objects.count() == 0

    def test_optional_fields_are_nullable(self, db, user_account):
        metrics = BodyMetrics.objects.create(user=user_account)
        assert metrics.weight is None
        assert metrics.height is None
        assert metrics.body_fat_pct is None
        assert metrics.muscle_mass_pct is None
        assert metrics.visceral_fat_level is None
        assert metrics.metabolic_age is None

    def test_ordering_by_recorded_at_desc(self, db, user_account):
        m1 = BodyMetrics.objects.create(user=user_account, weight=Decimal("80.00"))
        m2 = BodyMetrics.objects.create(user=user_account, weight=Decimal("79.00"))
        metrics = list(user_account.body_metrics.all())
        assert metrics[0] == m2
        assert metrics[1] == m1

    def test_recorded_at_is_set(self, body_metrics):
        assert body_metrics.recorded_at is not None

    def test_str(self, body_metrics):
        expected = (
            f"BodyMetrics(test@example.com @ {body_metrics.recorded_at:%Y-%m-%d})"
        )
        assert str(body_metrics) == expected
