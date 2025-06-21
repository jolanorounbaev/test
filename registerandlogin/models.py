from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from phonenumber_field.modelfields import PhoneNumberField
from datetime import date
from .choices import EUROPEAN_LANGUAGES
from django.contrib.gis.db import models as geomodels
# Ensure JSONField is imported if not already, or use models.JSONField if Django >= 3.1
from django.db.models import JSONField 
from django.contrib.gis.geos import Point

# Map language codes to their respective flag emojis
LANGUAGE_TO_FLAG_MAP = {
    'en': '🇬🇧',  # English - United Kingdom Flag
    'de': '🇩🇪',  # German - Germany Flag
    'fr': '🇫🇷',  # French - France Flag
    'es': '🇪🇸',  # Spanish - Spain Flag
    'it': '🇮🇹',  # Italian - Italy Flag
    'nl': '🇳🇱',  # Dutch - Netherlands Flag
    'pl': '🇵🇱',  # Polish - Poland Flag
    'pt': '🇵🇹',  # Portuguese - Portugal Flag
    'ru': '🇷🇺',  # Russian - Russia Flag
    'tr': '🇹🇷',  # Turkish - Turkey Flag
    'ro': '🇷🇴',  # Romanian - Romania Flag
    'el': '🇬🇷',  # Greek - Greece Flag
    'sv': '🇸🇪',  # Swedish - Sweden Flag
    'cs': '🇨🇿',  # Czech - Czech Republic Flag
    'hu': '🇭🇺',  # Hungarian - Hungary Flag
    'bg': '🇧🇬',  # Bulgarian - Bulgaria Flag
    'da': '🇩🇰',  # Danish - Denmark Flag
    'fi': '🇫🇮',  # Finnish - Finland Flag
    'no': '🇳🇴',  # Norwegian - Norway Flag
    'sk': '🇸🇰',  # Slovak - Slovakia Flag
    'hr': '🇭🇷',  # Croatian - Croatia Flag
    'sr': '🇷🇸',  # Serbian - Serbia Flag
    'lt': '🇱🇹',  # Lithuanian - Lithuania Flag
    'lv': '🇱🇻',  # Latvian - Latvia Flag
    'et': '🇪🇪',  # Estonian - Estonia Flag
    # Ensure all language codes from your EUROPEAN_LANGUAGES choices are mapped here
}

# Define choices here to avoid circular import with friendsearch.forms
# These should mirror the choices in friendsearch.forms.InterestSearchForm
AGE_FILTER_CHOICES = [
    ("strict", "Closer to my age"),
    ("relaxed", "5 year difference is fine"),
]

RADIUS_CHOICES = [
    (5, "5 km (nearby)"),
    (10, "10 km (short trip)"),
    (20, "20 km (wider city)"),
    (30, "30 km (regional)"),
    (50, "50 km (max range)"),
]

def validate_age(birth_year):
    current_year = timezone.now().year
    if current_year - birth_year < 18:
        raise ValidationError("You must be at least 18 years old to register.")

class CustomUserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, first_name, last_name, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)
    location = geomodels.PointField(geography=True, null=True, blank=True)
    interests = models.JSONField(default=list, blank=True)
    interest_descriptions = models.JSONField(default=dict, blank=True)
    description = models.CharField(max_length=150, blank=True, help_text="Write a short sentence about yourself.")
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)

    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ])
    pronouns = models.CharField(
        max_length=20,
        choices=[
            ('he/him', 'He/Him'),
            ('she/her', 'She/Her'),
            ('they/them', 'They/Them'),
        ],
        blank=True,
        null=True,
    )
    phone_number = PhoneNumberField()

    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    bio = models.TextField(max_length=200, blank=True, null=True)

    # Search Preferences Fields
    preferred_search_interests = models.JSONField(default=list, null=True, blank=True)
    preferred_search_language = models.CharField(max_length=10, choices=EUROPEAN_LANGUAGES, null=True, blank=True)
    preferred_search_age_mode = models.CharField(max_length=10, choices=AGE_FILTER_CHOICES, null=True, blank=True)
    preferred_search_radius_km = models.IntegerField(choices=RADIUS_CHOICES, null=True, blank=True)

    # Visibility settings (👁️ toggles)
    show_date_of_birth = models.BooleanField(default=True)
    show_gender = models.BooleanField(default=True)
    show_pronouns = models.BooleanField(default=True)
    show_phone_number = models.BooleanField(default=False)
    show_email = models.BooleanField(default=False)
    show_main_language = models.BooleanField(default=True)
    show_sublanguage = models.BooleanField(default=True)
    show_bio = models.BooleanField(default=True)
    show_location = models.BooleanField(default=True)  # Add this line

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def clean(self):
        super().clean()
        if self.date_of_birth:
            validate_age(self.date_of_birth.year)

    def get_age(self):
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None

    main_language = models.CharField(
        max_length=5,
        choices=EUROPEAN_LANGUAGES,
        blank=True,
        null=True
    )
    sublanguage = models.CharField(
        max_length=5,
        choices=EUROPEAN_LANGUAGES,
        blank=True,
        null=True
    )
    main_language_flag = models.CharField(max_length=4, blank=True, null=True)
    sublanguage_flag = models.CharField(max_length=4, blank=True, null=True)

    @property
    def latitude(self):
        return self.location.y if self.location else None

    @property
    def longitude(self):
        return self.location.x if self.location else None

    @latitude.setter
    def latitude(self, value):
        if self.location:
            self.location = Point(self.longitude or 0, float(value))
        else:
            self.location = Point(0, float(value))

    @longitude.setter
    def longitude(self, value):
        if self.location:
            self.location = Point(float(value), self.latitude or 0)
        else:
            self.location = Point(float(value), 0)    @property
    def username(self):
        # For compatibility with code expecting a username attribute
        return self.email

    # Ban/suspension fields
    is_temporarily_banned = models.BooleanField(default=False)
    ban_until = models.DateTimeField(null=True, blank=True, help_text="When the temporary ban expires")
    ban_reason = models.CharField(max_length=100, blank=True, help_text="Reason for the ban")
    approved_reports_count = models.IntegerField(default=0, help_text="Number of approved reports against this user")

    def save(self, *args, **kwargs):
        if self.main_language:
            self.main_language_flag = LANGUAGE_TO_FLAG_MAP.get(self.main_language, '')
        else:
            self.main_language_flag = ''
        
        if self.sublanguage:
            self.sublanguage_flag = LANGUAGE_TO_FLAG_MAP.get(self.sublanguage, '')
        else:
            self.sublanguage_flag = ''
            
        super().save(*args, **kwargs)

class Report(models.Model):
    REPORT_REASONS = [
        ('toxic_behavior', 'Toxic Behavior'),
        ('spam', 'Spam'),
        ('racism_homophobia', 'Racism or Homophobia'),
        ('harassment', 'Harassment'),
        ('inappropriate_content', 'Inappropriate Content'),
        ('fake_profile', 'Fake Profile'),
        ('other', 'Other'),
    ]
    
    APPROVAL_STATUS = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('dismissed', 'Dismissed'),
    ]
    
    reporter = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='reports_made')
    reported_user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='reports_received')
    reason = models.CharField(max_length=30, choices=REPORT_REASONS)
    description = models.TextField(blank=True, null=True, help_text="Additional details (optional)")
    timestamp = models.DateTimeField(default=timezone.now)
    is_reviewed = models.BooleanField(default=False)
    approval_status = models.CharField(max_length=10, choices=APPROVAL_STATUS, default='pending')
    admin_notes = models.TextField(blank=True, null=True, help_text="Admin notes about this report")
    
    class Meta:
        unique_together = ('reporter', 'reported_user', 'reason')  # Prevent duplicate reports for same reason
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.reporter.username} reported {self.reported_user.username} for {self.get_reason_display()}"
    
    @staticmethod
    def get_reported_users_with_threshold(threshold=5):
        """Get users who have been reported at least 'threshold' times"""
        from django.db.models import Count
        return CustomUser.objects.annotate(
            report_count=Count('reports_received')
        ).filter(report_count__gte=threshold).order_by('-report_count')
    
    def save(self, *args, **kwargs):
        """Override save to handle auto-banning logic"""
        old_approval_status = None
        if self.pk:  # If updating existing report
            old_report = Report.objects.get(pk=self.pk)
            old_approval_status = old_report.approval_status
        
        super().save(*args, **kwargs)
        
        # If report was just approved, update user's approved report count
        if old_approval_status != 'approved' and self.approval_status == 'approved':
            user = self.reported_user
            user.approved_reports_count += 1
            
            # Check if user should be temporarily banned (5+ approved reports)
            if user.approved_reports_count >= 5 and not user.is_temporarily_banned:
                from datetime import timedelta
                user.is_temporarily_banned = True
                user.ban_until = timezone.now() + timedelta(days=7)  # 7-day ban
                user.ban_reason = f"Automatically banned due to {user.approved_reports_count} approved reports"
                
            user.save()
        
        # If report was unapproved (dismissed), decrease count
        elif old_approval_status == 'approved' and self.approval_status != 'approved':
            user = self.reported_user
            user.approved_reports_count = max(0, user.approved_reports_count - 1)
            user.save()
