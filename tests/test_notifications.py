import pytest
from django.urls import reverse
from rest_framework import status
from main.models import Notification

pytestmark = pytest.mark.django_db


class TestNotificationListView:

    def test_get_notifications_unauthenticated(self, api_client):
        response = api_client.get(reverse('notifications_list'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_notifications_authenticated(self, authenticated_client):
        response = authenticated_client.get(reverse('notifications_list'))
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_get_notifications_with_data(self, authenticated_client, notification):
        response = authenticated_client.get(reverse('notifications_list'))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_get_unread_notifications(self, authenticated_client, notification):
        response = authenticated_client.get(reverse('notifications_list'))
        assert response.status_code == status.HTTP_200_OK
        unread = [n for n in response.data if not n['is_read']]
        assert len(unread) >= 1


class TestMarkNotificationAsRead:

    def test_mark_as_read_authenticated(self, authenticated_client, notification, student_user):
        notification.user = student_user
        notification.save()

        response = authenticated_client.post(
            reverse('mark_read', kwargs={'notification_id': notification.id})
        )
        assert response.status_code == status.HTTP_200_OK
        notification.refresh_from_db()
        assert notification.is_read is True

    def test_mark_as_read_unauthenticated(self, api_client, notification):
        response = api_client.post(
            reverse('mark_read', kwargs={'notification_id': notification.id})
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_mark_nonexistent_as_read(self, authenticated_client):
        response = authenticated_client.post(
            reverse('mark_read', kwargs={'notification_id': 9999})
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND