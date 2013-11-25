""" Supports SSH session. """

import shlex

from twisted.python import log
from zope.interface import implements
from twisted.conch.ssh.channel import SSHChannel
from twisted.conch.ssh.session import SSHSession, wrapProtocol
from twisted.conch.interfaces import ISession
from twisted.conch.insults.insults import ServerProtocol
from twisted.internet import reactor

from git.models import Repository, REPOSITORIES_DIRECTORY
from gateway.libs.terminal.protocol import GatewayTerminalProtocol
from gateway.libs.git.protocol import (
    GitProcessProtocol, GitReceivePackProcessProtocol)
from .utils import parse_repository_id


class GatewaySession(SSHSession):

    """ Support SSH sessions for joltem. """

    def channelOpen(self, specificData):
        """ Bind GatewaySessionInterface. """

        self.session = GatewaySessionInterface(self.avatar)

    def loseConnection(self):
        """ Overridden to fix possible bug.

        Described here : http://twistedmatrix.com/trac/ticket/2754

        """
        if self.client and self.client.transport:
            self.client.transport.loseConnection()
        SSHChannel.loseConnection(self)


class GatewaySessionInterface():

    """ Interface to an SSH session. """

    implements(ISession)

    def __init__(self, avatar):
        self.avatar = avatar
        self._git_protocol = None

    def getPty(self, term, windowSize, modes):
        """ Get a psuedo-terminal for use by a shell or command. """

        (rows, cols, xpixel, ypixel) = windowSize
        log.msg("Get PTY, window : %d x %d (%dpx x %dpx)" % (
            cols, rows, xpixel, ypixel))

    # protocol is instance of SSHSessionProcessProtocol
    def openShell(self, protocol):
        """ Open a shell and connect it to proto. """

        peer_address = protocol.getPeer().address  # IAddress
        (host, port) = (peer_address.host, peer_address.port)
        log.msg("Open shell from %s:%d." % (host, port))
        serverProtocol = ServerProtocol(GatewayTerminalProtocol, self.avatar)
        serverProtocol.makeConnection(protocol)
        protocol.makeConnection(wrapProtocol(serverProtocol))

    # protocol is instance of SSHSessionProcessProtocol
    def execCommand(self, protocol, command_string):
        """ Execute a command. """
        self.ssh_process_protocol = protocol
        log.msg("Execute command : %s" % command_string)
        command = shlex.split(command_string)
        process = command[0]
        if process == "git-upload-pack" or process == "git-receive-pack":
            try:
                repository_id = parse_repository_id(command[1])
                repository = Repository.objects.get(id=repository_id)
            except (
                    Repository.DoesNotExist,
                    Repository.MultipleObjectsReturned):
                log.msg("Repository not found.")
                protocol.loseConnection()
            else:
                if process == "git-receive-pack":
                    self._git_protocol = GitReceivePackProcessProtocol(
                        protocol, self.avatar, repository)
                else:
                    self._git_protocol = GitProcessProtocol(
                        protocol, self.avatar, repository)
                protocol.makeConnection(self._git_protocol)
                reactor.spawnProcess(
                    self._git_protocol, '/usr/bin/%s' % process,
                    (process, '%d.git' % repository_id),
                    path=REPOSITORIES_DIRECTORY)
        else:
            log.msg("Command not allowed.")
            protocol.loseConnection()

    def windowChanged(self, newWindowSize):
        """ Called when the size of the remote screen has changed. """

        (rows, cols, xpixel, ypixel) = newWindowSize
        log.msg("Window changed, new window : %d x %d (%dpx x %dpx)" % (
            cols, rows, xpixel, ypixel))
        # todo set terminalSize() on terminal protocol

    def eofReceived(self):
        """ Called when the other side has indicated no more data. """

        log.msg("No more data will be sent (EOF).")
        if self._git_protocol:
            self._git_protocol.eof_received()
        self.ssh_process_protocol.loseConnection()

    def closed(self):
        """ Called when the session is closed. """
        log.msg("Connection closed")

