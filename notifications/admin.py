from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('to_user', 'type', 'message', 'is_read', 'timestamp')
    list_filter = ('is_read', 'type')
    search_fields = ('to_user__email', 'message')
