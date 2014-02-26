""" View related tests for git app. """
from django.core.urlresolvers import reverse

from joltem.libs import mixer
from project.tests.test_views import BaseProjectPermissionsTestCase


class BaseRepositoryPermissionsTestCase(BaseProjectPermissionsTestCase):

    """ Base test case for a repository view's permissions. """

    def setUp(self):
        super(BaseRepositoryPermissionsTestCase, self).setUp()
        self.repository = mixer.blend('git.repository', project=self.project)

    def assertStatusCode(self, url_name):
        """ Assert the status code that should be received.

        :param url_name: url name string to reverse.

        """
        kwargs = dict(project_id=self.project.pk,
                      repository_id=self.repository.pk)
        response = self.client.get(reverse(url_name, kwargs=kwargs))
        self.assertEqual(response.status_code, self.expected_status_code)


class TestRepositoryPermissions(BaseRepositoryPermissionsTestCase):

    """ Test permissions to repository. """

    expected_status_code = 200
    login_user = True
    is_private = False

    def test_repository(self):
        """ Test repository view. """
        self.assertStatusCode('project:git:repository')


class TestRepositoryPermissionAnonymous(TestRepositoryPermissions):

    login_user = False


class TestPrivateRepositoryPermissions(TestRepositoryPermissions):

    expected_status_code = 404
    is_private = True


class TestPrivateRepositoryPermissionsAnonymous(
        TestPrivateRepositoryPermissions):

    login_user = False


class TestPrivateRepositoryPermissionInvitee(TestRepositoryPermissions):

    is_private = True
    group_name = "invitee"


class TestPrivateRepositoryPermissionAdmin(
        TestPrivateRepositoryPermissionInvitee):

    is_private = True
    group_name = "admin"


class TestPrivateRepositoryPermissionManager(
        TestPrivateRepositoryPermissionInvitee):

    is_private = True
    group_name = "manager"


class TestPrivateRepositoryPermissionDeveloper(
        TestPrivateRepositoryPermissionInvitee):

    is_private = True
    group_name = "developer"


class TestRepositoryListPermissions(BaseProjectPermissionsTestCase):

    """ Test permissions to repository lists. """

    expected_status_code = 200
    login_user = True
    is_private = False

    def test_active(self):
        """ Test active repositories list. """
        self.assertStatusCode('project:git:repositories')

    def test_hidden(self):
        """ Test hidden repositories list. """
        self.assertStatusCode('project:git:repositories_hidden')


class TestRepositoryListPermissionsAnonymous(TestRepositoryListPermissions):

    login_user = False


class TestPrivateRepositoryListPermissions(TestRepositoryListPermissions):

    expected_status_code = 404
    is_private = True


class TestPrivateRepositoryListPermissionsAnonymous(
        TestPrivateRepositoryListPermissions):

    login_user = False


class TestPrivateRepositoryListPermissionsInvitee(
        TestPrivateRepositoryListPermissions):

    expected_status_code = 200
    group_name = "invitee"


class TestPrivateRepositoryListPermissionsAdmin(
        TestPrivateRepositoryListPermissionsInvitee):

    group_name = "admin"


class TestPrivateRepositoryListPermissionsManager(
        TestPrivateRepositoryListPermissionsInvitee):

    group_name = "manager"


class TestPrivateRepositoryListPermissionsDeveloper(
        TestPrivateRepositoryListPermissionsInvitee):

    group_name = "developer"


class TestCreateRepositoryPermissions(BaseProjectPermissionsTestCase):

    """ Test permissions to create repository. """

    expected_status_code = 404
    login_user = True
    is_private = False

    def test_create_repository_get(self):
        """ Test GET of create repository page. """
        self.assertStatusCode('project:git:new_repository')

    def test_create_repository_post(self):
        """ Test POST of create repository page. """
        self.assertStatusCode('project:git:new_repository', method='post')


class TestCreateRepositoryPermissionsAnonymous(TestCreateRepositoryPermissions):

    expected_status_code = 302
    login_user = False


class TestCreateRepositoryPermissionsInvitee(TestCreateRepositoryPermissions):

    group_name = "invitee"


class TestCreateRepositoryPermissionsDeveloper(TestCreateRepositoryPermissions):

    group_name = "developer"


class TestCreateRepositoryPermissionsAdmin(TestCreateRepositoryPermissions):

    expected_status_code = 200
    group_name = "admin"


class TestCreateRepositoryPermissionsManager(
        TestCreateRepositoryPermissionsAdmin):

    group_name = "manager"
