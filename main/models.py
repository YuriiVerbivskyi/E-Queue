import uuid
import random
import string
from django.db import models
from django.contrib.auth.models import AbstractUser, User


def generate_short_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

class Queue(models.Model):
    title = models.CharField(max_length=255)
    code = models.CharField(max_length=10, default=generate_short_code, unique=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)

def generate_room_id():
    length = 6
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=length))

class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, null=True, blank=True)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_groups',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_permissions',
        blank=True
    )

    def __str__(self):
        return self.username

class Room(models.Model):
    id = models.CharField(max_length=8, primary_key=True, default=generate_room_id, editable=False)
    name = models.CharField(max_length=200)
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='rooms')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.id})"

class Queue(models.Model):
    name = models.CharField(max_length=200, default='Default Queue')
    description = models.TextField(blank=True, default='')
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_time = models.DateTimeField(null=True, blank=True)
    max_slots = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

class QueueEntry(models.Model):
    STATUS_CHOICES = (
        ('waiting', 'Waiting'),
        ('ready', 'Ready'),
        ('completed', 'Completed'),
        ('no_show', 'No Show'),
    )
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    queue = models.ForeignKey(Queue, on_delete=models.CASCADE, null=True, blank=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, null=True, blank=True, related_name='entries')
    position = models.IntegerField(default=0)
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default='waiting')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user.username} - Pos {self.position}"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('registration', 'Registration'),
        ('queue_joined', 'Queue Joined'),
        ('queue_position', 'Queue Position Update'),
        ('ready', 'Your Turn is Ready'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='registration')
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.notification_type}"