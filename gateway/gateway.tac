"""
Gateway Daemon -- start up a gateway for the git server and shell

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

from gateway.libs.ssh.factory import GatewayFactory
from gateway.libs.ssh.auth import GatewayRealm, GatewayCredentialChecker

from joltem.settings import GATEWAY_PORT

# Set up the gateway service
factory = GatewayFactory()
# Setup portal and credential checkers
portal = Portal(GatewayRealm())
portal.registerChecker(GatewayCredentialChecker())
factory.portal = portal

if __name__ == '__main__':
    """
    Start up the gateway for testing purposes simply by running : python gateway.tac
    Logs to standard output.
    """
    from twisted.python import log
    from twisted.internet import reactor
    from twisted.internet.endpoints import TCP4ServerEndpoint
    log.startLogging(sys.stdout)
    # Connect factory on endpoint
    d = TCP4ServerEndpoint(reactor, GATEWAY_PORT).listen(factory)
    d.addCallback(lambda port: log.msg("Listening on port %d." % GATEWAY_PORT))
    d.addErrback(lambda failure: log.err(failure, "Failed to open gateway on port %d." % GATEWAY_PORT))
    # Run reactor :)
    reactor.run()
else:
    """
    Start up the gateway as a daemon using twistd by running : twistd -y gateway.tac
    Logs to gateway log specified in settings, sets the `application` variable for the .tac file.
    """
    from twisted.application import service, internet
    from twisted.python.logfile import LogFile
    from twisted.python.log import ILogObserver, FileLogObserver
    from joltem.settings import (GATEWAY_LOGGER_FILE_NAME, GATEWAY_LOGGER_FILE_DIRECTORY,
                                 GATEWAY_LOGGER_MAX_BYTES, GATEWAY_LOGGER_BACKUP_COUNT)
    application = service.Application("Gateway")
    internet.TCPServer(GATEWAY_PORT, factory).setServiceParent(application)
    # Setup gateway logging
    logger = LogFile(GATEWAY_LOGGER_FILE_NAME, GATEWAY_LOGGER_FILE_DIRECTORY, rotateLength=GATEWAY_LOGGER_MAX_BYTES,
                     maxRotatedFiles=GATEWAY_LOGGER_BACKUP_COUNT)
    application.setComponent(ILogObserver, FileLogObserver(logger).emit)
