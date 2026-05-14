# Generate a personalised 4-week nutrition plan for a user based on their profile.
import random
import re
from datetime import date
from decimal import Decimal

from better_life_backend.db.models import DailyMealPlan
from better_life_backend.db.models import MealEntry
from better_life_backend.db.models import NutritionPlan
from better_life_backend.db.models import Recipe
from better_life_backend.db.models import UserProfile
from better_life_backend.db.models import WeeklyNutritionPlan

# Activity level multipliers for TDEE (Mifflin-St Jeor)
ACTIVITY_FACTORS = {
    "sedentary": 1.20,
    "lightly_active": 1.375,
    "moderately_active": 1.55,
    "very_active": 1.725,
    "extra_active": 1.90,
}

# Calorie delta per goal
GOAL_DELTA_KCAL = {
    "lose_weight": -500,
    "gain_muscle": +300,
    "maintain": 0,
    "improve_fitness": +100,
    "increase_flexibility": 0,
}

# Macro % of total calories (protein, carbs, fat)
MACRO_RATIOS = {
    "lose_weight": (0.35, 0.40, 0.25),
    "gain_muscle": (0.30, 0.45, 0.25),
    "maintain": (0.25, 0.45, 0.30),
    "improve_fitness": (0.28, 0.44, 0.28),
    "increase_flexibility": (0.25, 0.45, 0.30),
    "keto": (0.25, 0.10, 0.65),
}

# Meal type slots per number of meals/day
MEAL_SLOTS = {
    1: ["lunch"],
    2: ["lunch", "dinner"],
    3: ["breakfast", "lunch", "dinner"],
    4: ["breakfast", "lunch", "afternoon_snack", "dinner"],
    5: ["breakfast", "morning_snack", "lunch", "afternoon_snack", "dinner"],
    6: ["breakfast", "morning_snack", "lunch", "afternoon_snack", "dinner", "dinner"],
}

# Kcal distribution per meal slot (must sum to ~1.0)
MEAL_KCAL_FRACTION = {
    "breakfast": 0.25,
    "morning_snack": 0.10,
    "lunch": 0.35,
    "afternoon_snack": 0.10,
    "dinner": 0.30,
}


def _calculate_tdee(profile: UserProfile) -> int:
    """Return estimated TDEE in kcal using Mifflin-St Jeor formula."""
    metrics = profile.user.body_metrics.filter(deleted_at__isnull=True).first()

    weight = float(metrics.weight) if metrics and metrics.weight else 70.0
    height = float(metrics.height) if metrics and metrics.height else 170.0

    try:
        today = date.today()
        dob = profile.date_of_birth
        age = (today - dob).days // 365 if dob else 30
    except Exception:
        age = 30

    gender = (profile.gender or "").lower()
    if gender in ("male", "man", "m", "masculí", "masculino"):
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    activity = profile.activity_level or "sedentary"
    factor = ACTIVITY_FACTORS.get(activity, 1.375)

    return round(bmr * factor)


def _macro_targets(
    kcal: int, goal: str, dietary_preference: str
) -> tuple[int, int, int]:
    """Return (protein_g, carbs_g, fat_g) targets."""
    key = "keto" if dietary_preference == "keto" else goal
    p_ratio, c_ratio, f_ratio = MACRO_RATIOS.get(key, (0.25, 0.45, 0.30))
    protein_g = round(kcal * p_ratio / 4)  # 4 kcal/g
    carbs_g = round(kcal * c_ratio / 4)
    fat_g = round(kcal * f_ratio / 9)  # 9 kcal/g
    return protein_g, carbs_g, fat_g


def _parse_food_keywords(text: str | None) -> list[str]:
    """Split a free-text food list into lowercase keywords."""
    if not text:
        return []
    return [p.strip().lower() for p in re.split(r"[,;\n]+", text) if p.strip()]


def _filter_recipes(meal_type: str, profile: UserProfile) -> list[Recipe]:
    """Return recipes compatible with the user's dietary restrictions and dislikes."""
    from django.db.models import Q

    qs = Recipe.objects.filter(meal_type=meal_type)

    dietary = profile.dietary_preference or "omnivore"
    if dietary == "vegan":
        qs = qs.filter(is_vegan=True)
    elif dietary == "vegetarian":
        qs = qs.filter(is_vegetarian=True)
    elif dietary == "mediterranean":
        qs = qs.filter(is_mediterranean=True)
    elif dietary == "keto":
        qs = qs.filter(is_keto=True)

    try:
        hp = profile.user.health_profile
        if hp.celiac_disease:
            qs = qs.filter(is_gluten_free=True)
        if hp.lactose_intolerance:
            qs = qs.filter(is_lactose_free=True)
        if hp.nut_allergy:
            qs = qs.filter(contains_nuts=False)
        if hp.egg_allergy:
            qs = qs.filter(contains_eggs=False)
        if hp.shellfish_allergy:
            qs = qs.filter(contains_shellfish=False)
        if hp.soy_allergy:
            qs = qs.filter(contains_soy=False)
        if hp.diabetes != "none":
            qs = qs.filter(is_diabetic_friendly=True)
    except Exception:
        pass

    # Exclude recipes whose name matches any disliked food keyword
    disliked = _parse_food_keywords(profile.disliked_foods)
    if disliked:
        exclude_q = Q()
        for kw in disliked:
            exclude_q |= Q(name__icontains=kw)
        qs = qs.exclude(exclude_q)

    return list(qs)


