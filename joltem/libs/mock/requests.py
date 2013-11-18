from django.utils import timezone
from django.test import RequestFactory


class MockUser(object):

    """ A mock user for testing requests. """
    # todo maybe this is unnecessary

    username = 'johndoe'
    first_name = 'John'
    last_name = 'Doe'
    email = 'johndoe@example.com'
    is_staff = False
    is_active = True
    date_joined = timezone.now()
    _is_authenticated = False  # custom state

    def __init__(self, is_authenticated=False):
        self._is_authenticated = is_authenticated

    def is_authenticated(self):
        """ Return mock authentication state.

        :return: boolean of whether authenticated or not

        """
        return self._is_authenticated

    def get_full_name(self):
        """ Returns the first_name plus the last_name, with a space in between. """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """ Returns the short name for the user. """
        return self.first_name

    def get_profile(self):
        """ Return user's mock profile. """
        pass


def mock_authentication_middleware(request, user=None, is_authenticated=False):
    """
    A way to mock the authentication network to set
    the request.user setting that many of the views user

    """
    if user:
        user.is_authenticated = lambda x: is_authenticated
        request.user = user
    else:
        request.user = MockUser(is_authenticated)
    return request


def get_mock_get_request(path="/fakepath", user=None, is_authenticated=False):
    """
    Return a mock a GET request, to pass to a view
    `path` not important unless the view is using a path argument
    """
    return mock_authentication_middleware(RequestFactory().get(
        path=path), user=user, is_authenticated=is_authenticated)


def get_mock_post_request(path="/fakepath", user=None,
                          is_authenticated=False, data={}):
    """
    Return a mock a POST request, to pass to a view
    `path` not important unless the view is using a path argument
    """
    return mock_authentication_middleware(RequestFactory().post(
        path=path, data=data), user=user, is_authenticated=is_authenticated)
