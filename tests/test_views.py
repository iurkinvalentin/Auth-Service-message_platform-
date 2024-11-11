import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(
        username='testuser', email='test@example.com', password='password123'
    )


@pytest.fixture
def token(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token)
    }


# Дополнительные тесты для различных ошибок

@pytest.mark.django_db
def test_register_user_missing_field(api_client):
    """Тест на отсутствие обязательного поля при регистрации"""
    url = reverse('register')
    data = {
        'username': 'newuser',
        # Отсутствует email
        'first_name': 'First',
        'last_name': 'Last',
        'password': 'strongpassword123'
    }
    response = api_client.post(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'email' in response.data  # Ошибка должна быть связана с email


@pytest.mark.django_db
def test_login_invalid_credentials(api_client):
    """Тест на неправильные учетные данные при входе"""
    url = reverse('login')
    data = {
        'username': 'nonexistentuser',
        'password': 'wrongpassword'
    }
    response = api_client.post(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'detail' in response.data
    assert response.data['detail'] == 'Неверные учетные данные или учетная запись не активна.'


@pytest.mark.django_db
def test_logout_invalid_refresh_token(api_client, token):
    """Тест на невалидный refresh токен при выходе"""
    url = reverse('logout')
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token["access"]}')
    response = api_client.post(url, {'refresh_token': 'invalid_refresh_token'})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'detail' in response.data


@pytest.mark.django_db
def test_profile_detail_view_no_token(api_client):
    """Тест на доступ к профилю без токена"""
    url = reverse('profile-detail')
    response = api_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert 'detail' in response.data
    assert response.data['detail'] == 'Authentication credentials were not provided.'


@pytest.mark.django_db
def test_profile_update_view_no_token(api_client):
    """Тест на обновление профиля без токена"""
    url = reverse('update-user')
    data = {'bio': 'Updated bio'}
    response = api_client.patch(url, data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_delete_user_unauthenticated(api_client):
    """Тест на удаление пользователя без аутентификации"""
    url = reverse('delete-user')
    response = api_client.delete(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert 'detail' in response.data
    assert response.data['detail'] == 'Authentication credentials were not provided.'


@pytest.mark.django_db
def test_delete_user_authenticated(api_client, user, token):
    """Тест на удаление пользователя с аутентификацией"""
    url = reverse('delete-user')
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token["access"]}')
    response = api_client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_contact_management_missing_to_user_id(api_client, token):
    """Тест на отправку запроса в контакты без указания to_user_id"""
    url = reverse('contact_management')
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token["access"]}')
    response = api_client.post(url, {})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'detail' in response.data
    assert response.data['detail'] == 'User ID is required.'


@pytest.mark.django_db
def test_verify_token_invalid_token(api_client):
    """Тест на проверку недействительного токена"""
    url = reverse('verify_token')
    response = api_client.post(url, {'token': 'invalid_token'})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['detail'] == 'Token is invalid or expired.'
