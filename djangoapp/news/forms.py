"""Forms for the web app. These are used to get user input from the web app and
validate it. The forms are used in views.py.
"""
from datetime import timedelta
from django import forms
from django.utils import timezone
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError


class SupportedURLValidator(URLValidator):
    def __call__(self,value):
        super().__call__(value)
        if not ('abcnews' in value or 'cbsnews' in value or 'thesun' in value):
            raise ValidationError(
                "The URL is not supported."
            )

class URLForm(forms.Form):
    """Form for the URL input."""
    url = forms.URLField(
        label="", widget=forms.TextInput(),
        validators=[
            SupportedURLValidator(),
        ]
    )


class SiteSelectionForm(forms.Form):
    """Form for the site selection."""
    thesun = forms.BooleanField(required=False, initial=True, label="The Sun")
    cbsnews = forms.BooleanField(required=False, initial=True, label="CBS News")
    abcnews = forms.BooleanField(required=False, initial=True, label="ABC News")
    clickbait_tolerance = forms.ChoiceField(
        choices=[
            ("0", "Only non-clickbaits"),
            ("1", "Likely non-clickbaits"),
            ("2", "Possibly clickbaits"),
            ("3", "All"),
        ],
        required=False,
        initial="3",
    )
    category = forms.ChoiceField(
        choices=[
            ("Front Page", "Front Page"),
            ("World", "World"),
            ("Politics", "Politics"),
            ("Sports", "Sports"),
            ("Health", "Health"),
            ("Technology", "Technology"),
        ],
        initial="Front Page",
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
            ("0", "Only non-clickbaits"),
            ("1", "Likely non-clickbaits"),
            ("2", "Possibly clickbaits"),
            ("3", "All"),
        ],
        required=False,
        initial="3",
    )

    front_page = forms.BooleanField(required=False, initial=False, label="Front Page")
    World = forms.BooleanField(required=False, initial=False, label="World")
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
