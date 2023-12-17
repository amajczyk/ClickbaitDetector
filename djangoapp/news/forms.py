from django import forms

class URLForm(forms.Form):
    url = forms.URLField(label='', widget=forms.TextInput(attrs={'placeholder': 'Enter URL'}))


class SiteSelectionForm(forms.Form):
    thesun = forms.BooleanField(required=False, initial=True)
    cbsnews = forms.BooleanField(required=False, initial=True)
    abcnews = forms.BooleanField(required=False, initial=True)

