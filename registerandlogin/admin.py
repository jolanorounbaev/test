from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django import forms
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.contrib.gis.geos import Point
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.admin.helpers import ActionForm
from django.urls import path
from .models import CustomUser, Report

# --------------------------
# Custom User Form with Lat/Lng support
# --------------------------
class CustomUserForm(forms.ModelForm):
    latitude = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Enter latitude', 'style': 'width: 150px;'})
    )
    longitude = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Enter longitude', 'style': 'width: 150px;'})
    )

    class Meta:
        model = CustomUser
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.location:
            # Use period as decimal separator for display
            self.fields['latitude'].initial = str(self.instance.location.y)
            self.fields['longitude'].initial = str(self.instance.location.x)

        self.fields['latitude'].help_text = mark_safe(
            '<button type="button" onclick="document.getElementById(\'id_latitude\').value = \"\"">Clear</button>'
        )
        self.fields['longitude'].help_text = mark_safe(
            '<button type="button" onclick="document.getElementById(\'id_longitude\').value = \"\"">Clear</button>'
        )

    def clean(self):
        cleaned_data = super().clean()
        lat = cleaned_data.get('latitude')
        lon = cleaned_data.get('longitude')

        if isinstance(lat, str):
            lat = lat.replace(",", ".").strip()
        if isinstance(lon, str):
            lon = lon.replace(",", ".").strip()

        if lat in [None, "", " "] or lon in [None, "", " "]:
            cleaned_data['location'] = None
            return cleaned_data

        try:
            lat = float(lat)
            lon = float(lon)
            cleaned_data['location'] = Point(lon, lat)
        except (TypeError, ValueError):
            cleaned_data['location'] = None

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.location = self.cleaned_data.get('location')
        if commit:
            instance.save()
        return instance


