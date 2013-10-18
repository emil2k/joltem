import shlex

from twisted.python import log
from zope.interface import implements
from twisted.conch.ssh.channel import SSHChannel
from twisted.conch.ssh.session import SSHSession, wrapProtocol
from twisted.conch.interfaces import ISession
from twisted.conch.insults.insults import ServerProtocol
from twisted.internet import reactor

from git.models import REPOSITORIES_DIRECTORY
from gateway.libs.terminal.protocol import GatewayTerminalProtocol
from gateway.libs.git.protocol import GitProcessProtocol, GitReceivePackProcessProtocol


class GatewaySession(SSHSession):

    def channelOpen(self, specificData):
        self.session = GatewaySessionInterface(self.avatar)

    def loseConnection(self):
        """
        Overridden to fix possible bug described here :
        http://twistedmatrix.com/trac/ticket/2754
        """
        if self.client and self.client.transport:
            self.client.transport.loseConnection()
        SSHChannel.loseConnection(self)


class GatewaySessionInterface():
    """
    Interface to an SSH session
    """
    implements(ISession)

    def __init__(self, avatar):
        self.avatar = avatar
        self._git_protocol = None

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

    def execCommand(self, protocol, command_string):  # protocol is instance of SSHSessionProcessProtocol
        log.msg("Execute command : %s" % command_string)
        command = shlex.split(command_string)
        process = command[0]
        if process == "git-upload-pack" or process == "git-receive-pack":
            repository_id = int(command[1])
            if process == "git-receive-pack":
                self._git_protocol = GitReceivePackProcessProtocol(protocol, self.avatar)
            else:
                self._git_protocol = GitProcessProtocol(protocol, self.avatar)
            protocol.makeConnection(self._git_protocol)
            reactor.spawnProcess(
                self._git_protocol, '/usr/bin/%s' % process, (process, '%d.git' % repository_id),
                path=REPOSITORIES_DIRECTORY)
        else:
            protocol.write("Command not allowed.\n")
            protocol.loseConnection()

    def windowChanged(self, newWindowSize):
        (rows, cols, xpixel, ypixel) = newWindowSize
        log.msg("Window changed, new window : %d x %d (%dpx x %dpx)" % (cols, rows, xpixel, ypixel))
        # todo set terminalSize() on terminal protocol

    def eofReceived(self):
        log.msg("No more data will be sent (EOF).")
        if self._git_protocol:
            self._git_protocol.eof_received()

    def closed(self):
        log.msg("Connection closed")
