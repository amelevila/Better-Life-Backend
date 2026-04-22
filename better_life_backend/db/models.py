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

    class Meta:
        db_table = "user_account"

    def __str__(self):
        return self.email


class UserProfile(BaseModel):
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

    class Meta:
        db_table = "user_profile"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


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
