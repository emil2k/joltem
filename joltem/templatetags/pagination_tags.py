# coding: utf-8
from django.template.base import Library

register = Library()


@register.assignment_tag
def pagination(paginator, page_num):
    """This is slightly improved Django admin's ``pagination`` inclusion tag.

    https://github.com/django/django/blob/master/django/contrib/admin/templatetags/admin_list.py

    """
    DOT = '.'
    ON_EACH_SIDE = 3
    ON_ENDS = 2

    # If there are 10 or fewer pages, display links to every page.
    # Otherwise, do some fancy
    if paginator.num_pages <= 10:
        page_range = range(paginator.num_pages)
    else:
        # Insert "smart" pagination links, so that there are always ON_ENDS
        # links at either end of the list of pages, and there are always
        # ON_EACH_SIDE links at either end of the "current page" link.
        page_range = []
        if page_num > (ON_EACH_SIDE + ON_ENDS):
            page_range.extend(range(0, ON_ENDS))
            page_range.append(DOT)
            page_range.extend(range(page_num - ON_EACH_SIDE, page_num + 1))
        else:
            page_range.extend(range(0, page_num + 1))
        if page_num < (paginator.num_pages - ON_EACH_SIDE - ON_ENDS - 1):
            page_range.extend(range(page_num + 1, page_num + ON_EACH_SIDE + 1))
            page_range.append(DOT)
            page_range.extend(
                range(paginator.num_pages - ON_ENDS, paginator.num_pages))
        else:
            page_range.extend(range(page_num + 1, paginator.num_pages))

    return [p + 1 if p != DOT else DOT for p in page_range]
