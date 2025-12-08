from django.contrib import admin
from .models import CustomUser, Queue, QueueEntry, Notification

admin.site.register(CustomUser)
admin.site.register(Queue)
admin.site.register(QueueEntry)
admin.site.register(Notification)
