from unittest import TestCase

from gateway.libs.git.protocol import (
    BaseBufferedSplitter, PacketLineSplitter, GitReceivePackProcessProtocol, GitProcessProtocol)
from gateway.libs.git.utils import *
from gateway.libs.terminal.utils import *
from git.models import Authentication
from joltem.libs import mixer
from joltem.models import User


class __DjangoTestCase(TestCase):

    def setUp(self):
        from django.core.management import call_command
        from django.db.utils import OperationalError

        try:
            mixer.blend(User)
        except OperationalError:
            call_command('syncdb')
            call_command('migrate')


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


class TestSSH(__DjangoTestCase):

    def test_auth_user(self):
        from gateway.libs.factory import portal
        from twisted.cred.credentials import SSHPrivateKey

        authentication = mixer.blend(Authentication, user=mixer.RANDOM)
        credentials = SSHPrivateKey(
            authentication.user.username, None, authentication.key, None, None)

        result = portal.login(credentials, None)
        self.assertEqual(result.result[1].user, authentication.user)

        wrong_user = mixer.blend(User)
        credentials = SSHPrivateKey(
            wrong_user.username, None, 'WRONGBLOB', None, None)
        result = portal.login(credentials, None)
        self.assertTrue(isinstance(result.result.value, Exception))

    def test_auth_project(self):
        from gateway.libs.factory import portal
        from twisted.cred.credentials import SSHPrivateKey

        authentication = mixer.blend(Authentication, project=mixer.RANDOM)
        credentials = SSHPrivateKey(
            'joltem', None, authentication.key, None, None)
        result = portal.login(credentials, None)
        self.assertEqual(result.result[1].project, authentication.project)


class MockGitReceivePackProcessProtocol(GitReceivePackProcessProtocol):

    """ Mock git receive pack process protocol for testing push permission. """

    def __init__(self, authentication, repository): # noqa
        self.avatar = authentication
        self.repository = repository


class MockGitProcessProtocol(GitProcessProtocol):

    """ Mock general git process protocol for testing read permission. """

    def __init__(self, authentication, repository): # noqa
        self.avatar = authentication
        self.repository = repository


class TestReadPermissions(__DjangoTestCase):

    """ Base class for testing read permissions. """

    def test_project_key(self):
        repository1 = mixer.blend('git.repository')
        repository2 = mixer.blend('git.repository')
        authentication = mixer.blend(
            'git.authentication', project=repository1.project)
        pp1 = MockGitProcessProtocol(authentication, repository1)
        self.assertTrue(pp1.has_read_permission())

        pp2 = MockGitProcessProtocol(authentication, repository2)
        self.assertFalse(pp2.has_read_permission())


class TestPrivateProjectReadPermissions(__DjangoTestCase):

    """ Test read permissions of a private project. """

    def setUp(self):
        self.project = mixer.blend('project.project', is_private=True)
        self.repository = mixer.blend('git.repository', project=self.project)

    def assertReadPermission(self, user, expected):
        """ Assert whether or not user has read permissions on the repository.

        :param user:
        :param expected:

        """
        pp = MockGitProcessProtocol(
            mixer.blend('git.authentication', user=user), self.repository)
        self.assertEqual(expected, pp.has_read_permission())

    def test_uninvited(self):
        """ Test that an uninvited can't read repositories. """
        uninvited = mixer.blend('joltem.user')
        self.assertReadPermission(uninvited, False)

    def test_invited(self):
        """ Test that an invited user can read repositories. """
        invited = mixer.blend('joltem.user')
        self.project.invitee_set.add(invited)
        self.project.save()
        self.assertReadPermission(invited, True)

    def test_admin(self):
        """ Test that an admin can read repositories. """
        admin = mixer.blend('joltem.user')
        self.project.admin_set.add(admin)
        self.project.save()
        self.assertReadPermission(admin, True)

    def test_manager(self):
        """ Test that a manager can read repositories. """
        manager = mixer.blend('joltem.user')
        self.project.manager_set.add(manager)
        self.project.save()
        self.assertReadPermission(manager, True)

    def test_developer(self):
        """ Test that a developer can read repositories. """
        developer = mixer.blend('joltem.user')
        self.project.developer_set.add(developer)
        self.project.save()
        self.assertReadPermission(developer, True)


class TestPushPermissions(__DjangoTestCase):

    """ Base class for testing push permissions.

    Using a mock git receive pack process protocol.

    """

    def setUp(self):
        super(TestPushPermissions, self).setUp()
        self.repository = mixer.blend('git.repository')
        self.project = self.repository.project

    def test_mix(self):
        self.assertTrue(self.repository.project)

    def _test_push(self, authentication, reference, expected=True):
        """ Push test generator.

        :param pp: instance of git receive pack process protocol.
        :param reference: reference string passed in packet line.
        :param expected: whether has permissions

        """
        pp = MockGitReceivePackProcessProtocol(authentication, self.repository)
        self.assertEqual(
            pp.has_push_permission(reference, 'na', 'na'), expected)


