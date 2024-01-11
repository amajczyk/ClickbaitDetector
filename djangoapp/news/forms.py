from django import forms
from datetime import datetime, timedelta
from django.utils import timezone




class URLForm(forms.Form):
    url = forms.URLField(
        label="Enter article URL", widget=forms.TextInput()
    )


class SiteSelectionForm(forms.Form):
    thesun = forms.BooleanField(required=False, initial=True, label="The Sun")
    cbsnews = forms.BooleanField(required=False, initial=True, label="CBS News")
    abcnews = forms.BooleanField(required=False, initial=True, label="ABC News")
    clickbait_tolerance = forms.ChoiceField(
        choices=[
            ("0", "3/3"),
            ("1", "2/3"),
            ("2", "1/3"),
            ("3", "0"),
        ],
        required=False,
        initial="3",
    )
    category = forms.ChoiceField(
        choices=[
            ("main", "Front Page"),
            ("General", "General"),
            ("Politics", "Politics"),
            ("Sports", "Sports"),
            ("Health", "Health"),
            ("Technology", "Technology"),
        ],
        initial="main",
        required=False,
    )


class SearchArticlesForm(forms.Form):
    search_query = forms.CharField(max_length=100, required=False)
    date_scraped_from = forms.DateField(
        required=False, widget=forms.DateInput(attrs={"type": "date"})
    )
    date_scraped_to = forms.DateField(
        required=False, widget=forms.DateInput(attrs={"type": "date"})
    )
    thesun = forms.BooleanField(required=False, initial=True)
    cbsnews = forms.BooleanField(required=False, initial=True)
    abcnews = forms.BooleanField(required=False, initial=True)
    clickbait_tolerance = forms.ChoiceField(
        choices=[
            ("0", "3/3"),
            ("1", "2/3"),
            ("2", "1/3"),
        ],
        required=False,
        initial="3",
    )

    categories = forms.MultipleChoiceField(
        choices=[
            ("main", "Front Page"),
            ("general", "General"),
            ("politics", "Politics"),
            ("sports", "Sports"),
            ("health", "Health"),
            ("technology", "Technology"),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple,
        initial=["main", "general", "politics", "sports", "health", "technology"],
    )

    def __init__(self, *args, **kwargs):
        super(SearchArticlesForm, self).__init__(*args, **kwargs)

        # Set default values for date_from and date_to
        default_date_from = timezone.now() - timedelta(days=7)
        default_date_to = timezone.now()

        self.fields["date_scraped_from"].initial = default_date_from.date()
        self.fields["date_scraped_to"].initial = default_date_to.date()
