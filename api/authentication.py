from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import InvalidToken

from better_life_backend.db.models import UserAccount


class UserAccountJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        try:
            user_id = validated_token["user_id"]
        except KeyError:
            raise InvalidToken("Token contained no recognizable user identification")

        try:
            return UserAccount.objects.get(id=user_id, is_active=True)
        except UserAccount.DoesNotExist:
            raise AuthenticationFailed("User not found or inactive")
