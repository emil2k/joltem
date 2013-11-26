# coding: utf-8
""" Project's views. """
from django.core.cache import cache
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property
from django.views.generic import TemplateView

from .models import Project
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
