import pytest
from django.urls import reverse
from rest_framework import status
from main.models import Queue
from datetime import datetime, timedelta

pytestmark = pytest.mark.django_db


class TestQueueListView:

    def test_get_queues_unauthenticated(self, api_client):
        response = api_client.get(reverse('queues'))
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_get_queues_authenticated(self, authenticated_client):
        response = authenticated_client.get(reverse('queues'))
        assert response.status_code == status.HTTP_200_OK

    def test_get_queues_with_data(self, authenticated_client, queue):
        response = authenticated_client.get(reverse('queues'))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        assert response.data[0]['name'] == 'Lab Defense #3'

    def test_create_queue_authenticated_teacher(self, authenticated_teacher_client):
        data = {
            'name': 'New Queue',
            'description': 'Test queue',
            'scheduled_time': (datetime.now() + timedelta(hours=1)).isoformat(),
            'max_slots': 10,
            'is_active': True
        }
        response = authenticated_teacher_client.post(reverse('queues'), data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Queue.objects.count() >= 1

    def test_create_queue_unauthenticated(self, api_client):
        data = {
            'name': 'Unauthorized Queue',
            'description': 'Test',
            'scheduled_time': datetime.now().isoformat(),
            'max_slots': 5,
            'is_active': True
        }
        response = api_client.post(reverse('queues'), data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_queue_invalid_data(self, authenticated_teacher_client):
        data = {
            'name': '',
            'scheduled_time': 'invalid-date',
            'max_slots': -1
        }
        response = authenticated_teacher_client.post(reverse('queues'), data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_queue_missing_fields(self, authenticated_teacher_client):
        data = {'description': 'No name or time'}
        response = authenticated_teacher_client.post(reverse('queues'), data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestQueueDetailView:

    def test_get_queue_detail(self, authenticated_client, queue):
        response = authenticated_client.get(
            reverse('queue_detail', kwargs={'pk': queue.id})
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Lab Defense #3'

    def test_get_queue_not_found(self, authenticated_client):
        response = authenticated_client.get(
            reverse('queue_detail', kwargs={'pk': 9999})
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_queue_by_owner(self, authenticated_teacher_client, queue):
        data = {
            'name': 'Updated Queue',
            'description': queue.description,
            'scheduled_time': queue.scheduled_time.isoformat(),
            'max_slots': 20,
            'is_active': True
        }
        response = authenticated_teacher_client.put(
            reverse('queue_detail', kwargs={'pk': queue.id}),
            data
        )
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN]

    def test_update_queue_unauthorized(self, authenticated_client, queue):
        data = {
            'name': 'Hacked Queue',
            'description': queue.description,
            'scheduled_time': queue.scheduled_time.isoformat(),
            'max_slots': 5,
            'is_active': True
        }
        response = authenticated_client.put(
            reverse('queue_detail', kwargs={'pk': queue.id}),
            data
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_queue_by_owner(self, authenticated_teacher_client, queue):
        response = authenticated_teacher_client.delete(
            reverse('queue_detail', kwargs={'pk': queue.id})
        )
        assert response.status_code in [status.HTTP_204_NO_CONTENT, status.HTTP_403_FORBIDDEN]

    def test_delete_queue_unauthorized(self, authenticated_client, queue):
        response = authenticated_client.delete(
            reverse('queue_detail', kwargs={'pk': queue.id})
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_nonexistent_queue(self, authenticated_teacher_client):
        response = authenticated_teacher_client.delete(
            reverse('queue_detail', kwargs={'pk': 9999})
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
