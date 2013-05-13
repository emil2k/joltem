from django.shortcuts import render

from joltem.models import Project, Task, TaskBranch
from git.models import Repository, Branch


def home(request):
    context = {
        'projects': Project.objects.all()
    }
    return render(request, 'joltem/home.html', context)


def project(request, project_name):
    project = Project.objects.get(name=project_name)
    context = {
        'project': project
    }
    return render(request, 'joltem/project.html', context)


def task(request, task_id):
    task = Task.objects.get(id=task_id)
    context = {
        'task': task
    }
    return render(request, 'joltem/task.html', context)


def task_branch(request, task_id, task_branch_id):
    task_branch = TaskBranch.objects.get(id=task_branch_id)
    context = {
        'task_branch': task_branch
    }
    return render(request, 'joltem/task_branch.html', context)
