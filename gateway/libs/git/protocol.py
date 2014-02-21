""" Git protocol. """
import shlex
from twisted.internet.error import ProcessDone
from twisted.internet.interfaces import IProcessTransport
from twisted.internet.protocol import ProcessProtocol
from twisted.python import log
from twisted.python.failure import Failure
from zope.interface import implements

from ..utils import SubprocessProtocol, BaseBufferedSplitter
from .utils import get_report, FLUSH_PACKET_LINE, get_packet_line_size


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

    """ Implement Git Protocol.

    This is a ProcessProtocol for the git process ( git-receive-pack or
    git-upload-pack ) and a wrapper for a Process which implements
    IProcessTransport.

    Essentially creates a middleware that intercepts all communication
    between a git client and server.

    """

    implements(IProcessTransport)

    def __init__(self, protocol, avatar, repository):
        """ Initiate a git process protocol.

        :param protocol: a process protocol
        :param avatar: an instance of GatewayUser
        :param repository: an instance of a Repository model
        :return:

        """
        SubprocessProtocol.__init__(self, protocol)
        self.avatar = avatar
        self.repository = repository
        self.process_transport = None

    def wrap_process_transport(self, transport):
        """ Wrap the process transport to the git process.

        For intercepting writes to file descriptors.

        :param transport: process transport ot git process.

        """
        self.process_transport = transport

    def has_read_permission(self):
        """ Check that the avatar has permission to read.

        An avatar could represent a project deployment or a user key,
        this handles both cases.

        :returns bool:

        """
        if self.avatar.project:  # deployment key
            return self.repository.project == self.avatar.project
        elif self.avatar.user:  # user key
            return self.repository.project.has_access(self.avatar.user.id)

    @staticmethod
    def log(data, system, newline=False):
        """ Logging.

        :param data:
        :param system:
        :param newline: start with newline.
        :return:

        """
        # todo move this out of here and into utils
        output = "\n" if newline else ""
        output += data if len(data) < 8192 else \
            "large data : %d bytes" % len(data)
        log.msg(output, system=system)

    @staticmethod
    def eof_received():
        """ For receiving end of file requests, from the SSH connection. """
        GitProcessProtocol.log("End of file received.", "client")

    # ProcessProtocol

    def childDataReceived(self, childFD, data):
        """ Logging.

        :param childFD: file descriptor.
        :param data: received data.

        """
        self.log(data, "gateway - fd %d" % childFD, True)
        SubprocessProtocol.childDataReceived(self, childFD, data)

    def outReceived(self, data):
        """ Logging. """
        self.log(data, "gateway - out", True)
        SubprocessProtocol.outReceived(self, data)

    def errReceived(self, data):
        """ Logging. """
        self.log(data, "gateway - error", True)
        SubprocessProtocol.errReceived(self, data)

    def processEnded(self, reason):
        """ Logging, git process end.

        Called when the child process exits and all file descriptors associated
        with it have been closed.

        """
        self.log("process ended", "gateway - git process")
        ProcessProtocol.processEnded(self, reason)
        # Signal to the other end that the process has ended through
        # the underlying SSHSessionProcessProtocol
        self.protocol.processEnded(reason)

    def processExited(self, reason):
        """ Logging, git process exit.

        Called when the child process exits.

        """
        self.log("process exited", "gateway - git process")
        ProcessProtocol.processExited(self, reason)

    # todo edit docstrings for these

    # Process

    def write(self, data):
        """ Call this to write to standard input on this process.

        NOTE: This will silently lose data if there is no standard input.

        """
        self.log("write to stdin", "gateway")
        self.writeToChild(0, data)

    # IProcessTransport

    def closeStdin(self):
        """ Close stdin after all data has been written out. """
        self.log("close stdin", "gateway")
        self.process_transport.closeStdin()

    def closeStdout(self):
        """ Close stdout. """
        self.log("close stdout", "gateway")
        self.process_transport.closeStdin()

    def closeStderr(self):
        """ Close stderr. """
        self.log("close stderr", "gateway")
        self.process_transport.closeStderr()

    def closeChildFD(self, descriptor):
        """ Close a file descriptor which is connected to the child process.

        Identified by its FD in the child process.

        """
        self.log("close child fd %d" % descriptor, "gateway")
        self.process_transport.closeChildFD(descriptor)

    def writeToChild(self, childFD, data):
        """ Similar to L{ITransport.write} but also allows the file descriptor.

        In the child process which will receive the bytes to be specified.

        @type childFD: C{int}
        @param childFD: The file descriptor to which to write.

        @type data: C{str}
        @param data: The bytes to write.

        @return: C{None}

        @raise KeyError: If C{childFD} is not a file descriptor that was mapped
            in the child when L{IReactorProcess.spawnProcess} was used to create
            it.

        """
        self.log(data, "client - fd %d" % childFD, True)
        self.process_transport.writeToChild(childFD, data)

    def loseConnection(self):
        """ Close stdin, stderr and stdout. """
        self.log("lose connection", "gateway")
        self.process_transport.loseConnection()

    def signalProcess(self, signalID):
        """ Send a signal to the process.

        @param signalID: can be
          - one of C{"KILL"}, C{"TERM"}, or C{"INT"}.
              These will be implemented in a
              cross-platform manner, and so should be used
              if possible.
          - an integer, where it represents a POSIX
              signal ID.

        @raise twisted.internet.error.ProcessExitedAlready: If the process has
            already exited.
        @raise OSError: If the C{os.kill} call fails with an errno different
            from C{ESRCH}.

        """
        self.log("signal process %d" % signalID, "gateway")
        self.process_transport.signalProcess(signalID)


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
        self.log(self._buffer, "client - flush", True)
        self.process_transport.write(str(self._buffer))
        self._buffer = bytearray()

    def stop_buffering(self):
        """ Flush and stop buffering. """
        self.flush()
        self._buffering = False

    def write(self, data):
        """ Write data to the git process.

        Usually the data is received from the git client.

        While packet lines are being transferred to negotiate what
        to send in the PACK file, the client input is buffered.

        After negotiations end the gateway either accepts or rejects the push
        based on the user's permissions. If the push is rejected the input
        is ignored (not passed to the git process), but if accepted the PACK
        file is directly passed to the git-receive-pack process.

        :param data: data to write.

        """
        if self._buffering:
            self.log(data, "client - buffered", True)
            self._buffer.extend(data)
            self._splitter.data_received(data)
        elif self._rejected:
            self.log(data, "client - ignored", True)
        else:
            self.log(data, "client - written", True)
            self.process_transport.write(data)

    # Receivers

    def received_packet_line(self, line):
        """ Callback for when a packet line has been received. """
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

    def received_empty_packet_line(self):
        """ Callback for when an empty packet line has been received.

        An empty packet line is 0000 and acts a flush statement.

        """
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

        Only the solution owners have writes to push to their solution
        branch. Project admins and managers can push to all other branches.
        Developers can only push to `refs/heads/develop`.

        :param reference: pushing to this reference.
        :param old_oid: the old object id the reference pointed to.
        :param new_oid: the new object id the reference will point to
            if the push is accepted.
        :return bool: whether user has push permissions.

        """
        from solution.models import Solution

        parts = reference.split('/')
        project = self.repository.project

        # Read only for project keys
        if self.avatar.project or not self.avatar.user:
            return False

        user_id = self.avatar.user.id
        if parts[0] == 'refs' and parts[1] == 'heads':
            if parts[2] == 'master':
                return project.is_admin(user_id) or project.is_manager(user_id)

            if parts[2] == 'develop':
                return (
                    project.is_admin(user_id) or
                    project.is_manager(user_id) or
                    project.is_developer(user_id))

            if parts[2] == 's':  # solution branches
                try:
                    solution_id = int(parts[3])
                    solution = Solution.objects.get(id=solution_id)
                except (
                        ValueError,
                        Solution.DoesNotExist,
                        Solution.MultipleObjectsReturned):
                    return False
                else:
                    # Only solution owner can push to solution branch.
                    return solution.is_owner(self.avatar.user)

        # For all other branches and tags creation must be admin or manager.
        return project.is_admin(user_id) or project.is_manager(user_id)

    def eof_received(self):
        """ End of file received on git receive pack.

        The client has signaled that the PACK file transfer is over.
        If the push was rejected the must generate an unpack report, send
        it back, and end the process manually. Otherwise do nothing because
        git-receive-pack process will generate a report itself.

        """
        GitProcessProtocol.eof_received()  # just logging
        if self._rejected:
            # Respond back with a status report
            self.outReceived(get_report(self._command_statuses))
            self.outReceived(FLUSH_PACKET_LINE)
            # Manually end the process
            self.processEnded(Failure(ProcessDone(None)))
