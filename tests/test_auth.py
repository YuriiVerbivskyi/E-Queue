import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

User = get_user_model()
pytestmark = pytest.mark.django_db

class TestAuthenticatedAccess:
    def test_access_protected_endpoint_without_token(self, api_client):
        response = api_client.get(reverse('queue_entries'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_access_protected_endpoint_with_invalid_token(self, api_client):
        api_client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        response = api_client.get(reverse('queue_entries'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_access_protected_endpoint_with_valid_token(self, authenticated_client):
        response = authenticated_client.get(reverse('queue_entries'))
        assert response.status_code == status.HTTP_200_OK

@pytest.mark.django_db
class TestUserRegistration:
    def test_register_user(self, api_client):
        data = {
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'securepass123',
            'password2': 'securepass123'
        }
        response = api_client.post(reverse('register_api'), data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_register_duplicate_username(self, api_client, student_user):
        data = {
            'username': 'student',
            'email': 'another@test.com',
            'password': 'securepass123',
            'password2': 'securepass123'
        }
        response = api_client.post(reverse('register_api'), data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_page(self, api_client):
        response = api_client.get(reverse('login_page'))
        assert response.status_code == status.HTTP_200_OK

@pytest.mark.django_db
class TestLogout:
    def test_logout_authenticated(self, authenticated_client):
        response = authenticated_client.post(reverse('logout'))
        assert response.status_code == status.HTTP_302_FOUND

    def test_logout_unauthenticated(self, api_client):
        response = api_client.post(reverse('logout'))
        assert response.status_code == status.HTTP_302_FOUND