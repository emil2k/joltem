"""
Gateway Daemon

start with twistd -ny gateway.tac

"""
import sys

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "joltem.settings")

GATEWAY_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
MAIN_DIRECTORY = os.path.split(GATEWAY_DIRECTORY)[0]

os.chdir(GATEWAY_DIRECTORY)  # all files to open contained here
sys.path.append(MAIN_DIRECTORY)  # importing project modules should be done from here

from twisted.cred.portal import Portal
from twisted.application import service, internet

from gateway.libs.ssh.factory import GatewayFactory
from gateway.libs.ssh.auth import GatewayRealm, GatewayCredentialChecker

from joltem.settings import GATEWAY_PORT

# Set the `application` variable as for the .tac file
application = service.Application("Gateway")

# Set up the gateway service
factory = GatewayFactory()
# Setup portal and credential checkers
portal = Portal(GatewayRealm())
portal.registerChecker(GatewayCredentialChecker())
factory.portal = portal
internet.TCPServer(GATEWAY_PORT, factory).setServiceParent(application)