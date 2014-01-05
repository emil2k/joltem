""" SSH Authentication. """
from twisted.conch.avatar import ConchUser
from twisted.cred.checkers import ICredentialsChecker
from twisted.cred.credentials import ISSHPrivateKey
from twisted.cred.error import UnauthorizedLogin
from twisted.cred.portal import IRealm
from twisted.internet.defer import succeed
from twisted.python import log
from twisted.python.failure import Failure
from zope.interface import implements  # noqa

from gateway.libs.ssh.session import GatewaySession
from git.models import Authentication, BadKeyError


class GatewayUser(ConchUser):

    """ SSH user. """

    def __init__(self, key):
        ConchUser.__init__(self)
        # django, authentication model instance for logged in avatar
        self.user = key.user
        self.project = key.project
        self.channelLookup['session'] = GatewaySession

    @staticmethod
    def logout():
        """ Logout user. """
        log.msg('User logout')


class GatewayRealm(object):

    """ The realm connects application objects to authentication system. """

    implements(IRealm)

    @staticmethod
    def requestAvatar(authentication, mind, *interfaces):
        """ Return avatar which provides one of the given interfaces.

        :return tuple:

        """
        log.msg("Request avatar for key # %s." % authentication.pk)
        user = GatewayUser(authentication)
        return interfaces and interfaces[0] or None, user, user.logout


# Credential checkers

class GatewayCredentialChecker(object):

    """ Credential checker.

    That queries based on the passed username and credential signature the keys
    stored in the databases and attempts to retrieve the username related
    to the

    """

    implements(ICredentialsChecker)
    credentialInterfaces = (ISSHPrivateKey, )

    @staticmethod
    def requestAvatarId(credentials):
        """ Should have a docstring.

        :return : Status

        """
        log.msg("Request avatar id for %s." % credentials.username,
                system="auth")

        try:
            key = Authentication.load_key(credentials.blob)
            keys = Authentication.objects.filter(fingerprint=key.fingerprint)
            if not keys:
                raise AssertionError('Keys not found.')
        except (BadKeyError, AssertionError):
            return Failure(UnauthorizedLogin(
                "Invalid credentials provided, setup RSA keys for your SSH."))

        for key in [k for k in keys if k.user_id]:
            if credentials.username == key.user.username:
                return succeed(key)

        for key in [k for k in keys if k.project_id]:
            return succeed(key)

        return Failure(UnauthorizedLogin(
            "Authentication failed, key not found for user."))
