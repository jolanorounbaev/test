from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django import forms
from django.utils.safestring import mark_safe
from django.contrib.gis.geos import Point
from .models import CustomUser
from django.utils.translation import gettext_lazy as _


class CustomUserForm(forms.ModelForm):
    latitude = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter latitude',
            'style': 'width: 150px;',
        })
    )
    longitude = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter longitude',
            'style': 'width: 150px;',
        })
    )

    class Meta:
        model = CustomUser
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.location:
            self.fields['latitude'].initial = str(self.instance.location.y).replace('.', ',')
            self.fields['longitude'].initial = str(self.instance.location.x).replace('.', ',')

        self.fields['latitude'].help_text = mark_safe(
            '<button type="button" onclick="document.getElementById(\'id_latitude\').value = \'\'">Clear</button>'
        )
        self.fields['longitude'].help_text = mark_safe(
            '<button type="button" onclick="document.getElementById(\'id_longitude\').value = \'\'">Clear</button>'
        )

    def clean(self):
        cleaned_data = super().clean()
        lat = cleaned_data.get('latitude')
        lon = cleaned_data.get('longitude')

        # Convert comma to dot
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
        instance.location = self.cleaned_data.get('location')  # 🔥 important
        if commit:
            instance.save()
        return instance





@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    form = CustomUserForm

    list_display = ('id', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'location')
    list_filter = ('is_active', 'is_staff', 'main_language')
    readonly_fields = ('id',)  # ✅ Make ID read-only

    fieldsets = (
        (None, {'fields': ('id', 'email', 'password')}),  # ✅ Include ID here
        ('Personal Info', {
            'fields': (
                'first_name',
                'last_name',
                'date_of_birth',
                'gender',
                'pronouns',
                'phone_number',
                'bio',
                'latitude', 'longitude',
            )
        }),
        ('Language Settings', {'fields': ('main_language', 'sublanguage')}),
        ('Visibility Toggles', {
            'fields': (
                'show_date_of_birth', 'show_gender', 'show_pronouns',
                'show_phone_number', 'show_email', 'show_main_language',
                'show_sublanguage', 'show_bio',
            )
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

    search_fields = ('id', 'email', 'first_name', 'last_name')  # ✅ Optional: searchable by ID
    ordering = ('id',)
