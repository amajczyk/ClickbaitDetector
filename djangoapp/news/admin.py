"""Admin configuration for the articles' app."""
from django.contrib import admin

from .models import Article

# Register your models here.

admin.site.register(Article)
