from datetime import date
from decimal import Decimal

from api.services.nutrition_generator import _calculate_tdee
from api.services.nutrition_generator import _filter_recipes
from api.services.nutrition_generator import _macro_targets
from api.services.nutrition_generator import _parse_food_keywords
from api.services.nutrition_generator import _pick_recipe
from better_life_backend.db.models import Recipe


class TestCalculateTdee:
    def test_male_moderately_active(self, user_with_profile):
        tdee = _calculate_tdee(user_with_profile.profile)
        # Male, 75kg, 178cm, ~35 years old, moderately_active (×1.55)
        # BMR ≈ 10*75 + 6.25*178 - 5*35 + 5 = 1762.5 → TDEE ≈ 2732
        assert 2400 <= tdee <= 3000

    def test_female_profile(self, db, user):
        from better_life_backend.db.models import BodyMetrics, UserProfile

        UserProfile.objects.create(
            user=user,
            gender="female",
            date_of_birth=date(1995, 3, 10),
            activity_level="lightly_active",
            main_goal="lose_weight",
            created_by=user,
            updated_by=user,
        )
        BodyMetrics.objects.create(
            user=user,
            weight=Decimal("60.0"),
            height=Decimal("165.0"),
            created_by=user,
            updated_by=user,
        )
        tdee = _calculate_tdee(user.profile)
        # Female, 60kg, 165cm, ~31 years old, lightly_active (×1.375)
        # BMR ≈ 10*60 + 6.25*165 - 5*31 - 161 = 1270 → TDEE ≈ 1746
        assert 1500 <= tdee <= 2100

    def test_missing_body_metrics_uses_defaults(self, db, user):
        from better_life_backend.db.models import UserProfile

        UserProfile.objects.create(
            user=user,
            activity_level="sedentary",
            main_goal="maintain",
            created_by=user,
            updated_by=user,
        )
        tdee = _calculate_tdee(user.profile)
        # defaults: 70kg, 170cm, age 30, sedentary (×1.20)
        assert tdee > 0

    def test_unknown_activity_uses_default_factor(self, db, user):
        from better_life_backend.db.models import BodyMetrics, UserProfile

        UserProfile.objects.create(
            user=user,
            gender="male",
            activity_level="unknown_level",
            created_by=user,
            updated_by=user,
        )
        BodyMetrics.objects.create(
            user=user,
            weight=Decimal("70.0"),
            height=Decimal("170.0"),
            created_by=user,
            updated_by=user,
        )
        tdee = _calculate_tdee(user.profile)
        assert tdee > 0


class TestMacroTargets:
    def test_maintain_goal(self):
        protein, carbs, fat = _macro_targets(2000, "maintain", "omnivore")
        assert protein == round(2000 * 0.25 / 4)
        assert carbs == round(2000 * 0.45 / 4)
        assert fat == round(2000 * 0.30 / 9)

    def test_lose_weight_goal(self):
        protein, carbs, fat = _macro_targets(1700, "lose_weight", "omnivore")
        assert protein == round(1700 * 0.35 / 4)

    def test_gain_muscle_goal(self):
        protein, carbs, fat = _macro_targets(2300, "gain_muscle", "omnivore")
        assert protein == round(2300 * 0.30 / 4)

    def test_keto_diet_overrides_goal(self):
        protein, carbs, fat = _macro_targets(2000, "maintain", "keto")
        assert fat == round(2000 * 0.65 / 9)
        assert carbs == round(2000 * 0.10 / 4)

    def test_total_calories_approximately_correct(self):
        protein, carbs, fat = _macro_targets(2000, "maintain", "omnivore")
        total = protein * 4 + carbs * 4 + fat * 9
        assert abs(total - 2000) < 50


class TestParseFoodKeywords:
    def test_empty_returns_empty(self):
        assert _parse_food_keywords(None) == []
        assert _parse_food_keywords("") == []

    def test_comma_separated(self):
        result = _parse_food_keywords("chicken, rice, broccoli")
        assert result == ["chicken", "rice", "broccoli"]

    def test_semicolon_separated(self):
        result = _parse_food_keywords("salmon;tuna;cod")
        assert result == ["salmon", "tuna", "cod"]

    def test_newline_separated(self):
        result = _parse_food_keywords("apple\nbanana\norange")
        assert result == ["apple", "banana", "orange"]

    def test_strips_whitespace(self):
        result = _parse_food_keywords("  chicken  ,  rice  ")
        assert result == ["chicken", "rice"]

    def test_lowercase(self):
        result = _parse_food_keywords("Chicken, RICE, Broccoli")
        assert result == ["chicken", "rice", "broccoli"]

    def test_skips_empty_segments(self):
        result = _parse_food_keywords("chicken,,rice,")
        assert result == ["chicken", "rice"]


