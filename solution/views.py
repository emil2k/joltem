from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.http.response import HttpResponseNotFound, Http404
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType

from joltem.models import Vote, Comment
from joltem.holders import CommentHolder
from git.models import Repository
from project.models import Project
from task.models import Task
from solution.models import Solution

import logging
logger = logging.getLogger('django')


# todo convert to class based views

from project.views import ProjectObjectMixin, RequestTemplateView


class SolutionObjectMixin(ProjectObjectMixin):
    """
    Adds project object for manipulating
    """

    def initiate_variables(self, request, *args, **kwargs):
        super(SolutionObjectMixin, self).initiate_variables(request, args, kwargs)
        self.solution = get_object_or_404(Solution, id=self.kwargs.get("solution_id"))
        self.is_owner = self.solution.is_owner(self.user)

    def get_context_data(self, request, **kwargs):
        kwargs["solution"] = self.solution
        # Get the users vote on this solution # todo is this necessary on each page or only on review page
        try:
            kwargs["vote"] = self.solution.vote_set.get(voter_id=self.user.id)
        except Vote.DoesNotExist:
            kwargs["vote"] = None

        kwargs["comments"] = CommentHolder.get_comments(self.solution.comment_set.all().order_by('time_commented'), self.user)
        kwargs["subtasks"] = self.solution.subtask_set.all().order_by('-time_posted')
        kwargs["suggested_solutions"] = self.solution.solution_set.all().order_by('-time_posted')
        kwargs["is_owner"] = self.solution.is_owner(self.user)
        kwargs["is_acceptor"] = self.solution.is_acceptor(self.user)

        return super(SolutionObjectMixin, self).get_context_data(request, **kwargs)


class SolutionView(SolutionObjectMixin, RequestTemplateView):
    """
    View to display solution's information
    """
    template_name = "solution/solution.html"

    def post(self, request, *args, **kwargs):
        # Acceptance of suggested solution
        accept = request.POST.get('accept')
        unaccept = request.POST.get('unaccept')
        if (accept or unaccept) and self.solution.is_acceptor(self.user):
            if accept:
                self.solution.is_accepted = True
                self.solution.time_accepted = timezone.now()
            else:
                self.solution.is_accepted = False
                self.solution.time_accepted = None
            self.solution.save()

        # Mark solution complete
        if request.POST.get('complete') \
                and not self.solution.is_completed \
                and not self.solution.is_closed \
                and self.solution.is_owner(self.user):
            self.solution.is_completed = True
            self.solution.time_completed = timezone.now()
            self.solution.save()

        # Mark solution incomplete
        if request.POST.get('incomplete') \
                and self.solution.is_completed \
                and not self.solution.is_closed \
                and self.solution.is_owner(self.user):
            self.solution.is_completed = False
            self.solution.time_completed = None
            self.solution.save()

        # Close solution
        if request.POST.get('close') \
                and not self.solution.is_completed \
                and not self.solution.is_closed \
                and self.solution.is_owner(self.user):
            self.solution.is_closed = True
            self.solution.time_closed = timezone.now()
            self.solution.save()

        # Reopen solution
        if request.POST.get('reopen') \
                and self.solution.is_closed \
                and self.solution.is_owner(self.user):
            self.solution.is_closed = False
            self.solution.time_closed = None
            self.solution.save()

        # Vote on completed solution
        vote_input = request.POST.get('vote')
        if vote_input and not self.solution.is_owner(self.user):
            # Get or create with other parameters
            try:
                vote = Vote.objects.get(
                    solution_id=self.solution.id,
                    voter_id=self.user.id
                )
            except Vote.DoesNotExist:
                vote = Vote(
                    solution=self.solution,
                    voter=self.user
                )

            if vote_input == 'reject':
                vote.is_accepted = False
                vote.vote = None
            else:
                vote.is_accepted = True
                vote.vote = vote_input
            vote.comment = request.POST.get('comment')
            vote.time_voted = timezone.now()
            vote.voter_impact = self.user.get_profile().impact
            vote.save()

        return redirect('project:solution:solution', project_name=self.project.name, solution_id=self.solution.id)


