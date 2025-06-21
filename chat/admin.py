from django.contrib import admin
from .models import ChatRoom, Message

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    fields = ('sender', 'content', 'timestamp')
    readonly_fields = ('timestamp',)

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'is_group', 'participant_list')
    search_fields = ('name',)
    filter_horizontal = ('participants',)
    inlines = [MessageInline]

    def participant_list(self, obj):
        return ", ".join([u.get_full_name() for u in obj.participants.all()])

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'room', 'sender', 'content', 'timestamp')
    list_filter = ('room', 'sender')
    search_fields = ('content', 'sender__first_name', 'sender__last_name')
    readonly_fields = ('timestamp',)
