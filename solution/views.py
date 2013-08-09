from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.http.response import HttpResponseNotFound
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from git.models import Repository
from project.models import Project
from task.models import Task
from solution.models import Solution, Comment, Vote


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
            solution.is_completed = True
            solution.time_completed = timezone.now()
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

            if vote_input == 'reject':
                vote.is_accepted = False
                vote.vote = None
            else:
                vote.is_accepted = True
                vote.vote = vote_input
            vote.comment = request.POST.get('comment')
            vote.time_voted = timezone.now()
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
    solution_type = ContentType.objects.get_for_model(solution)
    try:
        vote = Vote.objects.get(
            voteable_type_id=solution_type.id,
            voteable_id=solution.id,
            voter_id=user.id
        )
    except Vote.DoesNotExist:
        vote = None
    if request.POST:
        comment_vote_input = request.POST.get('comment_vote')
        if comment_vote_input is not None:
            comment_vote_input = int(comment_vote_input)
            comment_id = request.POST.get('comment_id')
            comment = Comment.objects.get(id=comment_id)
            if comment.user.id == user.id:
                return redirect('project:solution:review', project_name=project_name, solution_id=solution_id)
            try:
                comment_type = ContentType.objects.get_for_model(comment)
                comment_vote = Vote.objects.get(
                    voteable_type_id=comment_type.id,
                    voteable_id=comment.id,
                    voter_id=user.id
                )
                if comment_vote.magnitude != comment_vote_input:
                    comment_vote.magnitude = comment_vote_input
                    comment_vote.is_accepted = comment_vote_input > 0
                    comment_vote.voter_impact = user.get_profile().impact
                    comment_vote.time_voted = timezone.now()
                    comment_vote.save()
            except Vote.DoesNotExist:
                comment_vote = Vote(
                    voter=user,
                    voter_impact=user.get_profile().impact,
                    voteable=comment,
                    magnitude=comment_vote_input,
                    is_accepted=comment_vote_input > 0,
                    time_voted=timezone.now()
                )
                comment_vote.save()
            return redirect('project:solution:review', project_name=project_name, solution_id=solution_id)
        comment_text = request.POST.get('comment')
        if comment_text is not None:
            review_comment = Comment(
                time_commented=timezone.now(),
                project=project,
                user=user,
                solution=solution,
                comment=comment_text
            )
            review_comment.save()
            return redirect('project:solution:review', project_name=project_name, solution_id=solution_id)
        vote_input = request.POST.get('vote')
        if vote_input is not None and not is_owner:
            vote_input = int(vote_input)
            if vote is None:
                vote = Vote(
                    voteable=solution,
                    voter=user
                )
            vote.is_accepted = vote_input > 0
            vote.magnitude = vote_input
            vote.time_voted = timezone.now()
            vote.voter_impact = user.get_profile().impact
            vote.save()
            return redirect('project:solution:review', project_name=project_name, solution_id=solution_id)

    class CommentHolder:
        def __init__(self, comment, user):
            self.comment = comment
            try:
                self.vote = comment.vote_set.get(voter_id=user.id)
            except Vote.DoesNotExist:
                self.vote = None
            self.is_author = user.id == comment.user.id
            self.vote_count = comment.vote_set.count()

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
        'reject_votes': solution.vote_set.filter(is_accepted=False),
        'vote': vote,
        'has_commented': solution.has_commented(user.id),
        'is_owner': is_owner
    }
    return render(request, 'solution/review.html', context)


@login_required
def commits(request, project_name, solution_id, repository_name):
    project = get_object_or_404(Project, name=project_name)
    solution = get_object_or_404(Solution, id=solution_id)
    repository_set = project.repository_set.filter(is_hidden=False).order_by('name')

    if project.repository_set.count() == 0:
        return HttpResponseNotFound()
    elif repository_name is not None:
        repository = get_object_or_404(Repository, project_id=project.id, name=repository_name)
    else:
        repository = repository_set[0]  # load the default active repository

    from pygit2 import Repository as GitRepository, GIT_SORT_TIME
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
        'repositories': repository_set,
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

    def get_queryset(self):
        if self.solutions_tab == 'completed':
            return self.project.solution_set.filter(is_completed=True).order_by('-time_completed')
        elif self.solutions_tab == 'accepted':
            return self.project.solution_set.filter(is_accepted=True).order_by('-time_accepted')
        else:
            return self.project.solution_set.all().order_by('-time_posted')

    def get_context_data(self, **kwargs):
        context = super(SolutionListView, self).get_context_data(**kwargs)
        context['solutions_tab'] = self.solutions_tab
        return context


def all():
    return SolutionListView.as_view(
        solutions_tab='all'
    )


def accepted():
    return SolutionListView.as_view(
        solutions_tab='accepted'
    )


def completed():
    return SolutionListView.as_view(
        solutions_tab='completed'
    )