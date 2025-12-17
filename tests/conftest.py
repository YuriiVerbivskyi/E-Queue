import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from main.models import Room, QueueEntry, Notification
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def teacher_user(db):
    user = User.objects.create_user(
        username='teacher',
        password='teacher123',
        email='teacher@test.com',
        is_staff=True
    )
    return user

@pytest.fixture
def authenticated_teacher_client(api_client, teacher_user):
    api_client.force_authenticate(user=teacher_user)
    return api_client

@pytest.fixture
def student_user(db):
    user = User.objects.create_user(
        username='student',
        password='student123',
        email='student@test.com'
    )
    return user

@pytest.fixture
def student_user_2(db):
    user = User.objects.create_user(
        username='student2',
        password='student123',
        email='student2@test.com'
    )
    return user

@pytest.fixture
def authenticated_client(api_client, student_user):
    api_client.force_authenticate(user=student_user)
    return api_client

@pytest.fixture
def room(db, teacher_user):
    return Room.objects.create(
        name='Lab Defense #3',
        description='Queue for lab defense',
        teacher=teacher_user,
        event_date=timezone.now() + timedelta(hours=2),
        is_active=True
    )

@pytest.fixture
def room_inactive(db, teacher_user):
    return Room.objects.create(
        name='Past Queue',
        description='Old queue',
        teacher=teacher_user,
        event_date=timezone.now() - timedelta(hours=2),
        is_active=False
    )

@pytest.fixture
def queue_entry(db, room, student_user):
    return QueueEntry.objects.create(
        room=room,
        user=student_user,
        position=1,
        status='waiting'
    )

@pytest.fixture
def notification(db, student_user):
    return Notification.objects.create(
        user=student_user,
        notification_type='ready',
        subject='Your turn',
        message='You are next in queue',
        is_read=False
    )