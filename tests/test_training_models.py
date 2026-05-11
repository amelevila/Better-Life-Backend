import uuid

import pytest

from better_life_backend.db.models import DailyRoutine
from better_life_backend.db.models import Exercise
from better_life_backend.db.models import RoutineExercise
from better_life_backend.db.models import TrainingPlan
from better_life_backend.db.models import UserHealthProfile
from better_life_backend.db.models import WeeklyPlan
from better_life_backend.db.models import WorkoutRating


@pytest.fixture
def training_plan(db, user):
    return TrainingPlan.objects.create(
        user=user,
        name="Intermediate Maintain Plan",
        goal="maintain",
        fitness_level="intermediate",
        weeks_duration=4,
        intensity_level=3,
        is_active=True,
        created_by=user,
        updated_by=user,
    )


@pytest.fixture
def weekly_plan(db, training_plan, user):
    return WeeklyPlan.objects.create(
        training_plan=training_plan,
        week_number=1,
        created_by=user,
        updated_by=user,
    )


@pytest.fixture
def daily_routine(db, weekly_plan, user):
    return DailyRoutine.objects.create(
        weekly_plan=weekly_plan,
        day_of_week=1,
        name="Chest & Triceps",
        is_rest_day=False,
        created_by=user,
        updated_by=user,
    )


class TestUserHealthProfile:
    def test_create(self, db, user):
        hp = UserHealthProfile.objects.create(
            user=user, created_by=user, updated_by=user
        )
        assert UserHealthProfile.objects.count() == 1
        assert hp.user == user

    def test_id_is_uuid(self, db, user):
        hp = UserHealthProfile.objects.create(user=user)
        assert isinstance(hp.id, uuid.UUID)

    def test_str(self, db, user):
        hp = UserHealthProfile.objects.create(user=user)
        assert str(hp) == "HealthProfile(test@example.com)"

    def test_defaults_all_false(self, db, user):
        hp = UserHealthProfile.objects.create(user=user)
        assert hp.diabetes == "none"
        assert hp.hypertension is False
        assert hp.heart_condition is False
        assert hp.celiac_disease is False
        assert hp.lactose_intolerance is False
        assert hp.nut_allergy is False
        assert hp.egg_allergy is False
        assert hp.shellfish_allergy is False
        assert hp.soy_allergy is False

    def test_one_to_one_with_user(self, db, user):
        hp = UserHealthProfile.objects.create(user=user)
        assert user.health_profile == hp

    def test_cascade_delete(self, db, user):
        UserHealthProfile.objects.create(user=user)
        user.delete()
        assert UserHealthProfile.objects.count() == 0

    def test_optional_text_fields_nullable(self, db, user):
        hp = UserHealthProfile.objects.create(user=user)
        assert hp.injuries is None
        assert hp.medications is None
        assert hp.other_conditions is None


class TestExercise:
    def test_create(self, exercise):
        assert Exercise.objects.count() == 1
        assert exercise.name == "Push-up"
        assert exercise.muscle_group == "chest"

    def test_id_is_uuid(self, exercise):
        assert isinstance(exercise.id, uuid.UUID)

    def test_str(self, exercise):
        assert str(exercise) == "Push-up"

    def test_defaults(self, db, user):
        ex = Exercise.objects.create(
            name="Pull-up",
            muscle_group="back",
            exercise_type="reps",
            difficulty="intermediate",
            created_by=user,
            updated_by=user,
        )
        assert ex.default_sets == 3
        assert ex.rest_seconds == 60
        assert ex.equipment == "none"

    def test_time_based_exercise(self, db, user):
        ex = Exercise.objects.create(
            name="Plank",
            muscle_group="core",
            exercise_type="time",
            default_sets=3,
            default_duration_seconds=60,
            difficulty="beginner",
            created_by=user,
            updated_by=user,
        )
        assert ex.exercise_type == "time"
        assert ex.default_duration_seconds == 60
        assert ex.default_reps is None


class TestTrainingPlan:
    def test_create(self, training_plan):
        assert TrainingPlan.objects.count() == 1
        assert training_plan.goal == "maintain"
        assert training_plan.is_active is True

    def test_id_is_uuid(self, training_plan):
        assert isinstance(training_plan.id, uuid.UUID)

    def test_str(self, training_plan):
        assert str(training_plan) == "Intermediate Maintain Plan (test@example.com)"

    def test_cascade_delete(self, db, user, training_plan):
        user.delete()
        assert TrainingPlan.objects.count() == 0

    def test_generated_at_is_set(self, training_plan):
        assert training_plan.generated_at is not None

    def test_default_intensity(self, db, user):
        plan = TrainingPlan.objects.create(
            user=user,
            name="Test",
            goal="maintain",
            fitness_level="beginner",
            created_by=user,
            updated_by=user,
        )
        assert plan.intensity_level == 3
        assert plan.weeks_duration == 4


class TestWeeklyPlan:
    def test_create(self, weekly_plan):
        assert WeeklyPlan.objects.count() == 1
        assert weekly_plan.week_number == 1

    def test_id_is_uuid(self, weekly_plan):
        assert isinstance(weekly_plan.id, uuid.UUID)

    def test_str(self, weekly_plan):
        assert "Week 1" in str(weekly_plan)
        assert "Intermediate Maintain Plan" in str(weekly_plan)

    def test_ordering_by_week_number(self, db, training_plan, user):
        w3 = WeeklyPlan.objects.create(
            training_plan=training_plan, week_number=3, created_by=user, updated_by=user
        )
        w1 = WeeklyPlan.objects.create(
            training_plan=training_plan, week_number=1, created_by=user, updated_by=user
        )
        w2 = WeeklyPlan.objects.create(
            training_plan=training_plan, week_number=2, created_by=user, updated_by=user
        )
        weeks = list(training_plan.weekly_plans.all())
        assert weeks[0] == w1
        assert weeks[1] == w2
        assert weeks[2] == w3

    def test_cascade_delete_from_plan(self, db, training_plan, weekly_plan):
        training_plan.delete()
        assert WeeklyPlan.objects.count() == 0


