from django import forms
from datetime import datetime, timedelta
from django.utils import timezone
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from crispy_forms.bootstrap import InlineRadios


class URLForm(forms.Form):
    url = forms.URLField(label='', widget=forms.TextInput(attrs={'placeholder': 'Enter article URL'}))


class SiteSelectionForm(forms.Form):
    thesun = forms.BooleanField(required=False, initial=True, label='The Sun')
    cbsnews = forms.BooleanField(required=False, initial=True, label='CBS News')
    abcnews = forms.BooleanField(required=False, initial=True, label='ABC News')
    clickbait_tolerance = forms.ChoiceField(
        choices=[
            ('0', '3/3'),
            ('1', '2/3'),
            ('2', '1/3'),
            ('3', '0'),
        ],
        required=False
    )
    category = forms.ChoiceField(
        choices=[
            ('front_page', 'Front Page'),
            ('General', 'General'),
            ('Politics', 'Politics'),
            ('Sports', 'Sports'),
            ('Health', 'Health'),
            ('Technology', 'Technology'),
        ],
        initial='front_page',
        required=False

    )
    


class SearchArticlesForm(forms.Form):
    search_query = forms.CharField(max_length=100, required=False)
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    show_clickbaits = forms.BooleanField(required=False, initial=True)
    thesun = forms.BooleanField(required=False, initial=True)
    cbsnews = forms.BooleanField(required=False, initial=True)
    abcnews = forms.BooleanField(required=False, initial=True)
    clickbait_tolerance = forms.ChoiceField(
        choices=[
            ('0', '3/3'),
            ('1', '2/3'),
            ('2', '1/3'),
            ('3', '0'),
        ],
        required=False,
        initial='0'
    )
    
    categories = forms.MultipleChoiceField(
        choices=[
            ('front_page', 'Front Page'),
            ('general', 'General'),
            ('politics', 'Politics'),
            ('sports', 'Sports'),
            ('health', 'Health'),
            ('technology', 'Technology'),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )


    def __init__(self, *args, **kwargs):
        super(SearchArticlesForm, self).__init__(*args, **kwargs)

        # Set default values for date_from and date_to
        default_date_from = timezone.now() - timedelta(days=7)
        default_date_to = timezone.now()

        self.fields['date_from'].initial = default_date_from.date()
        self.fields['date_to'].initial = default_date_to.date()


