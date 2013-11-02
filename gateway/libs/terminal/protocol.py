from twisted.conch.recvline import HistoricRecvLine

from gateway.libs.terminal.utils import force_ascii

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

    def __init__(self, avatar):
        self.avatar = avatar

    def connectionMade(self):
        HistoricRecvLine.connectionMade(self)
        self.write_to_terminal(GATEWAY_TERMINAL_WELCOME)
        self.terminal.nextLine()
        self.showPrompt()

    def showPrompt(self):
        self.write_to_terminal("joltem : %s > " % self.avatar.user.username)

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
                    self.write_to_terminal("Error: %s" % e)
                    self.terminal.nextLine()
            else:
                self.write_to_terminal("No such command.")
                self.terminal.nextLine()
        self.showPrompt()

    def write_to_terminal(self, raw):
        """ Write back to the terminal.

        The terminal expects ascii encoded text.

        Keyword arguments :
        raw -- the raw input could be either unicode or ascii (default encoding)

        """
        self.terminal.write(force_ascii(raw))

    # Commands

    def do_help(self, cmd=''):
        "Get help on a command. Usage: help command"
        if cmd:
            func = self.getCommandFunc(cmd)
            if func:
                self.write_to_terminal(func.__doc__)
                self.terminal.nextLine()
                return

        publicMethods = filter(
            lambda funcname: funcname.startswith('do_'), dir(self))
        commands = [cmd.replace('do_', '', 1) for cmd in publicMethods]
        self.write_to_terminal("Commands: " + " ".join(commands))
        self.terminal.nextLine()

    def do_echo(self, *args):
        "Echo a string. Usage: echo my line of text"
        self.write_to_terminal(" ".join(args))
        self.terminal.nextLine()

    def do_whoami(self):
        "Prints your user name. Usage: whoami"
        self.write_to_terminal(self.avatar.user.username)
        self.terminal.nextLine()

    def do_quit(self):
        "Ends your session. Usage: quit"
        self.write_to_terminal("Thanks for playing!")
        self.terminal.nextLine()
        self.terminal.loseConnection()

    def do_clear(self):
        "Clears the screen. Usage: clear"
        self.terminal.reset()