class SolutionCreateView(ProjectObjectMixin, RequestTemplateView):
    """
    View to create a new solution
    """
    template_name = "solution/new_solution.html"

    def initiate_variables(self, request, *args, **kwargs):
        super(SolutionCreateView, self).initiate_variables(request, *args, **kwargs)
        self.parent_task, self.parent_solution = [None] * 2
        task_id = kwargs.get('task_id', None)
        solution_id = kwargs.get('solution_id', None)
        if task_id:
            self.parent_task = get_object_or_404(Task, id=task_id)
        if solution_id:
            self.parent_solution = get_object_or_404(Solution, id=solution_id)

    def get_context_data(self, request, **kwargs):
        kwargs['task'] = self.parent_task
        kwargs['solution'] = self.parent_solution
        return super(SolutionCreateView, self).get_context_data(request, **kwargs)

    def post(self, request, *args, **kwargs):
        if self.parent_task and self.parent_task.is_closed:
            return redirect('project:task:task', project_name=self.project.name, task_id=self.parent_task.id)
        if self.parent_solution and (self.parent_solution.is_completed or self.parent_solution.is_closed):
            return redirect('project:solution:solution', project_name=self.project.name, solution_id=self.parent_solution.id)

        title = request.POST.get('title')
        description = request.POST.get('description')

        # If no parent task, title and description of solution required
        if self.parent_task is None \
                and not (title and description):
            context = self.get_context_data(request, **kwargs)
            context['error'] = "A title and description is required, please explain the suggested solution."
            if title:
                context['title'] = title
            if description:
                context['description'] = description
            return self.render_to_response(context)
        else:
            solution = Solution(
                user=request.user,
                task=self.parent_task,
                solution=self.parent_solution,
                project=self.project,
                title=title,
                description=description
            )
            solution.save()
            return redirect('project:solution:solution', project_name=self.project.name, solution_id=solution.id)


