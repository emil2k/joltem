from django.test import TestCase

from joltem.libs.mock.models import (get_mock_user, get_mock_solution,
                                     get_mock_project)
from joltem.libs.mock.requests import get_mock_get_request
from solution.views import SolutionView


class SolutionViewTestCase(TestCase):

    def setUp(self):
        self.project = get_mock_project(name="apple", title="Macintosh")
        self.admin = get_mock_user("sjobs", first_name="Steve")
        self.project.admin_set.add(self.admin)
        self.project.save()
        self.solution = get_mock_solution(
            self.project, self.admin,
            title="Build a Mouse",
            description="Building thing that eats cheese.")

    def test_get(self):
        """ Test GET request of a solution page. """
        view = SolutionView.as_view()
        response = view(get_mock_get_request(user=self.admin,
                                             is_authenticated=True),
                        project_name="apple", solution_id=self.solution.id)
        response.render()
        self.assertEqual(response.status_code, 200)
        content = response.content
        self.assertInHTML("<h4>Build a Mouse</h4>", content)
        self.assertInHTML("<p>Building thing that eats cheese.</p>", content)
