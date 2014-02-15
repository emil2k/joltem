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


@app.task(ignore_result=True)
def review_solutions():
    """ Make a solution is reviewed automatically. """
    from django.db.models import Count
    frontier = now() - timedelta(
        seconds=settings.SOLUTION_REVIEW_PERIOD_SECONDS)
    for solution in Solution.objects.select_related('owner')\
            .annotate(num_votes=Count('vote_set'))\
            .filter(
                time_completed__lte=frontier,
                is_completed=True,
                num_votes=0):
        solution.mark_close()
