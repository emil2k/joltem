from twisted.python import log
from zope.interface import implements
from twisted.cred.checkers import ICredentialsChecker
from twisted.cred.credentials import ISSHPrivateKey
from twisted.cred.portal import IRealm
from twisted.conch.avatar import ConchUser
from twisted.internet.defer import succeed
from twisted.python.failure import Failure
from twisted.cred.error import UnauthorizedLogin

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

class DummyEmilChecker():
    """
    Approves all users with the username `emil` for testing
    """
    implements(ICredentialsChecker)
    credentialInterfaces = (ISSHPrivateKey, )

    def requestAvatarId(self, credentials):
        log.msg("Request avatar id for %s." % credentials.username)
        if credentials.username == "emil":
            return succeed("emil")
        else:
            return Failure(UnauthorizedLogin("You are %s, not `emil`. Login failed." % credentials.username))
