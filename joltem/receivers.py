""" Receivers for updating related models when signals fire. """

from django.contrib.contenttypes.models import ContentType


def update_solution_metrics_from_comment(sender, **kwargs):
    """ Update vote metrics for a solution when it's comment is updated.

    Because a rejected vote's validity depends on whether there is a comment.

    """
    from solution.models import Solution  # avoid circular import
    comment = kwargs.get('instance')
    solution_type = ContentType.objects.get_for_model(Solution)
    # todo check that comment is part of the commentable comment_set and not
    # outside of it
    if comment and comment.commentable \
            and comment.commentable_type_id == solution_type.id:
        solution = comment.commentable
        solution.acceptance = solution.get_acceptance()
        solution.impact = solution.get_impact()
        solution.save()


def update_voteable_metrics_from_vote(sender, **kwargs):
    """ Update vote metrics (acceptance and impact) and save to DB. """
    vote = kwargs.get('instance')
    if vote and vote.voteable:
        voteable = vote.voteable
        voteable.acceptance = voteable.get_acceptance()
        voteable.impact = voteable.get_impact()
        voteable.save()


def update_project_metrics_from_vote(sender, **kwargs):
    """ Update project specific vote ratio due to vote.

    :param sender: class of the sender
    :param kwargs:

    """
    from solution.models import Solution  # avoid circular import
    from project.models import Ratio
    solution_type = ContentType.objects.get_for_model(Solution)
    vote = kwargs.get('instance')
    if vote and vote.voteable and vote.voteable_type_id == solution_type.id:
        solution = vote.voteable
        Ratio.update(solution.project_id, solution.owner_id)
        Ratio.update(solution.project_id, vote.voter_id)


def update_project_metrics_from_comment(sender, **kwargs):
    """ Update project specific vote ratio due to comment.

    For updating votes ratio metric when a comment is added, making
    the vote valid.

    :param sender: class of the Sender
    :param kwargs:

    """
    from solution.models import Solution  # avoid circular import
    from project.models import Ratio
    solution_type = ContentType.objects.get_for_model(Solution)
    comment = kwargs.get('instance')
    if comment and comment.commentable and \
            comment.commentable_type_id == solution_type.id:
        solution = comment.commentable
        Ratio.update(solution.project_id, solution.owner_id)
        Ratio.update(solution.project_id, comment.owner_id)


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
        project_impact.frozen_impact = project_impact.get_frozen_impact()
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


def immediately_senf_email_about_notification(sender, created=False,
                                              instance=None, **kwargs):
    """ Send email about new notification to user.

    :return Task:

    """

    user = instance.user

    if not user.notify_by_email == user.NOTIFY_CHOICES.immediately \
            or not created:
        return False
    instance.send_mail()
