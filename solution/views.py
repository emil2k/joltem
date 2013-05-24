from django.shortcuts import render, redirect, get_object_or_404
from project.models import Project
from task.models import Task
from solution.models import Solution, CompletionVote


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

    if request.POST:
        if request.POST.get('mark_complete') is not None \
                and solution.is_owner(request.user):
            from datetime import datetime
            solution.is_completed = True
            solution.time_completed = datetime.now()
            solution.save()
        vote = request.POST.get('vote')
        if vote is not None:
            # Get or create with other parameters
            try:
                completion_vote = CompletionVote.objects.get(
                    solution_id=solution.id,
                    voter_id=request.user.id
                )
            except CompletionVote.DoesNotExist:
                completion_vote = CompletionVote(
                    solution=solution,
                    voter=request.user
                )
            if vote == 'good':
                completion_vote.vote = 1
            elif vote == 'bad':
                completion_vote.vote = -1
            completion_vote.voter_impact = request.user.get_profile().impact
            completion_vote.save()
            return redirect('project:solution:solution', project_name=project_name, solution_id=solution_id)

    # Get current users vote on this solution
    try:
        vote = solution.completionvote_set.get(voter_id=request.user.id)
    except CompletionVote.DoesNotExist:
        vote = None

    context = {
        'project': project,
        'solution': solution,
        'vote': vote,
        'is_owner': solution.is_owner(request.user)
    }
    return render(request, 'solution/solution.html', context)