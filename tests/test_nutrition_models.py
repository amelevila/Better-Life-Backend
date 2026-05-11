import uuid
from decimal import Decimal

import pytest

from better_life_backend.db.models import DailyMealPlan
from better_life_backend.db.models import MealEntry
from better_life_backend.db.models import NutritionPlan
from better_life_backend.db.models import Recipe
from better_life_backend.db.models import WeeklyNutritionPlan


@pytest.fixture
def nutrition_plan(db, user):
    return NutritionPlan.objects.create(
        user=user,
        name="Maintenance Nutrition Plan",
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


@pytest.fixture
def weekly_plan(db, nutrition_plan, user):
    return WeeklyNutritionPlan.objects.create(
        nutrition_plan=nutrition_plan,
        week_number=1,
        created_by=user,
        updated_by=user,
    )


@pytest.fixture
def daily_plan(db, weekly_plan, user):
    return DailyMealPlan.objects.create(
        weekly_nutrition_plan=weekly_plan,
        day_of_week=1,
        total_kcal=2200,
        total_protein_g=Decimal("138.0"),
        total_carbs_g=Decimal("248.0"),
        total_fat_g=Decimal("73.0"),
        created_by=user,
        updated_by=user,
    )


class TestRecipe:
    def test_create(self, recipe):
        assert Recipe.objects.count() == 1
        assert recipe.name == "Oats with berries"
        assert recipe.meal_type == "breakfast"

    def test_id_is_uuid(self, recipe):
        assert isinstance(recipe.id, uuid.UUID)

    def test_str(self, recipe):
        assert str(recipe) == "Oats with berries"

    def test_name_is_unique(self, db, recipe, user):
        from django.db.utils import IntegrityError

        with pytest.raises(IntegrityError):
            Recipe.objects.create(
                name="Oats with berries",
                meal_type="lunch",
                kcal=400,
                protein_g=Decimal("15.0"),
                carbs_g=Decimal("50.0"),
                fat_g=Decimal("10.0"),
                created_by=user,
                updated_by=user,
            )

    def test_dietary_flags_default_false(self, db, user):
        r = Recipe.objects.create(
            name="Plain rice",
            meal_type="lunch",
            kcal=200,
            protein_g=Decimal("4.0"),
            carbs_g=Decimal("44.0"),
            fat_g=Decimal("1.0"),
            created_by=user,
            updated_by=user,
        )
        assert r.is_vegan is False
        assert r.is_vegetarian is False
        assert r.is_gluten_free is False
        assert r.is_lactose_free is False
        assert r.is_keto is False
        assert r.is_diabetic_friendly is False

    def test_allergen_flags_default_false(self, db, user):
        r = Recipe.objects.create(
            name="White pasta",
            meal_type="dinner",
            kcal=380,
            protein_g=Decimal("14.0"),
            carbs_g=Decimal("75.0"),
            fat_g=Decimal("2.0"),
            created_by=user,
            updated_by=user,
        )
        assert r.contains_nuts is False
        assert r.contains_eggs is False
        assert r.contains_shellfish is False
        assert r.contains_soy is False

    def test_vegan_recipe(self, db, user):
        r = Recipe.objects.create(
            name="Tofu stir fry",
            meal_type="dinner",
            kcal=320,
            protein_g=Decimal("18.0"),
            carbs_g=Decimal("30.0"),
            fat_g=Decimal("12.0"),
            is_vegan=True,
            is_vegetarian=True,
            created_by=user,
            updated_by=user,
        )
        assert r.is_vegan is True
        assert r.is_vegetarian is True

    def test_macros_stored_as_decimal(self, recipe):
        assert isinstance(recipe.protein_g, Decimal)
        assert isinstance(recipe.carbs_g, Decimal)
        assert isinstance(recipe.fat_g, Decimal)


class TestNutritionPlan:
    def test_create(self, nutrition_plan):
        assert NutritionPlan.objects.count() == 1
        assert nutrition_plan.name == "Maintenance Nutrition Plan"
        assert nutrition_plan.goal == "maintain"
        assert nutrition_plan.is_active is True

    def test_id_is_uuid(self, nutrition_plan):
        assert isinstance(nutrition_plan.id, uuid.UUID)

    def test_str(self, nutrition_plan):
        assert str(nutrition_plan) == "Maintenance Nutrition Plan (test@example.com)"

    def test_cascade_delete(self, db, user, nutrition_plan):
        user.delete()
        assert NutritionPlan.objects.count() == 0

    def test_multiple_plans_per_user(self, db, user, nutrition_plan):
        NutritionPlan.objects.create(
            user=user,
            name="Weight Loss Plan",
            goal="lose_weight",
            weeks_duration=4,
            daily_kcal_target=1700,
            daily_protein_g=150,
            daily_carbs_g=155,
            daily_fat_g=47,
            is_active=False,
            created_by=user,
            updated_by=user,
        )
        assert user.nutrition_plans.count() == 2

    def test_generated_at_is_set(self, nutrition_plan):
        assert nutrition_plan.generated_at is not None

    def test_macros_are_integers(self, nutrition_plan):
        assert isinstance(nutrition_plan.daily_kcal_target, int)
        assert isinstance(nutrition_plan.daily_protein_g, int)
        assert isinstance(nutrition_plan.daily_carbs_g, int)
        assert isinstance(nutrition_plan.daily_fat_g, int)


class TestWeeklyNutritionPlan:
    def test_create(self, weekly_plan):
        assert WeeklyNutritionPlan.objects.count() == 1
        assert weekly_plan.week_number == 1

    def test_id_is_uuid(self, weekly_plan):
        assert isinstance(weekly_plan.id, uuid.UUID)

    def test_str(self, weekly_plan):
        assert "Week 1" in str(weekly_plan)
        assert "Maintenance Nutrition Plan" in str(weekly_plan)

    def test_ordering_by_week_number(self, db, nutrition_plan, user):
        w3 = WeeklyNutritionPlan.objects.create(
            nutrition_plan=nutrition_plan,
            week_number=3,
            created_by=user,
            updated_by=user,
        )
        w1 = WeeklyNutritionPlan.objects.create(
            nutrition_plan=nutrition_plan,
            week_number=1,
            created_by=user,
            updated_by=user,
        )
        w2 = WeeklyNutritionPlan.objects.create(
            nutrition_plan=nutrition_plan,
            week_number=2,
            created_by=user,
            updated_by=user,
        )
        weeks = list(nutrition_plan.weekly_plans.all())
        assert weeks[0] == w1
        assert weeks[1] == w2
        assert weeks[2] == w3

    def test_cascade_delete_from_plan(self, db, nutrition_plan, weekly_plan):
        nutrition_plan.delete()
        assert WeeklyNutritionPlan.objects.count() == 0


class TestDailyMealPlan:
    def test_create(self, daily_plan):
        assert DailyMealPlan.objects.count() == 1
        assert daily_plan.day_of_week == 1
        assert daily_plan.total_kcal == 2200

    def test_id_is_uuid(self, daily_plan):
        assert isinstance(daily_plan.id, uuid.UUID)

    def test_str(self, daily_plan):
        assert "Day 1" in str(daily_plan)
        assert "Week 1" in str(daily_plan)

    def test_ordering_by_day(self, db, weekly_plan, user):
        d3 = DailyMealPlan.objects.create(
            weekly_nutrition_plan=weekly_plan,
            day_of_week=3,
            created_by=user,
            updated_by=user,
        )
        d1 = DailyMealPlan.objects.create(
            weekly_nutrition_plan=weekly_plan,
            day_of_week=1,
            created_by=user,
            updated_by=user,
        )
        d2 = DailyMealPlan.objects.create(
            weekly_nutrition_plan=weekly_plan,
            day_of_week=2,
            created_by=user,
            updated_by=user,
        )
        days = list(weekly_plan.daily_meal_plans.all())
        assert days[0] == d1
        assert days[1] == d2
        assert days[2] == d3

    def test_cascade_delete_from_weekly(self, db, weekly_plan, daily_plan):
        weekly_plan.delete()
        assert DailyMealPlan.objects.count() == 0

    def test_default_totals_are_zero(self, db, weekly_plan, user):
        plan = DailyMealPlan.objects.create(
            weekly_nutrition_plan=weekly_plan,
            day_of_week=2,
            created_by=user,
            updated_by=user,
        )
        assert plan.total_kcal == 0
        assert plan.total_protein_g == Decimal("0")


class TestMealEntry:
    def test_create(self, db, daily_plan, recipe, user):
        entry = MealEntry.objects.create(
            daily_meal_plan=daily_plan,
            recipe=recipe,
            meal_type="breakfast",
            order=0,
            serving_multiplier=Decimal("1.0"),
            kcal=350,
            protein_g=Decimal("12.0"),
            carbs_g=Decimal("55.0"),
            fat_g=Decimal("8.0"),
            created_by=user,
            updated_by=user,
        )
        assert MealEntry.objects.count() == 1
        assert entry.kcal == 350
        assert entry.recipe == recipe

    def test_id_is_uuid(self, db, daily_plan, recipe, user):
        entry = MealEntry.objects.create(
            daily_meal_plan=daily_plan,
            recipe=recipe,
            meal_type="breakfast",
            order=0,
            serving_multiplier=Decimal("1.0"),
            kcal=350,
            protein_g=Decimal("12.0"),
            carbs_g=Decimal("55.0"),
            fat_g=Decimal("8.0"),
            created_by=user,
            updated_by=user,
        )
        assert isinstance(entry.id, uuid.UUID)

    def test_str(self, db, daily_plan, recipe, user):
        entry = MealEntry.objects.create(
            daily_meal_plan=daily_plan,
            recipe=recipe,
            meal_type="breakfast",
            order=0,
            serving_multiplier=Decimal("1.0"),
            kcal=350,
            protein_g=Decimal("12.0"),
            carbs_g=Decimal("55.0"),
            fat_g=Decimal("8.0"),
            created_by=user,
            updated_by=user,
        )
        assert str(entry) == "Oats with berries (breakfast)"

    def test_ordering_by_order(self, db, daily_plan, recipe, user):
        e2 = MealEntry.objects.create(
            daily_meal_plan=daily_plan,
            recipe=recipe,
            meal_type="breakfast",
            order=2,
            serving_multiplier=Decimal("1.0"),
            kcal=200,
            protein_g=Decimal("10.0"),
            carbs_g=Decimal("30.0"),
            fat_g=Decimal("5.0"),
            created_by=user,
            updated_by=user,
        )
        e0 = MealEntry.objects.create(
            daily_meal_plan=daily_plan,
            recipe=recipe,
            meal_type="breakfast",
            order=0,
            serving_multiplier=Decimal("1.0"),
            kcal=350,
            protein_g=Decimal("12.0"),
            carbs_g=Decimal("55.0"),
            fat_g=Decimal("8.0"),
            created_by=user,
            updated_by=user,
        )
        entries = list(daily_plan.meal_entries.all())
        assert entries[0] == e0
        assert entries[1] == e2

    def test_cascade_delete_from_daily(self, db, daily_plan, recipe, user):
        MealEntry.objects.create(
            daily_meal_plan=daily_plan,
            recipe=recipe,
            meal_type="breakfast",
            order=0,
            serving_multiplier=Decimal("1.0"),
            kcal=350,
            protein_g=Decimal("12.0"),
            carbs_g=Decimal("55.0"),
            fat_g=Decimal("8.0"),
            created_by=user,
            updated_by=user,
        )
        daily_plan.delete()
        assert MealEntry.objects.count() == 0