class TestFilterRecipes:
    def test_filters_by_meal_type(self, db, user, recipe, lunch_recipe):
        from better_life_backend.db.models import UserProfile

        profile = UserProfile.objects.create(
            user=user,
            dietary_preference="omnivore",
            created_by=user,
            updated_by=user,
        )
        results = _filter_recipes("breakfast", profile)
        assert all(r.meal_type == "breakfast" for r in results)
        assert recipe in results
        assert lunch_recipe not in results

    def test_vegan_filter(self, db, user, recipe):
        from better_life_backend.db.models import UserProfile

        Recipe.objects.create(
            name="Beef steak",
            meal_type="breakfast",
            kcal=500,
            protein_g=Decimal("40.0"),
            carbs_g=Decimal("0.0"),
            fat_g=Decimal("35.0"),
            is_vegan=False,
            created_by=user,
            updated_by=user,
        )
        profile = UserProfile.objects.create(
            user=user,
            dietary_preference="vegan",
            created_by=user,
            updated_by=user,
        )
        results = _filter_recipes("breakfast", profile)
        assert all(r.is_vegan for r in results)
        assert recipe in results

    def test_nut_allergy_filter(self, db, user):
        from better_life_backend.db.models import UserHealthProfile, UserProfile

        safe = Recipe.objects.create(
            name="Plain oatmeal",
            meal_type="breakfast",
            kcal=300,
            protein_g=Decimal("10.0"),
            carbs_g=Decimal("50.0"),
            fat_g=Decimal("5.0"),
            contains_nuts=False,
            created_by=user,
            updated_by=user,
        )
        nut_recipe = Recipe.objects.create(
            name="Almond butter toast",
            meal_type="breakfast",
            kcal=400,
            protein_g=Decimal("12.0"),
            carbs_g=Decimal("45.0"),
            fat_g=Decimal("15.0"),
            contains_nuts=True,
            created_by=user,
            updated_by=user,
        )
        profile = UserProfile.objects.create(
            user=user,
            dietary_preference="omnivore",
            created_by=user,
            updated_by=user,
        )
        UserHealthProfile.objects.create(
            user=user,
            nut_allergy=True,
            created_by=user,
            updated_by=user,
        )
        results = _filter_recipes("breakfast", profile)
        assert safe in results
        assert nut_recipe not in results

    def test_disliked_foods_excluded(self, db, user, recipe):
        from better_life_backend.db.models import UserProfile

        profile = UserProfile.objects.create(
            user=user,
            dietary_preference="omnivore",
            disliked_foods="oats",
            created_by=user,
            updated_by=user,
        )
        results = _filter_recipes("breakfast", profile)
        assert recipe not in results

    def test_celiac_filter(self, db, user):
        from better_life_backend.db.models import UserHealthProfile, UserProfile

        safe = Recipe.objects.create(
            name="Rice porridge",
            meal_type="breakfast",
            kcal=280,
            protein_g=Decimal("6.0"),
            carbs_g=Decimal("58.0"),
            fat_g=Decimal("2.0"),
            is_gluten_free=True,
            created_by=user,
            updated_by=user,
        )
        gluten = Recipe.objects.create(
            name="Wheat bread toast",
            meal_type="breakfast",
            kcal=250,
            protein_g=Decimal("8.0"),
            carbs_g=Decimal("48.0"),
            fat_g=Decimal("3.0"),
            is_gluten_free=False,
            created_by=user,
            updated_by=user,
        )
        profile = UserProfile.objects.create(
            user=user,
            dietary_preference="omnivore",
            created_by=user,
            updated_by=user,
        )
        UserHealthProfile.objects.create(
            user=user,
            celiac_disease=True,
            created_by=user,
            updated_by=user,
        )
        results = _filter_recipes("breakfast", profile)
        assert safe in results
        assert gluten not in results


class TestPickRecipe:
    def test_returns_none_when_pool_empty(self):
        result = _pick_recipe("breakfast", [], set())
        assert result is None

    def test_picks_from_available(self, db, user, recipe):
        result = _pick_recipe("breakfast", [recipe], set())
        assert result == recipe

    def test_excludes_this_week(self, db, user, recipe, lunch_recipe):
        results = set()
        for _ in range(20):
            r = _pick_recipe("breakfast", [recipe, lunch_recipe], {recipe.pk})
            results.add(r.pk)
        # lunch_recipe should be picked since recipe is excluded
        assert lunch_recipe.pk in results

    def test_falls_back_to_all_when_all_excluded(self, db, user, recipe):
        result = _pick_recipe("breakfast", [recipe], {recipe.pk})
        assert result == recipe

    def test_prefers_favorite_keywords(self, db, user, recipe, lunch_recipe):
        # recipe is "Oats with berries", lunch_recipe is "Grilled chicken salad"
        # preferred keyword: "oats"
        results = set()
        for _ in range(20):
            r = _pick_recipe("breakfast", [recipe, lunch_recipe], set(), ["oats"])
            results.add(r.pk)
        assert recipe.pk in results
        # Should always pick the preferred one when available
        assert all(
            _pick_recipe("breakfast", [recipe, lunch_recipe], set(), ["oats"]) == recipe
            for _ in range(10)
        )
