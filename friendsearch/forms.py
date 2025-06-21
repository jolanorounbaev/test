from django import forms
from .wordlist import WORDLIST
from registerandlogin.models import EUROPEAN_LANGUAGES, CustomUser

class InterestUpdateForm(forms.Form):
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


class InterestSearchForm(forms.Form):
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

    description_1 = forms.CharField(max_length=300, required=False)
    description_2 = forms.CharField(max_length=300, required=False)
    description_3 = forms.CharField(max_length=300, required=False)
    
    main_language = forms.ChoiceField(
    choices=EUROPEAN_LANGUAGES,  # ('en', 'English') etc.
    required=False,
    widget=forms.Select(attrs={'class': 'form-select'})
)

    RADIUS_CHOICES = [
    (5, "5 km (nearby)"),
    (10, "10 km (short trip)"),
    (20, "20 km (wider city)"),
    (30, "30 km (regional)"),
    (50, "50 km (max range)"),
]
    radius_km = forms.ChoiceField(
    choices=RADIUS_CHOICES,
    required=False,
    initial=10  # Default to 10 km
)
    AGE_FILTER_CHOICES = [
        ("strict", "Closer to my age"),
        ("relaxed", "5 year difference is fine"),
    ]
    age_filtering_mode = forms.ChoiceField(
        choices=AGE_FILTER_CHOICES,
        required=False,
        widget=forms.RadioSelect
    )

    def clean(self):
        cleaned_data = super().clean()
        interests = [
            cleaned_data.get("interest_1"),
            cleaned_data.get("interest_2"),
            cleaned_data.get("interest_3"),
        ]
        cleaned_data["interests"] = [i.strip() for i in interests if i and i.strip()]
        print(f"🔍 [DEBUG] InterestSearchForm.clean() - interests: {cleaned_data['interests']}")
        return cleaned_data


class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['description']  # add this if you're using ModelForm
        widgets = {
            'description': forms.TextInput(attrs={
                'placeholder': 'E.g. Always down to jam 🎸',
                'class': 'form-control',
            }),
        }