# --------------------------
# CustomUser Admin Panel
# --------------------------
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    form = CustomUserForm

    list_display = ('id', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'display_interests', 'ban_status_display', 'approved_reports_count')
    list_filter = ('is_active', 'is_staff', 'is_temporarily_banned', 'main_language', 'gender', 'preferred_search_language')
    readonly_fields = ('id', 'interests_with_clear', 'interest_descriptions', 'preferred_search_interests')
    actions = ['clear_interests_action']

    fieldsets = (
        (None, {'fields': ('id', 'email', 'password')}),
        ('Personal Info', {
            'fields': (
                'first_name', 'last_name', 'date_of_birth', 'gender', 'pronouns',
                'phone_number', 'bio', 'latitude', 'longitude', 'profile_picture',
            )
        }),
        ('Interests & Description', {
            'fields': ('interests_with_clear', 'interest_descriptions', 'description'),
            'description': 'Interest fields are read-only - managed through the wordlist system. Users can only select from predefined interests. Use the "Clear Interests" button or bulk action to reset interests during testing.'
        }),
        ('Search Preferences', {
            'fields': ('preferred_search_interests', 'preferred_search_language', 'preferred_search_age_mode', 'preferred_search_radius_km'),
            'description': 'Search preferences are read-only - managed through the friend search interface.'
        }),
        ('Language Settings', {'fields': ('main_language', 'sublanguage')}),        ('Visibility Toggles', {
            'fields': (
                'show_date_of_birth', 'show_gender', 'show_pronouns',
                'show_phone_number', 'show_email', 'show_main_language',
                'show_sublanguage', 'show_bio',
            )
        }),
        ('Ban/Suspension Status', {
            'fields': ('is_temporarily_banned', 'ban_until', 'ban_reason', 'approved_reports_count'),
            'description': 'User ban and report status. Users are automatically banned for 7 days when they receive 5 approved reports.'
        }),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )

    search_fields = ('id', 'email', 'first_name', 'last_name', 'description')
    ordering = ('id',)

    def display_interests(self, obj):
        """Display user's interests in a readable format"""
        if obj.interests:
            return ', '.join(obj.interests)
        return 'No interests set'
    display_interests.short_description = _('Current Interests')

    def display_interest_descriptions(self, obj):
        """Display user's interest descriptions in a readable format"""
        if obj.interest_descriptions:
            descriptions = []
            for interest, description in obj.interest_descriptions.items():
                descriptions.append(f"{interest}: {description}")
            return ' | '.join(descriptions)
        return 'No descriptions set'
    display_interest_descriptions.short_description = _('Interest Descriptions')

    def display_search_interests(self, obj):
        """Display user's preferred search interests"""
        if obj.preferred_search_interests:
            return ', '.join(obj.preferred_search_interests)
        return 'No search preferences set'
    display_search_interests.short_description = _('Search Interests')

    def display_latitude(self, obj):
        if obj.location:
            return obj.location.y
        return None
    display_latitude.short_description = _('Latitude')

    def display_longitude(self, obj):
        if obj.location:
            return obj.location.x
        return None
    display_longitude.short_description = _('Longitude')

    def interests_with_clear(self, obj):
        """Display interests with a clear button for testing"""
        if not obj or not obj.pk:
            return 'No interests (new user)'
        
        interests_display = ', '.join(obj.interests) if obj.interests else 'No interests set'
        clear_button = f'''
        <div style="margin-top: 10px;">
            <span style="font-weight: bold;">Current Interests:</span> {interests_display}<br>
            <button type="button" onclick="
                if(confirm('Are you sure you want to clear all interests for this user? This is for testing purposes only.')) {{
                    fetch('/admin/registerandlogin/customuser/{obj.pk}/clear-interests/', {{
                        method: 'POST',
                        headers: {{
                            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                            'Content-Type': 'application/json'
                        }}
                    }}).then(response => response.json()).then(data => {{
                        if(data.status === 'success') {{
                            alert('Interests cleared successfully!');
                            location.reload();
                        }} else {{
                            alert('Error: ' + data.message);
                        }}
                    }}).catch(error => {{
                        alert('Error clearing interests: ' + error);
                    }});
                }}
            " style="background: #dc3545; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin-top: 5px;">
                🗑️ Clear All Interests (Testing)
            </button>
        </div>
        '''
        return mark_safe(clear_button)
    interests_with_clear.short_description = _('Interests (with clear option)')

    def clear_interests_action(self, request, queryset):
        """Admin action to clear interests for selected users"""
        count = queryset.count()
        for user in queryset:
            user.interests = []
            user.interest_descriptions = {}
            user.save(update_fields=['interests', 'interest_descriptions'])
        
        self.message_user(request, f'Successfully cleared interests for {count} user(s).')
    
    clear_interests_action.short_description = "Clear interests for selected users (Testing)"

    def ban_status_display(self, obj):
        """Display user's ban status"""
        if obj.is_temporarily_banned:
            return format_html(
                '<span style="color: red; font-weight: bold;">BANNED</span><br>'
                '<small>Until: {}</small><br>'
                '<small>Reason: {}</small>',
                obj.ban_until.strftime('%Y-%m-%d %H:%M') if obj.ban_until else 'Permanent',
                obj.ban_reason or 'No reason specified'
            )
        elif obj.approved_reports_count >= 3:
            return format_html(
                '<span style="color: orange; font-weight: bold;">⚠️ WARNING</span><br>'
                '<small>{}/5 reports</small>',
                obj.approved_reports_count
            )
        else:
            return format_html(
                '<span style="color: green;">✅ Good standing</span><br>'
                '<small>{}/5 reports</small>',
                obj.approved_reports_count
            )
    ban_status_display.short_description = 'Ban Status'

    def get_fieldsets(self, request, obj=None):
        if obj:
            return super().get_fieldsets(request, obj)
        else:
            return self.add_fieldsets

    # def has_delete_permission(self, request, obj=None):
    #     return False  # Commented out to allow user deletion    def get_urls(self):
        """Add custom URLs for admin actions"""
        urls = super().get_urls()
        custom_urls = [
            path('<int:user_id>/clear-interests/', self.clear_user_interests_view, name='admin_clear_user_interests'),
            path('<int:user_id>/unban/', self.unban_user_view, name='admin_unban_user'),
        ]
        return custom_urls + urls

    def clear_user_interests_view(self, request, user_id):
        """View to clear interests for a specific user"""
        if request.method == 'POST':
            try:
                user = CustomUser.objects.get(pk=user_id)
                user.interests = []
                user.interest_descriptions = {}
                user.save(update_fields=['interests', 'interest_descriptions'])
                return JsonResponse({'status': 'success', 'message': 'Interests cleared successfully'})
            except CustomUser.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'User not found'}, status=404)
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
        
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

    def unban_user_view(self, request, user_id):
        """View to unban a specific user"""
        if request.method == 'POST':
            try:
                user = CustomUser.objects.get(pk=user_id)
                user.is_temporarily_banned = False
                user.ban_until = None
                user.ban_reason = None
                user.save(update_fields=['is_temporarily_banned', 'ban_until', 'ban_reason'])
                return JsonResponse({'status': 'success', 'message': 'User unbanned successfully'})
            except CustomUser.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'User not found'}, status=404)
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
        
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


