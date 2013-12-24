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
from joltem.models import User


class GatewayUser(ConchUser):

    """ SSH user. """

    def __init__(self, username):
        ConchUser.__init__(self)
        # django, user model instance for logged in avatar
        self.user = User.objects.get(username=username)
        self.channelLookup['session'] = GatewaySession

    @staticmethod
    def logout():
        """ Logout user. """
        log.msg('User logout')


class GatewayRealm(object):

    """ The realm connects application objects to authentication system. """

    implements(IRealm)

    @staticmethod
    def requestAvatar(username, mind, *interfaces):
        """ Return avatar which provides one of the given interfaces.

        :return tuple:

        """
        log.msg("Request avatar for %s." % username)
        user = GatewayUser(username)
        return interfaces[0], user, user.logout


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
            user = User.objects.get(username=credentials.username)
        except User.DoesNotExist:
            return Failure(UnauthorizedLogin("Username not found."))
        except User.MultipleObjectsReturned:
            # should not happen
            return Failure(UnauthorizedLogin("Multiple usernames found."))
        else:
            try:
                key = Authentication.load_key(credentials.blob)
            except BadKeyError:
                return Failure(UnauthorizedLogin(
                    "Invalid credentials provided, setup RSA keys for your SSH."))  # noqa
            else:
                provided_fp = key.fingerprint()
                log.msg("Fingerprint of provided RSA key : %s" % provided_fp,
                        system="auth")
                if user.authentication_set.filter(
                        fingerprint=provided_fp).exists():
                    return succeed(credentials.username)
                else:
                    return Failure(UnauthorizedLogin(
                        "Authentication failed, key not found."))


class DummyEmilChecker(object):
    # todo remove this checker

    """ Approves all users with the username `emil` for testing. """

    implements(ICredentialsChecker)
    credentialInterfaces = (ISSHPrivateKey, )

    @staticmethod
    def requestAvatarId(credentials):
        """ Return success for username 'emil'.


        :return : Status

        """
        log.msg("Request avatar id for %s." % credentials.username,
                system="auth")
        if credentials.username == "emil":
            return succeed("emil")
        else:
            return Failure(UnauthorizedLogin("You are %s, not `emil`. Login failed." % credentials.username))  # noqa
