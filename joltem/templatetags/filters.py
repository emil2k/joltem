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

@register.filter
def css_class(check, css):
    """
    If check is true prints a CSS class to be applied to anything
    """
    if check:
        return css

@register.filter
def vote(vote, value):
    """
    If vote matches value of button print active CSS for vote button
    """
    if vote == value:
        return "btn-success"

