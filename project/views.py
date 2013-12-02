# coding: utf-8
""" Project's views. """
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property
from django.views.generic import TemplateView, UpdateView

from .models import Project
from .forms import ProjectSettingsForm
from joltem.views.generic import RequestBaseView, ValidUserMixin


class ProjectMixin(ValidUserMixin):

    """Gets project by name from url."""

    @cached_property
    def project(self):
        """ Return self.project. """
        return get_object_or_404(Project, name=self.kwargs['project_name'])


class ProjectBaseView(RequestBaseView):

    """ Parent class for project-context views. """

    project_tab = None

    def initiate_variables(self, request, *args, **kwargs):
        """ Init current project. """

        super(ProjectBaseView, self).initiate_variables(request, args, kwargs)
        try:
            name = self.kwargs.get("project_name")
            self.project = Project.objects.get(name=name)
        except Project.DoesNotExist:
            raise Http404('Project %s doesn\'t exists.' % name)
        self.is_admin = self.project.is_admin(request.user.id)

    def get_context_data(self, **kwargs):
        """ Get context for templates.

        :return dict:

        """
        kwargs["project"] = self.project
        kwargs["is_admin"] = self.is_admin
        kwargs["project_tab"] = self.project_tab
        return super(ProjectBaseView, self).get_context_data(**kwargs)


class ProjectView(TemplateView, ProjectBaseView):

    """ View to display a project's information. """

    template_name = "project/project.html"

    def get_context_data(self, **kwargs):
        """ Get context for templates.

        :return dict: A context

        """
        key = 'project:overview:%s' % self.project.id
        overview = cache.get(key)
        if not overview:
            overview = self.project.get_overview()
            cache.set(key, overview)
        kwargs.update(overview)
        return super(ProjectView, self).get_context_data(**kwargs)


class ProjectSettingsView(UpdateView, ProjectBaseView):

    """ View to display and modify a project's settings. """

    object = None
    form_class = ProjectSettingsForm
    template_name = "project/settings.html"

    def get_object(self):
        """ Check if user is an admin.

        Only admins are allowed to modify project settings.

        :return Project:

        """
        if self.is_admin:
            return self.project
        raise Http404

    def get_success_url(self):
        """ Get url to redirect to after successful form submission.

        :return str: url of project settings.

        """
        return reverse('project:settings', kwargs={
                'project_name': self.project.name
            })