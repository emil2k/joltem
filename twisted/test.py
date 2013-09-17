from twisted.python import log, components
from twisted.internet import reactor
from twisted.conch.ssh.keys import Key
import sys

log.startLogging(sys.stdout)
log.msg("Hello, cruel world!")

from twisted.conch.ssh.factory import SSHFactory


PRIVATE_KEY = Key.fromFile("id_rsa")
PUBLIC_KEY = Key.fromFile("id_rsa.pub")

from zope.interface import implements
from twisted.cred.checkers import ICredentialsChecker
from twisted.cred.credentials import ISSHPrivateKey
from twisted.cred.portal import Portal, IRealm
from twisted.conch.avatar import ConchUser
from twisted.conch.ssh.session import SSHSession
from twisted.conch.interfaces import ISession

###### # todo unknown, from http://www.devshed.com/c/a/Python/SSH-with-Twisted/

from twisted.conch.recvline import HistoricRecvLine

WELCOME = '''
    ___       ___       ___       ___       ___       ___
   /\\  \\     /\\  \\     /\\__\\     /\\  \\     /\\  \\     /\\__\\
  _\\:\\  \\   /::\\  \\   /:/  /     \\:\\  \\   /::\\  \\   /::L_L_
 /\\/::\\__\\ /:/\\:\\__\\ /:/__/      /::\\__\\ /::\\:\\__\\ /:/L:\\__\\
 \\::/\\/__/ \\:\\/:/  / \\:\\  \\     /:/\\/__/ \\:\\:\\/  / \\/_/:/  /
  \\/__/     \\::/  /   \\:\\__\\    \\/__/     \\:\\/  /    /:/  /
             \\/__/     \\/__/               \\/__/     \\/__/

                                     [welcome to the shell.]
============================================================
            enter `help` for available commands.

'''

class SSHDemoProtocol(HistoricRecvLine):

    def __init__(self, user):
        self.user = user

    def connectionMade(self):
        HistoricRecvLine.connectionMade(self)
        self.terminal.write(WELCOME)
        self.terminal.nextLine()
        self.showPrompt()

    def showPrompt(self):
        self.terminal.write("joltem : %s > " % self.user.username)

    def getCommandFunc(self, cmd):
        return getattr(self, 'do_' + cmd, None)

    def lineReceived(self, line):
        line = line.strip()
        if line:
            cmdAndArgs = line.split()
            cmd = cmdAndArgs[0]
            args = cmdAndArgs[1:]
            func = self.getCommandFunc(cmd)
            if func:
               try:
                   func(*args)
               except Exception, e:
                   self.terminal.write("Error: %s" % e)
                   self.terminal.nextLine()
            else:
               self.terminal.write("No such command.")
               self.terminal.nextLine()
        self.showPrompt()

    def do_help(self, cmd=''):
        "Get help on a command. Usage: help command"
        if cmd:
            func = self.getCommandFunc(cmd)
            if func:
                self.terminal.write(func.__doc__)
                self.terminal.nextLine()
                return

        publicMethods = filter(
            lambda funcname: funcname.startswith('do_'), dir(self))
        commands = [cmd.replace('do_', '', 1) for cmd in publicMethods]
        self.terminal.write("Commands: " + " ".join(commands))
        self.terminal.nextLine()

    def do_echo(self, *args):
        "Echo a string. Usage: echo my line of text"
        self.terminal.write(" ".join(args))
        self.terminal.nextLine()

    def do_whoami(self):
        "Prints your user name. Usage: whoami"
        self.terminal.write(self.user.username)
        self.terminal.nextLine()

    def do_quit(self):
        "Ends your session. Usage: quit"
        self.terminal.write("Thanks for playing!")
        self.terminal.nextLine()
        self.terminal.loseConnection()

    def do_clear(self):
        "Clears the screen. Usage: clear"
        self.terminal.reset()




#######

class TestShellSession():
    implements(ISession)

    def __init__(self, user):
        self.user = user

    def getPty(self, term, windowSize, modes):
        (rows, cols, xpixel, ypixel) = windowSize
        log.msg("Get PTY, window : %d x %d (%dpx x %dpx)" % (cols, rows, xpixel, ypixel))

    def openShell(self, protocol):  # todo what is this protocol being passed?
        peer_address = protocol.getPeer().address  # IAddress
        (host, port) = (peer_address.host, peer_address.port)
        log.msg("Open shell from %s:%d." % (host, port))
        #### todo unknown, from http://www.devshed.com/c/a/Python/SSH-with-Twisted/
        from twisted.conch.insults.insults import ServerProtocol
        from twisted.conch.ssh.session import wrapProtocol
        serverProtocol = ServerProtocol(SSHDemoProtocol, self.user)
        serverProtocol.makeConnection(protocol)
        protocol.makeConnection(wrapProtocol(serverProtocol))  # todo why is there a wrap protocol?
        ####

    def execCommand(self, proto, command):
        log.msg("Execute command : %s" % command)

    def windowChanged(self, newWindowSize):
        (rows, cols, xpixel, ypixel) = newWindowSize
        log.msg("Window changed, new window : %d x %d (%dpx x %dpx)" % (cols, rows, xpixel, ypixel))

    def eofReceived(self):
        log.msg("No more data will be sent (EOF).")

    def closed(self):
        log.msg("Connection closed")


class TestSSHSession(SSHSession):
    pass  # implement later


class TestUser(ConchUser):

    def __init__(self, username):
        ConchUser.__init__(self)
        self.username = username
        self.channelLookup['session'] = TestSSHSession

    def logout(self):
        pass  # implement when necessary

class TestRealm():
    implements(IRealm)

    def requestAvatar(self, username, mind, *interfaces):
        log.msg("Request avatar for %s." % username)
        user = TestUser(username)
        return interfaces[0], user, user.logout()

from twisted.internet.defer import succeed, fail
from twisted.python.failure import Failure
from twisted.cred.error import UnauthorizedLogin


class TestPublicKeyCredentialChecker():
    implements(ICredentialsChecker)
    credentialInterfaces = (ISSHPrivateKey, )

    def requestAvatarId(self, credentials):
        log.msg("Request avatar id for %s." % credentials.username)
        if credentials.username == "emil":  # todo for testing
            return succeed("emil")
        else:
            return Failure(UnauthorizedLogin("You are %s, not emil. Login failed." % credentials.username))


class TestFactory(SSHFactory):

    def __init__(self):
        self.privateKeys = {'ssh-rsa': PRIVATE_KEY}
        self.publicKeys = {'ssh-rsa': PUBLIC_KEY}


# Start it all up ...
if __name__ == '__main__':
    factory = TestFactory()
    # Setup portal and credential checkers
    components.registerAdapter(TestShellSession, TestUser, ISession)
    portal = Portal(TestRealm())
    portal.registerChecker(TestPublicKeyCredentialChecker())
    factory.portal = portal
    # Connect factory on endpoint
    from twisted.internet.endpoints import TCP4ServerEndpoint
    endpoint = TCP4ServerEndpoint(reactor, 2022)
    d = endpoint.listen(factory)
    d.addCallback(lambda port: log.msg("Listening on port."))
    d.addErrback(lambda failure: log.err(failure, "Failed to connect to TestFactory."))
    # Run reactor :)
    reactor.run()
