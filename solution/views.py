from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.http.response import HttpResponseNotFound
from git.models import Repository
from project.models import Project
from task.models import Task
from solution.models import Solution, Vote


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
                project=project,
                application=description
            )
            solution.save()
            return redirect('project:task:task', project_name=project.name, task_id=task.id)
    return render(request, 'solution/new_solution.html', context)


def solution(request, project_name, solution_id):
    project = get_object_or_404(Project, name=project_name)
    solution = get_object_or_404(Solution, id=solution_id)

    if request.POST:
        # Solution actions
        if request.POST.get('complete') is not None \
                and solution.is_owner(request.user) \
                and solution.is_accepted:
            from datetime import datetime
            solution.is_completed = True
            solution.time_completed = datetime.now()
            solution.save()
            return redirect('project:solution:solution', project_name=project_name, solution_id=solution_id)
        # TODO edit and delete
        # Vote on completed solution
        if request.POST.get('vote') is not None:
            # Get or create with other parameters
            try:
                vote = Vote.objects.get(
                    solution_id=solution.id,
                    voter_id=request.user.id
                )
            except Vote.DoesNotExist:
                vote = Vote(
                    solution=solution,
                    voter=request.user
                )
            from datetime import datetime
            vote.vote = request.POST.get('vote')
            vote.time_voted = datetime.now()
            vote.voter_impact = request.user.get_profile().impact
            vote.save()
            return redirect('project:solution:solution', project_name=project_name, solution_id=solution_id)

    # Get current users vote on this solution
    try:
        vote = solution.vote_set.get(voter_id=request.user.id)
    except Vote.DoesNotExist:
        vote = None

    context = {
        'project': project,
        'solution': solution,
        'vote': vote,
        'is_owner': solution.is_owner(request.user)
    }
    return render(request, 'solution/solution.html', context)


def commits(request, project_name, solution_id, repository_name):
    project = get_object_or_404(Project, name=project_name)
    solution = get_object_or_404(Solution, id=solution_id)

    if project.repository_set.count() == 0:
        return HttpResponseNotFound()
    elif repository_name is not None:
        repository = get_object_or_404(Repository, project_id=project.id, name=repository_name)
    else:
        # Load the latest repository
        repository = project.repository_set.all()[0]

    from pygit2 import Repository as GitRepository, GitError, GIT_SORT_TIME
    git_repo = GitRepository(repository.absolute_path)
    if not git_repo.is_empty:
        try:
            ref = git_repo.lookup_reference('refs/heads/s/%d' % solution.id)
        except KeyError:
            commits = None
        else:
            commits = []
            for commit in git_repo.walk(ref.target.hex, GIT_SORT_TIME):
                commits.append(commit)

    context = {
        'user': request.user,
        'project': project,
        'solution': solution,
        'repository': repository,
        'commits': commits,
    }
    return render(request, 'solution/commits.html', context)