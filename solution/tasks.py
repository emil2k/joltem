""" Solution's tasks. """
from django.conf import settings
from django.utils.timezone import timedelta, now

from .models import Solution
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
