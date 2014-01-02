""" Create gateway factory. """

from twisted.cred.portal import Portal

from .ssh.auth import GatewayRealm, GatewayCredentialChecker
from .ssh.factory import GatewayFactory


# Set up the gateway service
factory = GatewayFactory()
# Setup portal and credential checkers
portal = Portal(GatewayRealm())
portal.registerChecker(GatewayCredentialChecker())
factory.portal = portal
