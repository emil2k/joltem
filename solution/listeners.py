""" Signal's subscribers. """
from django.db.models.signals import post_save, post_delete

from .models import Solution
from joltem import receivers


post_save.connect(
    receivers.update_project_impact_from_voteables, sender=Solution)

post_delete.connect(
    receivers.update_project_impact_from_voteables, sender=Solution)
