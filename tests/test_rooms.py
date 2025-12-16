import pytest
import json
from django.urls import reverse
from main.models import Room, QueueEntry
from unittest.mock import patch

pytestmark = pytest.mark.django_db


class TestRoomViews:
    def test_create_room_authenticated_teacher(self, authenticated_teacher_client, teacher_user):
        authenticated_teacher_client.force_login(teacher_user)
        teacher_user.is_staff = True
        teacher_user.save()

        url = reverse('create_room')
        data = {'name': 'Physics 101'}
        response = authenticated_teacher_client.post(
            url,
            json.dumps(data),
            content_type='application/json'
        )
        assert response.status_code == 201
        assert Room.objects.filter(name='Physics 101').exists()
        assert response.json()['ok'] is True

    def test_create_room_unauthorized_student(self, authenticated_client, student_user):
        authenticated_client.force_login(student_user)
        url = reverse('create_room')
        data = {'name': 'Hacker Room'}
        response = authenticated_client.post(
            url,
            json.dumps(data),
            content_type='application/json'
        )
        assert response.status_code == 403
        assert not Room.objects.filter(name='Hacker Room').exists()

    def test_create_room_missing_name(self, authenticated_teacher_client, teacher_user):
        authenticated_teacher_client.force_login(teacher_user)
        teacher_user.is_staff = True
        teacher_user.save()

        url = reverse('create_room')
        data = {'name': ''}
        response = authenticated_teacher_client.post(
            url,
            json.dumps(data),
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_join_room_success(self, authenticated_client, teacher_user, student_user):
        authenticated_client.force_login(student_user)
        room = Room.objects.create(name="Math", teacher=teacher_user)
        url = reverse('join_room')
        data = {'room_id': room.id}

        response = authenticated_client.post(
            url,
            json.dumps(data),
            content_type='application/json'
        )

        assert response.status_code == 201
        assert response.json()['position'] == 1
        assert QueueEntry.objects.filter(room=room).count() == 1

    def test_join_nonexistent_room(self, authenticated_client, student_user):
        authenticated_client.force_login(student_user)
        url = reverse('join_room')
        data = {'room_id': 'INVALID_ID'}
        response = authenticated_client.post(
            url,
            json.dumps(data),
            content_type='application/json'
        )
        assert response.status_code == 404

    def test_join_room_already_in_queue(self, authenticated_client, teacher_user, student_user):
        authenticated_client.force_login(student_user)
        room = Room.objects.create(name="Biology", teacher=teacher_user)
        QueueEntry.objects.create(user=student_user, room=room, status='waiting')

        url = reverse('join_room')
        data = {'room_id': room.id}

        response = authenticated_client.post(
            url,
            json.dumps(data),
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_get_room_entries_owner(self, authenticated_teacher_client, teacher_user, student_user):
        authenticated_teacher_client.force_login(teacher_user)
        room = Room.objects.create(name="History", teacher=teacher_user)
        QueueEntry.objects.create(user=student_user, room=room, status='waiting')

        url = reverse('get_room_entries')
        response = authenticated_teacher_client.get(url, {'room_id': room.id})

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['username'] == student_user.username

    def test_get_room_entries_not_owner(self, authenticated_client, teacher_user, student_user):
        authenticated_client.force_login(student_user)
        room = Room.objects.create(name="History", teacher=teacher_user)
        url = reverse('get_room_entries')
        response = authenticated_client.get(url, {'room_id': room.id})

        assert response.status_code == 403

    @patch('main.views.Client')
    def test_next_student_in_room(self, mock_twilio, authenticated_teacher_client, teacher_user, student_user):
        authenticated_teacher_client.force_login(teacher_user)
        room = Room.objects.create(name="Chemistry", teacher=teacher_user)
        entry = QueueEntry.objects.create(user=student_user, room=room, status='waiting', position=1)

        url = reverse('next_student_in_room')
        data = {'room_id': room.id}

        response = authenticated_teacher_client.post(
            url,
            json.dumps(data),
            content_type='application/json'
        )

        assert response.status_code == 200
        assert response.json()['ok'] is True

        entry.refresh_from_db()
        assert entry.status == 'ready'

    def test_next_student_empty_queue(self, authenticated_teacher_client, teacher_user):
        authenticated_teacher_client.force_login(teacher_user)
        room = Room.objects.create(name="Empty Room", teacher=teacher_user)
        url = reverse('next_student_in_room')
        data = {'room_id': room.id}

        response = authenticated_teacher_client.post(
            url,
            json.dumps(data),
            content_type='application/json'
        )
        assert response.status_code == 400