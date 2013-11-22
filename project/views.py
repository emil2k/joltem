""" Project's views. """

from django.views.generic.base import TemplateView
from django.http import Http404
from joltem.views.generic import RequestBaseView
from project.models import Project


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
