from django import template

register = template.Library()

@register.filter
def replace_underscores(value):
    """Replace underscores with spaces and capitalize first letters"""
    return value.replace('_', ' ').title()
