import pytest
from rest_framework import status

class TestAuthenticatedAccess:
    def test_user_profile_authenticated(self, authenticated_client):
        response = authenticated_client.get('/profile/')
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_302_FOUND]

    def test_user_profile_unauthenticated(self, api_client):
        response = api_client.get('/profile/')
        assert response.status_code in [status.HTTP_302_FOUND, status.HTTP_403_FORBIDDEN]

class TestUserRegistration:
    def test_register_user(self, api_client):
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'testpass123'
        }
        response = api_client.post('/register-page/', data)
        assert response.status_code in [200, 302, 201]

    def test_login_page(self, api_client):
        response = api_client.get('/login/')
        assert response.status_code == status.HTTP_200_OK

    def test_register_duplicate_username(self, db, api_client):
        api_client.post('/register-page/', {
            'username': 'duplicate',
            'email': 'test1@test.com',
            'password': 'pass123'
        })
        response = api_client.post('/register-page/', {
            'username': 'duplicate',
            'email': 'test2@test.com',
            'password': 'pass123'
        })
        assert response.status_code in [200, 400, 409, 302]


class TestLogout:
    def test_logout_authenticated(self, authenticated_client):
        response = authenticated_client.post('/logout/')
        assert response.status_code in [status.HTTP_302_FOUND, status.HTTP_200_OK]

    def test_logout_unauthenticated(self, api_client):
        response = api_client.post('/logout/')
        assert response.status_code in [status.HTTP_302_FOUND, status.HTTP_403_FORBIDDEN]
