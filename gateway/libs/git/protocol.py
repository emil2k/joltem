import struct
import shlex

from zope.interface import implements
from twisted.python import log
from twisted.internet.interfaces import ITransport

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


def parse_line_size(raw, offset=0):
    """
    Parses the line size in bytes out of the git transfer protocol.
    The size of the line is represented in the first 4 bytes
    returns and int in bytes
    """
    hexdigit = struct.unpack('4s', str(raw[offset:offset+4]))[0]
    return int(hexdigit, 16)


# Buffering and splitting

class ISplitter():
    """
    Splitter interfaces, receives splices of data
    """

    def splice_received(self, splice):
        """
        Received a splice of data from the splitter mechanism
        """
        pass


class BaseBufferedSplitter():
    """
    Mechanism for buffering and splitting up data
    """
    splitter = None

    def __init__(self, interface):
        self._buffer = bytearray()  # stores data until it is split up
        self._interface = interface  # ISplitter, send splices here

    def buffer(self, data):
        if type(data) is not bytearray:
            data = bytearray(data)
        indexes = self._contains_splitter(data)
        if len(indexes):
            last = 0
            for index in indexes:
                splice = bytearray()
                if len(self._buffer):
                    splice.extend(self._buffer)
                    self._buffer = bytearray()  # flush buffer
                splice.extend(data[last:index])
                self._interface.splice_received(splice)
                last = index
            self._buffer = data[last + len(self.splitter):]
        else:  # no splits simply buffer
            self._buffer.extend(data)

    def _contains_splitter(self, data):
        """
        Check if a chunk of data contains the splitter, return a tuple of indexes of the splitter
        """
        return tuple(self._seek_split(data))

    def _seek_split(self, data):
        """
        Generator function to seek for indexes of a split, default behaviour is to find instances of the
        `splitter` attribute, but if necessary can completely override this function to seek in anyway necessary
        """
        if not self.splitter:
            raise NotImplementedError("Splitter not set.")
        index = 0
        while index < len(data):
            if data[index:index+len(self.splitter)] == self.splitter:
                found = index
                index += len(self.splitter)
                yield found
            index += 1


class NewLineSplitter(BaseBufferedSplitter):
    splitter = '\n'


class NullByteSplitter(BaseBufferedSplitter):
    splitter = '\x00'


class FlushPacketSplitter(BaseBufferedSplitter):
    splitter = '0000'


class PacketLineSplitter(BaseBufferedSplitter):
    """
    Packet line format is used by gits transfer protocol, here is a description directly
    from git's docs (technical/protocol-common.txt):

    pkt-line Format
    ---------------

    Much (but not all) of the payload is described around pkt-lines.

    A pkt-line is a variable length binary string.  The first four bytes
    of the line, the pkt-len, indicates the total length of the line,
    in hexadecimal.  The pkt-len includes the 4 bytes used to contain
    the length's hexadecimal representation.

    A pkt-line MAY contain binary data, so implementors MUST ensure
    pkt-line parsing/formatting routines are 8-bit clean.

    A non-binary line SHOULD BE terminated by an LF, which if present
    MUST be included in the total length.

    The maximum length of a pkt-line's data component is 65520 bytes.
    Implementations MUST NOT send pkt-line whose length exceeds 65524
    (65520 bytes of payload + 4 bytes of length data).

    Implementations SHOULD NOT send an empty pkt-line ("0004").

    A pkt-line with a length field of 0 ("0000"), called a flush-pkt,
    is a special case and MUST be handled differently than an empty
    pkt-line ("0004").

    ----
      pkt-line     =  data-pkt / flush-pkt

      data-pkt     =  pkt-len pkt-payload
      pkt-len      =  4*(HEXDIG)
      pkt-payload  =  (pkt-len - 4)*(OCTET)

      flush-pkt    = "0000"
    ----

    Examples (as C-style strings):

    ----
      pkt-line          actual value
      ---------------------------------
      "0006a\n"         "a\n"
      "0005a"           "a"
      "000bfoobar\n"    "foobar\n"
      "0004"            ""
    ----
    """
    def _seek_split(self, data):
        index = 0
        if len(self._buffer):
            # Buffer not empty, need to parse buffer to determine size of last line and where to
            # start looking for new lines in the new data
            index = 4 + parse_line_size(self._buffer) - len(self._buffer)
        if index >= 0:
            while index < len(data):
                line_size = parse_line_size(data, index)
                found = index
                index += line_size
                yield found


# Git stuff


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