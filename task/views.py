from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from project.models import Project
from task.models import Task
from solution.models import Solution


def new_task(request, project_name, parent_task_id):
    project = Project.objects.get(name=project_name)
    context = {
        'project': project
    }
    if parent_task_id is not None:
        parent = Task.objects.get(id=parent_task_id)
        context['parent'] = parent
    else:
        parent = None
    # Create a task
    if request.POST and request.POST.get('action') == 'create_task':
        title = request.POST.get('title')
        description = request.POST.get('description')
        if title is not None:
            created_task = Task(
                project=project,
                parent=parent,
                title=title,
                description=description
            )
            created_task.save()
            if parent is not None:
                return redirect('project:task:task', project_name=project.name, task_id=parent_task_id)
            return redirect('project:project', project_name=project.name)
    return render(request, 'task/new_task.html', context)


def task(request, project_name, task_id):
    project = Project.objects.get(name=project_name)
    task = Task.objects.get(id=task_id)
    sub_tasks = task.task_set.all()
    context = {
        'project': project,
        'task': task,
        'sub_tasks': sub_tasks
    }
    return render(request, 'task/task.html', context)
