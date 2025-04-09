from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from phonenumber_field.modelfields import PhoneNumberField
from datetime import date
from .choices import EUROPEAN_LANGUAGES
from django.contrib.gis.db import models as geomodels
from django.db.models import JSONField
from django.contrib.gis.geos import Point

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


    # Visibility settings (👁️ toggles)
    show_date_of_birth = models.BooleanField(default=True)
    show_gender = models.BooleanField(default=True)
    show_pronouns = models.BooleanField(default=True)
    show_phone_number = models.BooleanField(default=False)
    show_email = models.BooleanField(default=False)
    show_main_language = models.BooleanField(default=True)
    show_sublanguage = models.BooleanField(default=True)
    show_bio = models.BooleanField(default=True)

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
            self.location = Point(float(value), 0)
