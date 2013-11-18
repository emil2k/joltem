""" Utils. """


def list_string_join(strings, glue=", ", last="and "):
    """ Utility function, that joins strings into a list.

    String like : jill, zack, and bob or zack and bob

    :return str:

    """
    if len(strings) < 2:
        return "".join(strings)

    strings[-1] = last + strings[-1]
    if len(strings) > 2:
        return glue.join(strings)

    return " ".join(strings)
