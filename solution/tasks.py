""" Solution's tasks. """
from django.conf import settings
from django.utils.timezone import timedelta, now

from .models import Solution
from project.models import Impact
from joltem.celery import app


@app.task(ignore_result=True)
def archive_solutions():
    """ Archive solutions after a time period. """
    frontier = now() - timedelta(seconds=settings.SOLUTION_LIFE_PERIOD_SECONDS)
    for solution in Solution.objects.select_related('owner').filter(
            time_completed__lte=frontier):
        archive_solution.delay(solution)


@app.task(ignore_result=True)
def archive_solution(solution):
    """ Make a solution is archived. """
    solution.mark_archived()


@app.task(ignore_result=True)
def review_solutions():
    """ Check solutions with no votes, for defaulting impact.

    After SOLUTION_REVIEW_PERIOD_SECONDS, if there is no valid votes
    the contributor will be awarded the demanded impact. This
    task updates the impact for users that pass this threshold.

    """
    frontier = now() - timedelta(
        seconds=settings.SOLUTION_REVIEW_PERIOD_SECONDS)
    for solution in Solution.objects\
            .filter(
                time_completed__lte=frontier,
                is_completed=True):
        # Update project specific impact
        try:
            impact = Impact.objects.get(user_id=solution.owner_id,
                                        project_id=solution.project_id)
        except Impact.DoesNotExist:
            impact = Impact(user=solution.owner, project=solution.project)
        impact.impact = impact.get_impact()
        impact.save()
