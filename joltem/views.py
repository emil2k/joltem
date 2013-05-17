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
    if request.POST:
        action = request.POST.get('action')
        # Create a repository
        if action == 'create_repo':
            name = request.POST.get('name')
            description = request.POST.get('description')
            if name is not None:
                created_repo = Repository(
                    project=project,
                    name=name,
                    description=description
                )
                created_repo.save()
                context['created_repo'] = created_repo
        # Create a task
        if action == 'create_task':
            title = request.POST.get('title')
            description = request.POST.get('description')
            if title is not None:
                created_task = Task(
                    project=project,
                    title=title,
                    description=description
                )
                created_task.save()
                context['created_task'] = created_task
        # Remove repository
        removed_repo_id = request.POST.get('remove_repo')
        if removed_repo_id is not None:
            removed_repo = Repository.objects.get(id=removed_repo_id)
            removed_repo.delete()
            context['removed_repo'] = removed_repo
        # Remove task
        removed_task_id = request.POST.get('remove_task')
        if removed_task_id is not None:
            removed_task = Task.objects.get(id=removed_task_id)
            removed_task.delete()
            context['removed_task'] = removed_task
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
