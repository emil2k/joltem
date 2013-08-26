import logging
logger = logging.getLogger("django")


def update_user_metrics_from_project_impact(sender, **kwargs):
    """
    Update user metrics from project impact
    """
    project_impact = kwargs.get('instance')
    logger.info("UPDATE USER STATS from project impact : %s : %d for %s" % (sender, project_impact.project.id, project_impact.user.username))
    if project_impact:
        project_impact.user.get_profile().update().save()


def update_project_impact_from_project(sender, **kwargs):
    """
    Update project specific impact due project modification, mainly change to the admin set
    """
    from project.models import Impact
    project = kwargs.get('instance')
    logger.info("UPDATE PROJECT IMPACT from project : %s" % sender)
    if project:
        for admin in project.admin_set.all():
            logger.info("UPDATE PROJECT IMPACT for %s" % admin.username)
            (project_impact, create) = Impact.objects.get_or_create(
                project_id=project.id,
                user_id=admin.id
            )
            project_impact.impact = project_impact.get_impact()
            project_impact.save()