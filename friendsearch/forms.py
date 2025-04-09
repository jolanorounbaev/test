from django import forms

class InterestUpdateForm(forms.Form):
    interest_1 = forms.CharField(max_length=50, required=False)
    interest_2 = forms.CharField(max_length=50, required=False)
    interest_3 = forms.CharField(max_length=50, required=False)

    def clean(self):
        cleaned_data = super().clean()
        interests = [cleaned_data.get(f"interest_{i}") for i in range(1, 4)]
        interests = [i.strip() for i in interests if i and i.strip()]
        cleaned_data["interests"] = interests
        return cleaned_data
