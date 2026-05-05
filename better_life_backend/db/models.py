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
    favorite_foods = models.TextField(blank=True, null=True)
    disliked_foods = models.TextField(blank=True, null=True)

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
