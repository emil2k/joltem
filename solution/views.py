from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.http.response import HttpResponseNotFound
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from git.models import Repository
from project.models import Project
from task.models import Task
from solution.models import Solution, Vote, Comment, CommentVote

@login_required
def new_solution(request, project_name, task_id):
    project = get_object_or_404(Project, name=project_name)
    task = get_object_or_404(Task, id=task_id)
    if task.is_closed:
        return redirect('project:task:task', project_name=project.name, task_id=task.id)
    context = {
        'project': project,
        'project_tab': "solutions",
        'task': task
    }
    if request.POST:
        title = request.POST.get('title')
        description = request.POST.get('description')
        solution = Solution(
            user=request.user,
            task=task,
            project=project,
            title=title,
            description=description
        )
        solution.save()
        return redirect('project:solution:solution', project_name=project.name, solution_id=solution.id)
    return render(request, 'solution/new_solution.html', context)

@login_required
def solution(request, project_name, solution_id):
    project = get_object_or_404(Project, name=project_name)
    solution = get_object_or_404(Solution, id=solution_id)
    user = request.user
    if request.POST:
        # Solution actions
        if request.POST.get('complete') is not None \
                and solution.is_owner(user) \
                and solution.is_accepted:
            from datetime import datetime
            solution.is_completed = True
            solution.time_completed = datetime.now()
            solution.save()
            return redirect('project:solution:solution', project_name=project_name, solution_id=solution_id)
        # Delete solution
        if request.POST.get('delete') is not None:
            solution.delete()
            return redirect('project:solution:all', project_name=project_name)
        # Vote on completed solution
        vote_input = request.POST.get('vote')
        if vote_input is not None:
            # Get or create with other parameters
            try:
                vote = Vote.objects.get(
                    solution_id=solution.id,
                    voter_id=user.id
                )
            except Vote.DoesNotExist:
                vote = Vote(
                    solution=solution,
                    voter=user
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
            vote.voter_impact = user.get_profile().impact
            vote.save()
            return redirect('project:solution:solution', project_name=project_name, solution_id=solution_id)
    # Get current users vote on this solution
    try:
        vote = solution.vote_set.get(voter_id=user.id)
    except Vote.DoesNotExist:
        vote = None
    context = {
        'project': project,
        'solution_tab': "solution",
        'solution': solution,
        'subtasks': solution.tasks.all().order_by('-time_posted'),
        'vote': vote,
        'is_owner': solution.is_owner(user)
    }
    return render(request, 'solution/solution.html', context)

@login_required
def solution_edit(request, project_name, solution_id):
    project = get_object_or_404(Project, name=project_name)
    solution = get_object_or_404(Solution, id=solution_id)
    is_owner = solution.is_owner(request.user)
    if not is_owner:
        return redirect('project:solution:solution', project_name=project_name, solution_id=solution_id)
    if request.POST:
        solution.title = request.POST.get('title')
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

@login_required
def review(request, project_name, solution_id):
    project = get_object_or_404(Project, name=project_name)
    solution = get_object_or_404(Solution, id=solution_id)
    is_owner = solution.is_owner(request.user)
    user = request.user

    # Redirect if solution is not ready for review
    if not solution.is_completed:
            return redirect('project:solution:solution', project_name=project_name, solution_id=solution_id)

    try:
        vote = Vote.objects.get(
            solution_id=solution.id,
            voter_id=user.id
        )
    except Vote.DoesNotExist:
        vote = None
    if request.POST:
        from datetime import datetime
        comment_vote_input = request.POST.get('comment_vote')
        if comment_vote_input:
            comment_id = request.POST.get('comment_id')
            comment = Comment.objects.get(id=comment_id)
            if comment.commenter.id == user.id:
                return redirect('project:solution:review', project_name=project_name, solution_id=solution_id)
            try:
                comment_vote = CommentVote.objects.get(
                    solution_id=solution.id,
                    comment_id=comment.id,
                    voter_id=user.id
                )
                if comment_vote.vote != comment_vote_input:
                    comment_vote.vote = comment_vote_input
                    comment_vote.voter_impact = user.get_profile().impact
                    comment_vote.time_voted = datetime.now()
                    comment_vote.save()
            except CommentVote.DoesNotExist:
                comment_vote = CommentVote(
                    voter=user,
                    voter_impact=user.get_profile().impact,
                    comment=comment,
                    solution=solution,
                    vote=comment_vote_input,
                    time_voted=datetime.now()
                )
                comment_vote.save()
            return redirect('project:solution:review', project_name=project_name, solution_id=solution_id)
        comment_text = request.POST.get('comment')
        if comment_text is not None:
            review_comment = Comment(
                time_commented=datetime.now(),
                commenter=user,
                solution=solution,
                comment=comment_text
            )
            review_comment.save()
            return redirect('project:solution:review', project_name=project_name, solution_id=solution_id)
        vote_input = request.POST.get('vote')
        if vote_input is not None and not is_owner:
            if vote is None:
                vote = Vote(
                    solution=solution,
                    voter=user
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
            vote.voter_impact = user.get_profile().impact
            vote.save()
            return redirect('project:solution:review', project_name=project_name, solution_id=solution_id)

    class CommentHolder:
        def __init__(self, comment, user):
            self.comment = comment
            try:
                self.vote = comment.commentvote_set.get(voter_id=user.id)
            except CommentVote.DoesNotExist:
                self.vote = None
            self.is_author = user.id == comment.commenter.id
            self.vote_count = comment.commentvote_set.count()

    comments = []
    for comment in solution.comment_set.all().order_by('time_commented'):
        comments.append(CommentHolder(comment, user))

    context = {
        'project': project,
        'solution_tab': "review",
        'solution': solution,
        'comments': comments,
        'vote_count': solution.vote_set.count(),
        'accept_votes': solution.vote_set.filter(is_accepted=True),
        'reject_votes': solution.vote_set.filter(is_rejected=True),
        'vote': vote,
        'has_commented': solution.has_commented(user.id),
        'is_owner': is_owner
    }
    return render(request, 'solution/review.html', context)

@login_required
def commits(request, project_name, solution_id, repository_name):
    project = get_object_or_404(Project, name=project_name)
    solution = get_object_or_404(Solution, id=solution_id)

    if project.repository_set.count() == 0:
        return HttpResponseNotFound()
    elif repository_name is not None:
        repository = get_object_or_404(Repository, project_id=project.id, name=repository_name)
    else:
        # Load the latest repository
        repository = project.repository_set.all().order_by('name')[0]

    from pygit2 import Repository as GitRepository, GitError, GIT_SORT_TIME
    git_repo = GitRepository(repository.absolute_path)
    commits = []
    if not git_repo.is_empty:
        try:
            ref = git_repo.lookup_reference('refs/heads/s/%d' % solution.id)
        except KeyError:
            commits = None
        else:
            for commit in git_repo.walk(ref.target.hex, GIT_SORT_TIME):
                commits.append(commit)

    context = {
        'user': request.user,
        'project': project,
        'solution_tab': "commits",
        'solution': solution,
        'repository': repository,
        'repositories': project.repository_set.filter(is_hidden=False).order_by('name'),
        'commits': commits,
    }
    return render(request, 'solution/commits.html', context)


# Generic views
from project.views import ProjectListView


class SolutionListView(ProjectListView):
    model = Solution
    template_name = 'solution/solutions_list.html'
    project_tab = 'solutions'
    solutions_tab = None
    context_object_name = 'solutions'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(SolutionListView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SolutionListView, self).get_context_data(**kwargs)
        context['solutions_tab'] = self.solutions_tab
        return context


def all():
    return SolutionListView.as_view(
        solutions_tab='all',
        queryset=Solution.objects.all().order_by('-time_posted')
    )


def accepted():
    return SolutionListView.as_view(
        solutions_tab='accepted',
        queryset=Solution.objects.all().order_by('-time_accepted')
    )


def completed():
    return SolutionListView.as_view(
        solutions_tab='completed',
        queryset=Solution.objects.all().order_by('-time_completed')
    )