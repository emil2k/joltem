from unittest import TestCase
from gateway.libs.git.protocol import BaseBufferedSplitter, PacketLineSplitter
from gateway.libs.git.protocol import get_packet_line, get_packet_line_size, get_unpack_status, get_command_status, get_report


class TestingPacketLineSplitter(TestCase):

    def test_buffered(self):
        b = PacketLineSplitter(lambda: None, lambda: None)
        b._buffer_data('0007a')  # bc bytes will arrive later, buffer for now
        self.assertTupleEqual(b.splices(), ())
        b._buffer_data('bc00040006te')  # rest of data arrived
        self.assertTupleEqual(b.splices(), (b'abc', b'', b'te'))

    def test_empty_packet_line(self):
        b = PacketLineSplitter(lambda: None, lambda: None)
        b._buffer_data('0007abc0000')
        self.assertTupleEqual(b.splices(), (b'abc',))


class TestingBaseBufferedSplitter(TestCase):

    def test_buffering(self):
        b = BaseBufferedSplitter(lambda: None)
        self.assertEqual(b._buffer, '')
        b._buffer_data('some test data\x00lol')
        self.assertEqual(b._buffer, 'some test data\x00lol')

    def test_unimplemented_seek_spit(self):
        b = BaseBufferedSplitter(lambda: None)
        b._buffer_data('some test data\x00lol')
        with self.assertRaises(NotImplementedError):
            b._process_buffer()


class GitProtocol(TestCase):

    def test_get_packet_line(self):
        raw = 'ng refs/heads/master permission-denied\n'
        expected = '002bng refs/heads/master permission-denied\n'
        self.assertEqual(get_packet_line(raw), expected)

    def test_get_packet_line_invalid(self):
        raw = 'x' * (int('ffff', 16) - 4 + 1)  # generate string one byte longer than can be packed
        with self.assertRaises(IOError):
            get_packet_line(raw)

    def test_get_packet_line_size(self):
        raw = '003f7217a7c7e582c46cec22a130adf4b9d7d950fba0 refs/heads/master'
        self.assertEqual(get_packet_line_size(raw), 63)

    def test_get_packet_line_size_offset(self):
        raw = 'offset003f7217a7c7e582c46cec22a130adf4b9d7d950fba0 refs/heads/master'
        self.assertEqual(get_packet_line_size(raw, 6), 63)

    def test_get_packet_line_size_from_bytearray(self):
        raw = bytearray('003f7217a7c7e582c46cec22a130adf4b9d7d950fba0 refs/heads/master')
        self.assertEqual(get_packet_line_size(raw), 63)

    def test_get_packet_line_size_invalid(self):
        """Pass an invalid packet line, less than 4 bytes long"""
        with self.assertRaises(IOError):
            get_packet_line_size("001")

    def test_get_unpack_status(self):
        self.assertEqual(get_unpack_status(), 'unpack ok\n')

    def test_get_unpack_status_error(self):
        self.assertEqual(get_unpack_status('permission denied'), 'unpack permission denied\n')

    def test_get_command_status(self):
        self.assertEqual(get_command_status('refs/heads/master'), 'ok refs/heads/master\n')

    def test_get_command_status_error(self):
        self.assertEqual(get_command_status('refs/heads/master', 'permission denied'),
                         'ng refs/heads/master permission denied\n')

    def test_get_report(self):
        """
        exceptions.AssertionError:
        '0076001dunpack permission-denied\n002bng refs/heads/master permission-denied\n0026ng refs/heads/s/1 push-seperately\n0000'
        !=
        '0077\x01001dunpack permission-denied\n002bng refs/heads/master permission-denied\n0026ng refs/heads/s/1 push-seperately\n0000'
        """
        expected = '0077001dunpack permission-denied\n002bng refs/heads/master permission-denied\n0026ng refs/heads/s/1 push-seperately\n0000'
        command_statuses = [
            ('refs/heads/master', 'permission-denied'),
            ('refs/heads/s/1', 'push-seperately'),
        ]
        self.assertEqual(get_report(command_statuses, 'permission-denied'), expected)








