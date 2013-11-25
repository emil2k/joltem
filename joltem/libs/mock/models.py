""" Mocking utils. """

from django.utils import timezone

from joltem.models import User, Vote, Comment
from project.models import Project, Impact
from task.models import Task
from solution.models import Solution


def load_model(model_object):
    """ Reload model to check if metrics updated properly.

    :return Model: Reloaded instance.

    """
    return model_object.__class__.objects.get(id=model_object.id)


def load_project_impact(project, user):
    """ Reload votable to check if metrics updated properly.

    Uses one time on the project's test.

    :return Impact:

    """
    if project and user:
        return Impact.objects.get(user_id=user.id, project_id=project.id)

# Models


def get_mock_user(username, **extra_fields):
    """ Generate User.

    :return User:

    """
    return User.objects.create_user(
        username, '%s@gmail.com' % username,
        '%s_password' % username, **extra_fields)


def get_mock_project(name, title=None):
    """ Generate project.

    :return Project:

    """
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
    """ Generate task.

    :return Task:

    """
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
    """ Generate solution.

    :return Solution:

    """
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
    """ Generate comment.

    :return Comment:

    """
    c = Comment(
        project=project,
        owner=owner,
        commentable=commentable
    )
    c.save()
    return c


def get_mock_vote(voter, voteable, voter_impact, magnitude):
    """ Generate Vote.

    :return Vote:

    """
    v = Vote(
        voter_impact=voter_impact,  # mock the voter's impact
        is_accepted=magnitude > 0,
        magnitude=magnitude,
        voter=voter,
        voteable=voteable,
    )
    v.save()
    return v

# Setups


def get_mock_setup_solution(
        project_name, username, is_completed=True, is_closed=False):
    """ A shortcut to get a solution to a task.

    The task is reviewed, accepted, and open

    Keyword arguments :
    project_name -- the name of the project.
    username -- a username for the task & solution owner.
    is_completed -- whether or not the mock solution is_completed.
    is_closed -- whether or not the mock solution is closed.

    :return (Project, User, Task, Solution):

    """
    p = get_mock_project(project_name)
    u = get_mock_user(username)
    t = get_mock_task(p, u, is_reviewed=True, is_accepted=True)
    s = get_mock_solution(
        p, u, task=t, is_completed=is_completed, is_closed=is_closed)
    return p, u, t, s


def get_mock_setup_comment(project_name, username):
    """ A shortcut to get a comment.

    :return (Project, User, Task, Solution, Comment):

    """
    p, u, t, s = get_mock_setup_solution(project_name, username)
    c = get_mock_comment(p, u, s)
    return p, u, t, s, c
