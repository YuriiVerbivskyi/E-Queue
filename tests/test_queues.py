import pytest
from django.urls import reverse
from rest_framework import status
from main.models import Room, QueueEntry
from datetime import timedelta
from django.utils import timezone

pytestmark = pytest.mark.django_db


class TestQueueListView:
    def test_get_queues_unauthenticated(self, api_client):
        response = api_client.get(reverse('queue-list'))
        assert response.status_code == status.HTTP_200_OK

    def test_get_queues_authenticated(self, authenticated_client):
        response = authenticated_client.get(reverse('queue-list'))
        assert response.status_code == status.HTTP_200_OK

    def test_get_queues_with_data(self, authenticated_client, room):
        response = authenticated_client.get(reverse('queue-list'))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_filter_queues_by_active(self, authenticated_client, room, room_inactive):
        response = authenticated_client.get(reverse('queue-list') + '?is_active=true')
        assert response.status_code == status.HTTP_200_OK

    def test_create_queue_authenticated_teacher(self, authenticated_teacher_client):
        data = {
            'name': 'New Queue',
            'description': 'Test queue',
            'event_date': (timezone.now() + timedelta(hours=1)).isoformat(),
            'is_active': True
        }
        response = authenticated_teacher_client.post(reverse('queue-list'), data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Room.objects.count() >= 1

    def test_create_queue_unauthenticated(self, api_client):
        data = {
            'name': 'Unauthorized Queue',
            'description': 'Test',
            'event_date': timezone.now().isoformat(),
            'is_active': True
        }
        response = api_client.post(reverse('queue-list'), data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_queue_invalid_data(self, authenticated_teacher_client):
        data = {
            'name': '',
            'event_date': 'invalid-date'
        }
        response = authenticated_teacher_client.post(reverse('queue-list'), data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_queue_missing_fields(self, authenticated_teacher_client):
        data = {'description': 'No name or time'}
        response = authenticated_teacher_client.post(reverse('queue-list'), data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_queue_past_time(self, authenticated_teacher_client):
        data = {
            'name': 'Past Queue',
            'description': 'Test',
            'event_date': (timezone.now() - timedelta(hours=1)).isoformat(),
            'is_active': True
        }
        response = authenticated_teacher_client.post(reverse('queue-list'), data)
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST]


class TestQueueDetailView:
    def test_get_queue_detail(self, authenticated_client, room):
        response = authenticated_client.get(
            reverse('queue-detail', kwargs={'pk': room.id})
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == room.name

    def test_get_queue_not_found(self, authenticated_client):
        response = authenticated_client.get(
            reverse('queue-detail', kwargs={'pk': 9999})
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_queue_by_owner(self, authenticated_teacher_client, room):
        data = {
            'name': 'Updated Queue',
            'description': room.description,
            'event_date': room.event_date.isoformat(),
            'is_active': True
        }
        response = authenticated_teacher_client.put(
            reverse('queue-detail', kwargs={'pk': room.id}),
            data
        )
        assert response.status_code == status.HTTP_200_OK
        room.refresh_from_db()
        assert room.name == 'Updated Queue'

    def test_update_queue_unauthorized(self, authenticated_client, room):
        data = {
            'name': 'Hacked Queue',
            'description': room.description,
            'event_date': room.event_date.isoformat(),
            'is_active': True
        }
        response = authenticated_client.put(
            reverse('queue-detail', kwargs={'pk': room.id}),
            data
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_partial_update_queue(self, authenticated_teacher_client, room):
        data = {'name': 'Partially Updated'}
        response = authenticated_teacher_client.patch(
            reverse('queue-detail', kwargs={'pk': room.id}),
            data
        )
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_405_METHOD_NOT_ALLOWED]

    def test_delete_queue_by_owner(self, authenticated_teacher_client, room):
        response = authenticated_teacher_client.delete(
            reverse('queue-detail', kwargs={'pk': room.id})
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Room.objects.count() == 0

    def test_delete_queue_unauthorized(self, authenticated_client, room):
        response = authenticated_client.delete(
            reverse('queue-detail', kwargs={'pk': room.id})
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_nonexistent_queue(self, authenticated_teacher_client):
        response = authenticated_teacher_client.delete(
            reverse('queue-detail', kwargs={'pk': 9999})
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_queue_with_full_slots(self, db, room, student_user, student_user_2):
        QueueEntry.objects.create(room=room, user=student_user, position=1, status='waiting')
        QueueEntry.objects.create(room=room, user=student_user_2, position=2, status='waiting')
        assert QueueEntry.objects.filter(room=room).count() == 2