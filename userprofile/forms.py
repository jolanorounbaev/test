from django import forms
from registerandlogin.models import CustomUser
from .models import ContentItem, VisitedPlace, Achievement, Quote
from friendsearch.wordlist import WORDLIST # Use friendsearch wordlist for consistency

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

class InterestUpdateForm(forms.Form):
    """
    Exact copy of friendsearch InterestUpdateForm for consistency
    """
    interest_1 = forms.CharField(
        max_length=50, 
        required=False,
        widget=forms.TextInput(attrs={'autocomplete': 'off'})
    )
    interest_2 = forms.CharField(
        max_length=50, 
        required=False,
        widget=forms.TextInput(attrs={'autocomplete': 'off'})
    )
    interest_3 = forms.CharField(
        max_length=50, 
        required=False,
        widget=forms.TextInput(attrs={'autocomplete': 'off'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.valid_words = {word.lower(): word for word in WORDLIST}

    def clean_interest_field(self, field_name):
        value = self.cleaned_data.get(field_name, '').strip()
        if value and value.lower() not in self.valid_words:
            raise forms.ValidationError(
                f"'{value}' is not a valid interest. Please select from the list."
            )
        return self.valid_words.get(value.lower(), value)

    def clean_interest_1(self):
        return self.clean_interest_field('interest_1')

    def clean_interest_2(self):
        return self.clean_interest_field('interest_2')

    def clean_interest_3(self):
        return self.clean_interest_field('interest_3')

    def clean(self):
        cleaned_data = super().clean()
        interests = [
            cleaned_data.get(f"interest_{i}") 
            for i in range(1, 4)
            if cleaned_data.get(f"interest_{i}")
        ]

        if len(interests) < 1:
            raise forms.ValidationError("Please select at least one interest")

        # Check for duplicate interests
        if len(interests) != len(set(interests)):
            raise forms.ValidationError("You cannot select the same interest multiple times. Please choose different interests.")

        cleaned_data["interests"] = interests
        return cleaned_data

class VisitedPlaceForm(forms.ModelForm):
    class Meta:
        model = VisitedPlace
        fields = ['name', 'image']

class AchievementForm(forms.ModelForm):
    class Meta:
        model = Achievement
        fields = ['title', 'icon']

class QuoteForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = ['text']
