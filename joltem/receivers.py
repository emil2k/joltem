""" Receivers for updating related models when signals fire. """

from django.contrib.contenttypes.models import ContentType

def create_profile(sender, **kw):
    """ Create a user profile when user created. """
    from joltem.models import Profile
    user = kw["instance"]
    if kw["created"]:
        profile = Profile(user=user)
        profile.update().save()


def update_solution_metrics_from_comment(sender, **kwargs):
    """ Update vote metrics for a solution when it's comment is updated.

    Because a rejected vote's validity depends on whether there is a comment.

    """
    from solution.models import Solution  # avoid circular import
    comment = kwargs.get('instance')
    solution_type = ContentType.objects.get_for_model(Solution)
    # todo check that comment is part of the commentable comment_set and not outside of it
    if comment and comment.commentable \
            and comment.commentable_type_id == solution_type.id:  # check if this is a Solution
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


def update_project_impact_from_voteables(sender, **kwargs):
    """ Update project specific impact due to vote on voteable. """
    from project.models import Impact  # avoid circular import
    voteable = kwargs.get('instance')
    if voteable:
        (project_impact, create) = Impact.objects.get_or_create(
            project_id=voteable.project.id,
            user_id=voteable.owner.id
        )
        project_impact.impact = project_impact.get_impact()
        project_impact.save()


def update_notification_count(sender, **kwargs):
    """ Update notification count (excluding cleared) for the user. """
    notification = kwargs.get('instance')
    user = notification.user
    profile = user.get_profile()
    profile.notifications = user.notification_set.filter(is_cleared=False).count()
    profile.save()
