from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    gravatar_email = models.CharField(max_length=200, null=True,blank=True)
    gravatar_hash = models.CharField(max_length=200, null=True,blank=True)
    # Relations
    user = models.OneToOneField(User, related_name="profile")

    @property
    def impact(self):
        from project.models import Project
        # TODO this should later be switched to project specific impact, but it is fine for now as there is only one project
        impact = 0
        # The admins of the project start with an impact of 1, for weighted voting to be effective
        if self.user.project_set.count() > 0:
            impact = 1
        # Impact from solutions
        for solution in self.user.solution_set.filter():
            # A solutions weighted acceptance must be higher than 90% to count towards impact
            if solution.acceptance < 90:
                continue
            if solution.impact:
                impact += solution.impact
        # Impact from review comments
        for comment in self.user.comment_set.filter():
            if comment.impact:
                impact += comment.impact
        return impact

    @property
    def completed(self):
        return self.user.solution_set.filter(is_completed=True).count()

    def set_gravatar_email(self, gravatar_email):
        """
        Set gravatar email and hash, checks if changed from old
        return boolean whether changed value or not
        """
        if self.gravatar_email != gravatar_email:
            import hashlib
            self.gravatar_email = gravatar_email
            self.gravatar_hash = hashlib.md5(gravatar_email).hexdigest()
            return True
        return False