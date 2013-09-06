from django.shortcuts import redirect, get_object_or_404

from django.http.response import Http404
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.views.generic.base import TemplateView
from django.views.generic.list import ListView

from joltem.models import Vote
from joltem.holders import CommentHolder
from git.models import Repository

from task.models import Task
from solution.models import Solution
from joltem.views.generic import VoteableView, CommentableView
from project.views import ProjectBaseView


class SolutionBaseView(ProjectBaseView):
    solution_tab = None

    def initiate_variables(self, request, *args, **kwargs):
        super(SolutionBaseView, self).initiate_variables(request, args, kwargs)
        self.solution = get_object_or_404(Solution, id=self.kwargs.get("solution_id"))
        self.is_owner = self.solution.is_owner(self.user)

    def get_context_data(self, **kwargs):
        kwargs["solution"] = self.solution
        kwargs["solution_tab"] = self.solution_tab
        # Get the users vote on this solution
        try:
            kwargs["vote"] = self.solution.vote_set.get(voter_id=self.user.id)
        except Vote.DoesNotExist:
            kwargs["vote"] = None

        kwargs["comments"] = CommentHolder.get_comments(self.solution.comment_set.all().order_by('time_commented'), self.user)
        kwargs["subtasks"] = self.solution.subtask_set.filter(is_accepted=True).order_by('-time_posted')
        kwargs["suggested_solutions"] = self.solution.solution_set.all().order_by('-time_posted')
        kwargs["is_owner"] = self.solution.is_owner(self.user)

        return super(SolutionBaseView, self).get_context_data(**kwargs)


class SolutionView(VoteableView, CommentableView, TemplateView, SolutionBaseView):
    """
    View to display solution's information
    """
    template_name = "solution/solution.html"
    solution_tab = "solution"

    def post(self, request, *args, **kwargs):
        # Mark solution complete
        if request.POST.get('complete') \
                and not self.solution.is_completed \
                and not self.solution.is_closed \
                and self.solution.is_owner(self.user):
            self.solution.is_completed = True
            self.solution.time_completed = timezone.now()
            self.solution.save()
            return redirect('project:solution:solution', project_name=self.project.name, solution_id=self.solution.id)

        # Mark solution incomplete
        if request.POST.get('incomplete') \
                and self.solution.is_completed \
                and not self.solution.is_closed \
                and self.solution.is_owner(self.user):
            self.solution.mark_incomplete()
            return redirect('project:solution:solution', project_name=self.project.name, solution_id=self.solution.id)

        # Close solution
        if request.POST.get('close') \
                and not self.solution.is_completed \
                and not self.solution.is_closed \
                and self.solution.is_owner(self.user):
            self.solution.mark_complete()
            return redirect('project:solution:solution', project_name=self.project.name, solution_id=self.solution.id)

        # Reopen solution
        if request.POST.get('reopen') \
                and self.solution.is_closed \
                and self.solution.is_owner(self.user):
            self.solution.is_closed = False
            self.solution.time_closed = None
            self.solution.save()
            return redirect('project:solution:solution', project_name=self.project.name, solution_id=self.solution.id)

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

        return super(SolutionView, self).post(request, *args, **kwargs)

    def get_vote_redirect(self):
        return redirect('project:solution:solution', project_name=self.project.name, solution_id=self.solution.id)

    def get_commentable(self):
        return self.solution

    def get_comment_redirect(self):
        return redirect('project:solution:solution', project_name=self.project.name, solution_id=self.solution.id)


class SolutionEditView(TemplateView, SolutionBaseView):
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


class SolutionReviewView(VoteableView, CommentableView, TemplateView, SolutionBaseView):
    template_name = "solution/review.html"
    solution_tab = "review"

    def get_context_data(self, **kwargs):
        kwargs["vote_count"] = self.solution.vote_set.count()
        kwargs["accept_votes"] = self.solution.vote_set.filter(is_accepted=True)
        kwargs["reject_votes"] = self.solution.vote_set.filter(is_accepted=False)
        kwargs["has_commented"] = self.solution.has_commented(self.user.id)
        return super(SolutionReviewView, self).get_context_data(**kwargs)

    def get_vote_redirect(self):
        return redirect('project:solution:review', project_name=self.project.name, solution_id=self.solution.id)

    def get_commentable(self):
        return self.solution

    def get_comment_redirect(self):
        return redirect('project:solution:review', project_name=self.project.name, solution_id=self.solution.id)


