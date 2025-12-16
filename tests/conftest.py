import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from main.models import Queue, QueueEntry, Notification
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
        email='teacher@test.com'
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
def queue(db, teacher_user):
    return Queue.objects.create(
        name='Lab Defense #3',
        description='Queue for lab defense',
        created_by=teacher_user,
        scheduled_time=timezone.now() + timedelta(hours=2),
        max_slots=10,
        is_active=True
    )

@pytest.fixture
def queue_inactive(db, teacher_user):
    return Queue.objects.create(
        name='Past Queue',
        description='Old queue',
        created_by=teacher_user,
        scheduled_time=timezone.now() - timedelta(hours=2),
        max_slots=5,
        is_active=False
    )

@pytest.fixture
def queue_entry(db, queue, student_user):
    return QueueEntry.objects.create(
        queue=queue,
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