""" Gateway related tasks. """

from __future__ import absolute_import

from .models import GitReport
from joltem.celery import app


@app.task(ignore_result=True)
def send_new_relic_report():
    """ Send a report to New Relic about gateway. """
    report = GitReport(duration=GitReport.get_duration())
    report.send_report()
