""" Protocols. """

from twisted.internet.protocol import ProcessProtocol


class SubprocessProtocol(ProcessProtocol):

    """ A process protocol that runs atop of another process protocol. """

    def __init__(self, protocol):
        """ Initialize subprocess.

        :param protocol: parent process protocol
        :return:

        """
        self.protocol = protocol  # parent process protocol

    def childDataReceived(self, childFD, data):
        """ Pass all data through to parent process protocol.

        :param childFD: file descriptor receiving the data.
        :param data: received data

        """
        self.protocol.childDataReceived(childFD, data)

    def outReceived(self, data):
        """ Pass output to parent process protocol.

        :param data: output data received.

        """
        self.protocol.outReceived(data)

    def errReceived(self, data):
        """ Pass error output to parent process protocol.

        :param data: output data received.

        """
        self.protocol.errReceived(data)


class BaseBufferedSplitter(object):

    """ Mechanism for buffering and splitting up data into splices. """

    def __init__(self, callback):
        self._buffer = bytearray()  # stores data until it is split up
        self._callback = callback  # send splices here

    def data_received(self, data):
        """ Process data. """
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
        """ Make tuple from splices.

        :return tuple:

        """
        return tuple(splice for splice in self._iterate_splices())

    def _iterate_splices(self):
        """ Generator function to splice up the buffer.

        Must implement in extending class.

        """
        raise NotImplementedError("Splitting not implemented.")