def _pick_recipe(
    meal_type: str,
    pool: list[Recipe],
    exclude_this_week: set[int],
    preferred_keywords: list[str] | None = None,
) -> Recipe | None:
    """Pick a recipe preferring favorites, avoiding weekly repeats."""
    available = [r for r in pool if r.pk not in exclude_this_week]
    if not available:
        available = pool
    if not available:
        return None
    # Prefer recipes whose name matches a favourite food keyword
    if preferred_keywords:
        preferred = [
            r
            for r in available
            if any(kw in r.name.lower() for kw in preferred_keywords)
        ]
        if preferred:
            return random.choice(preferred)
    return random.choice(available)


def generate_nutrition_plan(user) -> NutritionPlan:
    """Create (or regenerate) a personalised 4-week nutrition plan for *user*."""
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        profile = None

    goal = profile.main_goal if profile and profile.main_goal else "maintain"
    dietary = (
        profile.dietary_preference
        if profile and profile.dietary_preference
        else "omnivore"
    )
    meals_n = max(1, min(6, (profile.meals_per_day or 3) if profile else 3))

    tdee = _calculate_tdee(profile) if profile else 2000
    goal_kcal = tdee + GOAL_DELTA_KCAL.get(goal, 0)
    goal_kcal = max(1200, goal_kcal)

    protein_g, carbs_g, fat_g = _macro_targets(goal_kcal, goal, dietary)

    goal_names = {
        "lose_weight": "Weight Loss Nutrition Plan",
        "gain_muscle": "Muscle Building Nutrition Plan",
        "maintain": "Maintenance Nutrition Plan",
        "improve_fitness": "Fitness Nutrition Plan",
        "increase_flexibility": "Balanced Nutrition Plan",
    }

    NutritionPlan.objects.filter(user=user, is_active=True).update(is_active=False)

    plan = NutritionPlan.objects.create(
        user=user,
        name=goal_names.get(goal, "Nutrition Plan"),
        goal=goal,
        weeks_duration=4,
        daily_kcal_target=goal_kcal,
        daily_protein_g=protein_g,
        daily_carbs_g=carbs_g,
        daily_fat_g=fat_g,
        is_active=True,
        created_by=user,
        updated_by=user,
    )

    slots = MEAL_SLOTS.get(meals_n, MEAL_SLOTS[3])
    preferred_keywords = _parse_food_keywords(
        profile.favorite_foods if profile else None
    )

    # Pre-build recipe pools per meal type
    pools: dict[str, list[Recipe]] = {}
    for slot in set(slots):
        pools[slot] = (
            _filter_recipes(slot, profile)
            if profile
            else list(Recipe.objects.filter(meal_type=slot))
        )

    for week_num in range(1, 5):
        weekly = WeeklyNutritionPlan.objects.create(
            nutrition_plan=plan,
            week_number=week_num,
            created_by=user,
            updated_by=user,
        )

        week_used: dict[str, set] = {slot: set() for slot in set(slots)}

        for day_num in range(1, 8):
            daily = DailyMealPlan.objects.create(
                weekly_nutrition_plan=weekly,
                day_of_week=day_num,
                created_by=user,
                updated_by=user,
            )

            day_kcal = 0
            day_protein = Decimal("0")
            day_carbs = Decimal("0")
            day_fat = Decimal("0")

            # Compute total fraction sum to normalise
            total_fraction = sum(MEAL_KCAL_FRACTION.get(s, 0.20) for s in slots)

            for order, slot in enumerate(slots):
                pool = pools.get(slot, [])
                recipe = _pick_recipe(slot, pool, week_used[slot], preferred_keywords)
                if not recipe:
                    continue

                week_used[slot].add(recipe.pk)

                # Serving multiplier: scale recipe to hit per-meal kcal target
                fraction = MEAL_KCAL_FRACTION.get(slot, 0.20) / total_fraction
                target_kcal = goal_kcal * fraction
                multiplier = round(target_kcal / recipe.kcal, 2) if recipe.kcal else 1.0
                multiplier = max(0.5, min(2.5, multiplier))

                entry_kcal = round(recipe.kcal * multiplier)
                entry_protein = (recipe.protein_g * Decimal(str(multiplier))).quantize(
                    Decimal("0.1")
                )
                entry_carbs = (recipe.carbs_g * Decimal(str(multiplier))).quantize(
                    Decimal("0.1")
                )
                entry_fat = (recipe.fat_g * Decimal(str(multiplier))).quantize(
                    Decimal("0.1")
                )

                MealEntry.objects.create(
                    daily_meal_plan=daily,
                    recipe=recipe,
                    meal_type=slot,
                    order=order,
                    serving_multiplier=Decimal(str(multiplier)),
                    kcal=entry_kcal,
                    protein_g=entry_protein,
                    carbs_g=entry_carbs,
                    fat_g=entry_fat,
                    created_by=user,
                    updated_by=user,
                )

                day_kcal += entry_kcal
                day_protein += entry_protein
                day_carbs += entry_carbs
                day_fat += entry_fat

            daily.total_kcal = day_kcal
            daily.total_protein_g = day_protein
            daily.total_carbs_g = day_carbs
            daily.total_fat_g = day_fat
            daily.save(
                update_fields=[
                    "total_kcal",
                    "total_protein_g",
                    "total_carbs_g",
                    "total_fat_g",
                ]
            )

    return plan


def current_nutrition_week(plan: NutritionPlan) -> int:
    """Return which week (1-4) the user is currently on."""
    days_elapsed = (date.today() - plan.generated_at.date()).days
    return min(plan.weeks_duration, max(1, days_elapsed // 7 + 1))
