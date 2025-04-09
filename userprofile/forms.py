from django import forms
from registerandlogin.models import CustomUser
from .models import ContentItem

class EditProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            'email', 'phone_number', 'pronouns',
            'profile_picture', 'main_language', 'sublanguage',
            'show_email', 'show_date_of_birth', 'show_pronouns',
            'show_phone_number', 'show_main_language', 'show_sublanguage',
            'bio', 'show_bio'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        gender = self.instance.gender

        if gender in ['male', 'female']:
            self.fields['gender_display'] = forms.CharField(
                label="Gender",
                initial=gender.capitalize(),
                disabled=True,
                required=False
            )
            self.show_pronouns_field = False  # Hide pronouns for male/female
        else:
            self.show_pronouns_field = True  # Show pronouns only for 'other'
            # Add pronouns back into form fields
            self.fields['pronouns'] = forms.ChoiceField(
                choices=[
                    ('he/him', 'He/Him'),
                    ('she/her', 'She/Her'),
                    ('they/them', 'They/Them'),
                ],
                required=False
            )
            
        if self.instance.date_of_birth:
            self.fields['age_display'] = forms.CharField(
                label="Age",
                initial=self.instance.get_age(),
                disabled=True,
                required=False
            )

class ContentItemForm(forms.ModelForm):
    class Meta:
        model = ContentItem
        fields = ['title', 'description', 'image', 'youtube_url']
