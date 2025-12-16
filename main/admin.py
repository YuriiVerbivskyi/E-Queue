from django.contrib import admin
from .models import CustomUser, Room, QueueEntry, Notification
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework_simplejwt.token_blacklist.admin import OutstandingTokenAdmin

admin.site.register(CustomUser)
admin.site.register(Room)
admin.site.register(QueueEntry)
admin.site.register(Notification)

admin.site.unregister(OutstandingToken)

@admin.register(OutstandingToken)
class CustomOutstandingTokenAdmin(OutstandingTokenAdmin):
    list_display = (
        "jti",
        "user",
        "created_at",
        "expires_at",
    )
    search_fields = ("user__username", "jti")
    ordering = ("-created_at",)

    class Media:
        css = {
            "all": ("css/admin_custom.css",)
        }