class TestDailyRoutine:
    def test_create(self, daily_routine):
        assert DailyRoutine.objects.count() == 1
        assert daily_routine.day_of_week == 1
        assert daily_routine.name == "Chest & Triceps"
        assert daily_routine.is_rest_day is False

    def test_id_is_uuid(self, daily_routine):
        assert isinstance(daily_routine.id, uuid.UUID)

    def test_str(self, daily_routine):
        assert str(daily_routine) == "Day 1: Chest & Triceps"

    def test_rest_day(self, db, weekly_plan, user):
        rest = DailyRoutine.objects.create(
            weekly_plan=weekly_plan,
            day_of_week=7,
            name="Rest Day",
            is_rest_day=True,
            created_by=user,
            updated_by=user,
        )
        assert rest.is_rest_day is True

    def test_ordering_by_day(self, db, weekly_plan, user):
        d3 = DailyRoutine.objects.create(
            weekly_plan=weekly_plan,
            day_of_week=3,
            name="Day 3",
            created_by=user,
            updated_by=user,
        )
        d1 = DailyRoutine.objects.create(
            weekly_plan=weekly_plan,
            day_of_week=1,
            name="Day 1",
            created_by=user,
            updated_by=user,
        )
        days = list(weekly_plan.daily_routines.all())
        assert days[0] == d1
        assert days[1] == d3

    def test_cascade_delete_from_weekly(self, db, weekly_plan, daily_routine):
        weekly_plan.delete()
        assert DailyRoutine.objects.count() == 0


class TestRoutineExercise:
    def test_create(self, db, daily_routine, exercise, user):
        re = RoutineExercise.objects.create(
            daily_routine=daily_routine,
            exercise=exercise,
            order=0,
            sets=3,
            reps=12,
            rest_seconds=60,
            created_by=user,
            updated_by=user,
        )
        assert RoutineExercise.objects.count() == 1
        assert re.sets == 3
        assert re.reps == 12

    def test_id_is_uuid(self, db, daily_routine, exercise, user):
        re = RoutineExercise.objects.create(
            daily_routine=daily_routine,
            exercise=exercise,
            order=0,
            sets=3,
            reps=12,
            rest_seconds=60,
            created_by=user,
            updated_by=user,
        )
        assert isinstance(re.id, uuid.UUID)

    def test_str(self, db, daily_routine, exercise, user):
        re = RoutineExercise.objects.create(
            daily_routine=daily_routine,
            exercise=exercise,
            order=0,
            sets=3,
            reps=12,
            rest_seconds=60,
            created_by=user,
            updated_by=user,
        )
        assert str(re) == "Push-up — Chest & Triceps"

    def test_ordering_by_order(self, db, daily_routine, exercise, user):
        re2 = RoutineExercise.objects.create(
            daily_routine=daily_routine,
            exercise=exercise,
            order=2,
            sets=3,
            reps=10,
            rest_seconds=60,
            created_by=user,
            updated_by=user,
        )
        re0 = RoutineExercise.objects.create(
            daily_routine=daily_routine,
            exercise=exercise,
            order=0,
            sets=3,
            reps=12,
            rest_seconds=60,
            created_by=user,
            updated_by=user,
        )
        entries = list(daily_routine.routine_exercises.all())
        assert entries[0] == re0
        assert entries[1] == re2


class TestWorkoutRating:
    def test_create(self, db, user, daily_routine):
        rating = WorkoutRating.objects.create(
            user=user,
            daily_routine=daily_routine,
            rating=4,
            intensity_feedback="same",
            created_by=user,
            updated_by=user,
        )
        assert WorkoutRating.objects.count() == 1
        assert rating.rating == 4

    def test_id_is_uuid(self, db, user, daily_routine):
        rating = WorkoutRating.objects.create(
            user=user,
            daily_routine=daily_routine,
            rating=3,
            created_by=user,
            updated_by=user,
        )
        assert isinstance(rating.id, uuid.UUID)

    def test_str(self, db, user, daily_routine):
        rating = WorkoutRating.objects.create(
            user=user,
            daily_routine=daily_routine,
            rating=5,
            created_by=user,
            updated_by=user,
        )
        assert str(rating) == "Rating 5/5 by test@example.com"

    def test_default_intensity_feedback(self, db, user, daily_routine):
        rating = WorkoutRating.objects.create(
            user=user,
            daily_routine=daily_routine,
            rating=3,
            created_by=user,
            updated_by=user,
        )
        assert rating.intensity_feedback == "same"

    def test_completed_at_is_set(self, db, user, daily_routine):
        rating = WorkoutRating.objects.create(
            user=user,
            daily_routine=daily_routine,
            rating=3,
            created_by=user,
            updated_by=user,
        )
        assert rating.completed_at is not None

    def test_cascade_delete_from_user(self, db, user, daily_routine):
        WorkoutRating.objects.create(
            user=user,
            daily_routine=daily_routine,
            rating=3,
            created_by=user,
            updated_by=user,
        )
        user.delete()
        assert WorkoutRating.objects.count() == 0