class SolutionEditView(SolutionObjectMixin, RequestTemplateView):
    """
    View to edit solution
    """
    template_name = "solution/solution_edit.html"

    def get(self, request, *args, **kwargs):
        if not self.is_owner or self.solution.is_closed:
            return redirect('project:solution:solution', project_name=self.project, solution_id=self.solution.id)
        return super(SolutionEditView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not self.is_owner or self.solution.is_closed:
            return redirect('project:solution:solution', project_name=self.project, solution_id=self.solution.id)
        self.solution.title = request.POST.get('title')
        self.solution.description = request.POST.get('description')
        self.solution.save()
        return redirect('project:solution:solution', project_name=self.project.name, solution_id=self.solution.id)


class SolutionReviewView(SolutionObjectMixin, RequestTemplateView):
    template_name = "solution/review.html"

    def get_context_data(self, request, **kwargs):
        kwargs["vote_count"] = self.solution.vote_set.count()
        kwargs["accept_votes"] = self.solution.vote_set.filter(is_accepted=True)
        kwargs["reject_votes"] = self.solution.vote_set.filter(is_accepted=False)
        kwargs["maximum_magnitude"] = Vote.MAXIMUM_MAGNITUDE
        kwargs["has_commented"] = self.solution.has_commented(self.user.id)
        return super(SolutionReviewView, self).get_context_data(request, **kwargs)

    def post(self, request, *args, **kwargs):
        if not self.solution.is_completed:
            return redirect('project:solution:solution', project_name=self.project.name, solution_id=self.solution.id)

        comment_vote_input = request.POST.get('comment_vote')
        if comment_vote_input is not None:
            comment_vote_input = int(comment_vote_input)
            comment_vote_input = Vote.MAXIMUM_MAGNITUDE if comment_vote_input > Vote.MAXIMUM_MAGNITUDE else comment_vote_input
            comment_id = request.POST.get('comment_id')
            comment = Comment.objects.get(id=comment_id)
            if comment.user.id == self.user.id:
                return redirect('project:solution:review', project_name=self.project.name, solution_id=self.solution.id)
            try:
                comment_type = ContentType.objects.get_for_model(comment)
                comment_vote = Vote.objects.get(
                    voteable_type_id=comment_type.id,
                    voteable_id=comment.id,
                    voter_id=self.user.id
                )
                if comment_vote.magnitude != comment_vote_input:
                    comment_vote.magnitude = comment_vote_input
                    comment_vote.is_accepted = comment_vote_input > 0
                    comment_vote.voter_impact = self.user.get_profile().impact
                    comment_vote.time_voted = timezone.now()
                    comment_vote.save()
            except Vote.DoesNotExist:
                comment_vote = Vote(
                    voter=self.user,
                    voter_impact=self.user.get_profile().impact,
                    voteable=comment,
                    magnitude=comment_vote_input,
                    is_accepted=comment_vote_input > 0,
                    time_voted=timezone.now()
                )
                comment_vote.save()
            return redirect('project:solution:review', project_name=self.project.name, solution_id=self.solution.id)
        comment_text = request.POST.get('comment')
        if comment_text is not None:
            review_comment = Comment(
                time_commented=timezone.now(),
                project=self.project,
                user=self.user,
                commentable=self.solution,
                comment=comment_text
            )
            review_comment.save()
            return redirect('project:solution:review', project_name=self.project.name, solution_id=self.solution.id)

        solution_type = ContentType.objects.get_for_model(self.solution)
        try:
            vote = Vote.objects.get(
                voteable_type_id=solution_type.id,
                voteable_id=self.solution.id,
                voter_id=self.user.id
            )
        except Vote.DoesNotExist:
            vote = None

        vote_input = request.POST.get('vote')
        if vote_input is not None and not self.is_owner:
            vote_input = int(vote_input)
            vote_input = Vote.MAXIMUM_MAGNITUDE if vote_input > Vote.MAXIMUM_MAGNITUDE else vote_input
            if vote is None:
                vote = Vote(
                    voteable=self.solution,
                    voter=self.user
                )
            vote.is_accepted = vote_input > 0
            vote.magnitude = vote_input
            vote.time_voted = timezone.now()
            vote.voter_impact = self.user.get_profile().impact
            vote.save()
            return redirect('project:solution:review', project_name=self.project.name, solution_id=self.solution.id)


class SolutionCommitsView(SolutionObjectMixin, RequestTemplateView):
    template_name = "solution/commits.html"

    def initiate_variables(self, request, *args, **kwargs):
        super(SolutionCommitsView, self).initiate_variables(request, *args, **kwargs)
        self.repository_set = self.project.repository_set.filter(is_hidden=False).order_by('name')
        repository_name = kwargs.get("repository_name")
        if self.repository_set.count() == 0:
            raise Http404
        elif repository_name is not None:
            self.repository = get_object_or_404(Repository, project_id=self.project.id, name=repository_name)
        else:
            self.repository = self.repository_set[0]  # load the default active repository

    def get_context_data(self, request, **kwargs):
        kwargs['repositories'] = self.repository_set
        kwargs['repository'] = self.repository
        pygit_repository = self.repository.load_pygit_object()
        try:
            kwargs['commits'] = self.solution.get_commit_set(pygit_repository)
            kwargs['diff'] = self.solution.get_pygit_diff(pygit_repository)
        except KeyError:
            kwargs['commits'] = []
            kwargs['diff'] = []
        return super(SolutionCommitsView, self).get_context_data(request, **kwargs)

### todo refactor these views

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

    def reviewed(self):
        """
        Generator for solutions that have been reviewed by requesting user
        """
        # todo test for this
        solution_type = ContentType.objects.get_for_model(Solution)
        for vote in self.user.vote_set.filter(voteable_type_id=solution_type.id).order_by('-time_voted'):
            yield vote.voteable

    def get_queryset(self):
        if self.solutions_tab == 'my_reviewed':
            return (solution for solution in self.reviewed())
        elif self.solutions_tab == 'my_incomplete':
            return self.project.solution_set.filter(is_completed=False, user_id=self.user.id).order_by('-time_completed')
        elif self.solutions_tab == 'my_complete':
            return self.project.solution_set.filter(is_completed=True, user_id=self.user.id).order_by('-time_completed')
        elif self.solutions_tab == 'all_incomplete':
            return self.project.solution_set.filter(is_completed=False).order_by('-time_completed')
        elif self.solutions_tab == 'all_complete':
            return self.project.solution_set.filter(is_completed=True).order_by('-time_completed')
        else:
            return self.project.solution_set.all().order_by('-time_posted')

    def get_context_data(self, **kwargs):
        context = super(SolutionListView, self).get_context_data(**kwargs)
        context['solutions_tab'] = self.solutions_tab
        return context


def my_reviewed():
    return SolutionListView.as_view(
        solutions_tab='my_reviewed'
    )


def my_incomplete():
    return SolutionListView.as_view(
        solutions_tab='my_incomplete'
    )


def my_complete():
    return SolutionListView.as_view(
        solutions_tab='my_complete'
    )


def all_incomplete():
    return SolutionListView.as_view(
        solutions_tab='all_incomplete'
    )


def all_complete():
    return SolutionListView.as_view(
        solutions_tab='all_complete'
    )