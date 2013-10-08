from twisted.python import log
from zope.interface import implements
from twisted.conch.ssh.session import SSHSession, wrapProtocol
from twisted.conch.interfaces import ISession
from twisted.conch.insults.insults import ServerProtocol

from gateway.libs.terminal.protocol import GatewayTerminalProtocol


class GatewaySession(SSHSession):

    def channelOpen(self, specificData):
        self.session = GatewaySessionInterface(self.avatar)


class GatewaySessionInterface():
    """
    Interface to an SSH session
    """
    implements(ISession)

    def __init__(self, user):
        self.user = user

    def getPty(self, term, windowSize, modes):
        (rows, cols, xpixel, ypixel) = windowSize
        log.msg("Get PTY, window : %d x %d (%dpx x %dpx)" % (cols, rows, xpixel, ypixel))

    def openShell(self, protocol):  # protocol is instance of SSHSessionProcessProtocol
        peer_address = protocol.getPeer().address  # IAddress
        (host, port) = (peer_address.host, peer_address.port)
        log.msg("Open shell from %s:%d." % (host, port))
        serverProtocol = ServerProtocol(GatewayTerminalProtocol, self.user)
        serverProtocol.makeConnection(protocol)
        protocol.makeConnection(wrapProtocol(serverProtocol))

    def execCommand(self, protocol, command):  # protocol is instance of SSHSessionProcessProtocol
        pass  # todo

    def windowChanged(self, newWindowSize):
        (rows, cols, xpixel, ypixel) = newWindowSize
        log.msg("Window changed, new window : %d x %d (%dpx x %dpx)" % (cols, rows, xpixel, ypixel))
        # todo set terminalSize() on terminal protocol

    def eofReceived(self):
        log.msg("No more data will be sent (EOF).")

    def closed(self):
        log.msg("Connection closed")
