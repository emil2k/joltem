import struct
import shlex

from twisted.python import log
from twisted.internet.interfaces import ITransport
from zope.interface import implements

from gateway.libs.util import SubprocessProtocol


# Utility functions for parsing git protocol

def parse_reference(raw):
    """
    Parses a reference and the object it is pointing to from the git transfer protocol
    """
    line = parse_line(raw).split('\x00')[0]
    return shlex.split(line)


def parse_line(raw):
    """
    Parses a line out of git transfer protocol
    returns the cleaned up line
    """
    size = parse_line_size(raw)
    return raw[4:size]


def parse_line_size(raw):
    """
    Parses the line size in bytes out of the git transfer protocol.
    The size of the line is represented in the first 4 bytes
    returns and int in bytes
    """
    hexdigit = struct.unpack('4s', raw[:4])[0]
    return int(hexdigit, 16)


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