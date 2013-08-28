from django.shortcuts import render, get_object_or_404
from project.models import Project

from django.views.generic import ListView
from django.views.generic.base import View, TemplateView, ContextMixin, TemplateResponseMixin


class RequestContextMixin(ContextMixin):
    """
    A context mixin that adds the request and the user to the context, and initiates some variables
    """

    def initiate_variables(self, request, *args, **kwargs):
        """Override to initiate other variables"""
        self.request = request
        self.user = request.user

    def get_context_data(self, request, **kwargs):
        kwargs['request'] = request
        kwargs['user'] = request.user
        return super(RequestContextMixin, self).get_context_data(**kwargs)


class RequestTemplateView(TemplateResponseMixin, RequestContextMixin, View):
    """
    A view that renders a template for GET request, where the context depends on the request or the user
    """

    def dispatch(self, request, *args, **kwargs):
        self.initiate_variables(request, *args, **kwargs)
        return super(RequestTemplateView, self).dispatch(request, args, kwargs)

    def get(self, request, *args, **kwargs):
        """Default GET behaviour with the custom context mixin"""
        context = self.get_context_data(request, **kwargs)
        return self.render_to_response(context)


class ProjectObjectMixin(RequestContextMixin):
    """
    Adds project object for manipulating
    """

    def initiate_variables(self, request, *args, **kwargs):
        super(ProjectObjectMixin, self).initiate_variables(request, args, kwargs)
        self.project = Project.objects.get(name=self.kwargs.get("project_name"))
        self.is_admin = self.project.is_admin(request.user.id)

    def get_context_data(self, request, **kwargs):
        kwargs["project"] = self.project
        kwargs["is_admin"] = self.is_admin
        return super(ProjectObjectMixin, self).get_context_data(request, **kwargs)


class ProjectView(ProjectObjectMixin, RequestTemplateView):
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
