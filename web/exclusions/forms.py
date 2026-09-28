from django import forms

from .models import DataSource


class ProviderSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        label="Search",
        widget=forms.TextInput(attrs={"placeholder": "Name, business name, NPI, or UPIN"}),
    )
    party_type = forms.ChoiceField(
        required=False,
        choices=[("", "All types"), ("INDIVIDUAL", "Individual"), ("ENTITY", "Entity")],
    )
    state = forms.CharField(required=False, max_length=30)
    city = forms.CharField(required=False, max_length=50)
    zip_code = forms.CharField(required=False, max_length=10, label="ZIP")
    source = forms.ModelChoiceField(required=False, queryset=DataSource.objects.none(), empty_label="All sources")
    exclusion_type = forms.CharField(required=False, max_length=50)
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["source"].queryset = DataSource.objects.all()
