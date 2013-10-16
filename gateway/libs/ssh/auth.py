from twisted.python import log
from zope.interface import implements
from twisted.cred.checkers import ICredentialsChecker
from twisted.cred.credentials import ISSHPrivateKey
from twisted.cred.portal import IRealm
from twisted.conch.avatar import ConchUser
from twisted.internet.defer import succeed
from twisted.python.failure import Failure
from twisted.cred.error import UnauthorizedLogin

from git.models import Authentication, User, BadKeyError
from gateway.libs.ssh.session import GatewaySession


class GatewayUser(ConchUser):

    def __init__(self, username):
        ConchUser.__init__(self)
        self.username = username
        self.channelLookup['session'] = GatewaySession

    def logout(self):
        pass  # implement when necessary


class GatewayRealm():
    implements(IRealm)

    def requestAvatar(self, username, mind, *interfaces):
        log.msg("Request avatar for %s." % username)
        user = GatewayUser(username)
        return interfaces[0], user, user.logout


# Credential checkers

class GatewayCredentialChecker():
    """
    Credential checker that queries based on the passed username and credential signature the keys stored
    in the databases and attempts to retrieve the username related to the

    """
    implements(ICredentialsChecker)
    credentialInterfaces = (ISSHPrivateKey, )

    def requestAvatarId(self, credentials):
        log.msg("Request avatar id for %s." % credentials.username, system="auth")
        try:
            user = User.objects.get(username=credentials.username)
        except User.DoesNotExist:
            return Failure(UnauthorizedLogin("Username not found."))
        except User.MultipleObjectsReturned:
            return Failure(UnauthorizedLogin("Multiple usernames found."))  # should not happen
        else:
            try:
                key = Authentication.load_key(credentials.blob)
            except BadKeyError:
                return Failure(UnauthorizedLogin("Invalid credentials provided, setup RSA keys for your SSH."))
            else:
                provided_fp = key.fingerprint()
                log.msg("Fingerprint of provided RSA key : %s" % provided_fp, system="auth")
                if user.authentication_set.filter(fingerprint=provided_fp).exists():
                    return succeed(credentials.username)
                else:
                    return Failure(UnauthorizedLogin("Authentication failed, key not found."))


class DummyEmilChecker():
    """
    Approves all users with the username `emil` for testing
    """
    implements(ICredentialsChecker)
    credentialInterfaces = (ISSHPrivateKey, )

    def requestAvatarId(self, credentials):
        log.msg("Request avatar id for %s." % credentials.username, system="auth")
        if credentials.username == "emil":
            return succeed("emil")
        else:
            return Failure(UnauthorizedLogin("You are %s, not `emil`. Login failed." % credentials.username))
