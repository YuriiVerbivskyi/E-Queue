import pytest
from django.urls import reverse
from rest_framework import status
from main.models import QueueEntry

pytestmark = pytest.mark.django_db


class TestQueueEntryListView:

    def test_get_entries_unauthenticated(self, api_client):
        response = api_client.get(reverse('queue_entries'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_entries_authenticated(self, authenticated_client):
        response = authenticated_client.get(reverse('queue_entries'))
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_get_entries_with_data(self, authenticated_client, queue_entry):
        response = authenticated_client.get(reverse('queue_entries'))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_create_entry_authenticated(self, authenticated_client, queue):
        data = {
            'queue': queue.id,
            'status': 'waiting'
        }
        response = authenticated_client.post(reverse('queue_entries'), data)
        assert response.status_code == status.HTTP_201_CREATED
        assert QueueEntry.objects.count() >= 1

    def test_create_entry_unauthenticated(self, api_client, queue):
        data = {
            'queue': queue.id,
            'status': 'waiting'
        }
        response = api_client.post(reverse('queue_entries'), data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_entry_invalid_queue(self, authenticated_client):
        data = {
            'queue': 9999,
            'status': 'waiting'
        }
        response = authenticated_client.post(reverse('queue_entries'), data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_position_assignment(self, authenticated_client, queue):
        data = {'queue': queue.id, 'status': 'waiting'}
        response = authenticated_client.post(reverse('queue_entries'), data)
        assert response.status_code == status.HTTP_201_CREATED
        entry = QueueEntry.objects.first()
        assert entry.position > 0


class TestQueueEntryDetailView:

    def test_get_entry_detail_authenticated(self, authenticated_client, queue_entry):
        response = authenticated_client.get(
            reverse('queue_entry_detail', kwargs={'pk': queue_entry.id})
        )
        assert response.status_code == status.HTTP_200_OK

    def test_get_entry_unauthenticated(self, api_client, queue_entry):
        response = api_client.get(
            reverse('queue_entry_detail', kwargs={'pk': queue_entry.id})
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_entry_not_found(self, authenticated_client):
        response = authenticated_client.get(
            reverse('queue_entry_detail', kwargs={'pk': 9999})
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_entry_status(self, authenticated_client, queue_entry):
        data = {
            'queue': queue_entry.queue.id,
            'status': 'completed',
            'position': queue_entry.position
        }
        response = authenticated_client.put(
            reverse('queue_entry_detail', kwargs={'pk': queue_entry.id}),
            data
        )
        assert response.status_code == status.HTTP_200_OK

    def test_delete_entry(self, authenticated_client, queue_entry):
        response = authenticated_client.delete(
            reverse('queue_entry_detail', kwargs={'pk': queue_entry.id})
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert QueueEntry.objects.count() == 0

    def test_delete_entry_unauthenticated(self, api_client, queue_entry):
        response = api_client.delete(
            reverse('queue_entry_detail', kwargs={'pk': queue_entry.id})
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_entry_not_found(self, authenticated_client):
        response = authenticated_client.delete(
            reverse('queue_entry_detail', kwargs={'pk': 9999})
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
