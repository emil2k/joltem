from twisted.conch.recvline import HistoricRecvLine

GATEWAY_TERMINAL_WELCOME = '''
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


class GatewayTerminalProtocol(HistoricRecvLine):

    def __init__(self, user):
        self.user = user

    def connectionMade(self):
        HistoricRecvLine.connectionMade(self)
        self.terminal.write(GATEWAY_TERMINAL_WELCOME)
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
