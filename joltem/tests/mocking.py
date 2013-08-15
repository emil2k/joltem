from django.utils import timezone

from joltem.models import User
from project.models import Project, Impact
from task.models import Task
from solution.models import Solution, Comment, Vote
from git.models import Repository

from joltem.tests import TEST_LOGGER


def get_mock_user(username):
    return User.objects.create_user(username, '%s@gmail.com' % username, '%s_password' % username)


def get_mock_project(name):
    p = Project(
        name=name,
        title="Project : %s" %  name,
    )
    p.save()
    return p


def get_mock_task(project, user, solution=None):
    t = Task(
        title="A task by %s" % user.username,
        owner=user,
        project=project,
        parent=solution
    )
    t.save()
    return t


def get_mock_solution(project, user, task=None, solution=None, is_completed=True):
    s = Solution(
        project=project,
        user=user,
        task=task,
        solution=solution,
        is_completed=is_completed,
        time_completed=timezone.now() if is_completed else None,
    )
    s.save()
    return s


def get_mock_comment(project, user, solution):
    c = Comment(
        project=project,
        user=user,
        solution=solution
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


def get_mock_setup_solution(project_name, username, is_completed=True):
    """
    A shortcut to get a solution
    """
    p = get_mock_project(project_name)
    u = get_mock_user(username)
    t = get_mock_task(p, u)
    s = get_mock_solution(p, u, t, None, is_completed)
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


def debug_votes(voteable):
    TEST_LOGGER.debug("DEBUG VOTES")
    for vote in voteable.vote_set.all():
        TEST_LOGGER.debug("VOTE : %s : %d impact : %d mag" % (vote.voter.username, vote.voter_impact, vote.magnitude))