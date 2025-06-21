from django.contrib import admin
from .models import FriendRequest, Notification, Friendship
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

# Custom Notification admin
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "sender", "notification_type", "message", "is_read", "timestamp")
    list_filter = ("notification_type", "is_read", "timestamp")
    search_fields = ("user__username", "sender__username", "message")
    ordering = ("-timestamp",)

# Register models in admin
admin.site.register(FriendRequest)
admin.site.register(Friendship)
admin.site.register(Notification, NotificationAdmin)
