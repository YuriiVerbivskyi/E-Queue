import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

User = get_user_model()
pytestmark = pytest.mark.django_db


class TestRegistration:

    def test_register_valid_user(self, api_client):
        data = {
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'securepass123',
            'password2': 'securepass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        response = api_client.post(reverse('register_api'), data)
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.count() >= 1

    def test_register_missing_fields(self, api_client):
        data = {'username': 'newuser'}
        response = api_client.post(reverse('register_api'), data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_duplicate_username(self, api_client, student_user):
        data = {
            'username': 'student',
            'email': 'another@test.com',
            'password': 'securepass123',
            'password2': 'securepass123'
        }
        response = api_client.post(reverse('register_api'), data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_invalid_email(self, api_client):
        data = {
            'username': 'newuser',
            'email': 'invalid-email',
            'password': 'securepass123',
            'password2': 'securepass123'
        }
        response = api_client.post(reverse('register_api'), data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestLogin:

    def test_login_valid_credentials(self, api_client, student_user):
        data = {
            'username': 'student',
            'password': 'student123'
        }
        response = api_client.post(reverse('token_obtain_pair'), data)
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_login_invalid_username(self, api_client):
        data = {
            'username': 'nonexistent',
            'password': 'password123'
        }
        response = api_client.post(reverse('token_obtain_pair'), data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_invalid_password(self, api_client, student_user):
        data = {
            'username': 'student',
            'password': 'wrongpassword'
        }
        response = api_client.post(reverse('token_obtain_pair'), data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_refresh(self, api_client, student_user):
        login_data = {
            'username': 'student',
            'password': 'student123'
        }
        login_response = api_client.post(reverse('token_obtain_pair'), login_data)
        refresh_token = login_response.data['refresh']

        refresh_data = {'refresh': refresh_token}
        response = api_client.post(reverse('token_refresh'), refresh_data)
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data


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

    def test_user_profile_authenticated(self, authenticated_client):
        response = authenticated_client.get(reverse('user_profile'))
        assert response.status_code == status.HTTP_200_OK
        assert 'username' in response.data

    def test_user_profile_unauthenticated(self, api_client):
        response = api_client.get(reverse('user_profile'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED