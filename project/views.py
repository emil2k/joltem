from django.shortcuts import render, get_object_or_404
from project.models import Project
from task.models import Task
from git.models import Repository


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
    return render(request, 'project/project.html', context)


def tasks(request, project_name):
    project = get_object_or_404(Project, name=project_name)
    context = {
        'project': project
    }
    return render(request, 'project/tasks.html', context)