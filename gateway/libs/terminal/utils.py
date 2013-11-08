""" Protocol utils. """


def force_ascii(raw):
    """Force the raw data to be ascii encoded, without error.

    :return unicode:

    """
    try:
        unicode(raw, "ascii")
    except TypeError:
        return raw.encode('ascii')

    return raw
