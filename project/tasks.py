#!/usr/bin/env python
# coding: utf-8

""" Project's tasks. """
from datetime import timedelta

from collections import defaultdict
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import Context
from django.template.loader import get_template
from django.utils import timezone

from joltem.celery import app


PERIOD = 60 * 60 * 24


@app.task(ignore_result=True)
def prepare_activity_feeds():
    """ Notify subscribers about project's updates. """
    from solution.models import Solution
    from task.models import Task
    from joltem.models import Comment

    from_time = timezone.now() - timedelta(seconds=PERIOD)
    activities = defaultdict(list)

    for solution in Solution.objects.select_related('owner', 'task')\
            .filter(time_updated__gte=from_time):
        activities[solution.project_id].append(solution)

    for task in Task.objects.select_related('owner')\
            .filter(time_updated__gte=from_time):
        activities[task.project_id].append(task)

    for comment in Comment.objects.select_related('owner')\
            .filter(time_commented__gte=from_time):
        activities[comment.project_id].append(comment)

    for project_id, feed in activities.items():
        send_project_feed.delay(project_id, feed)


@app.task(ignore_result=True)
def send_project_feed(project_id, feed):
    """ Send feed to project's subscribers.

    :return bool:

    """

    from .models import Project

    project = Project.objects.get(pk=project_id)
    if not project.subscriber_set.exists():
        return False

    now = timezone.now()
    subject = "%s Activity Feed - %s" % (
        project.title, now.strftime("%d-%m-%Y"))
    context = {
        'subject': subject,
        'project': project,
        'comments': [],
        'solutions': [],
        'tasks': [],
    }
    for o in feed:
        context[type(o).__name__.lower() + 's'].append(o)
    context = Context(context)

    txt = get_template('project/emails/feed.txt').render(context)
    html = get_template('project/emails/feed.html').render(context)
    msg = EmailMultiAlternatives(subject, txt, settings.NOTIFY_FROM_EMAIL)
    msg.attach_alternative(html, "text/html")

    for subscriber in project.subscriber_set.all():
        send_feed_to_subscriber.delay(msg, subscriber.email)


@app.task(ignore_result=True)
def send_feed_to_subscriber(msg, email):
    """ Render email and send to subscriber. """
    msg.to = [email]
    msg.send()
