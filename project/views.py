from django.views.generic.base import TemplateView
from joltem.views.generic import RequestBaseView
from project.models import Project


class ProjectBaseView(RequestBaseView):
    project_tab = None

    def initiate_variables(self, request, *args, **kwargs):
        super(ProjectBaseView, self).initiate_variables(request, args, kwargs)
        self.project = Project.objects.get(
            name=self.kwargs.get("project_name"))
        self.is_admin = self.project.is_admin(request.user.id)

    def get_context_data(self, **kwargs):
        kwargs["project"] = self.project
        kwargs["is_admin"] = self.is_admin
        kwargs["project_tab"] = self.project_tab
        return super(ProjectBaseView, self).get_context_data(**kwargs)


class ProjectView(TemplateView, ProjectBaseView):

    """
    View to display a project's information
    """
    template_name = "project/project.html"
