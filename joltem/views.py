from django.shortcuts import render

from joltem.models import Project, Task, TaskBranch
from git.models import Repository, Branch
from joltem.models import User


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
    context = {}
    if request.POST:
        modified = False;
        if request.POST.get('action') == "assign":
            try:
                assignee = User.objects.get(username=request.POST.get('assignee'))
            except User.DoesNotExist:
                # do nothing
                print "Trying to assign user that does not exist."
            else:
                task_branch.assignees.add(assignee)
                task_branch.save()
                context['assigned'] = assignee
                modified = True
        if request.POST.get('remove') is not None:
            try:
                remove = User.objects.get(username=request.POST.get('remove'))
            except User.DoesNotExist:
                # do nothing
                print "Trying to delete user that does not exist."
            else:
                task_branch.assignees.remove(remove)
                task_branch.save()
                context['removed'] = remove
                modified = True
        if modified:
            from git.gitolite import permissions
            permissions.update_permissions()

    context['task_branch'] = task_branch
    return render(request, 'joltem/task_branch.html', context)
