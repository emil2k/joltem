from unittest import TestCase

from gateway.libs.terminal.utils import *
from gateway.libs.git.utils import *
from gateway.libs.git.protocol import BaseBufferedSplitter, PacketLineSplitter
from gateway.libs.git.utils import (
    get_packet_line, get_packet_line_size, get_unpack_status,
    get_command_status, get_report,
)
from git.models import Authentication
from joltem.models import User
from mixer.backend.django import mixer


class TestTerminalProtocolUtilities(TestCase):

    def test_unicode_force_ascii(self):
        self.assertEqual(force_ascii(u'a'), 'a')

    def test_default_force_ascii(self):
        self.assertEqual(force_ascii('a'), 'a')


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


class TestingGitProtocolUtilities(TestCase):

    def test_get_packet_line(self):
        raw = 'ng refs/heads/master permission-denied\n'
        expected = '002bng refs/heads/master permission-denied\n'
        self.assertEqual(get_packet_line(raw), expected)

    def test_get_packet_line_invalid(self):
        # generate string one byte longer than can be packed
        raw = 'x' * (int('ffff', 16) - 4 + 1)
        with self.assertRaises(IOError):
            get_packet_line(raw)

    def test_get_packet_line_size(self):
        raw = '003f7217a7c7e582c46cec22a130adf4b9d7d950fba0 refs/heads/master'
        self.assertEqual(get_packet_line_size(raw), 63)

    def test_get_packet_line_size_offset(self):
        raw = 'offset003f7217a7c7e582c46cec22a130adf4b9d7d950fba0 refs/heads/master'
        self.assertEqual(get_packet_line_size(raw, 6), 63)

    def test_get_packet_line_size_from_bytearray(self):
        raw = bytearray(
            '003f7217a7c7e582c46cec22a130adf4b9d7d950fba0 refs/heads/master')
        self.assertEqual(get_packet_line_size(raw), 63)

    def test_get_packet_line_size_invalid(self):
        """Pass an invalid packet line, less than 4 bytes long"""
        with self.assertRaises(IOError):
            get_packet_line_size("001")

    def test_get_unpack_status_default(self):
        self.assertEqual(get_unpack_status(), 'unpack ok\n')

    def test_get_unpack_status_ok(self):
        self.assertEqual(get_unpack_status('ok'), 'unpack ok\n')

    def test_get_unpack_status_error(self):
        self.assertEqual(get_unpack_status('permission denied'),
                         'unpack permission denied\n')

    def test_get_command_status_default(self):
        self.assertEqual(get_command_status('refs/heads/master'),
                         'ok refs/heads/master\n')

    def test_get_command_status_ok(self):
        self.assertEqual(get_command_status('refs/heads/master', 'ok'),
                         'ok refs/heads/master\n')

    def test_get_command_status_error(self):
        self.assertEqual(
            get_command_status('refs/heads/master', 'permission denied'),
            'ng refs/heads/master permission denied\n')

    def test_get_report(self):
        expected = '0077\x01001dunpack permission-denied\n002bng refs/heads/master permission-denied\n0026ng refs/heads/s/1 push-seperately\n0000'
        command_statuses = [
            ('refs/heads/master', 'permission-denied'),
            ('refs/heads/s/1', 'push-seperately'),
        ]
        self.assertEqual(
            get_report(command_statuses, 'permission-denied'), expected)


class TestSSH(TestCase):

    def setUp(self):
        from django.core.management import call_command
        from django.db.utils import OperationalError

        try:
            mixer.blend(User)
        except OperationalError:
            call_command('syncdb')
            call_command('migrate')

    def test_auth(self):
        from gateway.libs.ssh.auth import GatewayCredentialChecker

        key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQD6qRSV4zDxKXp5vqLiGYj0y3CmoBtXSXuh3ZUyBLwwgw62Wmn1JyqbqlM9dOJysz+gwAi8YlPKCRsAPSr2moR3ThZlk/5qflaiTT4NgGwl/n5XNHVW8Ot5n2KrtnwOMbX7PtSomARhXE9ejpGZwL3SKDaScIGRNbz8cWmVKG1JqdiBo+qTe4HeabREunqztN0Oq44FXCuqlYbvkRud4lkjnzZTP2XL36MfeT3AdCDCs30AgzuVq2nerCnVdRD5v/MkUW2uzonLuJaLDvJZ75ha/vn/l2XINgsfl4SzZtYe50r04YHVflK/p2TdQNhV69eK87WBDwp8xsSR4Rr0swcd joltem@joltem.local"

        authentication = mixer.blend(Authentication)
        authentication.blob = key
        authentication.save()
        authentication.user.blob = key

        checker = GatewayCredentialChecker()

        result = checker.requestAvatarId(authentication.user)
        self.assertEqual(result.result, authentication.user.username)

        wrong_user = mixer.blend(User)
        wrong_user.blob = key

        result = checker.requestAvatarId(wrong_user)
        self.assertTrue(isinstance(result.value, Exception))
