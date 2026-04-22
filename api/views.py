from rest_framework import generics
from rest_framework import permissions
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import BodyMetricsSerializer
from .serializers import UserAccountCreateSerializer
from .serializers import UserAccountSerializer
from .serializers import UserProfileSerializer
from better_life_backend.db.models import BodyMetrics
from better_life_backend.db.models import UserProfile


# POST /users/
class UserCreateView(generics.CreateAPIView):
    serializer_class = UserAccountCreateSerializer
    permission_classes = [permissions.AllowAny]


# GET /users/me/
class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserAccountSerializer(request.user)
        return Response(serializer.data)


# GET /users/me/profile/
class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            return Response(
                {"detail": "El usuario aún no tiene perfil."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = UserProfileSerializer(profile, context={"request": request})
        return Response(serializer.data)


# POST /users/me/profile/add/
class UserProfileCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = UserProfileSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()
        return Response(
            UserProfileSerializer(profile, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


# POST /users/me/body-metrics/
class BodyMetricsCreateView(generics.CreateAPIView):
    serializer_class = BodyMetricsSerializer
    permission_classes = [permissions.IsAuthenticated]


# GET /users/me/body-metrics/
class BodyMetricsListView(generics.ListAPIView):
    serializer_class = BodyMetricsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return BodyMetrics.objects.filter(
            user=self.request.user,
            deleted_at__isnull=True,
        )
