from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    impact = models.BigIntegerField(default=1)
    # Relations
    user = models.OneToOneField(User, related_name="profile")