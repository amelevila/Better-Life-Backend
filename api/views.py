from rest_framework import generics
from rest_framework import permissions
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import BodyMetricsSerializer
from .serializers import TokenObtainSerializer
from .serializers import TokenRefreshSerializer
from .serializers import TrainingPlanSerializer
from .serializers import UserAccountCreateSerializer
from .serializers import UserAccountSerializer
from .serializers import UserHealthProfileSerializer
from .serializers import UserProfileSerializer
from .serializers import WorkoutRatingSerializer
from better_life_backend.db.models import BodyMetrics
from better_life_backend.db.models import TrainingPlan
from better_life_backend.db.models import UserHealthProfile
from better_life_backend.db.models import UserProfile


# POST /auth/token/
class TokenObtainView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = TokenObtainSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


# POST /auth/token/refresh/
class TokenRefreshView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


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


# GET /users/me/health-profile/
class UserHealthProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            health_profile = request.user.health_profile
        except UserHealthProfile.DoesNotExist:
            return Response(
                {"detail": "El usuario aún no tiene perfil de salud."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = UserHealthProfileSerializer(
            health_profile, context={"request": request}
        )
        return Response(serializer.data)


# POST /users/me/health-profile/add/
class UserHealthProfileCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = UserHealthProfileSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        health_profile = serializer.save()
        return Response(
            UserHealthProfileSerializer(
                health_profile, context={"request": request}
            ).data,
            status=status.HTTP_201_CREATED,
        )


# POST /users/me/body-metrics/add/
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


# GET /training/plans/active/
class ActiveTrainingPlanView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        plan = TrainingPlan.objects.filter(user=request.user, is_active=True).first()

        if not plan:
            from api.services.training_generator import generate_training_plan

            plan = generate_training_plan(request.user)

        serializer = TrainingPlanSerializer(plan, context={"request": request})
        return Response(serializer.data)


# POST /training/plans/generate/
class GenerateTrainingPlanView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from api.services.training_generator import generate_training_plan

        plan = generate_training_plan(request.user)
        serializer = TrainingPlanSerializer(plan, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# POST /training/ratings/
class WorkoutRatingCreateView(generics.CreateAPIView):
    serializer_class = WorkoutRatingSerializer
    permission_classes = [permissions.IsAuthenticated]
