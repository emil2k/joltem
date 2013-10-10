from twisted.python import log
from twisted.internet.interfaces import ITransport
from zope.interface import implements

from gateway.libs.util import SubprocessProtocol


class GitProcessProtocol(SubprocessProtocol):

    implements(ITransport)

    # ProcessProtocol

    def childDataReceived(self, childFD, data):
        log.msg("CHILD DATA RECEIVED : %s" % childFD)
        SubprocessProtocol.childDataReceived(self, childFD, data)

    def outReceived(self, data):
        log.msg("OUT\n"+data)
        SubprocessProtocol.outReceived(self, data)

    def errReceived(self, data):
        log.msg("ERROR\n"+data)
        SubprocessProtocol.errReceived(self, data)

    # ITransport

    def getHost(self):
        return self.transport.getHost()

    def getPeer(self):
        return self.transport.getPeer()

    def write(self, data):
        log.msg("WRITE\n"+data)
        self.transport.write(data)

    def writeSequence(self, seq):
        log.msg("WRITE SEQ\n"+"\n".join(seq))
        self.transport.writeSequence(seq)

    def loseConnection(self):
        log.msg("LOSE CONNECTION")
        self.transport.loseConnection()