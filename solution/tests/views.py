from django.test import TestCase, RequestFactory

from joltem.tests.mocking import (get_mock_user, get_mock_solution,
                                  get_mock_project)
from solution.views import SolutionView


def mock_authentication_middleware(request, user=None):
    """
    A way to mock the authentication network to set
    the request.user setting that many of the views user
    """
    if user:
        request.user = user  # mock authentication middleware
    return request


def get_mock_get_request(path="/fakepath", user=None):
    """
    Return a mock a GET request, to pass to a view
    `path` not important unless the view is using a path argument
    """
    return mock_authentication_middleware(RequestFactory().get(path=path), user)


def get_mock_post_request(path="/fakepath", user=None, data={}):
    """
    Return a mock a POST request, to pass to a view
    `path` not important unless the view is using a path argument
    """
    return mock_authentication_middleware(RequestFactory().post(path=path, data=data), user)


class SolutionViewTestCase(TestCase):

    def setUp(self):
        self.project = get_mock_project(name="apple", title="Macintosh")
        self.admin = get_mock_user("sjobs", first_name="Steve")
        self.project.admin_set.add(self.admin)
        self.project.save()
        self.solution = get_mock_solution(self.project, self.admin,
                                          title="Build a Mouse", description="Building thing that eats cheese.")

    def test_get(self):
        """ Test GET request of a solution page. """
        view = SolutionView.as_view()
        response = view(get_mock_get_request(user=self.admin), project_name="apple", solution_id=self.solution.id)
        response.render()
        self.assertEqual(response.status_code, 200)
        content = response.content
        self.assertInHTML("<h4>Build a Mouse</h4>", content)
        self.assertInHTML("<p>Building thing that eats cheese.</p>", content)
