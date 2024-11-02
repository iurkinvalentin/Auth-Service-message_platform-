from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.db import DatabaseError, IntegrityError
from django.db.models import Q
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from .models import Connections, CustomUser, Profile
from .serializers import (ConnectionsSerializer, LoginSerializer,
                          ProfileSerializer, ProfileUpdateSerializer,
                          RegisterSerializer)


class VerifyTokenView(APIView):
    """Проверка JWT токена и возврат данных пользователя"""

    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        token = request.data.get("token")
        if not token:
            return Response(
                {"detail": "Token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            access_token = AccessToken(token)
            user_id = access_token["user_id"]
            user = CustomUser.objects.get(id=user_id)
            return Response(
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                },
                status=status.HTTP_200_OK,
            )
        except AccessToken.Error:
            return Response(
                {"detail": "Token is invalid or expired."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except CustomUser.DoesNotExist:
            return Response(
                {"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND
            )


class LoginView(APIView):
    """Представление для авторизации пользователя"""

    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """Представление для выхода пользователя"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return Response(
                {"detail": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            RefreshToken(refresh_token).blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(
                {"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )


class RegisterView(generics.CreateAPIView):
    """Представление для регистрации пользователей"""

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        try:
            serializer.save()
        except IntegrityError:
            return Response(
                {"detail": "User with this email or username already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        tokens = {"refresh": str(refresh), "access": str(refresh.access_token)}

        return Response(
            {"user": RegisterSerializer(user).data, "tokens": tokens},
            status=status.HTTP_201_CREATED,
        )


class ConfirmEmailView(APIView):
    """Представление для подтверждения email пользователя"""

    def get(self, request, uidb64, token, *args, **kwargs):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(
            user, token
        ):
            user.is_active = True
            user.save()
            return Response(
                {"message": "Email успешно подтвержден!"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"message": "Недействительная ссылка для подтверждения."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class DeleteView(APIView):
    """Представление для удаления пользователя"""

    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        try:
            request.user.delete()
            return Response(
                {"message": "User deleted successfully."},
                status=status.HTTP_204_NO_CONTENT,
            )
        except DatabaseError:
            return Response(
                {"detail": "An error occurred while deleting the user."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ProfileUpdateView(generics.RetrieveUpdateAPIView):
    """Представление для редактирования профиля и пользователя"""

    serializer_class = ProfileUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        try:
            return self.request.user.profile
        except Profile.DoesNotExist:
            return Response(
                {"detail": "Profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )


class ProfileDetailView(generics.RetrieveAPIView):
    """Представление для получения профиля пользователя"""

    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        user_id = self.kwargs.get("pk", self.request.user.id)
        cache_key = f"profile_{user_id}"
        profile = cache.get(cache_key)

        if not profile:
            user = CustomUser.objects.filter(id=user_id).first()
            if not user:
                raise serializers.ValidationError({"detail": "User not found"})
            profile = user.profile
            cache.set(cache_key, profile, timeout=300)

        profile.update_online_status()
        return profile


class ContactManagementView(APIView):
    """Управление запросами в контакты: отправка, подтверждение и удаление"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        to_user_id = request.data.get("to_user_id")
        if not to_user_id:
            return Response(
                {"detail": "User ID is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            to_user = CustomUser.objects.get(id=to_user_id)
            if Connections.objects.filter(
                from_user=request.user, to_user=to_user
            ).exists():
                return Response(
                    {"detail": "Request already sent"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            connection = Connections.objects.create(
                from_user=request.user, to_user=to_user
            )
            return Response(
                ConnectionsSerializer(connection).data,
                status=status.HTTP_201_CREATED,
            )
        except CustomUser.DoesNotExist:
            return Response(
                {"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except IntegrityError:
            return Response(
                {"detail": "Error creating connection request."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def patch(self, request, *args, **kwargs):
        connection_id = kwargs.get("pk")
        if not connection_id:
            return Response(
                {"detail": "Connection ID is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            connection = Connections.objects.get(
                id=connection_id, to_user=request.user, is_confirmed=False
            )
            connection.is_confirmed = True
            connection.save()
            return Response(
                ConnectionsSerializer(connection).data,
                status=status.HTTP_200_OK,
            )
        except Connections.DoesNotExist:
            return Response(
                {"detail": "Request not found or already confirmed"},
                status=status.HTTP_404_NOT_FOUND,
            )

    def delete(self, request, *args, **kwargs):
        connection_id = kwargs.get("pk")
        if not connection_id:
            return Response(
                {"detail": "Connection ID is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            connection = Connections.objects.get(id=connection_id)
            if (
                request.user != connection.to_user
                and request.user != connection.from_user
            ):
                return Response(
                    {"detail": "Not allowed"}, status=status.HTTP_403_FORBIDDEN
                )
            connection.delete()
            return Response(
                {"detail": "Connection removed"},
                status=status.HTTP_204_NO_CONTENT,
            )
        except Connections.DoesNotExist:
            return Response(
                {"detail": "Connection not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

    def get(self, request, *args, **kwargs):
        user_id = request.user.id
        cache_key = f"confirmed_contacts_{user_id}"
        contacts = cache.get(cache_key)

        if not contacts:
            confirmed_connections = Connections.objects.filter(
                Q(from_user=request.user) | Q(to_user=request.user),
                is_confirmed=True,
            )
            contacts = ConnectionsSerializer(
                confirmed_connections, many=True
            ).data
            cache.set(cache_key, contacts, timeout=300)

        return Response(contacts, status=status.HTTP_200_OK)