class SolutionCommitsView(TemplateView, SolutionBaseView):
    template_name = "solution/commits.html"
    solution_tab = "commits"

    def initiate_variables(self, request, *args, **kwargs):
        super(SolutionCommitsView, self).initiate_variables(request, *args, **kwargs)
        self.repository_set = self.project.repository_set.filter(is_hidden=False).order_by('name')
        repository_name = kwargs.get("repository_name")
        if self.repository_set.count() == 0:
            raise Http404
        elif repository_name is not None:
            # todo for some reason a non existent repository is not returning 404
            self.repository = get_object_or_404(Repository, project_id=self.project.id, name=repository_name)
        else:
            self.repository = self.repository_set[0]  # load the default active repository

    def get_context_data(self, **kwargs):
        kwargs['repositories'] = self.repository_set
        kwargs['repository'] = self.repository
        pygit_repository = self.repository.load_pygit_object()
        try:
            kwargs['commits'] = self.solution.get_commit_set(pygit_repository)
            kwargs['diff'] = self.solution.get_pygit_diff(pygit_repository)
        except KeyError:
            kwargs['commits'] = []
            kwargs['diff'] = []
        return super(SolutionCommitsView, self).get_context_data(**kwargs)


class SolutionCreateView(TemplateView, ProjectBaseView):
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

    def get_context_data(self, **kwargs):
        kwargs['task'] = self.parent_task
        kwargs['solution'] = self.parent_solution
        return super(SolutionCreateView, self).get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        if self.parent_task and (self.parent_task.is_closed or not self.parent_task.is_accepted):
            return redirect('project:task:task', project_name=self.project.name, task_id=self.parent_task.id)
        if self.parent_solution and (self.parent_solution.is_completed or self.parent_solution.is_closed):
            return redirect('project:solution:solution', project_name=self.project.name, solution_id=self.parent_solution.id)

        title = request.POST.get('title')
        description = request.POST.get('description')

        # If no parent task, title and description of solution required
        if self.parent_task is None \
                and not (title and description):
            context = self.get_context_data(**kwargs)
            context['error'] = "A title and description is required, please explain the suggested solution."
            if title:
                context['title'] = title
            if description:
                context['description'] = description
            return self.render_to_response(context)
        else:
            solution = Solution(
                owner=request.user,
                task=self.parent_task,
                solution=self.parent_solution,
                project=self.project,
                title=title,
                description=description
            )
            solution.save()
            return redirect('project:solution:solution', project_name=self.project.name, solution_id=solution.id)


class SolutionBaseListView(ListView, ProjectBaseView):
    """
    Base view for displaying lists of solutions
    """
    template_name = 'solution/solutions_list.html'
    context_object_name = 'solutions'
    project_tab = "solutions"
    solutions_tab = None

    def get_context_data(self, **kwargs):
        kwargs["solutions_tab"] = self.solutions_tab
        return super(SolutionBaseListView, self).get_context_data(**kwargs)


class MyReviewedSolutionsView(SolutionBaseListView):
    solutions_tab = "my_reviewed"

    def reviewed_filter(self):
        """
        Generator for solutions that have been reviewed by requesting user
        """
        # todo test for this
        solution_type = ContentType.objects.get_for_model(Solution)
        for vote in self.user.vote_set.filter(voteable_type_id=solution_type.id).order_by('-time_voted'):
            yield vote.voteable

    def get_queryset(self):
        return (solution for solution in self.reviewed_filter())


class MyIncompleteSolutionsView(SolutionBaseListView):
    solutions_tab = "my_incomplete"

    def get_queryset(self):
        return self.project.solution_set.filter(is_completed=False, is_closed=False, owner_id=self.user.id).order_by('-time_posted')


class MyCompleteSolutionsView(SolutionBaseListView):
    solutions_tab = "my_complete"

    def get_queryset(self):
        return self.project.solution_set.filter(is_completed=True, is_closed=False, owner_id=self.user.id).order_by('-time_completed')


class AllIncompleteSolutionsView(SolutionBaseListView):
    solutions_tab = "all_incomplete"

    def get_queryset(self):
        return self.project.solution_set.filter(is_completed=False, is_closed=False).order_by('-time_posted')


class AllCompleteSolutionsView(SolutionBaseListView):
    solutions_tab = "all_complete"

    def get_queryset(self):
        return self.project.solution_set.filter(is_completed=True,  is_closed=False).order_by('-time_completed')
