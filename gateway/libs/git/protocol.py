import struct
import shlex

from zope.interface import implements
from twisted.python import log
from twisted.internet.interfaces import ITransport
from twisted.internet.protocol import Protocol

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


class BaseBufferedProtocol(Protocol):
    """
    Buffered protocol that receives and buffers data

    As data is received it is checked against the `splitters` dictionary if the data contains a splitter,
    the buffer is spliced from the position of last occurrence of that splitter and routed to the appropriate
    function in the extending class in the form of : dataReceived_{name of splitter, key of splitters dict}

    Example `splitters` attribute :

    splitters = {
        'linefeed': '\n',
        'nullbyte': '\x00',
    }
    """

    splitters = {}

    def __init__(self):
        self._buffer = bytearray()

    def dataReceived(self, data):
        self._buffer.extend(data)
        for name, splitter in self.splitters.iteritems():
            indexes = self.containsSplitter(data, splitter) # todo pass an offset, to convert to buffer indexes
            last = 0  # todo convert data indexes to buffer indexes and split the buffer instead
            for index in indexes:  # found splitter
                self.routeSplitData(name, data)  # todo splice data
                last = index

    def routeSplitData(self, name, data):
        """
        Route split data to the appropriate function in the extending class
        """
        f = getattr(self, 'dataReceived_%s' % name, None)
        if callable(f):
            return f(data)
        else:
            raise NotImplementedError("Unimplemented routing method : dataReceived_%s" % name)

    def containsSplitter(self, data, splitter):
        """
        Check if a chunk of data contains the splitter, return a tuple of indexes of all the occurrences of
        the splitter in the chunk of data
        """
        def seekSplitter(data, splitter):
            """Generator to seek for occurrences of the splitter"""
            index = 0
            while index < len(data):
                if data[index:index+len(splitter)] == splitter:
                    found = index
                    index += len(splitter)
                    yield found
                index += 1
        return tuple(seekSplitter(data, splitter))


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