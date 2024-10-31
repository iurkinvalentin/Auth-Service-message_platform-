import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import CustomUser


@pytest.mark.django_db
def test_register_user():
    client = APIClient()
    url = reverse('register')
    data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "password123",
        "first_name": "New",
        "last_name": "User"
    }
    
    response = client.post(url, data, format='json')
    
    assert response.status_code == 201
    assert CustomUser.objects.count() == 1
    user = CustomUser.objects.get(username="newuser")
    assert user.email == "newuser@example.com"