# --------------------------
# Enhanced Report Admin
# --------------------------
@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        'report_id_display', 'reporter_full_display', 'reported_user_full_display', 
        'reason_with_icon', 'description_preview', 'review_status_display', 
        'approval_status_display', 'timestamp_display', 'quick_actions'
    )
    list_display_links = ('report_id_display', 'reason_with_icon')  # Make these clickable
    list_filter = (
        'reason', 'approval_status', 'is_reviewed', 'timestamp',
        ('timestamp', admin.DateFieldListFilter),
        ('reported_user__is_temporarily_banned', admin.BooleanFieldListFilter),
    )
    search_fields = (
        'id', 'description', 'admin_notes',
        'reporter__first_name', 'reporter__last_name', 'reporter__email',
        'reported_user__first_name', 'reported_user__last_name', 'reported_user__email'
    )
    readonly_fields = ('timestamp', 'report_summary_display')
    ordering = ('-timestamp',)
    list_per_page = 50
    actions = ['mark_as_reviewed', 'approve_reports', 'dismiss_reports']
    
    fieldsets = (
        ('Report Overview', {
            'fields': ('report_summary_display',),
            'description': 'Summary of this report with key information and quick links.'
        }),
        ('Report Details', {
            'fields': ('reporter', 'reported_user', 'reason', 'description', 'timestamp'),
            'description': 'Core information about the report. Reporter and reported user cannot be changed after creation.'
        }),
        ('Admin Review', {
            'fields': ('is_reviewed', 'approval_status', 'admin_notes'),
            'description': 'Admin decision and notes. Marking as approved/dismissed automatically sets reviewed=True.'
        }),
    )

    def report_id_display(self, obj):
        """Display report ID with priority indicator"""
        priority_icon = ""
        if not obj.is_reviewed:
            priority_icon = "🔴 "
        elif obj.approval_status == 'pending':
            priority_icon = "🟡 "
        else:
            priority_icon = "🟢 "
        
        return format_html(
            '{}<strong>#{}</strong>',
            priority_icon,
            obj.id
        )
    report_id_display.short_description = 'ID'
    report_id_display.admin_order_field = 'id'

    def reporter_full_display(self, obj):
        """Enhanced reporter display with profile link and user info"""
        full_name = f"{obj.reporter.first_name} {obj.reporter.last_name}".strip()
        if not full_name:
            full_name = f"User {obj.reporter.id}"
        
        # Get reporter's report count
        reporter_reports = Report.objects.filter(reporter=obj.reporter).count()
        
        return format_html(
            '<div style="line-height: 1.3;">'
            '<strong><a href="/profile/{}" target="_blank" title="View Profile">{}</a></strong><br>'
            '<small style="color: #666;">{}</small><br>'
            '<small style="color: #007cba;">Reports made: {}</small><br>'
            '<a href="/admin/registerandlogin/customuser/{}/change/" style="font-size: 11px;">Edit User</a>'
            '</div>',
            obj.reporter.id,
            full_name,
            obj.reporter.email,
            reporter_reports,
            obj.reporter.id
        )
    reporter_full_display.short_description = 'Reporter'
    reporter_full_display.admin_order_field = 'reporter__first_name'

    def reported_user_full_display(self, obj):
        """Enhanced reported user display with ban status and report count"""
        full_name = f"{obj.reported_user.first_name} {obj.reported_user.last_name}".strip()
        if not full_name:
            full_name = f"User {obj.reported_user.id}"
        
        # Ban status styling
        ban_status_html = ""
        if obj.reported_user.is_temporarily_banned:
            ban_until = obj.reported_user.ban_until.strftime('%m/%d %H:%M') if obj.reported_user.ban_until else 'Permanent'
            ban_status_html = f'<div style="color: #dc3545; font-weight: bold; font-size: 11px;">BANNED until {ban_until}</div>'
        elif obj.reported_user.approved_reports_count >= 3:
            ban_status_html = f'<div style="color: #fd7e14; font-weight: bold; font-size: 11px;">HIGH RISK ({obj.reported_user.approved_reports_count}/5)</div>'
        
        return format_html(
            '<div style="line-height: 1.3;">'
            '<strong><a href="/profile/{}" target="_blank" title="View Profile">{}</a></strong><br>'
            '<small style="color: #666;">{}</small><br>'
            '<small style="color: #dc3545;">Reports: {} total, {} approved</small><br>'
            '{}'
            '<a href="/admin/registerandlogin/customuser/{}/change/" style="font-size: 11px;">Edit User</a>'
            '</div>',
            obj.reported_user.id,
            full_name,
            obj.reported_user.email,
            Report.objects.filter(reported_user=obj.reported_user).count(),
            obj.reported_user.approved_reports_count,
            ban_status_html,
            obj.reported_user.id
        )
    reported_user_full_display.short_description = 'Reported User'
    reported_user_full_display.admin_order_field = 'reported_user__first_name'

    def reason_with_icon(self, obj):
        """Display reason with appropriate icon"""        reason_icons = {
            'spam': 'SPAM',
            'harassment': 'HARASSMENT',
            'inappropriate_content': 'INAPPROPRIATE',
            'fake_profile': 'FAKE',
            'scam': 'SCAM',
            'violence': 'VIOLENCE',
            'racism_or_homophobia': 'HATE',
            'other': 'OTHER'
        }
        
        icon = reason_icons.get(obj.reason.lower(), 'OTHER')
        reason_display = obj.get_reason_display() if hasattr(obj, 'get_reason_display') else obj.reason
        
        return format_html(
            '<span title="{}">{} {}</span>',
            reason_display,
            icon,
            reason_display
        )
    reason_with_icon.short_description = 'Reason'
    reason_with_icon.admin_order_field = 'reason'

    def description_preview(self, obj):
        """Show truncated description with full text on hover"""
        if not obj.description:
            return format_html('<em style="color: #999;">No description</em>')
        
        truncated = obj.description[:100]
        if len(obj.description) > 100:
            truncated += "..."
        
        return format_html(
            '<span title="{}" style="cursor: help;">{}</span>',
            obj.description,
            truncated
        )
    description_preview.short_description = 'Description'

    def review_status_display(self, obj):
        """Display review status with clear visual indicators"""
        if obj.is_reviewed:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">✅ Reviewed</span>'
            )
        else:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">❌ Needs Review</span>'
            )
    review_status_display.short_description = 'Reviewed'
    review_status_display.admin_order_field = 'is_reviewed'

    def approval_status_display(self, obj):
        """Display approval status with color coding"""
        status_styles = {
            'pending': ('🟡', '#fd7e14', 'Pending'),
            'approved': ('✅', '#28a745', 'Approved'),
            'dismissed': ('❌', '#6c757d', 'Dismissed'),
        }
        
        icon, color, text = status_styles.get(obj.approval_status, ('❓', '#666', obj.approval_status))
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color,
            icon,
            text
        )
    approval_status_display.short_description = 'Status'
    approval_status_display.admin_order_field = 'approval_status'

    def timestamp_display(self, obj):
        """Display formatted timestamp with relative time"""
        from django.utils import timezone
        import datetime
        
        now = timezone.now()
        diff = now - obj.timestamp
        
        if diff.days > 0:
            relative = f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            relative = f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            minutes = diff.seconds // 60
            relative = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        
        return format_html(
            '<div style="line-height: 1.3;">'
            '<strong>{}</strong><br>'
            '<small style="color: #666;">{}</small>'
            '</div>',
            obj.timestamp.strftime('%m/%d/%Y %H:%M'),
            relative
        )
    timestamp_display.short_description = 'Date/Time'
    timestamp_display.admin_order_field = 'timestamp'

    def quick_actions(self, obj):
        """Display quick action buttons"""
        actions_html = []
        
        if not obj.is_reviewed:
            actions_html.append(
                '<button onclick="quickReview({}, \'approved\')" '
                'style="background: #28a745; color: white; border: none; padding: 2px 6px; '
                'border-radius: 3px; cursor: pointer; font-size: 10px; margin: 1px;">✅ Approve</button>'
            )
            actions_html.append(
                '<button onclick="quickReview({}, \'dismissed\')" '
                'style="background: #6c757d; color: white; border: none; padding: 2px 6px; '
                'border-radius: 3px; cursor: pointer; font-size: 10px; margin: 1px;">❌ Dismiss</button>'
            )
        
        actions_html.append(
            '<a href="/admin/registerandlogin/report/?reported_user__id__exact={}" '
            'style="background: #007cba; color: white; padding: 2px 6px; text-decoration: none; '
            'border-radius: 3px; font-size: 10px; margin: 1px; display: inline-block;">📋 All Reports</a>'
        )
        
        return format_html(
            '<div style="white-space: nowrap;">{}</div>',
            ''.join(actions_html).format(obj.id, obj.id, obj.reported_user.id)
        )
    quick_actions.short_description = 'Actions'

    def report_summary_display(self, obj):
        """Comprehensive report summary for detail view"""
        if not obj.pk:
            return "Report summary will appear here after saving."
        
        # Get related reports for this user
        related_reports = Report.objects.filter(reported_user=obj.reported_user).exclude(id=obj.id)
        
        summary_html = f'''
        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #dee2e6;">
            <h3 style="margin-top: 0; color: #495057;">📋 Report Summary</h3>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 15px;">
                <div>
                    <h4 style="color: #007cba; margin-bottom: 10px;">👤 Reporter Info</h4>
                    <p><strong>Name:</strong> {obj.reporter.first_name} {obj.reporter.last_name}</p>
                    <p><strong>Email:</strong> {obj.reporter.email}</p>
                    <p><strong>Total Reports Made:</strong> {Report.objects.filter(reporter=obj.reporter).count()}</p>
                    <a href="/profile/{obj.reporter.id}/" target="_blank" style="color: #007cba;">👀 View Profile</a>
                </div>
                
                <div>                    <h4 style="color: #dc3545; margin-bottom: 10px;">Reported User Info</h4>
                    <p><strong>Name:</strong> {obj.reported_user.first_name} {obj.reported_user.last_name}</p>
                    <p><strong>Email:</strong> {obj.reported_user.email}</p>
                    <p><strong>Total Reports Against:</strong> {Report.objects.filter(reported_user=obj.reported_user).count()}</p>
                    <p><strong>Approved Reports:</strong> {obj.reported_user.approved_reports_count}/5</p>
                    <p><strong>Ban Status:</strong> {"BANNED" if obj.reported_user.is_temporarily_banned else "Active"}</p>
                    <a href="/profile/{obj.reported_user.id}/" target="_blank" style="color: #007cba;">View Profile</a>
                </div>
            </div>
            
            <div style="margin-bottom: 15px;">
                <h4 style="color: #fd7e14; margin-bottom: 10px;">📄 This Report</h4>
                <p><strong>Reason:</strong> {obj.get_reason_display() if hasattr(obj, 'get_reason_display') else obj.reason}</p>
                <p><strong>Description:</strong> {obj.description or 'No description provided'}</p>
                <p><strong>Submitted:</strong> {obj.timestamp.strftime('%B %d, %Y at %I:%M %p')}</p>
            </div>
            
            <div>
                <h4 style="color: #6f42c1; margin-bottom: 10px;">📊 Related Reports</h4>
                <p><strong>Other reports against this user:</strong> {related_reports.count()}</p>
                {f'<a href="/admin/registerandlogin/report/?reported_user__id__exact={obj.reported_user.id}" style="color: #007cba;">📋 View All Reports</a>' if related_reports.exists() else '<em>No other reports found</em>'}
            </div>
        </div>
        '''
        
        return format_html(summary_html)
    report_summary_display.short_description = 'Report Summary'

    # Admin Actions
    def mark_as_reviewed(self, request, queryset):
        """Mark selected reports as reviewed"""
        count = queryset.update(is_reviewed=True)
        self.message_user(request, f'{count} report(s) marked as reviewed.')
    mark_as_reviewed.short_description = "✅ Mark selected reports as reviewed"

    def approve_reports(self, request, queryset):
        """Approve selected reports"""
        count = queryset.update(approval_status='approved', is_reviewed=True)
        self.message_user(request, f'{count} report(s) approved.')
    approve_reports.short_description = "✅ Approve selected reports"

    def dismiss_reports(self, request, queryset):
        """Dismiss selected reports"""
        count = queryset.update(approval_status='dismissed', is_reviewed=True)
        self.message_user(request, f'{count} report(s) dismissed.')
    dismiss_reports.short_description = "❌ Dismiss selected reports"

    def save_model(self, request, obj, form, change):
        """Override to handle auto-marking as reviewed when approval status is set"""
        if obj.approval_status in ['approved', 'dismissed']:
            obj.is_reviewed = True
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('reporter', 'reported_user')

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('reporter', 'reported_user', 'reason')
        return self.readonly_fields

    class Media:
        js = ('admin/js/report_admin.js',)
        css = {
            'all': ('admin/css/report_admin.css',)
        }

