from django import forms
from .models import CustomUser
from django.core.exceptions import ValidationError
import datetime
from django.forms.widgets import SelectDateWidget
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox
from phonenumber_field.formfields import PhoneNumberField as PhoneNumberFormField

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)

    # Everything included with phone_number
    phone_number = PhoneNumberFormField(
        widget=forms.TextInput(attrs={
            'placeholder': '+32 470 12 34 56'
        })
    )

    # Date of birth as dropdowns (day/month/year)
    date_of_birth = forms.DateField(
        widget=SelectDateWidget(years=range(datetime.datetime.now().year, 1900, -1)),
        label="Date of Birth"
    )

    # Pronouns dropdown (no custom option)
    pronouns = forms.ChoiceField(
        choices=[
            ('', '---------'),
            ('he/him', 'He/Him'),
            ('she/her', 'She/Her'),
            ('they/them', 'They/Them'),
        ],
        required=False,
        label="Preferred Pronouns"
    )

    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'email', 'date_of_birth',
            'gender', 'pronouns', 'phone_number', 'password'
        ]

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            today = datetime.date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 18:
                raise ValidationError("You must be at least 18 years old to register.")
        return dob

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm_password")
        gender = cleaned_data.get("gender")
        pronouns = cleaned_data.get("pronouns")

        if password and confirm and password != confirm:
            raise ValidationError("Passwords do not match.")

        if gender == 'other' and not pronouns:
            raise ValidationError("Please select your preferred pronouns.")

def save(self, commit=True):
    user = super().save(commit=False)
    user.set_password(self.cleaned_data["password"])

    # Set smart default visibility options
    user.show_email = True
    user.show_date_of_birth = True
    user.show_gender = True
    user.show_pronouns = True
    user.show_phone_number = False
    user.show_main_language = True
    user.show_sublanguage = True

    if commit:
        user.save()
    return user


class LoginForm(forms.Form):
    identifier = forms.CharField(label="Email or Phone Number")
    password = forms.CharField(widget=forms.PasswordInput)
