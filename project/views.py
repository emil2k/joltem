from django.shortcuts import render, get_object_or_404
from project.models import Project

from django.views.generic import ListView
from django.views.generic.base import View, TemplateView, ContextMixin, TemplateResponseMixin


class RequestBaseView(ContextMixin, View):
    """
    A view that renders a template for GET request, where the context depends on the request or the user
    """

    def initiate_variables(self, request, *args, **kwargs):
        """Override to initiate other variables, make sure to call super on first line"""
        self.request = request
        self.user = request.user

    def dispatch(self, request, *args, **kwargs):
        self.initiate_variables(request, *args, **kwargs)
        return super(RequestBaseView, self).dispatch(request, args, kwargs)

    def get_context_data(self, **kwargs):
        kwargs["user"] = self.user
        return super(RequestBaseView, self).get_context_data(**kwargs)


class ProjectBaseView(RequestBaseView):

    def initiate_variables(self, request, *args, **kwargs):
        super(ProjectBaseView, self).initiate_variables(request, args, kwargs)
        self.project = Project.objects.get(name=self.kwargs.get("project_name"))
        self.is_admin = self.project.is_admin(request.user.id)

    def get_context_data(self, **kwargs):
        kwargs["project"] = self.project
        kwargs["is_admin"] = self.is_admin
        return super(ProjectBaseView, self).get_context_data(**kwargs)


class ProjectView(TemplateView, ProjectBaseView):
    """
    View to display a project's information
    """
    template_name = "project/project.html"

#######
# TODO all stuff below is old may need to be removed


class ArgumentsMixin:
    """
    Mixin for views to store request arguments
    """
    def store_arguments(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs


#todo unnecessary eventually
class ProjectListView(ListView, ArgumentsMixin):
    project_tab = None

    def dispatch(self, request, *args, **kwargs):
        self.store_arguments(request, *args, **kwargs)
        project_name = kwargs.get('project_name')
        self.project = get_object_or_404(Project, name=project_name)
        self.user = request.user
        self.is_admin = self.project.is_admin(request.user.id)
        return super(ProjectListView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ProjectListView, self).get_context_data(**kwargs)
        context['project_tab'] = self.project_tab
        context['project'] = self.project
        context['is_admin'] = self.is_admin
        return context
