from unittest.mock import patch

import pytest

from better_life_backend.db.models import NutritionPlan
from better_life_backend.db.models import WeeklyNutritionPlan


@pytest.fixture
def active_plan(db, user_with_profile):
    plan = NutritionPlan.objects.create(
        user=user_with_profile,
        name="Maintenance Nutrition Plan",
        goal="maintain",
        weeks_duration=4,
        daily_kcal_target=2200,
        daily_protein_g=138,
        daily_carbs_g=248,
        daily_fat_g=73,
        is_active=True,
        created_by=user_with_profile,
        updated_by=user_with_profile,
    )
    WeeklyNutritionPlan.objects.create(
        nutrition_plan=plan,
        week_number=1,
        created_by=user_with_profile,
        updated_by=user_with_profile,
    )
    return plan


class TestActiveNutritionPlanEndpoint:
    url = "/nutrition/plans/active/"

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

    def test_response_includes_macros(self, auth_client_with_profile, active_plan):
        response = auth_client_with_profile.get(self.url)
        data = response.json()
        assert data["daily_kcal_target"] == 2200
        assert data["daily_protein_g"] == 138
        assert data["daily_carbs_g"] == 248
        assert data["daily_fat_g"] == 73

    def test_response_includes_weekly_plans(
        self, auth_client_with_profile, active_plan
    ):
        response = auth_client_with_profile.get(self.url)
        data = response.json()
        assert "weekly_plans" in data
        assert len(data["weekly_plans"]) == 1
        assert data["weekly_plans"][0]["week_number"] == 1

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
            return NutritionPlan.objects.create(
                user=user,
                name="Auto-generated Plan",
                goal="maintain",
                weeks_duration=4,
                daily_kcal_target=2200,
                daily_protein_g=138,
                daily_carbs_g=248,
                daily_fat_g=73,
                is_active=True,
                created_by=user,
                updated_by=user,
            )

        with patch(
            "api.services.nutrition_generator.generate_nutrition_plan",
            side_effect=_gen,
        ) as mock_gen:
            response = auth_client_with_profile.get(self.url)
            assert response.status_code == 200
            mock_gen.assert_called_once_with(user_with_profile)


class TestGenerateNutritionPlanEndpoint:
    url = "/nutrition/plans/generate/"

    def test_unauthenticated_returns_401(self, client):
        response = client.post(self.url)
        assert response.status_code == 401

    def test_get_method_not_allowed(self, auth_client_with_profile):
        response = auth_client_with_profile.get(self.url)
        assert response.status_code == 405

    def test_generates_new_plan(self, auth_client_with_profile, user_with_profile):
        mock_plan = NutritionPlan.objects.create(
            user=user_with_profile,
            name="Weight Loss Nutrition Plan",
            goal="lose_weight",
            weeks_duration=4,
            daily_kcal_target=1700,
            daily_protein_g=149,
            daily_carbs_g=170,
            daily_fat_g=47,
            is_active=True,
            created_by=user_with_profile,
            updated_by=user_with_profile,
        )
        with patch(
            "api.services.nutrition_generator.generate_nutrition_plan",
            return_value=mock_plan,
        ) as mock_gen:
            response = auth_client_with_profile.post(self.url)
            assert response.status_code == 201
            mock_gen.assert_called_once_with(user_with_profile)

    def test_generated_plan_in_response(
        self, auth_client_with_profile, user_with_profile
    ):
        mock_plan = NutritionPlan.objects.create(
            user=user_with_profile,
            name="Fitness Nutrition Plan",
            goal="improve_fitness",
            weeks_duration=4,
            daily_kcal_target=2100,
            daily_protein_g=147,
            daily_carbs_g=231,
            daily_fat_g=65,
            is_active=True,
            created_by=user_with_profile,
            updated_by=user_with_profile,
        )
        with patch(
            "api.services.nutrition_generator.generate_nutrition_plan",
            return_value=mock_plan,
        ):
            response = auth_client_with_profile.post(self.url)
            data = response.json()
            assert data["goal"] == "improve_fitness"
            assert data["is_active"] is True
