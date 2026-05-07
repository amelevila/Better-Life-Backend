from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from better_life_backend.db.models import BodyMetrics
from better_life_backend.db.models import DailyRoutine
from better_life_backend.db.models import Exercise
from better_life_backend.db.models import RoutineExercise
from better_life_backend.db.models import TrainingPlan
from better_life_backend.db.models import UserAccount
from better_life_backend.db.models import UserHealthProfile
from better_life_backend.db.models import UserProfile
from better_life_backend.db.models import WeeklyPlan
from better_life_backend.db.models import WorkoutRating


class TokenObtainSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        try:
            user = UserAccount.objects.get(email=attrs["email"], is_active=True)
        except UserAccount.DoesNotExist:
            raise serializers.ValidationError("Invalid credentials")

        if not check_password(attrs["password"], user.password_hash):
            raise serializers.ValidationError("Invalid credentials")

        refresh = RefreshToken()
        refresh["user_id"] = str(user.id)

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }


class TokenRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        try:
            refresh = RefreshToken(attrs["refresh"])
        except TokenError as e:
            raise serializers.ValidationError(str(e))

        try:
            user_id = refresh["user_id"]
            UserAccount.objects.get(id=user_id, is_active=True)
        except KeyError, UserAccount.DoesNotExist:
            raise serializers.ValidationError("User not found or inactive")

        return {"access": str(refresh.access_token)}


class UserAccountCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = UserAccount
        fields = ["id", "email", "password", "is_active", "is_member"]
        read_only_fields = ["id", "is_active", "is_member"]

    def create(self, validated_data):
        validated_data["password_hash"] = make_password(validated_data.pop("password"))
        return super().create(validated_data)


class UserAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAccount
        fields = ["id", "email", "is_active", "is_member", "created_at", "updated_at"]
        read_only_fields = fields


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            "id",
            "first_name",
            "last_name",
            "dni",
            "phone",
            "gender",
            "date_of_birth",
            "profile_picture_url",
            "activity_level",
            "main_goal",
            "fitness_level",
            "training_days_per_week",
            "workout_duration_minutes",
            "training_location",
            "dietary_preference",
            "meals_per_day",
            "food_allergies",
            "onboarding_completed",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        user = self.context["request"].user
        profile, _ = UserProfile.objects.update_or_create(
            user=user,
            defaults={**validated_data, "created_by": user, "updated_by": user},
        )
        return profile


class UserHealthProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserHealthProfile
        fields = [
            "id",
            "diabetes",
            "hypertension",
            "heart_condition",
            "celiac_disease",
            "lactose_intolerance",
            "injuries",
            "medications",
            "other_conditions",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        user = self.context["request"].user
        health_profile, _ = UserHealthProfile.objects.update_or_create(
            user=user,
            defaults={**validated_data, "created_by": user, "updated_by": user},
        )
        return health_profile


class BodyMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BodyMetrics
        fields = [
            "id",
            "weight",
            "height",
            "body_fat_pct",
            "muscle_mass_pct",
            "visceral_fat_level",
            "metabolic_age",
            "recorded_at",
        ]
        read_only_fields = ["id", "recorded_at"]

    def create(self, validated_data):
        user = self.context["request"].user
        return BodyMetrics.objects.create(
            user=user,
            created_by=user,
            updated_by=user,
            **validated_data,
        )


# ── Training ──────────────────────────────────────────────────────────────────


class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = [
            "id",
            "name",
            "description",
            "muscle_group",
            "exercise_type",
            "difficulty",
            "equipment",
        ]


class RoutineExerciseSerializer(serializers.ModelSerializer):
    exercise = ExerciseSerializer(read_only=True)

    class Meta:
        model = RoutineExercise
        fields = [
            "id",
            "order",
            "sets",
            "reps",
            "duration_seconds",
            "rest_seconds",
            "exercise",
        ]


class DailyRoutineSerializer(serializers.ModelSerializer):
    routine_exercises = RoutineExerciseSerializer(many=True, read_only=True)
    is_completed = serializers.SerializerMethodField()

    class Meta:
        model = DailyRoutine
        fields = [
            "id",
            "day_of_week",
            "name",
            "is_rest_day",
            "is_completed",
            "routine_exercises",
        ]

    def get_is_completed(self, obj):
        request = self.context.get("request")
        if not request:
            return False
        return obj.ratings.filter(user=request.user).exists()


class WeeklyPlanSerializer(serializers.ModelSerializer):
    daily_routines = DailyRoutineSerializer(many=True, read_only=True)

    class Meta:
        model = WeeklyPlan
        fields = ["id", "week_number", "daily_routines"]


class TrainingPlanSerializer(serializers.ModelSerializer):
    weekly_plans = WeeklyPlanSerializer(many=True, read_only=True)
    current_week = serializers.SerializerMethodField()

    class Meta:
        model = TrainingPlan
        fields = [
            "id",
            "name",
            "goal",
            "fitness_level",
            "weeks_duration",
            "intensity_level",
            "is_active",
            "generated_at",
            "current_week",
            "weekly_plans",
        ]

    def get_current_week(self, obj):
        from api.services.training_generator import current_week_number

        return current_week_number(obj)


class WorkoutRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkoutRating
        fields = [
            "id",
            "daily_routine",
            "rating",
            "intensity_feedback",
            "completed_at",
            "notes",
        ]
        read_only_fields = ["id", "completed_at"]

    def create(self, validated_data):
        user = self.context["request"].user
        rating = WorkoutRating.objects.create(
            user=user,
            created_by=user,
            updated_by=user,
            **validated_data,
        )
        # Adjust plan intensity based on feedback
        plan = TrainingPlan.objects.filter(user=user, is_active=True).first()
        if plan:
            feedback = validated_data.get("intensity_feedback", "same")
            if feedback == WorkoutRating.IntensityFeedback.MORE:
                plan.intensity_level = min(5, plan.intensity_level + 1)
            elif feedback == WorkoutRating.IntensityFeedback.LESS:
                plan.intensity_level = max(1, plan.intensity_level - 1)
            plan.updated_by = user
            plan.save(update_fields=["intensity_level", "updated_by", "updated_at"])
        return rating
