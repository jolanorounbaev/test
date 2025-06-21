from django.contrib import admin
from .models import Moment, MomentComment, MomentReply, FlaggedMoment  # ✅ Import proxy model only

# === Inline replies under comments ===
class MomentReplyInline(admin.TabularInline):
    model = MomentReply
    extra = 0
    fields = ('user', 'content', 'created_at')
    readonly_fields = ('created_at',)

class MomentCommentInline(admin.TabularInline):
    model = MomentComment
    extra = 0
    fields = ('user', 'content', 'created_at')
    readonly_fields = ('created_at',)
    inlines = [MomentReplyInline]

# === Sidebar filter for flags ===
class FlaggedMomentFilter(admin.SimpleListFilter):
    title = 'Flagged Status'
    parameter_name = 'flagged'

    def lookups(self, request, model_admin):
        return (
            ('flagged', 'Flagged (10+)'),
            ('not_flagged', 'Not Flagged'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'flagged':
            return queryset.filter(flag_count__gte=10)
        if self.value() == 'not_flagged':
            return queryset.filter(flag_count__lt=10)
        return queryset

# === Main Moment admin ===
@admin.register(Moment)
class MomentAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'fire_count', 'heart_count', 'flag_count', 'is_active', 'created_at')
    list_filter = ('is_active', FlaggedMomentFilter, 'created_at')
    search_fields = ('title', 'user__email', 'content')
    readonly_fields = ('created_at', 'expires_at', 'remaining_time')
    inlines = [MomentCommentInline]
    ordering = ('-created_at',)

    fieldsets = (
        (None, {
            'fields': (
                'title', 'content', 'user',
                'image', 'video', 'youtube_link',
                'interests',
            )
        }),
        ('Activity', {
            'fields': (
                'fire_count', 'heart_count', 'flag_count',
                'activity_count', 'last_active', 'is_active',
                'created_at', 'expires_at', 'remaining_time'
            )
        }),
        ('Participants', {
            'fields': ('participants', 'max_participants')
        }),
    )

# === Admin for Flagged Moments (proxy model) ===
@admin.register(FlaggedMoment)
class FlaggedMomentAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'flag_count', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'user__email', 'content')
    ordering = ('-flag_count',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(flag_count__gte=10)
