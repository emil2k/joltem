""" Project related receivers for handling signals. """


def update_user_metrics_from_project_impact(sender, instance=None, **kwargs):
    """ Update user metrics from project impact. """
    project_impact = instance
    if project_impact:
        project_impact.user.update().save()


def update_project_impact_from_project_ratio(sender, **kwargs):
    """ Update project impact from project vote ratio.

    In case of freezing or unfreezing.

    """
    from project.models import Impact  # avoid circular import

    project_ratio = kwargs.get('instance')
    if project_ratio:
        try:
            project_impact = Impact.objects.get(
                project_id=project_ratio.project_id,
                user_id=project_ratio.user_id
            )
        except (Impact.DoesNotExist, Impact.MultipleObjectsReturned):
            pass
        else:
            project_impact.impact = project_impact.get_impact()
            project_impact.frozen_impact = project_impact.get_frozen_impact()
            project_impact.save()


def update_project_impact_from_project(sender, **kwargs):
    """ Update project specific impact due project modification.

    Mainly change to the admin set.

    """
    from project.models import Impact  # avoid circular import
    project = kwargs.get('instance')
    if project:
        for admin in project.admin_set.all():
            (project_impact, _) = Impact.objects.get_or_create(
                project_id=project.id,
                user_id=admin.id
            )
            project_impact.impact = project_impact.get_impact()
            project_impact.save()
