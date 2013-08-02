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
def is_true(boolean, string):
    """
    Outputs a string if true
    """
    if boolean:
        return string



def is_match(string, actual, expected):
    """
    If value is a bool checks if true and if checks if matches expectations prints given string
    """
    if actual == expected:
        return string

@register.filter
def icon_white(actual, expected):
    return is_match('icon-white', actual, expected)

@register.filter
def btn_success(actual, expected):
    return is_match('btn-success', actual, expected)

@register.filter
def btn_danger(actual, expected):
    return is_match('btn-danger', actual, expected)

@register.filter
def btn_warning(actual, expected):
    return is_match('btn-warning', actual, expected)

