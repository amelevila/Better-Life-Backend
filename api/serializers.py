from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from better_life_backend.db.models import BodyMetrics
from better_life_backend.db.models import UserAccount
from better_life_backend.db.models import UserProfile


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