# --------------------------
# Reported Users View (Custom Admin View)
# --------------------------
class ReportedUsersAdmin(admin.ModelAdmin):
    """Custom admin view to show users with multiple reports"""
    change_list_template = 'admin/reported_users_changelist.html'
    
    def changelist_view(self, request, extra_context=None):
        # Get users with 5+ reports
        reported_users = Report.get_reported_users_with_threshold(5)
        
        # Create summary data
        user_data = []
        for user in reported_users:
            reports = Report.objects.filter(reported_user=user).order_by('-timestamp')
            user_data.append({
                'user': user,
                'report_count': reports.count(),
                'recent_reports': reports[:3],  # Show 3 most recent
                'unreviewed_count': reports.filter(is_reviewed=False).count()
            })
        
        extra_context = extra_context or {}
        extra_context['reported_users'] = user_data
        extra_context['title'] = 'Reported Users (5+ Reports)'
        
        return super().changelist_view(request, extra_context=extra_context)
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


# --------------------------
# Banned Users View (Custom Admin View)
# --------------------------
class BannedUsersAdmin(admin.ModelAdmin):
    """Custom admin view to show currently banned users"""
    change_list_template = 'admin/banned_users_changelist.html'
    
    def changelist_view(self, request, extra_context=None):
        from django.utils import timezone
        
        # Get currently banned users
        banned_users = CustomUser.objects.filter(
            is_temporarily_banned=True
        ).order_by('-ban_until')
        
        # Separate permanent and temporary bans
        permanent_bans = banned_users.filter(ban_until__isnull=True)
        temporary_bans = banned_users.filter(ban_until__isnull=False)
        
        # Check for expired bans that should be lifted
        now = timezone.now()
        expired_bans = temporary_bans.filter(ban_until__lt=now)
        active_temporary_bans = temporary_bans.filter(ban_until__gte=now)
        
        # Auto-lift expired bans
        if expired_bans.exists():
            expired_count = expired_bans.count()
            expired_bans.update(
                is_temporarily_banned=False,
                ban_until=None,
                ban_reason=None
            )
            self.message_user(request, f'Automatically lifted {expired_count} expired ban(s).')
        
        # Create summary data
        banned_data = []
        
        # Add permanent bans
        for user in permanent_bans:
            banned_data.append({
                'user': user,
                'ban_type': 'Permanent',
                'ban_until': None,
                'ban_reason': user.ban_reason or 'No reason specified',
                'approved_reports_count': user.approved_reports_count,
                'days_remaining': None,
                'is_expired': False
            })
        
        # Add active temporary bans
        for user in active_temporary_bans:
            days_remaining = (user.ban_until - now).days if user.ban_until else 0
            banned_data.append({
                'user': user,
                'ban_type': 'Temporary',
                'ban_until': user.ban_until,
                'ban_reason': user.ban_reason or 'No reason specified',
                'approved_reports_count': user.approved_reports_count,
                'days_remaining': days_remaining,
                'is_expired': False
            })
        
        extra_context = extra_context or {}
        extra_context['banned_users'] = banned_data
        extra_context['total_banned'] = len(banned_data)
        extra_context['permanent_count'] = permanent_bans.count()
        extra_context['temporary_count'] = active_temporary_bans.count()
        extra_context['title'] = 'Currently Banned Users'
        
        return super().changelist_view(request, extra_context=extra_context)
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


# --------------------------
# Proxy Models for Custom Admin Views
# --------------------------
class ReportedUserProxy(CustomUser):
    class Meta:
        proxy = True
        verbose_name = 'Reported User'
        verbose_name_plural = 'Reported Users (5+ Reports)'

class BannedUserProxy(CustomUser):
    class Meta:
        proxy = True
        verbose_name = 'Banned User'
        verbose_name_plural = 'Banned Users'

# Register the custom admin views
admin.site.register(ReportedUserProxy, ReportedUsersAdmin)
admin.site.register(BannedUserProxy, BannedUsersAdmin)
