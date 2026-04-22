from django.urls import path
from drf_spectacular.views import SpectacularAPIView
from drf_spectacular.views import SpectacularSwaggerView

from .views import BodyMetricsCreateView
from .views import BodyMetricsListView
from .views import MeView
from .views import UserCreateView
from .views import UserProfileCreateView
from .views import UserProfileView

urlpatterns = [
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    path("users/", UserCreateView.as_view(), name="user-create"),
    path("users/me/", MeView.as_view(), name="user-me"),
    path("users/me/profile/", UserProfileView.as_view(), name="user-profile"),
    path(
        "users/me/profile/add/",
        UserProfileCreateView.as_view(),
        name="user-profile-add",
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
]
