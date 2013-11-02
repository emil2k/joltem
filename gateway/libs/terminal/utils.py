

def force_ascii(raw):
    """Force the raw data to be ascii encoded, without error."""
    try:
        unicode(raw, "ascii")
    except TypeError, e:
        return raw.encode('ascii')
    else:
        return raw