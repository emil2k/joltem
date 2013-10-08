from twisted.python import log
from twisted.internet.defer import succeed, fail
from twisted.conch.ssh.transport import SSHClientTransport
from twisted.conch.error import ConchError
from twisted.conch.ssh.common import NS
from twisted.conch.ssh.connection import SSHConnection
from twisted.conch.ssh.userauth import SSHUserAuthClient
from twisted.conch.ssh.keys import Key
from twisted.conch.ssh.session import SSHSession

CLIENT_PUBLIC_KEY = 'ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAGEArzJx8OYOnJmzf4tfBEvLi8DVPrJ3\
/c9k2I/Az64fxjHf9imyRJbixtQhlH9lfNjUIx+4LmrJH5QNRsFporcHDKOTwTTYLh5KmRpslkYHR\
ivcJSkbh/C+BR3utDS555mV'

CLIENT_PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIByAIBAAJhAK8ycfDmDpyZs3+LXwRLy4vA1T6yd/3PZNiPwM+uH8Yx3/YpskSW
4sbUIZR/ZXzY1CMfuC5qyR+UDUbBaaK3Bwyjk8E02C4eSpkabJZGB0Yr3CUpG4fw
vgUd7rQ0ueeZlQIBIwJgbh+1VZfr7WftK5lu7MHtqE1S1vPWZQYE3+VUn8yJADyb
Z4fsZaCrzW9lkIqXkE3GIY+ojdhZhkO1gbG0118sIgphwSWKRxK0mvh6ERxKqIt1
xJEJO74EykXZV4oNJ8sjAjEA3J9r2ZghVhGN6V8DnQrTk24Td0E8hU8AcP0FVP+8
PQm/g/aXf2QQkQT+omdHVEJrAjEAy0pL0EBH6EVS98evDCBtQw22OZT52qXlAwZ2
gyTriKFVoqjeEjt3SZKKqXHSApP/AjBLpF99zcJJZRq2abgYlf9lv1chkrWqDHUu
DZttmYJeEfiFBBavVYIF1dOlZT0G8jMCMBc7sOSZodFnAiryP+Qg9otSBjJ3bQML
pSTqy7c3a2AScC/YyOwkDaICHnnD3XyjMwIxALRzl0tQEKMXs6hH8ToUdlLROCrP
EhQ0wahUTCk1gKA4uPD6TMTChavbh4K63OvbKg==
-----END RSA PRIVATE KEY-----"""


class GatewayClientTransport(SSHClientTransport):

    def verifyHostKey(self, hostKey, fingerprint):
        log.msg("Verify host key, fingerprint : %s" % fingerprint)
        if fingerprint == "e7:e2:fb:93:73:39:c3:76:23:dc:13:e1:3d:2d:a5:64":
            return succeed(True)
        else:
            return fail(ConchError)

    def connectionSecure(self):
        self.requestService(GatewayClientUserAuth('emil', GatewayClientConnection()))


class GatewayClientUserAuth(SSHUserAuthClient):

    def getPassword(self, prompt=None):
        return  # not supported

    def getPublicKey(self):
        return Key.fromString(data=CLIENT_PUBLIC_KEY).blob()

    def getPrivateKey(self):
        return succeed(Key.fromString(data=CLIENT_PRIVATE_KEY).keyObject)


class GatewayClientConnection(SSHConnection):

    def serviceStarted(self):
        self.openChannel(GatewayClientChannel(conn=self))


class GatewayClientChannel(SSHSession):

    def channelOpen(self, specificData):
        self.runHelp()

    def runHelp(self):
        d = self.conn.sendRequest(self, 'exec', NS('help'), wantReply=True)
        d.addCallback(self._cbSendRequest)

    def _cbSendRequest(self, ignored):
        # print "SSH SESSION TRANSPORT : %s" % self.client.transport
        self.loseConnection()
