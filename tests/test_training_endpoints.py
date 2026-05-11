from unittest.mock import patch

import pytest

from better_life_backend.db.models import DailyRoutine
from better_life_backend.db.models import TrainingPlan
from better_life_backend.db.models import WeeklyPlan


@pytest.fixture
def active_plan(db, user_with_profile):
    plan = TrainingPlan.objects.create(
        user=user_with_profile,
        name="Intermediate Maintain Plan",
        goal="maintain",
        fitness_level="intermediate",
        weeks_duration=4,
        intensity_level=3,
        is_active=True,
        created_by=user_with_profile,
        updated_by=user_with_profile,
    )
    week = WeeklyPlan.objects.create(
        training_plan=plan,
        week_number=1,
        created_by=user_with_profile,
        updated_by=user_with_profile,
    )
    DailyRoutine.objects.create(
        weekly_plan=week,
        day_of_week=1,
        name="Chest & Triceps",
        created_by=user_with_profile,
        updated_by=user_with_profile,
    )
    return plan


class TestActiveTrainingPlanEndpoint:
    url = "/training/plans/active/"

    def test_unauthenticated_returns_401(self, client):
        response = client.get(self.url)
        assert response.status_code == 401

    def test_returns_existing_active_plan(self, auth_client_with_profile, active_plan):
        response = auth_client_with_profile.get(self.url)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(active_plan.id)
        assert data["goal"] == "maintain"
        assert data["is_active"] is True

    def test_response_includes_weekly_plans(
        self, auth_client_with_profile, active_plan
    ):
        response = auth_client_with_profile.get(self.url)
        data = response.json()
        assert "weekly_plans" in data
        assert len(data["weekly_plans"]) == 1
        week = data["weekly_plans"][0]
        assert week["week_number"] == 1
        assert len(week["daily_routines"]) == 1

    def test_response_includes_current_week(
        self, auth_client_with_profile, active_plan
    ):
        response = auth_client_with_profile.get(self.url)
        data = response.json()
        assert "current_week" in data
        assert 1 <= data["current_week"] <= 4

    def test_generates_plan_when_none_exists(
        self, auth_client_with_profile, user_with_profile
    ):
        def _gen(user):
            return TrainingPlan.objects.create(
                user=user,
                name="Auto Plan",
                goal="maintain",
                fitness_level="intermediate",
                weeks_duration=4,
                intensity_level=3,
                is_active=True,
                created_by=user,
                updated_by=user,
            )

        with patch(
            "api.services.training_generator.generate_training_plan",
            side_effect=_gen,
        ) as mock_gen:
            response = auth_client_with_profile.get(self.url)
            assert response.status_code == 200
            mock_gen.assert_called_once_with(user_with_profile)


class TestGenerateTrainingPlanEndpoint:
    url = "/training/plans/generate/"

    def test_unauthenticated_returns_401(self, client):
        response = client.post(self.url)
        assert response.status_code == 401

    def test_get_method_not_allowed(self, auth_client_with_profile):
        response = auth_client_with_profile.get(self.url)
        assert response.status_code == 405

    def test_generates_new_plan(self, auth_client_with_profile, user_with_profile):
        mock_plan = TrainingPlan.objects.create(
            user=user_with_profile,
            name="Muscle Building Plan",
            goal="gain_muscle",
            fitness_level="intermediate",
            weeks_duration=4,
            intensity_level=4,
            is_active=True,
            created_by=user_with_profile,
            updated_by=user_with_profile,
        )
        with patch(
            "api.services.training_generator.generate_training_plan",
            return_value=mock_plan,
        ) as mock_gen:
            response = auth_client_with_profile.post(self.url)
            assert response.status_code == 201
            mock_gen.assert_called_once_with(user_with_profile)

    def test_generated_plan_in_response(
        self, auth_client_with_profile, user_with_profile
    ):
        mock_plan = TrainingPlan.objects.create(
            user=user_with_profile,
            name="Weight Loss Plan",
            goal="lose_weight",
            fitness_level="beginner",
            weeks_duration=4,
            intensity_level=2,
            is_active=True,
            created_by=user_with_profile,
            updated_by=user_with_profile,
        )
        with patch(
            "api.services.training_generator.generate_training_plan",
            return_value=mock_plan,
        ):
            response = auth_client_with_profile.post(self.url)
            data = response.json()
            assert data["goal"] == "lose_weight"
            assert data["fitness_level"] == "beginner"


class TestWorkoutRatingEndpoint:
    url = "/training/ratings/"

    def test_unauthenticated_returns_401(self, client):
        response = client.post(self.url)
        assert response.status_code == 401

    def test_create_rating(
        self, auth_client_with_profile, active_plan, user_with_profile
    ):
        routine = active_plan.weekly_plans.first().daily_routines.first()
        response = auth_client_with_profile.post(
            self.url,
            {
                "daily_routine": str(routine.id),
                "rating": 4,
                "intensity_feedback": "same",
            },
            format="json",
        )
        assert response.status_code == 201

    def test_rating_response_includes_fields(
        self, auth_client_with_profile, active_plan
    ):
        routine = active_plan.weekly_plans.first().daily_routines.first()
        response = auth_client_with_profile.post(
            self.url,
            {
                "daily_routine": str(routine.id),
                "rating": 5,
                "intensity_feedback": "more",
            },
            format="json",
        )
        data = response.json()
        assert data["rating"] == 5
        assert data["intensity_feedback"] == "more"
        assert "id" in data
        assert "completed_at" in data

    def test_rating_adjusts_plan_intensity_up(
        self, auth_client_with_profile, active_plan
    ):
        routine = active_plan.weekly_plans.first().daily_routines.first()
        auth_client_with_profile.post(
            self.url,
            {
                "daily_routine": str(routine.id),
                "rating": 4,
                "intensity_feedback": "more",
            },
            format="json",
        )
        active_plan.refresh_from_db()
        assert active_plan.intensity_level == 4

    def test_rating_adjusts_plan_intensity_down(
        self, auth_client_with_profile, active_plan
    ):
        routine = active_plan.weekly_plans.first().daily_routines.first()
        auth_client_with_profile.post(
            self.url,
            {
                "daily_routine": str(routine.id),
                "rating": 2,
                "intensity_feedback": "less",
            },
            format="json",
        )
        active_plan.refresh_from_db()
        assert active_plan.intensity_level == 2

    def test_intensity_does_not_exceed_max(self, auth_client_with_profile, active_plan):
        active_plan.intensity_level = 5
        active_plan.save(update_fields=["intensity_level"])

        routine = active_plan.weekly_plans.first().daily_routines.first()
        auth_client_with_profile.post(
            self.url,
            {
                "daily_routine": str(routine.id),
                "rating": 5,
                "intensity_feedback": "more",
            },
            format="json",
        )
        active_plan.refresh_from_db()
        assert active_plan.intensity_level == 5

    def test_intensity_does_not_go_below_min(
        self, auth_client_with_profile, active_plan
    ):
        active_plan.intensity_level = 1
        active_plan.save(update_fields=["intensity_level"])

        routine = active_plan.weekly_plans.first().daily_routines.first()
        auth_client_with_profile.post(
            self.url,
            {
                "daily_routine": str(routine.id),
                "rating": 1,
                "intensity_feedback": "less",
            },
            format="json",
        )
        active_plan.refresh_from_db()
        assert active_plan.intensity_level == 1

    def test_get_method_not_allowed(self, auth_client_with_profile):
        response = auth_client_with_profile.get(self.url)
        assert response.status_code == 405
