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
        'project': project,
        'is_admin': is_admin,
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
    project = get_object_or_404(Project, name=project_name)
    task = get_object_or_404(Task, id=task_id)
    is_owner = task.is_owner(request.user)
    if request.POST:
        if not is_owner:
            return redirect('project:task:task', project_name=project_name, task_id=task_id)
        accept = request.POST.get('accept')
        from datetime import datetime
        if accept is not None:
            solution = task.solution_set.get(id=accept)
            solution.is_accepted = True
            solution.time_accepted = datetime.now()
            solution.save()
            return redirect('project:task:task', project_name=project_name, task_id=task_id)
        cancel = request.POST.get('cancel')
        if cancel is not None:
            solution = task.solution_set.get(id=cancel)
            solution.is_accepted = False
            solution.time_accepted = None
            solution.save()
            return redirect('project:task:task', project_name=project_name, task_id=task_id)
        if request.POST.get('close'):
            task.is_closed = True
            task.time_closed = datetime.now()
            task.save()
            return redirect('project:task:task', project_name=project_name, task_id=task_id)

    context = {
        'project_tab': "tasks",
        'project': project,
        'task': task,
        'solutions': task.solution_set.all().order_by('-id'),
        'is_owner': is_owner,
    }
    return render(request, 'task/task.html', context)


def edit(request, project_name, task_id):
    project = get_object_or_404(Project, name=project_name)
    task = get_object_or_404(Task, id=task_id)
    is_owner = task.is_owner(request.user)
    if request.POST:
        if not is_owner:
            return redirect('project:task:task', project_name=project_name, task_id=task_id)
        title = request.POST.get('title')
        if title is not None:
            task.title = title
            task.description = request.POST.get('description')
            task.save()
            return redirect('project:task:task', project_name=project_name, task_id=task_id)
    context = {
        'project_tab': "tasks",
        'tasks_tab': "my",
        'project': project,
        'task': task,
        'is_owner': is_owner,
    }
    return render(request, 'task/task_edit.html', context)


def list(request, project_name, parent_task_id):
    project = get_object_or_404(Project, name=project_name)
    is_admin = project.is_admin(request.user)
    context = {
        'project_tab': "tasks",
        'tasks_tab': "open",
        'project': project,
        'is_admin': is_admin,
    }
    if parent_task_id is not None:
        parent_task = get_object_or_404(Task, id=parent_task_id)
        context['parent_task'] = parent_task

        class SubtaskGroup:
            def __init__(self, solution, tasks):
                self.solution = solution
                self.tasks = tasks
        subtask_groups = []
        for solution in parent_task.solution_set.all().order_by('-id'):
            open_subtasks = solution.tasks.filter(is_closed=False).order_by('-id')
            if open_subtasks.count() > 0:
                subtask_group = SubtaskGroup(solution, open_subtasks)
                subtask_groups.append(subtask_group)
        context['subtask_groups'] = subtask_groups
        return render(request, 'task/list_parent.html', context)
    else:
        context['tasks'] = project.task_set.filter(is_closed=False).order_by('-id')
        return render(request, 'task/list.html', context)


def browse(request, project_name):
    project = get_object_or_404(Project, name=project_name)
    is_admin = project.is_admin(request.user)
    context = {
        'project_tab': "tasks",
        'tasks_tab': "browse",
        'project': project,
        'tasks': project.task_set.filter(parent=None, is_closed=False),
        'is_admin': is_admin,
    }
    return render(request, 'task/list.html', context)


def my(request, project_name):
    project = get_object_or_404(Project, name=project_name)
    is_admin = project.is_admin(request.user)
    context = {
        'project_tab': "tasks",
        'tasks_tab': "my",
        'project': project,
        'tasks': project.task_set.filter(owner=request.user),
        'is_admin': is_admin,
    }
    return render(request, 'task/list.html', context)


def closed(request, project_name):
    project = get_object_or_404(Project, name=project_name)
    is_admin = project.is_admin(request.user)
    context = {
        'project_tab': "tasks",
        'tasks_tab': "closed",
        'project': project,
        'tasks': project.task_set.filter(is_closed=True),
        'is_admin': is_admin,
    }
    return render(request, 'task/list.html', context)