from django.contrib.auth import authenticate
from django.core.validators import RegexValidator
from django.db import IntegrityError
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Connections, CustomUser, Profile


class LoginSerializer(serializers.Serializer):
    """Сериализатор для логирования пользователя"""

    username = serializers.CharField(required=True)
    password = serializers.CharField(
        write_only=True, required=True, style={'input_type': 'password'}
    )

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        user = authenticate(username=username, password=password)

        if user and user.is_active:
            data['user'] = user
            return data
        raise serializers.ValidationError(
            'Неверные учетные данные или учетная запись не активна.'
        )

    def create(self, validated_data):
        user = validated_data['user']
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }


class RegisterSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации пользователя"""

    email = serializers.EmailField(required=True)
    username = serializers.CharField(
        max_length=150,
        validators=[RegexValidator(r'^[\w.@+-]+$')],
        required=True,
    )
    first_name = serializers.CharField(max_length=150, required=True)
    last_name = serializers.CharField(max_length=150, required=True)
    password = serializers.CharField(
        write_only=True, required=True, style={'input_type': 'password'}
    )

    class Meta:
        model = CustomUser
        fields = [
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
        ]

    def create(self, validated_data):
        """Создание нового пользователя"""
        try:
            user = CustomUser.objects.create_user(
                username=validated_data['username'],
                email=validated_data['email'],
                first_name=validated_data.get('first_name', ''),
                last_name=validated_data.get('last_name', ''),
                password=validated_data['password'],
            )
            return user
        except IntegrityError:
            raise serializers.ValidationError(
                {'username': 'Пользователь с такими данными уже существует'}
            )


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя"""

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name')


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор редактирования профиля"""

    user = UserSerializer()

    class Meta:
        model = Profile
        fields = (
            'user',
            'status_message',
            'bio',
            'avatar',
            'birthday',
            'is_online',
            'last_seen',
        )

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data:
            for attr, value in user_data.items():
                setattr(instance.user, attr, value)
            instance.user.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class CustomUserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения профиля пользователя без email."""

    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name')


class ProfileSerializer(serializers.ModelSerializer):
    """Сериализатор профиля пользователя"""

    user = CustomUserProfileSerializer()

    class Meta:
        model = Profile
        fields = (
            'id',
            'user',
            'bio',
            'avatar',
            'birthday',
            'status_message',
            'is_online',
            'last_seen',
        )


class ConnectionsSerializer(serializers.ModelSerializer):
    """Сериализатор связей"""

    class Meta:
        model = Connections
        fields = '__all__'
