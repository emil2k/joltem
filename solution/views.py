from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.http.response import HttpResponseNotFound
from git.models import Repository
from project.models import Project
from task.models import Task
from solution.models import Solution, Vote, VoteComment


def new_solution(request, project_name, task_id):
    project = get_object_or_404(Project, name=project_name)
    task = get_object_or_404(Task, id=task_id)
    if task.is_closed:
        return redirect('project:task:task', project_name=project.name, task_id=task.id)
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
        # Delete solution
        if request.POST.get('delete') is not None:
            solution.delete()
            return redirect('project:solution:solutions', project_name=project_name)
        # Vote on completed solution
        vote_input = request.POST.get('vote')
        if vote_input is not None:
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
            if vote_input == 'reject':
                vote.is_accepted = False
                vote.is_rejected = True
                vote.vote = None
            else:
                vote.is_accepted = True
                vote.is_rejected = False
                vote.vote = vote_input
            vote.comment = request.POST.get('comment')
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
        'solution_tab': "solution",
        'solution': solution,
        'vote': vote,
        'is_owner': solution.is_owner(request.user)
    }
    return render(request, 'solution/solution.html', context)


def solution_edit(request, project_name, solution_id):
    project = get_object_or_404(Project, name=project_name)
    solution = get_object_or_404(Solution, id=solution_id)
    is_owner = solution.is_owner(request.user)
    if not is_owner:
        return redirect('project:solution:solution', project_name=project_name, solution_id=solution_id)

    if request.POST:
        solution.description = request.POST.get('description')
        solution.save()
        return redirect('project:solution:solution', project_name=project_name, solution_id=solution_id)

    context = {
        'project': project,
        'solution_tab': "solution",
        'solution': solution,
        'is_owner': solution.is_owner(request.user)
    }
    return render(request, 'solution/solution_edit.html', context)


def review(request, project_name, solution_id):
    project = get_object_or_404(Project, name=project_name)
    solution = get_object_or_404(Solution, id=solution_id)
    is_owner = solution.is_owner(request.user)

    # Redirect if solution is not ready for review
    if not solution.is_completed:
            return redirect('project:solution:solution', project_name=project_name, solution_id=solution_id)

    try:
        vote = Vote.objects.get(
            solution_id=solution.id,
            voter_id=request.user.id
        )
    except Vote.DoesNotExist:
        vote = None
    if request.POST:
        from datetime import datetime
        comment = request.POST.get('comment')
        if comment is not None:
            vote_comment = VoteComment(
                time_commented=datetime.now(),
                commenter=request.user,
                solution=solution,
                comment=comment
            )
            vote_comment.save()
            return redirect('project:solution:review', project_name=project_name, solution_id=solution_id)
        vote_input = request.POST.get('vote')
        if vote_input is not None and not is_owner:
            if vote is None:
                vote = Vote(
                    solution=solution,
                    voter=request.user
                )
            if vote_input == 'reject':
                vote.is_accepted = False
                vote.is_rejected = True
                vote.vote = None
            else:
                vote.is_accepted = True
                vote.is_rejected = False
                vote.vote = vote_input
            vote.comment = request.POST.get('comment')
            vote.time_voted = datetime.now()
            vote.voter_impact = request.user.get_profile().impact
            vote.save()
            return redirect('project:solution:review', project_name=project_name, solution_id=solution_id)
    context = {
        'project': project,
        'solution_tab': "review",
        'solution': solution,
        'accept_votes': solution.vote_set.filter(is_accepted=True),
        'reject_votes': solution.vote_set.filter(is_rejected=True),
        'vote': vote,
        'is_owner': is_owner
    }
    return render(request, 'solution/review.html', context)


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
        'solution_tab': "commits",
        'solution': solution,
        'repository': repository,
        'commits': commits,
    }
    return render(request, 'solution/commits.html', context)


def solutions(request, project_name):
    project = get_object_or_404(Project, name=project_name)
    context = {
        'solutions_tab': "all",
        'project_tab': "solutions",
        'project': project,
        'solutions': project.solution_set.all().order_by('-id')
    }
    return render(request, 'solution/solutions_all.html', context)


def solutions_my(request, project_name):
    project = get_object_or_404(Project, name=project_name)
    context = {
        'solutions_tab': "my",
        'project_tab': "solutions",
        'project': project,
        'solutions': request.user.solution_set.filter(project_id=project.id).order_by('-id')
    }
    return render(request, 'solution/solutions_my.html', context)


def solutions_review(request, project_name):
    project = get_object_or_404(Project, name=project_name)
    need_review = []
    for solution in Solution.objects.filter(project_id=project.id, is_completed=True).order_by('-id'):
        if solution.user_id != request.user.id \
                and Vote.objects.filter(solution_id=solution.id, voter_id=request.user.id).count() == 0:
            need_review.append(solution)
    context = {
        'solutions_tab': "review",
        'project_tab': "solutions",
        'project': project,
        'solutions': need_review
    }
    return render(request, 'solution/solutions_review.html', context)