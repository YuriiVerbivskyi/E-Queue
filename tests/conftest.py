import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from main.models import Queue, QueueEntry, Notification
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    user = User.objects.create_user(
        username='admin',
        email='admin@test.com',
        password='admin123',
        is_staff=True,
        is_superuser=True,
        role='admin'
    )
    return user

@pytest.fixture
def teacher_user(db):
    user = User.objects.create_user(
        username='teacher',
        email='teacher@test.com',
        password='teacher123',
        role='teacher'
    )
    return user

@pytest.fixture
def student_user(db):
    user = User.objects.create_user(
        username='student',
        email='student@test.com',
        password='student123',
        role='student'
    )
    return user

@pytest.fixture
def student_user_2(db):
    user = User.objects.create_user(
        username='student2',
        email='student2@test.com',
        password='student123',
        role='student'
    )
    return user


@pytest.fixture
def authenticated_client(api_client, student_user):
    refresh = RefreshToken.for_user(student_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client

@pytest.fixture
def authenticated_teacher_client(api_client, teacher_user):
    refresh = RefreshToken.for_user(teacher_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client

@pytest.fixture
def authenticated_admin_client(api_client, admin_user):
    refresh = RefreshToken.for_user(admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def queue(db, teacher_user):
    queue = Queue.objects.create(
        name='Lab Defense #3',
        description='Testing lab defense',
        created_by=teacher_user,
        scheduled_time=timezone.now() + timedelta(hours=2),
        max_slots=5,
        is_active=True
    )
    return queue

@pytest.fixture
def queue_inactive(db, teacher_user):
    queue = Queue.objects.create(
        name='Past Queue',
        description='Old queue',
        created_by=teacher_user,
        scheduled_time=timezone.now() - timedelta(hours=2),
        max_slots=5,
        is_active=False
    )
    return queue

@pytest.fixture
def queue_entry(db, queue, student_user):
    entry = QueueEntry.objects.create(
        queue=queue,
        user=student_user,
        position=1,
        status='waiting'
    )
    return entry

@pytest.fixture
def notification(db, student_user):
    notification = Notification.objects.create(
        user=student_user,
        message='Your turn is coming',
        notification_type='ready',
        is_read=False
    )
    return notification
