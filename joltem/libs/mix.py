""" Prepare mixer to generate Joltem models. """
from mixer.backend.django import mixer


def _set_password(user):
    user.set_password(user.password)
    return user

mixer.register('joltem.user', {}, postprocess=_set_password)

mixer.register('project.project', {
    'title': mixer.F.get_simple_username
})

SSH_TEMPLATE = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCfg+CS9hIcTTI6qRAqfkhS3lzIxlKut25NRr+FIQNTGwHPfDBS3kCATJKKe9MNAO5pqOaWqZ4i5PmHMb+CbfjBxB2IeJR8JqzXocLo8pTTiNoJqWGyGgxZKZK87yLeAAFqthCT2l5QdVoXaygkCK0JZ4Deh63USy4MBWWFLjRHFmE2nVV7vJuoLCEbn7TuiP7M3HQZLTHrZx9liVEIc72d5jdBaNhcthK8oW0rb1zaYCYbBFwvAWVwQNgBC5d7Pgf1XqHKt5j9DlA1pEbHlj8hKNJao6YYSlVlXA8oUuEXoSC/SnguXyP6xsbd9WStPqDh9iMYSqYIu/Ikf7V4%s %s" # noqa
mixer.register('git.authentication', {
    'key': lambda: SSH_TEMPLATE % (
        mixer.G.get_string(length=4), mixer.F.get_email()),
    'name': mixer.F.get_simple_username,
    'fingerprint': mixer.SKIP,
})

mixer.register('git.repository', {
    'name': mixer.MIX.project.title,
})
