from django import template

register = template.Library()

@register.filter
def as_percentage_of(part, whole):
    try:
        return "%d%%" % (float(part) / whole * 100)
    except (ValueError, ZeroDivisionError):
        return ""

@register.filter
def active(check, active):
    """
    If check matches active prints "active" which can be applied as a CSS class to a tab or anything else
    """
    if check == active:
        return "active"