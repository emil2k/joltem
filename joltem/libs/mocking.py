from django.utils import timezone
from django.test import RequestFactory

from joltem.models import User, Vote, Comment
from project.models import Project, Impact
from task.models import Task
from solution.models import Solution

def get_mock_user(username, **extra_fields):
    return User.objects.create_user(username, '%s@gmail.com' % username, '%s_password' % username, **extra_fields)


def get_mock_project(name, title=None):
    title = "Project : %s" % name if not title else title
    p = Project(
        name=name,
        title=title
    )
    p.save()
    return p


def get_mock_task(project, owner,
                  is_reviewed=False, is_accepted=False, is_closed=False,
                  solution=None, author=None):
    author = owner if author is None else author
    t = Task(
        title="A task by %s" % owner.username,
        owner=owner,
        author=author,
        project=project,
        parent=solution,
        is_reviewed=is_reviewed,
        time_reviewed=timezone.now() if is_reviewed else None,
        is_accepted=is_accepted,
        is_closed=is_closed,
        time_closed=timezone.now() if is_closed else None,
    )
    t.save()
    return t


def get_mock_solution(project, owner,
                      is_completed=False, is_closed=False,
                      task=None, solution=None,
                      title=None, description=None):
    s = Solution(
        title=title,
        description=description,
        project=project,
        owner=owner,
        task=task,
        solution=solution,
        is_completed=is_completed,
        time_completed=timezone.now() if is_completed else None,
        is_closed=is_closed,
        time_closed=timezone.now() if is_closed else None,
    )
    s.save()
    return s


def get_mock_comment(project, owner, commentable):
    c = Comment(
        project=project,
        owner=owner,
        commentable=commentable
    )
    c.save()
    return c


def get_mock_vote(voter, voteable, voter_impact, magnitude):
    v = Vote(
        voter_impact=voter_impact,  # mock the voter's impact
        is_accepted=magnitude > 0,
        magnitude=magnitude,
        voter=voter,
        voteable=voteable,
    )
    v.save()
    return v


def get_mock_setup_solution(project_name, username, is_completed=True, is_closed=False):
    """
    A shortcut to get a solution to a task.

    The task is reviewed, accepted, and open

    Keyword arguments :
    project_name -- the name of the project.
    username -- a username for the task & solution owner.
    is_completed -- whether or not the mock solution is_completed.
    is_closed -- whether or not the mock solution is closed.

    """
    p = get_mock_project(project_name)
    u = get_mock_user(username)
    t = get_mock_task(p, u, is_reviewed=True, is_accepted=True)
    s = get_mock_solution(p, u, task=t, is_completed=is_completed, is_closed=is_closed)
    return p, u, t, s


def get_mock_setup_comment(project_name, username):
    """
    A shortcut to get a comment
    """
    p, u, t, s = get_mock_setup_solution(project_name, username)
    c = get_mock_comment(p, u, s)
    return p, u, t, s, c


def load_model(model_class, model_object):
    """
    Load model to check if metrics updated properly
    """
    if model_object:
        return model_class.objects.get(id=model_object.id)


def load_project_impact(project, user):
    """
    Reload votable to check if metrics updated properly
    """
    if project and user:
        return Impact.objects.get(user_id=user.id, project_id=project.id)


# Mock requests
# todo organize this file maybe into separate files

class MockUser(object):

    """ A mock user for testing requests. """

    username = 'johndoe'
    first_name = 'John'
    last_name = 'Doe'
    email = 'johndoe@example.com'
    is_staff = False
    is_active = True
    date_joined = timezone.now()
    _is_authenticated = False  # custom state

    def __init__(self, is_authenticated=False):
        self._is_authenticated = is_authenticated

    def is_authenticated(self):
        """ Return mock authentication state.

        :return: boolean of whether authenticated or not

        """
        return self._is_authenticated

    def get_full_name(self):
        """ Returns the first_name plus the last_name, with a space in between. """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """ Returns the short name for the user. """
        return self.first_name

    def get_profile(self):
        """ Return user's mock profile. """
        pass

def mock_authentication_middleware(request, user=None, is_authenticated=False):
    """
    A way to mock the authentication network to set
    the request.user setting that many of the views user
    """
    if user:
        user.is_authenticated = lambda x: is_authenticated
        request.user = user
    else:
        request.user = MockUser(is_authenticated)
    return request


def get_mock_get_request(path="/fakepath", user=None, is_authenticated=False):
    """
    Return a mock a GET request, to pass to a view
    `path` not important unless the view is using a path argument
    """
    return mock_authentication_middleware(RequestFactory().get(
        path=path), user=user, is_authenticated=is_authenticated)


def get_mock_post_request(path="/fakepath", user=None,
                          is_authenticated=False, data={}):
    """
    Return a mock a POST request, to pass to a view
    `path` not important unless the view is using a path argument
    """
    return mock_authentication_middleware(RequestFactory().post(
        path=path, data=data), user=user, is_authenticated=is_authenticated)