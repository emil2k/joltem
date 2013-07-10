from django.shortcuts import render, get_object_or_404
from project.models import Project


def project(request, project_name):
    project = get_object_or_404(Project, name=project_name)
    context = {
        'project_tab': "main",
        'project': project
    }
    return render(request, 'project/project.html', context)
