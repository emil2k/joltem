from django.shortcuts import render, get_object_or_404
from project.models import Project


def project(request, project_name):
    project = get_object_or_404(Project, name=project_name)
    context = {
        'project_tab': "main",
        'project': project
    }
    return render(request, 'project/project.html', context)

# Generic views
from django.views.generic import ListView


class ArgumentsMixin:
    """
    Mixin for views to store request arguments
    """
    def store_arguments(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs


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
