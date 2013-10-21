"""
Gateway Daemon

start with twistd -ny gateway.tac

"""
import sys
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "joltem.settings")
# Configure sys.path and current working directory
GATEWAY_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
MAIN_DIRECTORY = os.path.split(GATEWAY_DIRECTORY)[0]
os.chdir(GATEWAY_DIRECTORY)  # all files to open contained here
sys.path.append(MAIN_DIRECTORY)  # importing project modules should be done from here
# Continue imports
from twisted.cred.portal import Portal
from twisted.application import service, internet
from twisted.python.log import ILogObserver, FileLogObserver
from twisted.python.logfile import LogFile

from gateway.libs.ssh.factory import GatewayFactory
from gateway.libs.ssh.auth import GatewayRealm, GatewayCredentialChecker

from joltem.settings import (GATEWAY_PORT, GATEWAY_LOGGER_FILE_NAME, GATEWAY_LOGGER_FILE_DIRECTORY,
                             GATEWAY_LOGGER_MAX_BYTES, GATEWAY_LOGGER_BACKUP_COUNT)

# Set the `application` variable for the .tac file
application = service.Application("Gateway")

# Set up the gateway service
factory = GatewayFactory()
# Setup portal and credential checkers
portal = Portal(GatewayRealm())
portal.registerChecker(GatewayCredentialChecker())
factory.portal = portal
internet.TCPServer(GATEWAY_PORT, factory).setServiceParent(application)
# Setup gateway logging
logger = LogFile(GATEWAY_LOGGER_FILE_NAME, GATEWAY_LOGGER_FILE_DIRECTORY, rotateLength=GATEWAY_LOGGER_MAX_BYTES,
                 maxRotatedFiles=GATEWAY_LOGGER_BACKUP_COUNT)
application.setComponent(ILogObserver, FileLogObserver(logger).emit)
