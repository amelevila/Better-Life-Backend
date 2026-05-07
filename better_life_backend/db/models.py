import uuid

from django.db import models


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        "db.UserAccount",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(class)s_created_by",
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        "db.UserAccount",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(class)s_updated_by",
    )
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        "db.UserAccount",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(class)s_deleted_by",
    )

    class Meta:
        abstract = True


class UserAccount(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, null=False)
    password_hash = models.TextField(null=False)
    is_active = models.BooleanField(default=True)
    is_member = models.BooleanField(default=False)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    class Meta:
        db_table = "user_account"

    def __str__(self):
        return self.email


class UserProfile(BaseModel):
    class ActivityLevel(models.TextChoices):
        SEDENTARY = "sedentary", "Sedentary"
        LIGHTLY_ACTIVE = "lightly_active", "Lightly Active"
        MODERATELY_ACTIVE = "moderately_active", "Moderately Active"
        VERY_ACTIVE = "very_active", "Very Active"
        EXTRA_ACTIVE = "extra_active", "Extra Active"

    class MainGoal(models.TextChoices):
        LOSE_WEIGHT = "lose_weight", "Lose Weight"
        GAIN_MUSCLE = "gain_muscle", "Gain Muscle"
        MAINTAIN = "maintain", "Maintain"
        IMPROVE_FITNESS = "improve_fitness", "Improve Fitness"
        INCREASE_FLEXIBILITY = "increase_flexibility", "Increase Flexibility"

    class FitnessLevel(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"

    class TrainingLocation(models.TextChoices):
        GYM = "gym", "Gym"
        HOME = "home", "Home"
        OUTDOOR = "outdoor", "Outdoor"
        MIXED = "mixed", "Mixed"

    class DietaryPreference(models.TextChoices):
        OMNIVORE = "omnivore", "Omnivore"
        VEGETARIAN = "vegetarian", "Vegetarian"
        VEGAN = "vegan", "Vegan"
        KETO = "keto", "Keto"
        MEDITERRANEAN = "mediterranean", "Mediterranean"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        UserAccount,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    first_name = models.CharField(max_length=150, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    dni = models.CharField(max_length=20, unique=True, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    gender = models.CharField(max_length=30, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_picture_url = models.TextField(blank=True, null=True)

    # Fitness
    activity_level = models.CharField(
        max_length=20, choices=ActivityLevel.choices, blank=True, null=True
    )
    main_goal = models.CharField(
        max_length=30, choices=MainGoal.choices, blank=True, null=True
    )
    fitness_level = models.CharField(
        max_length=20, choices=FitnessLevel.choices, blank=True, null=True
    )
    training_days_per_week = models.IntegerField(blank=True, null=True)
    workout_duration_minutes = models.IntegerField(blank=True, null=True)
    training_location = models.CharField(
        max_length=20, choices=TrainingLocation.choices, blank=True, null=True
    )

    # Nutrition
    dietary_preference = models.CharField(
        max_length=20, choices=DietaryPreference.choices, blank=True, null=True
    )
    meals_per_day = models.IntegerField(blank=True, null=True)
    food_allergies = models.TextField(blank=True, null=True)

    onboarding_completed = models.BooleanField(default=False)

    class Meta:
        db_table = "user_profile"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class UserHealthProfile(BaseModel):
    class DiabetesType(models.TextChoices):
        NONE = "none", "None"
        TYPE1 = "type1", "Type 1"
        TYPE2 = "type2", "Type 2"
        PREDIABETES = "prediabetes", "Prediabetes"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        UserAccount,
        on_delete=models.CASCADE,
        related_name="health_profile",
    )
    diabetes = models.CharField(
        max_length=20,
        choices=DiabetesType.choices,
        default=DiabetesType.NONE,
    )
    hypertension = models.BooleanField(default=False)
    heart_condition = models.BooleanField(default=False)
    celiac_disease = models.BooleanField(default=False)
    lactose_intolerance = models.BooleanField(default=False)
    injuries = models.TextField(blank=True, null=True)
    medications = models.TextField(blank=True, null=True)
    other_conditions = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "user_health_profile"

    def __str__(self):
        return f"HealthProfile({self.user.email})"


class BodyMetrics(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        UserAccount,
        on_delete=models.CASCADE,
        related_name="body_metrics",
    )
    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    body_fat_pct = models.DecimalField(
        max_digits=4, decimal_places=2, blank=True, null=True
    )
    muscle_mass_pct = models.DecimalField(
        max_digits=4, decimal_places=2, blank=True, null=True
    )
    visceral_fat_level = models.IntegerField(blank=True, null=True)
    metabolic_age = models.IntegerField(blank=True, null=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "body_metrics"
        ordering = ["-recorded_at"]

    def __str__(self):
        return f"BodyMetrics({self.user.email} @ {self.recorded_at:%Y-%m-%d})"


class Exercise(BaseModel):
    class MuscleGroup(models.TextChoices):
        CHEST = "chest", "Chest"
        BACK = "back", "Back"
        LEGS = "legs", "Legs"
        SHOULDERS = "shoulders", "Shoulders"
        ARMS = "arms", "Arms"
        CORE = "core", "Core"
        CARDIO = "cardio", "Cardio"
        FULL_BODY = "full_body", "Full Body"

    class ExerciseType(models.TextChoices):
        REPS = "reps", "Reps"
        TIME = "time", "Time"

    class Difficulty(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"

    class Equipment(models.TextChoices):
        NONE = "none", "None (Bodyweight)"
        DUMBBELLS = "dumbbells", "Dumbbells"
        BARBELL = "barbell", "Barbell"
        MACHINE = "machine", "Machine"
        RESISTANCE_BAND = "resistance_band", "Resistance Band"
        PULL_UP_BAR = "pull_up_bar", "Pull-up Bar"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    muscle_group = models.CharField(max_length=20, choices=MuscleGroup.choices)
    exercise_type = models.CharField(max_length=10, choices=ExerciseType.choices)
    default_sets = models.IntegerField(default=3)
    default_reps = models.IntegerField(null=True, blank=True)
    default_duration_seconds = models.IntegerField(null=True, blank=True)
    rest_seconds = models.IntegerField(default=60)
    difficulty = models.CharField(max_length=15, choices=Difficulty.choices)
    equipment = models.CharField(
        max_length=20, choices=Equipment.choices, default=Equipment.NONE
    )

    class Meta:
        db_table = "exercise"

    def __str__(self):
        return self.name


class TrainingPlan(BaseModel):
    class Goal(models.TextChoices):
        LOSE_WEIGHT = "lose_weight", "Lose Weight"
        GAIN_MUSCLE = "gain_muscle", "Gain Muscle"
        MAINTAIN = "maintain", "Maintain"
        IMPROVE_FITNESS = "improve_fitness", "Improve Fitness"
        INCREASE_FLEXIBILITY = "increase_flexibility", "Increase Flexibility"

    class FitnessLevel(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        UserAccount,
        on_delete=models.CASCADE,
        related_name="training_plans",
    )
    name = models.CharField(max_length=200)
    goal = models.CharField(max_length=30, choices=Goal.choices)
    fitness_level = models.CharField(max_length=20, choices=FitnessLevel.choices)
    weeks_duration = models.IntegerField(default=4)
    intensity_level = models.IntegerField(default=3)
    is_active = models.BooleanField(default=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "training_plan"

    def __str__(self):
        return f"{self.name} ({self.user.email})"


class WeeklyPlan(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    training_plan = models.ForeignKey(
        TrainingPlan,
        on_delete=models.CASCADE,
        related_name="weekly_plans",
    )
    week_number = models.IntegerField()

    class Meta:
        db_table = "weekly_plan"
        ordering = ["week_number"]

    def __str__(self):
        return f"Week {self.week_number} — {self.training_plan.name}"


class DailyRoutine(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    weekly_plan = models.ForeignKey(
        WeeklyPlan,
        on_delete=models.CASCADE,
        related_name="daily_routines",
    )
    day_of_week = models.IntegerField()  # 1=Monday … 7=Sunday
    name = models.CharField(max_length=200)
    is_rest_day = models.BooleanField(default=False)

    class Meta:
        db_table = "daily_routine"
        ordering = ["day_of_week"]

    def __str__(self):
        return f"Day {self.day_of_week}: {self.name}"


class RoutineExercise(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    daily_routine = models.ForeignKey(
        DailyRoutine,
        on_delete=models.CASCADE,
        related_name="routine_exercises",
    )
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name="routine_exercises",
    )
    order = models.IntegerField(default=0)
    sets = models.IntegerField(default=3)
    reps = models.IntegerField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    rest_seconds = models.IntegerField(default=60)

    class Meta:
        db_table = "routine_exercise"
        ordering = ["order"]

    def __str__(self):
        return f"{self.exercise.name} — {self.daily_routine.name}"


class WorkoutRating(BaseModel):
    class IntensityFeedback(models.TextChoices):
        MORE = "more", "More"
        SAME = "same", "Same"
        LESS = "less", "Less"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        UserAccount,
        on_delete=models.CASCADE,
        related_name="workout_ratings",
    )
    daily_routine = models.ForeignKey(
        DailyRoutine,
        on_delete=models.CASCADE,
        related_name="ratings",
    )
    rating = models.IntegerField()  # 1-5
    intensity_feedback = models.CharField(
        max_length=10,
        choices=IntensityFeedback.choices,
        default=IntensityFeedback.SAME,
    )
    completed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "workout_rating"

    def __str__(self):
        return f"Rating {self.rating}/5 by {self.user.email}"
