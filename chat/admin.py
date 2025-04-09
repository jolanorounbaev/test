from django.contrib import admin
from .models import ChatMessage, GroupChat, GroupMember

class GroupMemberInline(admin.TabularInline):  # or use StackedInline if you prefer
    model = GroupMember
    extra = 1  # how many empty fields to show

@admin.register(GroupChat)
class GroupChatAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at')
    search_fields = ('name', 'created_by__email')
    ordering = ('-created_at',)
    inlines = [GroupMemberInline]  # <-- nested here

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'group', 'content', 'timestamp')
    list_filter = ('group', 'timestamp')
    search_fields = ('sender__email', 'receiver__email', 'content')
    ordering = ('-timestamp',)
