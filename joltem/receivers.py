""" Receivers for updating related models when signals fire. """

from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save


def update_solution_metrics_from_comment(sender, **kwargs):
    """ Update vote metrics for a solution when it's comment is updated.

    Because a rejected vote's validity depends on whether there is a comment.

    """
    from solution.models import Solution  # avoid circular import
    comment = kwargs.get('instance')
    solution_type = ContentType.objects.get_for_model(Solution)
    # todo check that comment is part of the commentable comment_set and not
    # outside of it
    if comment and comment.commentable_id \
            and comment.commentable_type_id == solution_type.id:
        solution = comment.commentable
        solution.acceptance = solution.get_acceptance()
        Solution.objects.filter(pk=solution.pk).update(
            acceptance=solution.acceptance)
        post_save.send(Solution, instance=solution)


def update_voteable_metrics_from_vote(sender, **kwargs):
    """ Update vote metrics (acceptance and impact) and save to DB. """
    vote = kwargs.get('instance')
    if vote and vote.voteable:
        voteable = vote.voteable
        voteable.acceptance = voteable.get_acceptance()
        type(voteable).objects.filter(pk=voteable.pk).update(
            acceptance=voteable.acceptance)
        post_save.send(type(voteable), instance=voteable)


def update_project_impact_from_voteables(sender, **kwargs):
    """ Update project specific impact due to vote on voteable. """
    from project.models import Impact  # avoid circular import

    voteable = kwargs.get('instance')
    if voteable:
        (project_impact, _) = Impact.objects.get_or_create(
            project_id=voteable.project_id,
            user_id=voteable.owner_id
        )
        project_impact.impact = project_impact.get_impact()
        project_impact.completed = project_impact.get_completed()
        project_impact.save()


def update_notification_count(sender, **kwargs):
    """ Update notification count (excluding cleared) for the user. """
    from joltem.models import User
    notification = kwargs.get('instance')
    # Reload user otherwise, the instance send by the signal
    # may be outdated already
    user = User.objects.get(id=notification.user_id)
    user.notifications = user.notification_set.filter(is_cleared=False).count()
    user.save()


def immediately_send_email_about_notification(sender, created=False,
                                              instance=None, **kwargs):
    """ Send email about new notification to user.

    :return Task:

    """

    user = instance.user

    if not user.notify_by_email == user.NOTIFY_CHOICES.immediately \
            or not created:
        return False
    instance.send_mail()
