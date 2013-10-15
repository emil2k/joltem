from unittest import TestCase
from gateway.libs.git.protocol import BaseBufferedSplitter, PacketLineSplitter


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
        from gateway.libs.git.protocol import get_packet_line
        raw = 'ng refs/heads/master permission-denied\n'
        expected = '002bng refs/heads/master permission-denied\n'
        self.assertEqual(get_packet_line(raw), expected)

    def test_parse_line(self):
        from gateway.libs.git.protocol import parse_line
        raw = '003f7217a7c7e582c46cec22a130adf4b9d7d950fba0 refs/heads/master'
        self.assertEqual(parse_line(raw), '7217a7c7e582c46cec22a130adf4b9d7d950fba0 refs/heads/master')

    # todo test parse line size with less than 4 char input

    def test_parse_line_size(self):
        from gateway.libs.git.protocol import parse_line_size
        raw = '003f7217a7c7e582c46cec22a130adf4b9d7d950fba0 refs/heads/master'
        self.assertEqual(parse_line_size(raw), 63)

    def test_parse_line_size_from_bytearray(self):
        from gateway.libs.git.protocol import parse_line_size
        raw = bytearray('003f7217a7c7e582c46cec22a130adf4b9d7d950fba0 refs/heads/master')
        self.assertEqual(parse_line_size(raw), 63)

    def _test_parse_reference(self, raw, expected_object, expected_reference):
        from gateway.libs.git.protocol import parse_reference
        object, reference = parse_reference(raw)
        self.assertEqual(object, expected_object)
        self.assertEqual(reference, expected_reference)

    def test_parse_reference(self):
        self._test_parse_reference('003c525128480b96c89e6418b1e40909bf6c5b2d580f refs/tags/v1.0',
                                   '525128480b96c89e6418b1e40909bf6c5b2d580f',
                                   'refs/tags/v1.0')

    def test_parse_peeled_reference(self):
        """
        A peeled reference is provided when the server is advertising an annotated tag
        The reference will append a ^{} at the end of the reference
        """
        self._test_parse_reference('003fe92df48743b7bc7d26bcaabfddde0a1e20cae47c refs/tags/v1.0^{}',
                                   'e92df48743b7bc7d26bcaabfddde0a1e20cae47c',
                                   'refs/tags/v1.0^{}')

    def test_first_reference(self):
        """
        The first reference in the stream will include capability declarations behind a NULL byte
        """
        self._test_parse_reference('00887217a7c7e582c46cec22a130adf4b9d7d950fba0 HEAD\0multi_ack thin-pack side-band side-band-64k ofs-delta shallow no-progress include-tag',
                                   '7217a7c7e582c46cec22a130adf4b9d7d950fba0',
                                   'HEAD')




