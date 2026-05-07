from django.urls import path
from drf_spectacular.views import SpectacularAPIView
from drf_spectacular.views import SpectacularSwaggerView

from .views import ActiveNutritionPlanView
from .views import ActiveTrainingPlanView
from .views import BodyMetricsCreateView
from .views import BodyMetricsListView
from .views import GenerateNutritionPlanView
from .views import GenerateTrainingPlanView
from .views import MeView
from .views import TokenObtainView
from .views import TokenRefreshView
from .views import UserCreateView
from .views import UserHealthProfileCreateView
from .views import UserHealthProfileView
from .views import UserProfileCreateView
from .views import UserProfileView
from .views import WorkoutRatingCreateView

urlpatterns = [
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    path("auth/token/", TokenObtainView.as_view(), name="token-obtain"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("users/", UserCreateView.as_view(), name="user-create"),
    path("users/me/", MeView.as_view(), name="user-me"),
    path("users/me/profile/", UserProfileView.as_view(), name="user-profile"),
    path(
        "users/me/profile/add/",
        UserProfileCreateView.as_view(),
        name="user-profile-add",
    ),
    path(
        "users/me/health-profile/",
        UserHealthProfileView.as_view(),
        name="health-profile",
    ),
    path(
        "users/me/health-profile/add/",
        UserHealthProfileCreateView.as_view(),
        name="health-profile-add",
    ),
    path(
        "users/me/body-metrics/",
        BodyMetricsListView.as_view(),
        name="body-metrics-list",
    ),
    path(
        "users/me/body-metrics/add/",
        BodyMetricsCreateView.as_view(),
        name="body-metrics-create",
    ),
    path(
        "training/plans/active/",
        ActiveTrainingPlanView.as_view(),
        name="training-plan-active",
    ),
    path(
        "training/plans/generate/",
        GenerateTrainingPlanView.as_view(),
        name="training-plan-generate",
    ),
    path(
        "training/ratings/",
        WorkoutRatingCreateView.as_view(),
        name="training-rating-create",
    ),
    path(
        "nutrition/plans/active/",
        ActiveNutritionPlanView.as_view(),
        name="nutrition-plan-active",
    ),
    path(
        "nutrition/plans/generate/",
        GenerateNutritionPlanView.as_view(),
        name="nutrition-plan-generate",
    ),
]