class TestAdminPushPermissions(TestPushPermissions):

    """ Test an administrator's push permissions.

    Administrator should be able to push to all branches and create tags
    ( test peeled push also ) except for solution branches that belong
    to someone else.

    """

    def setUp(self):
        super(TestAdminPushPermissions, self).setUp()
        self.authentication = mixer.blend(
            'git.authentication', user=mixer.RANDOM)
        self.project.admin_set.add(self.authentication.user)

    def test_push_master(self):
        """ Test admin's ability to push to master. """
        self._test_push(self.authentication, 'refs/heads/master')

    def test_push_develop(self):
        """ Test admin's ability to push to develop. """
        self._test_push(self.authentication, 'refs/heads/develop')

    def test_create_branch(self):
        """ Test admin's ability to create branches. """
        self._test_push(self.authentication, 'refs/heads/release/0.0.1')

    def test_create_tag(self):
        """ Test admin's ability to create tags. """
        self._test_push(self.authentication, 'refs/tags/0.0.1')
        self._test_push(self.authentication, 'refs/tags/0.0.1^{}')

    def test_push_nonexistent_solution(self):
        """ Test push to nonexistent solution's branch. """
        self._test_push(self.authentication, 'refs/heads/s/183895997', False)

    def test_push_another_solution(self):
        """ Test push to an other user's solution.

        Even an administrator should not be able to push to another user's
        solution branch.

        """
        s = mixer.blend('solution.solution')
        self._test_push(self.authentication, s.get_reference(), False)


class TestManagerPushPermissions(TestPushPermissions):

    """ Test an manager's push permissions.

    Manager should be able to push to all branches and create tags
    ( test peeled push also ) except for solution branches that belong
    to someone else.

    """

    def setUp(self):
        super(TestManagerPushPermissions, self).setUp()
        self.authentication = mixer.blend(
            'git.authentication', user=mixer.RANDOM)
        self.project.manager_set.add(self.authentication.user)

    def test_push_master(self):
        """ Test manager's ability to push to master. """
        self._test_push(self.authentication, 'refs/heads/master')

    def test_push_develop(self):
        """ Test manager's ability to push to develop. """
        self._test_push(self.authentication, 'refs/heads/develop')

    def test_create_branch(self):
        """ Test manager's ability to create branches. """
        self._test_push(self.authentication, 'refs/heads/release/0.0.1')

    def test_create_tag(self):
        """ Test manager's ability to create tags. """
        self._test_push(self.authentication, 'refs/tags/0.0.1')
        self._test_push(self.authentication, 'refs/tags/0.0.1^{}')  # peeled version

    def test_push_nonexistent_solution(self):
        """ Test push to nonexistent solution's branch. """
        self._test_push(self.authentication, 'refs/heads/s/183895997', False)

    def test_push_another_solution(self):
        """ Test push to an other user's solution.

        A manager should not be able to push to another user's
        solution branch.

        """
        s = mixer.blend('solution.solution')
        self._test_push(self.authentication, s.get_reference(), False)


class TestDeveloperPushPermissions(TestPushPermissions):

    """ Test an developer's push permissions.

    A developer should be able to push to `develop` branch, but can't
    create new branches or tags.

    """

    def setUp(self):
        super(TestDeveloperPushPermissions, self).setUp()
        self.authentication = mixer.blend(
            'git.authentication', user=mixer.RANDOM)
        self.project.developer_set.add(self.authentication.user)

    def test_push_master(self):
        """ Test developer's inability to push to master. """
        self._test_push(self.authentication, 'refs/heads/master', False)

    def test_push_develop(self):
        """ Test developer's ability to push to develop. """
        self._test_push(self.authentication, 'refs/heads/develop')

    def test_create_branch(self):
        """ Test developer's inability to create branches. """
        self._test_push(self.authentication, 'refs/heads/release/0.0.1', False)

    def test_create_tag(self):
        """ Test developer's inability to create tags. """
        self._test_push(self.authentication, 'refs/tags/0.0.1', False)
        self._test_push(self.authentication, 'refs/tags/0.0.1^{}', False)  # peeled version

    def test_push_nonexistent_solution(self):
        """ Test push to nonexistent solution's branch. """
        self._test_push(self.authentication, 'refs/heads/s/183895997', False)

    def test_push_another_solution(self):
        """ Test push to an other user's solution.

        A developer should not be able to push to another user's
        solution branch.

        """
        s = mixer.blend('solution.solution')
        self._test_push(self.authentication, s.get_reference(), False)
