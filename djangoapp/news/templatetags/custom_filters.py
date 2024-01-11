from django import template

register = template.Library()


@register.filter
def split_by_newline(value):
    return value.split("\n")
