from django import forms
from datetime import datetime, timedelta
from django.utils import timezone

class URLForm(forms.Form):
    url = forms.URLField(label='', widget=forms.TextInput(attrs={'placeholder': 'Enter URL'}))


class SiteSelectionForm(forms.Form):
    thesun = forms.BooleanField(required=False, initial=True)
    cbsnews = forms.BooleanField(required=False, initial=True)
    abcnews = forms.BooleanField(required=False, initial=True)

class SearchArticlesForm(forms.Form):
    search_query = forms.CharField(max_length=100, required=False)
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    show_clickbaits = forms.BooleanField(required=False, initial=True)
    thesun = forms.BooleanField(required=False, initial=True)
    cbsnews = forms.BooleanField(required=False, initial=True)
    abcnews = forms.BooleanField(required=False, initial=True)


    def __init__(self, *args, **kwargs):
        super(SearchArticlesForm, self).__init__(*args, **kwargs)

        # Set default values for date_from and date_to
        default_date_from = timezone.now() - timedelta(days=7)
        default_date_to = timezone.now()

        self.fields['date_from'].initial = default_date_from.date()
        self.fields['date_to'].initial = default_date_to.date()
