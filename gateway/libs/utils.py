from twisted.internet.protocol import ProcessProtocol


class SubprocessProtocol(ProcessProtocol):
    """
    A process protocol that runs atop of another process protocol,
    by default all methods pass through to parent protocol

    """

    def __init__(self, protocol):
        self.protocol = protocol  # parent process protocol
        if protocol.transport:
            self.makeConnection(protocol.transport)  # connect to remote end

    def childDataReceived(self, childFD, data):
        # Default to ProcessProtocol implementation routes to outReceived and errReceived based on file descriptor
        ProcessProtocol.childDataReceived(self, childFD, data)

    def outReceived(self, data):
        self.protocol.outReceived(data)

    def errReceived(self, data):
        self.protocol.errReceived(data)

    def childConnectionLost(self, childFD):
        self.protocol.childConnectionLost(childFD)

    def inConnectionLost(self):
        self.protocol.inConnectionLost()

    def outConnectionLost(self):
        self.protocol.outConnectionLost()

    def errConnectionLost(self):
        self.protocol.errConnectionLost()

    def processExited(self, reason):
        self.protocol.processExited(reason)

    def processEnded(self, reason):
        self.protocol.processEnded(reason)


class BaseBufferedSplitter():
    """
    Mechanism for buffering and splitting up data into splices

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