import struct
import shlex

from zope.interface import implements, Interface
from twisted.python import log
from twisted.internet.interfaces import ITransport
from twisted.conch.ssh.session import SSHSession

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


class BaseBufferedSplitter():
    """
    Mechanism for buffering and splitting up data
    """

    def __init__(self, callback):
        self._buffer = bytearray()  # stores data until it is split up
        self._callback = callback  # send splices here

    def data_received(self, data):
        self._buffer_data(data)
        self._process_buffer()

    def _buffer_data(self, data):
        if type(data) is not bytearray:
            data = bytearray(data)
        self._buffer.extend(data)

    def _process_buffer(self):
        for splice in self._iterate_splices():
            self._callback(splice)

    def splices(self):
        return tuple(splice for splice in self._iterate_splices())

    def _iterate_splices(self):
        """
        Generator function to splice up the buffer, must implement in extending class
        """
        raise NotImplementedError("Splitting not implemented.")


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

    def __init__(self, callback, empty_line_callback):
        BaseBufferedSplitter.__init__(self, callback)
        self._empty_line_callback = empty_line_callback

    def _iterate_splices(self):
        """
        Iterates through a packet line buffer pruning it as it goes.
        Stops at an empty packet line (0000) or if a line is not fully buffered.
        """
        while len(self._buffer) >= 4:
            line_size = parse_line_size(self._buffer)
            if line_size == 0:  # handle empty packet line 0000
                self._buffer = self._buffer[4:]  # adjust buffer, in case it is used again
                self._empty_line_callback()
                break
            elif line_size < 4:
                raise IOError("Packet line size is less than 4 but not 0.")
            if line_size <= len(self._buffer):  # if line fully buffered, flush it out
                found = self._buffer[4:line_size]
                self._buffer = self._buffer[line_size:]
                yield found
            else:
                break  # wait till line is fully buffered


# Git stuff

class GitProcessProtocol(SubprocessProtocol):

    implements(ITransport)

    # ProcessProtocol

    def outReceived(self, data):
        log.msg("\n" + data, system="gateway")
        SubprocessProtocol.outReceived(self, data)

    def errReceived(self, data):
        log.msg("\n" + data, system="gateway")
        SubprocessProtocol.errReceived(self, data)

    # ITransport

    def getHost(self):
        return self.transport.getHost()

    def getPeer(self):
        return self.transport.getPeer()

    def write(self, data):
        log.msg("\n" + data, system="client")
        self.transport.write(data)

    def writeSequence(self, seq):
        raise NotImplementedError("Write sequence is not implemented.")

    def loseConnection(self):
        log.msg("Lose connection.")
        self.transport.loseConnection()


class GitReceivePackProcessProtocol(GitProcessProtocol):
    """
    Protocol for handling a `git receive pack` from a client.
    This command runs when someone attempts to push to the server.

    Buffer and parse clients input then either pass through inputs to the process or kill the connection.
    """

    def __init__(self, protocol):
        GitProcessProtocol.__init__(self, protocol)
        self._splitter = PacketLineSplitter(self.received_packet_line, self.received_empty_packet_line)
        self._pack = False  # indicates whether pack is being transferred
        self._buffer = bytearray()  # buffer clients input here until authorized
        self._abilities = None

    def outReceived(self, data):  # todo
        GitProcessProtocol.outReceived(self, data)

    def write(self, data):
        if not self._pack:
            log.msg("\n" + data, system="client")
            self._splitter.data_received(data)
        self._buffer.extend(data)

    def processEnded(self, reason):
        log.msg("Process ended : %s" % reason, system="client")
        GitProcessProtocol.processEnded(self, reason)

    def processExited(self, reason):
        log.msg("Process exited : %s" % reason, system="client")
        GitProcessProtocol.processExited(self, reason)

    # Receivers

    def received_packet_line(self, line):
        log.msg(line, system="packet-line")
        # todo parse a packet line, end connection if necessary with error message
        if self._abilities is None:
            parts = line.split('\x00')
            if len(parts) == 2:
                line, self._abilities = parts
            elif len(parts) > 2:
                raise IOError('Multiple null bytes in abilities lines.')
        # Parse line
        old_oid, new_oid, reference = line.split(' ')
        log.msg("parse packed line : %s -> %s : %s" % (old_oid, new_oid, reference), system='parser')

    def received_empty_packet_line(self):
        log.msg("empty packet line received.", system="packet-line")
        # Now it should be sending the packet data
        self._pack = True
        # todo Parse the received lines and authorize the request
        # Flush buffer to the process
        GitProcessProtocol.write(self, self._buffer)
        self._buffer = bytearray()