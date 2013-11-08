# coding: utf-8

""" SSH utils. """


def parse_repository_id(repository_id):
    """Parse repositoty id.

    Repository id must be integer but user could specify ssh port so we
    should consider leading slash:

        $ git clone ssh://username@joltem.com:1
        $ git clone ssh://username@joltem.com:222/1

    :return long|None: Repository ID

    """
    if repository_id.startswith('/'):
        repository_id = repository_id[1:]
    try:
        return long(repository_id)
    except ValueError:
        return
