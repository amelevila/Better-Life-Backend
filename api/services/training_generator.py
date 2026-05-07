# Generate a personalised 4-week training plan for a user based on their profile.
import random
from datetime import date

from better_life_backend.db.models import DailyRoutine
from better_life_backend.db.models import Exercise
from better_life_backend.db.models import RoutineExercise
from better_life_backend.db.models import TrainingPlan
from better_life_backend.db.models import UserProfile
from better_life_backend.db.models import WeeklyPlan

# Routine names and target muscle-groups per split index
WEEKLY_SPLITS = {
    1: [("Full Body", ["chest", "back", "legs", "core"])],
    2: [
        ("Upper Body", ["chest", "back", "shoulders", "arms"]),
        ("Lower Body & Core", ["legs", "core"]),
    ],
    3: [
        ("Push", ["chest", "shoulders", "arms"]),
        ("Pull", ["back", "arms"]),
        ("Legs & Core", ["legs", "core"]),
    ],
    4: [
        ("Chest & Triceps", ["chest", "arms"]),
        ("Back & Biceps", ["back", "arms"]),
        ("Legs", ["legs"]),
        ("Shoulders & Core", ["shoulders", "core"]),
    ],
    5: [
        ("Chest", ["chest"]),
        ("Back & Biceps", ["back", "arms"]),
        ("Legs", ["legs"]),
        ("Shoulders & Arms", ["shoulders", "arms"]),
        ("Core & Cardio", ["core", "cardio"]),
    ],
    6: [
        ("Chest & Triceps", ["chest", "arms"]),
        ("Back & Biceps", ["back", "arms"]),
        ("Legs", ["legs"]),
        ("Shoulders", ["shoulders"]),
        ("Core & Cardio", ["core", "cardio"]),
        ("Full Body", ["chest", "back", "legs"]),
    ],
    7: [
        ("Chest & Triceps", ["chest", "arms"]),
        ("Back & Biceps", ["back", "arms"]),
        ("Legs", ["legs"]),
        ("Shoulders", ["shoulders"]),
        ("Core & Cardio", ["core", "cardio"]),
        ("Full Body", ["chest", "back", "legs"]),
        ("Active Recovery", ["core"]),
    ],
}

# Which weekdays (1=Mon…7=Sun) are workout days for each training_days value
DAY_DISTRIBUTION = {
    1: [1],
    2: [1, 4],
    3: [1, 3, 5],
    4: [1, 2, 4, 5],
    5: [1, 2, 3, 4, 5],
    6: [1, 2, 3, 4, 5, 6],
    7: [1, 2, 3, 4, 5, 6, 7],
}

SETS_CONFIG = {
    "beginner": (2, 3),
    "intermediate": (3, 4),
    "advanced": (4, 5),
}

# Multiplier applied to default reps/duration based on plan intensity (1-5)
INTENSITY_FACTOR = {1: 0.70, 2: 0.85, 3: 1.0, 4: 1.15, 5: 1.30}


def _exercises_per_session(duration_minutes: int) -> int:
    if duration_minutes <= 20:
        return 3
    if duration_minutes <= 30:
        return 4
    if duration_minutes <= 45:
        return 5
    if duration_minutes <= 60:
        return 6
    return 7


def _allowed_equipment(training_location: str) -> list[str]:
    if training_location in ("home", "outdoor"):
        return ["none"]
    if training_location == "gym":
        return [
            "none",
            "dumbbells",
            "barbell",
            "machine",
            "resistance_band",
            "pull_up_bar",
        ]
    # mixed
    return ["none", "dumbbells", "resistance_band", "pull_up_bar"]


