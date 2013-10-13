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