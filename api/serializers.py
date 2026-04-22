from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from better_life_backend.db.models import BodyMetrics
from better_life_backend.db.models import UserAccount
from better_life_backend.db.models import UserProfile


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
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        user = self.context["request"].user
        # si ya existe perfil lo actualiza, si no lo crea
        profile, _ = UserProfile.objects.update_or_create(
            user=user,
            defaults={**validated_data, "created_by": user, "updated_by": user},
        )
        return profile


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
