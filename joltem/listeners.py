from django.db.models.signals import post_save, post_delete

from .models import Comment, Notification, Vote
from .receivers import *


# Comment's signals
# -----------------
post_save.connect(update_solution_metrics_from_comment, sender=Comment)

post_delete.connect(update_solution_metrics_from_comment, sender=Comment)

post_save.connect(update_project_impact_from_voteables, sender=Comment)

post_delete.connect(update_project_impact_from_voteables, sender=Comment)


# Notification's signals
# ----------------------
post_save.connect(update_notification_count, sender=Notification)

post_save.connect(
    immediately_send_email_about_notification, sender=Notification)

post_delete.connect(update_notification_count, sender=Notification)


# Vote's signals
# ---------------
post_save.connect(update_voteable_metrics_from_vote, sender=Vote)
post_delete.connect(update_voteable_metrics_from_vote, sender=Vote)