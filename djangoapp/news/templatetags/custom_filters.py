"""Custom template filters for the app."""
from django import template

register = template.Library()


@register.filter
def split_by_newline(value):
    """Split by newline."""
    return value.split("\n")


@register.filter
def multiply(value, arg):
    """Multiply."""
    return float(value) * float(arg)
