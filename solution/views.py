from django.shortcuts import render, redirect, get_object_or_404
from project.models import Project
from task.models import Task
from solution.models import Solution


def new_solution(request, project_name, task_id):
    project = get_object_or_404(Project, name=project_name)
    task = get_object_or_404(Task, id=task_id)
    context = {
        'project': project,
        'task': task
    }
    if request.POST:
        description = request.POST.get('description')
        if description is not None:
            solution = Solution(
                user=request.user,
                task=task,
                description=description
            )
            solution.save()
            return redirect('project:task:task', project_name=project.name, task_id=task.id)
    return render(request, 'solution/new_solution.html', context)


def solution(request, project_name, solution_id):
    project = get_object_or_404(Project, name=project_name)
    solution = get_object_or_404(Solution, id=solution_id)

    if request.POST \
        and request.POST.get('mark_complete') is not None \
            and solution.is_owner(request.user):
        from datetime import datetime
        solution.is_completed = True
        solution.time_completed = datetime.now()
        solution.save()

    context = {
        'project': project,
        'solution': solution,
        'is_owner': solution.is_owner(request.user)
    }
    return render(request, 'solution/solution.html', context)