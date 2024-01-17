"""Forms for the web app. These are used to get user input from the web app and
validate it. The forms are used in views.py.
"""
from datetime import timedelta
from django import forms
from django.utils import timezone


class URLForm(forms.Form):
    """Form for the URL input."""
    url = forms.URLField(
        label="", widget=forms.TextInput()
    )


class SiteSelectionForm(forms.Form):
    """Form for the site selection."""
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
    """Form for the search articles page."""
    search_query = forms.CharField(max_length=100, required=False)
    date_scraped_from = forms.DateField(
        required=False, widget=forms.DateInput(attrs={"type": "date"})
    )
    date_scraped_to = forms.DateField(
        required=False, widget=forms.DateInput(attrs={"type": "date"})
    )
    thesun = forms.BooleanField(required=False, initial=True, label="The Sun UK")
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

    main = forms.BooleanField(required=False, initial=False, label="Front Page")
    General = forms.BooleanField(required=False, initial=False, label="General")
    Politics = forms.BooleanField(required=False, initial=False, label="Politics")
    Sports = forms.BooleanField(required=False, initial=False, label="Sports")
    Health = forms.BooleanField(required=False, initial=False, label="Health")
    Technology = forms.BooleanField(required=False, initial=False, label="Technology")

    def __init__(self, *args, **kwargs):
        """Set default values for date_from and date_to."""
        super().__init__(*args, **kwargs)

        # Set default values for date_from and date_to
        default_date_from = timezone.now() - timedelta(days=7)
        default_date_to = timezone.now()

        self.fields["date_scraped_from"].initial = default_date_from.date()
        self.fields["date_scraped_to"].initial = default_date_to.date()
