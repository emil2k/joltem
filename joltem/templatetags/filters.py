""" Joltem filters. """

from django import template

register = template.Library()


@register.filter
def as_percentage_of(part, whole):
    """ Render as percent.

    :return str:

    """
    try:
        return "%d%%" % (float(part) / whole * 100)
    except (ValueError, ZeroDivisionError):
        return ""


@register.filter
def active(check, actv):
    """ If check matches active prints "active".

    Which can be applied as a CSS class to a tab or anything else.

    :return str:

    """
    if check == actv:
        return "active"


@register.filter
def is_true(boolean, string):
    """ Output a string if true.

    :return str:

    """
    if boolean:
        return string
    return ""


@register.filter
def is_false(boolean, string):
    """ Output a string if false.

    :return str:

    """
    if not boolean:
        return string


def is_match(string, actual, expected):
    """ Print given string.

    If value is a bool checks if true and if checks if matches expectations
    prints given string.

    :return str:

    """
    if actual == expected:
        return string


@register.filter
def icon_white(actual, expected):
    """ Render icon when metches.

    :return str:

    """
    return is_match('icon-white', actual, expected)


@register.filter
def btn_success(actual, expected):
    """ Render button when metches.

    :return str:

    """
    return is_match('btn-success', actual, expected)


@register.filter
def btn_danger(actual, expected):
    """ Render button when metches.

    :return str:

    """
    return is_match('btn-danger', actual, expected)


@register.filter
def btn_warning(actual, expected):
    """ Render button when metches.

    :return str:

    """
    return is_match('btn-warning', actual, expected)
