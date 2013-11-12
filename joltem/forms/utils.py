""" Form related utilities. """

import re

def is_valid_email(email):
    """ Validate if the passed string is a valid email address.

    :param email: string to test.
    :return: boolean of whether email is considered valid.

    """
    return re.match(r'^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.(?:[A-Z]{2}|com|org|net|edu|gov|mil|biz|info|mobi|name|aero|asia|jobs|museum)$', email, re.I )
