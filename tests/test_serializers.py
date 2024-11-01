import pytest

from accounts.serializers import RegisterSerializer


@pytest.mark.django_db
def test_valid_registration_serializer():
    data = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "password123",
        "first_name": "Test",
        "last_name": "User",
    }
    serializer = RegisterSerializer(data=data)
    assert serializer.is_valid()
    user = serializer.save()
    assert user.username == "testuser"
    assert user.email == "testuser@example.com"