def _pick_exercises(muscle_groups, difficulty, equipment, n, exclude_ids):
    """Return up to *n* exercises covering the given muscle groups."""
    selected = []
    difficulties = {
        "beginner": ["beginner"],
        "intermediate": ["beginner", "intermediate"],
        "advanced": ["beginner", "intermediate", "advanced"],
    }.get(difficulty, ["beginner"])

    per_group = max(1, n // len(muscle_groups))

    for group in muscle_groups:
        pool = list(
            Exercise.objects.filter(
                muscle_group=group,
                difficulty__in=difficulties,
                equipment__in=equipment,
            ).exclude(id__in=exclude_ids)
        )
        if pool:
            count = min(per_group, len(pool))
            chosen = random.sample(pool, count)
            selected.extend(chosen)
            exclude_ids = exclude_ids | {e.id for e in chosen}

    # Pad with core/cardio if short
    if len(selected) < n:
        filler = list(
            Exercise.objects.filter(
                muscle_group__in=["core", "cardio"],
                equipment__in=equipment,
            ).exclude(id__in=exclude_ids)[: n - len(selected)]
        )
        selected.extend(filler)

    return selected[:n]


def generate_training_plan(user) -> TrainingPlan:
    """Create (or regenerate) a personalised training plan for *user*."""
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        profile = None

    goal = profile.main_goal if profile and profile.main_goal else "maintain"
    fitness_level = (
        profile.fitness_level if profile and profile.fitness_level else "beginner"
    )
    training_days = max(
        1, min(7, (profile.training_days_per_week or 3) if profile else 3)
    )
    duration = (profile.workout_duration_minutes or 45) if profile else 45
    location = (profile.training_location or "home") if profile else "home"

    intensity_map = {"beginner": 2, "intermediate": 3, "advanced": 4}
    intensity_level = intensity_map.get(fitness_level, 3)

    goal_names = {
        "lose_weight": "Weight Loss Plan",
        "gain_muscle": "Muscle Building Plan",
        "maintain": "Maintenance Plan",
        "improve_fitness": "Fitness Plan",
        "increase_flexibility": "Flexibility & Mobility Plan",
    }

    # Deactivate previous plans
    TrainingPlan.objects.filter(user=user, is_active=True).update(is_active=False)

    plan = TrainingPlan.objects.create(
        user=user,
        name=goal_names.get(goal, "Training Plan"),
        goal=goal,
        fitness_level=fitness_level,
        weeks_duration=4,
        intensity_level=intensity_level,
        is_active=True,
        created_by=user,
        updated_by=user,
    )

    split = WEEKLY_SPLITS.get(training_days, WEEKLY_SPLITS[3])
    workout_days = DAY_DISTRIBUTION.get(training_days, DAY_DISTRIBUTION[3])
    equipment = _allowed_equipment(location)
    n_exercises = _exercises_per_session(duration)
    sets_min, sets_max = SETS_CONFIG.get(fitness_level, (2, 3))
    factor = INTENSITY_FACTOR.get(intensity_level, 1.0)

    # For weight-loss / fitness goals, add a cardio exercise per session
    add_cardio = goal in ("lose_weight", "improve_fitness")

    for week_num in range(1, 5):
        weekly_plan = WeeklyPlan.objects.create(
            training_plan=plan,
            week_number=week_num,
            created_by=user,
            updated_by=user,
        )

        split_index = 0
        for day_num in range(1, 8):
            if day_num not in workout_days:
                DailyRoutine.objects.create(
                    weekly_plan=weekly_plan,
                    day_of_week=day_num,
                    name="Rest Day",
                    is_rest_day=True,
                    created_by=user,
                    updated_by=user,
                )
                continue

            routine_name, muscle_groups = split[split_index % len(split)]
            split_index += 1

            routine = DailyRoutine.objects.create(
                weekly_plan=weekly_plan,
                day_of_week=day_num,
                name=routine_name,
                is_rest_day=False,
                created_by=user,
                updated_by=user,
            )

            exclude_ids: set = set()

            # Optional cardio warm-up
            exercises: list[Exercise] = []
            if add_cardio:
                cardio = list(
                    Exercise.objects.filter(
                        muscle_group="cardio",
                        difficulty__in=(
                            ["beginner", "intermediate"]
                            if fitness_level != "beginner"
                            else ["beginner"]
                        ),
                        equipment__in=equipment,
                    )[:3]
                )
                if cardio:
                    pick = random.choice(cardio)
                    exercises.append(pick)
                    exclude_ids.add(pick.id)

            remaining = n_exercises - len(exercises)
            exercises += _pick_exercises(
                muscle_groups, fitness_level, equipment, remaining, exclude_ids
            )

            sets = random.randint(sets_min, sets_max)

            for order, ex in enumerate(exercises):
                reps = None
                duration_seconds = None
                if ex.exercise_type == Exercise.ExerciseType.REPS:
                    reps = max(1, round((ex.default_reps or 10) * factor))
                else:
                    duration_seconds = max(
                        10, round((ex.default_duration_seconds or 30) * factor)
                    )

                RoutineExercise.objects.create(
                    daily_routine=routine,
                    exercise=ex,
                    order=order,
                    sets=sets,
                    reps=reps,
                    duration_seconds=duration_seconds,
                    rest_seconds=ex.rest_seconds,
                    created_by=user,
                    updated_by=user,
                )

    return plan


def current_week_number(plan: TrainingPlan) -> int:
    """Return which week (1-4) the user is currently on."""
    days_elapsed = (date.today() - plan.generated_at.date()).days
    return min(plan.weeks_duration, max(1, days_elapsed // 7 + 1))
