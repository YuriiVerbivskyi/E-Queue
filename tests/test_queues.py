import pytest
from django.urls import reverse
from rest_framework import status
from main.models import Queue
from datetime import datetime, timedelta
from django.utils import timezone

pytestmark = pytest.mark.django_db


class TestQueueListView:
    def test_get_queues_unauthenticated(self, api_client):
        response = api_client.get(reverse('queue_list_api'))
        assert response.status_code == status.HTTP_200_OK

    def test_get_queues_authenticated(self, authenticated_client):
        response = authenticated_client.get(reverse('queue_list_api'))
        assert response.status_code == status.HTTP_200_OK

    def test_get_queues_with_data(self, authenticated_client, queue):
        response = authenticated_client.get(reverse('queue_list_api'))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_filter_queues_by_active(self, authenticated_client, queue, queue_inactive):
        response = authenticated_client.get(reverse('queue_list_api') + '?is_active=true')
        assert response.status_code == status.HTTP_200_OK

    def test_create_queue_authenticated_teacher(self, authenticated_teacher_client):
        data = {
            'name': 'New Queue',
            'description': 'Test queue',
            'scheduled_time': (timezone.now() + timedelta(hours=1)).isoformat(),
            'max_slots': 10,
            'is_active': True
        }
        response = authenticated_teacher_client.post(reverse('queue_list_api'), data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Queue.objects.count() >= 1

    def test_create_queue_unauthenticated(self, api_client):
        data = {
            'name': 'Unauthorized Queue',
            'description': 'Test',
            'scheduled_time': timezone.now().isoformat(),
            'max_slots': 5,
            'is_active': True
        }
        response = api_client.post(reverse('queue_list_api'), data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_queue_invalid_data(self, authenticated_teacher_client):
        data = {
            'name': '',
            'scheduled_time': 'invalid-date',
            'max_slots': -1
        }
        response = authenticated_teacher_client.post(reverse('queue_list_api'), data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_queue_missing_fields(self, authenticated_teacher_client):
        data = {'description': 'No name or time'}
        response = authenticated_teacher_client.post(reverse('queue_list_api'), data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_queue_past_time(self, authenticated_teacher_client):
        data = {
            'name': 'Past Queue',
            'description': 'Test',
            'scheduled_time': (timezone.now() - timedelta(hours=1)).isoformat(),
            'max_slots': 5,
            'is_active': True
        }
        response = authenticated_teacher_client.post(reverse('queue_list_api'), data)
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST]


class TestQueueDetailView:
    def test_get_queue_detail(self, authenticated_client, queue):
        response = authenticated_client.get(
            reverse('queue_detail_api', kwargs={'pk': queue.id})
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == queue.name

    def test_get_queue_not_found(self, authenticated_client):
        response = authenticated_client.get(
            reverse('queue_detail_api', kwargs={'pk': 9999})
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
            reverse('queue_detail_api', kwargs={'pk': queue.id}),
            data
        )
        assert response.status_code == status.HTTP_200_OK
        queue.refresh_from_db()
        assert queue.name == 'Updated Queue'

    def test_update_queue_unauthorized(self, authenticated_client, queue):
        data = {
            'name': 'Hacked Queue',
            'description': queue.description,
            'scheduled_time': queue.scheduled_time.isoformat(),
            'max_slots': 5,
            'is_active': True
        }
        response = authenticated_client.put(
            reverse('queue_detail_api', kwargs={'pk': queue.id}),
            data
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_partial_update_queue(self, authenticated_teacher_client, queue):
        data = {'name': 'Partially Updated'}
        response = authenticated_teacher_client.patch(
            reverse('queue_detail_api', kwargs={'pk': queue.id}),
            data
        )
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_405_METHOD_NOT_ALLOWED]

    def test_delete_queue_by_owner(self, authenticated_teacher_client, queue):
        response = authenticated_teacher_client.delete(
            reverse('queue_detail_api', kwargs={'pk': queue.id})
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Queue.objects.count() == 0

    def test_delete_queue_unauthorized(self, authenticated_client, queue):
        response = authenticated_client.delete(
            reverse('queue_detail_api', kwargs={'pk': queue.id})
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_nonexistent_queue(self, authenticated_teacher_client):
        response = authenticated_teacher_client.delete(
            reverse('queue_detail_api', kwargs={'pk': 9999})
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_queue_with_full_slots(self, db, queue, student_user, student_user_2):
        from main.models import QueueEntry
        QueueEntry.objects.create(queue=queue, user=student_user, position=1, status='waiting')
        QueueEntry.objects.create(queue=queue, user=student_user_2, position=2, status='waiting')
        assert QueueEntry.objects.filter(queue=queue).count() == 2