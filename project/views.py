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