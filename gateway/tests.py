from unittest import TestCase

from gateway.libs.git.protocol import (
    BaseBufferedSplitter, PacketLineSplitter, GitReceivePackProcessProtocol)
from gateway.libs.git.utils import *
from gateway.libs.terminal.utils import *
from git.models import Authentication
from joltem.libs import mixer
from joltem.models import User


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

    def test_auth_user(self):
        from gateway.libs.ssh.auth import GatewayCredentialChecker

        authentication = mixer.blend(Authentication, user=mixer.RANDOM)
        authentication.user.blob = authentication.key

        checker = GatewayCredentialChecker()

        result = checker.requestAvatarId(authentication.user)
        self.assertEqual(result.result, authentication.user.username)

        wrong_user = mixer.blend(User)
        wrong_user.blob = 'WRONGBLOB'

        result = checker.requestAvatarId(wrong_user)
        self.assertTrue(isinstance(result.value, Exception))

    def test_auth_project(self):
        from gateway.libs.ssh.auth import GatewayCredentialChecker

        authentication = mixer.blend(Authentication, project=mixer.RANDOM)


class MockAvatar(object):

    """ A mock avatar for testing push permissions. """

    def __init__(self, user):
        self.user = user


class MockGitReceivePackProcessProtocol(GitReceivePackProcessProtocol):

    """ Mock git receive pack process protocol for testing push permission. """

    def __init__(self, user, repository): # noqa
        self.avatar = MockAvatar(user)
        self.repository = repository


class TestPushPermissions(TestCase):

    """ Base class for testing push permissions.

    Using a mock git receive pack process protocol.

    """

    def setUp(self):
        self.repository = mixer.blend('git.repository')
        self.project = self.repository.project

    def test_mix(self):
        self.assertTrue(self.repository.project)

    def _test_push(self, user, reference, expected=True):
        """ Push test generator.

        :param pp: instance of git receive pack process protocol.
        :param reference: reference string passed in packet line.
        :param expected: whether has permissions

        """
        pp = MockGitReceivePackProcessProtocol(user, self.repository)
        self.assertEqual(pp.has_push_permission(reference, 'na', 'na'),
                         expected)


class TestAdminPushPermissions(TestPushPermissions):

    """ Test an administrator's push permissions.

    Administrator should be able to push to all branches and create tags
    ( test peeled push also ) except for solution branches that belong
    to someone else.

    """

    def setUp(self):
        super(TestAdminPushPermissions, self).setUp()
        self.admin = mixer.blend('joltem.user')
        self.project.admin_set.add(self.admin)
        self.project.save()

    def test_push_master(self):
        """ Test admin's ability to push to master. """
        self._test_push(self.admin, 'refs/heads/master')

    def test_push_develop(self):
        """ Test admin's ability to push to develop. """
        self._test_push(self.admin, 'refs/heads/develop')

    def test_create_branch(self):
        """ Test admin's ability to create branches. """
        self._test_push(self.admin, 'refs/heads/release/0.0.1')

    def test_create_tag(self):
        """ Test admin's ability to create tags. """
        self._test_push(self.admin, 'refs/tags/0.0.1')
        self._test_push(self.admin, 'refs/tags/0.0.1^{}')  # peeled version

    def test_push_nonexistent_solution(self):
        """ Test push to nonexistent solution's branch. """
        self._test_push(self.admin, 'refs/heads/s/183895997', False)

    def test_push_another_solution(self):
        """ Test push to an other user's solution.

        Even an administrator should not be able to push to another user's
        solution branch.

        """
        s = mixer.blend('solution.solution', owner=mixer.blend('joltem.user'))
        self._test_push(self.admin, s.get_reference(), False)


class TestManagerPushPermissions(TestPushPermissions):

    """ Test an manager's push permissions.

    Manager should be able to push to all branches and create tags
    ( test peeled push also ) except for solution branches that belong
    to someone else.

    """

    def setUp(self):
        super(TestManagerPushPermissions, self).setUp()
        self.manager = mixer.blend('joltem.user')
        self.project.manager_set.add(self.manager)
        self.project.save()

    def test_push_master(self):
        """ Test manager's ability to push to master. """
        self._test_push(self.manager, 'refs/heads/master')

    def test_push_develop(self):
        """ Test manager's ability to push to develop. """
        self._test_push(self.manager, 'refs/heads/develop')

    def test_create_branch(self):
        """ Test manager's ability to create branches. """
        self._test_push(self.manager, 'refs/heads/release/0.0.1')

    def test_create_tag(self):
        """ Test manager's ability to create tags. """
        self._test_push(self.manager, 'refs/tags/0.0.1')
        self._test_push(self.manager, 'refs/tags/0.0.1^{}')  # peeled version

    def test_push_nonexistent_solution(self):
        """ Test push to nonexistent solution's branch. """
        self._test_push(self.manager, 'refs/heads/s/183895997', False)

    def test_push_another_solution(self):
        """ Test push to an other user's solution.

        A manager should not be able to push to another user's
        solution branch.

        """
        s = mixer.blend('solution.solution', owner=mixer.blend('joltem.user'))
        self._test_push(self.manager, s.get_reference(), False)


class TestDeveloperPushPermissions(TestPushPermissions):

    """ Test an developer's push permissions.

    A developer should be able to push to `develop` branch, but can't
    create new branches or tags.

    """

    def setUp(self):
        super(TestDeveloperPushPermissions, self).setUp()
        self.developer = mixer.blend('joltem.user')
        self.project.developer_set.add(self.developer)
        self.project.save()

    def test_push_master(self):
        """ Test developer's inability to push to master. """
        self._test_push(self.developer, 'refs/heads/master', False)

    def test_push_develop(self):
        """ Test developer's ability to push to develop. """
        self._test_push(self.developer, 'refs/heads/develop')

    def test_create_branch(self):
        """ Test developer's inability to create branches. """
        self._test_push(self.developer, 'refs/heads/release/0.0.1', False)

    def test_create_tag(self):
        """ Test developer's inability to create tags. """
        self._test_push(self.developer, 'refs/tags/0.0.1', False)
        self._test_push(self.developer, 'refs/tags/0.0.1^{}', False)  # peeled version

    def test_push_nonexistent_solution(self):
        """ Test push to nonexistent solution's branch. """
        self._test_push(self.developer, 'refs/heads/s/183895997', False)

    def test_push_another_solution(self):
        """ Test push to an other user's solution.

        A developer should not be able to push to another user's
        solution branch.

        """
        s = mixer.blend('solution.solution', owner=mixer.blend('joltem.user'))
        self._test_push(self.developer, s.get_reference(), False)
