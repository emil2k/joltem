from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from project.models import Project
from task.models import Task
from solution.models import Solution


def new_task(request, project_name, parent_solution_id):
    project = get_object_or_404(Project, name=project_name)
    context = {
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
                title=title,
                description=description
            )
            created_task.save()
            if parent_solution is not None:
                return redirect('project:solution:solution', project_name=project.name, solution_id=parent_solution_id)
            return redirect('project:project', project_name=project.name)
    return render(request, 'task/new_task.html', context)


def task(request, project_name, task_id):
    project = Project.objects.get(name=project_name)
    task = Task.objects.get(id=task_id)
    context = {
        'project': project,
        'task': task
    }
    return render(request, 'task/task.html', context)
