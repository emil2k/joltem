from django.shortcuts import render, get_object_or_404
from solution.models import Solution

def new_solution(request, project_name, task_id):
    context = {}
    # TODO
    return render(request, 'solution/new_solution.html', context)


def solution(request, project_name, solution_id):
    solution = get_object_or_404(Solution)
    context = {}
    # TODO
    return render(request, 'solution/solution.html', context)