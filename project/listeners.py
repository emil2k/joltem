from django.db.models.signals import post_save, post_delete

from .models import Project, Impact, Ratio
from .receivers import *


post_save.connect(update_project_impact_from_project, sender=Project)

post_delete.connect(update_project_impact_from_project, sender=Project)

post_save.connect(update_user_metrics_from_project_impact, sender=Impact)

post_delete.connect(update_user_metrics_from_project_impact, sender=Impact)

post_save.connect(update_project_impact_from_project_ratio, sender=Ratio)

post_delete.connect(update_project_impact_from_project_ratio, sender=Ratio)
