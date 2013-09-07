
def list_string_join(strings, glue=", ", last="and "):
    """
    Utility function, that joins strings into a list string like :
    jill, zack, and bob or zack and bob
    """
    if len(strings) < 2:
        return "".join(strings)
    else:
        strings[-1] = last + strings[-1]
        if len(strings) > 2:
            return glue.join(strings)
        else:
            return " ".join(strings)

