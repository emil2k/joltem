from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from project.models import Project
from task.models import Task
from solution.models import Solution


def new(request, project_name, parent_solution_id):
    project = get_object_or_404(Project, name=project_name)
    is_admin = project.is_admin(request.user)
    if not is_admin and parent_solution_id is None:
        return redirect('project:task:list', project_name=project_name)
    context = {
        'project_tab': "tasks",
        'tasks_tab': "new",
        'project': project
    }
    if parent_solution_id is not None:
        parent_solution = Solution.objects.get(id=parent_solution_id)
        context['parent_solution'] = parent_solution
    else:
        parent_solution = None
    # Create a task
    if request.POST and request.POST.get('action') == 'create_task':
        title = request.POST.get('title')
        description = request.POST.get('description')
        if title is not None:
            created_task = Task(
                project=project,
                parent=parent_solution,
                owner=request.user,
                title=title,
                description=description
            )
            created_task.save()
            if parent_solution is not None:
                return redirect('project:solution:solution', project_name=project.name, solution_id=parent_solution_id)
            return redirect('project:task:list', project_name=project.name)
    return render(request, 'task/new_task.html', context)


def task(request, project_name, task_id):
    project = Project.objects.get(name=project_name)
    task = Task.objects.get(id=task_id)

    if request.POST:
        accept = request.POST.get('accept')
        cancel = request.POST.get('cancel')
        if accept is not None:
            from datetime import datetime
            solution = task.solution_set.get(id=accept)
            solution.is_accepted = True
            solution.time_accepted = datetime.now()
            solution.save()
            return redirect('project:task:task', project_name=project_name, task_id=task_id)
        if cancel is not None:
            from datetime import datetime
            solution = task.solution_set.get(id=cancel)
            solution.is_accepted = False
            solution.time_accepted = None
            solution.save()
            return redirect('project:task:task', project_name=project_name, task_id=task_id)

    context = {
        'project': project,
        'task': task,
        'is_owner': task.is_owner(request.user),
    }
    return render(request, 'task/task.html', context)


def list(request, project_name):
    project = get_object_or_404(Project, name=project_name)
    tasks = project.task_set.all().order_by('-id')
    is_admin = project.is_admin(request.user)
    context = {
        'project_tab': "tasks",
        'tasks_tab': "all",
        'project': project,
        'tasks': tasks,
        'is_admin': is_admin,
    }
    return render(request, 'task/list.html', context)


def browse(request, project_name):
    project = get_object_or_404(Project, name=project_name)
    is_admin = project.is_admin(request.user)
    context = {
        'project_tab': "tasks",
        'tasks_tab': "browse",
        'project': project,
        'is_admin': is_admin,
    }
    return render(request, 'task/browse.html', context)
