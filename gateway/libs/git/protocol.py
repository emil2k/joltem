""" Git protocol. """
import shlex
from twisted.internet.error import ProcessDone
from twisted.internet.interfaces import ITransport
from twisted.python import log
from twisted.python.failure import Failure
from zope.interface import implements

from ..utils import SubprocessProtocol, BaseBufferedSplitter
from .utils import get_report, FLUSH_PACKET_LINE, get_packet_line_size
from solution.models import Solution


class PacketLineSplitter(BaseBufferedSplitter):

    r""" Packet line format is used by gits transfer protocol.

    Here is a description directly from git's docs
    (technical/protocol-common.txt):

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
        """ Iterate through a packet line buffer pruning it as it goes.

        Stops at an empty packet line (0000) or if a line is not fully
        buffered.

        """
        while len(self._buffer) >= 4:
            line_size = get_packet_line_size(self._buffer)
            if line_size == 0:  # handle empty packet line 0000
                # adjust buffer, in case it is used again
                self._buffer = self._buffer[4:]
                self._empty_line_callback()
                break
            elif line_size < 4:
                raise IOError("Packet line size is less than 4 but not 0.")

            # if line fully buffered, flush it out
            if line_size <= len(self._buffer):
                found = self._buffer[4:line_size]
                self._buffer = self._buffer[line_size:]
                yield found
            else:
                break  # wait till line is fully buffered


# Git stuff

class GitProcessProtocol(SubprocessProtocol):

    """ Implement Git Protocol. """

    implements(ITransport)

    def __init__(self, protocol, avatar, repository):
        SubprocessProtocol.__init__(self, protocol)
        self.avatar = avatar
        self.repository = repository  # repository model instance

    @staticmethod
    def eof_received():
        """For receiving end of file requests, from the SSH connection."""
        log.msg("End of file received", system="client")

    # ProcessProtocol

    def outReceived(self, data):
        """ Logging. """
        log.msg("\n" + data, system="gateway")
        SubprocessProtocol.outReceived(self, data)

    def errReceived(self, data):
        """ Logging. """
        log.msg("\n" + data, system="gateway error")
        SubprocessProtocol.errReceived(self, data)

    def processEnded(self, reason):
        """ Logging. """
        log.msg("Process ended.", system="gateway")
        SubprocessProtocol.processEnded(self, reason)

    def processExited(self, reason):
        """ Logging. """
        log.msg("Process exited.", system="gateway")
        SubprocessProtocol.processExited(self, reason)

    # ITransport

    def getHost(self):
        """ Proxy to self.transport.

        :return str:

        """
        return self.transport.getHost()

    def getPeer(self):
        """ Proxy to self.transport.

        :return :

        """
        return self.transport.getPeer()

    def write(self, data):
        """ Proxy to self.transport. """
        log.msg("\n" + data, system="client")
        self.transport.write(data)

    def writeSequence(self, seq):
        """ WTF?. """
        raise NotImplementedError("Write sequence is not implemented.")

    def loseConnection(self):
        """ Proxy to self.transport. """
        log.msg("Lose connection.", system="gateway")
        self.transport.loseConnection()


class GitReceivePackProcessProtocol(GitProcessProtocol):

    """ Protocol for handling a `git receive pack` from a client.

    This command runs when someone attempts to push to the server.

    Buffer and parse clients input then either pass through inputs to
    the process or kill the connection.

    """

    OK_PUSH_SEPARATELY = 'ok, push separately'
    PERMISSION_DENIED = 'permission denied'

    def __init__(self, protocol, avatar, repository):
        GitProcessProtocol.__init__(self, protocol, avatar, repository)
        self._splitter = PacketLineSplitter(
            self.received_packet_line, self.received_empty_packet_line)
        self._buffering = True  # whether to buffer
        self._buffer = bytearray()  # buffer clients input until authorized
        self._abilities = None
        self._rejected = False
        # list of push statuses of each reference in order received,
        # (reference, has_permission)
        self._command_statuses = []

    def flush(self):
        """ Flush input buffers into process. """

        self.transport.write(str(self._buffer))
        self._buffer = bytearray()

    def stop_buffering(self):
        """ Flush and stop buffering. """
        self.flush()
        self._buffering = False

    def write(self, data):
        """ Write data to self.transport. """
        if self._buffering:
            log.msg("\n" + data, system="client - buffered")
            self._buffer.extend(data)
            self._splitter.data_received(data)
        elif self._rejected:
            log.msg("\n" + data, system="client - ignored")
        else:
            log.msg("\n" + data, system="client - written")
            self.transport.write(data)

    # Receivers

    def received_packet_line(self, line):
        """ Should have dosctrings. """

        log.msg(line, system="packet-line")
        if self._abilities is None:
            parts = line.split('\x00')
            if len(parts) == 2:
                line, abilities = parts
                self._abilities = shlex.split(str(abilities))
                log.msg("abilities : %s" % self._abilities, system='parser')
            elif len(parts) > 2:
                raise IOError('Multiple null bytes in abilities lines.')
        # Parse line
        self.handle_push_line(line)
        if not self._rejected:
            # Flush buffer to process input, to pass through data
            self.flush()

    def received_empty_packet_line(self):
        """ Should have dosctrings. """

        log.msg("empty packet line received.", system="packet-line")
        self.stop_buffering()  # client should now send PACK data

    def handle_push_line(self, inp):
        """ Process a push request line, end connection if not authorized.

        Input should be a string in the form : {old_oid} {new_oid} {reference}

        Example :
        a45c1e5fdc0938b97b0ac98e1ba6d8cdf81c4f5c f9d4af97f4b0b9e4188597dcff930fababce8fd8 refs/heads/master # noqa

        """
        parts = inp.split(' ')
        if not len(parts) == 3:
            raise IOError("Push line does not contain 3 parts.")
        old, new, ref = parts
        log.msg("parse push line : %s -> %s : %s" %
                (old, new, ref), system='parser')
        if self.has_push_permission(ref, old, new):
            self._command_statuses.append((
                ref, GitReceivePackProcessProtocol.OK_PUSH_SEPARATELY))
        else:
            self._rejected = True
            self._command_statuses.append((
                ref, GitReceivePackProcessProtocol.PERMISSION_DENIED))

    def has_push_permission(self, reference, old_oid, new_oid):
        """ Determine whether the logged user has permission.

        To push to the specified reference, returns a boolean.

        Keyword arguments :
        reference -- pushing to this reference
        old_oid -- the old object id the reference pointed to
        new_oid -- the new object id the reference will point to
                   if the push is accepted

        """
        parts = reference.split('/')
        if parts[0] == 'refs' and parts[1] == 'heads':
            if parts[2] == 'master':
                return self.repository.project.is_admin(self.avatar.user.id)
            elif parts[2] == 's':  # solution branches
                try:
                    solution_id = int(parts[3])
                    solution = Solution.objects.get(id=solution_id)
                except (
                        ValueError,
                        Solution.DoesNotExist,
                        Solution.MultipleObjectsReturned):
                    return False
                else:
                    return solution.is_owner(self.avatar.user)
        return False

    def eof_received(self):
        """ Should have docstring. """

        GitProcessProtocol.eof_received()  # just logging
        if self._rejected:
            # Respond back with a status report
            self.outReceived(get_report(self._command_statuses))
            self.outReceived(FLUSH_PACKET_LINE)
            # Manually end the process
            self.processEnded(Failure(ProcessDone(None)))

    def writeSequence(self, seq):
        """ Redefine abstract method.

        Do nothing for now.

        """
        pass
