""" Solution related views. """
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import redirect, get_object_or_404
from django.views.generic.base import TemplateView
from django.views.generic.list import ListView

from git.models import Repository
from joltem.holders import CommentHolder
from joltem.models import Vote
from joltem.views.generic import VoteableView, CommentableView
from project.views import ProjectBaseView
from solution.models import Solution
from task.models import Task


class SolutionBaseView(ProjectBaseView):

    """ Base view for solution related views. """

    solution_tab = None

    def __init__(self, *args, **kwargs):
        self.solution = None
        self.is_owner = None
        super(SolutionBaseView, self).__init__(*args, **kwargs)

    def initiate_variables(self, request, *args, **kwargs):
        """ Initiate variables for view.

        Initiates the solution instance ( or throws 404 ) and whether
        the requesting user is the owner of the solution itself.

        Returns nothing.

        """
        super(SolutionBaseView, self).initiate_variables(request, args, kwargs)
        self.solution = get_object_or_404(Solution,
                                          id=self.kwargs.get("solution_id"))
        self.is_owner = self.solution.is_owner(self.user)

    def get_context_data(self, **kwargs):
        """ Return context for template. """
        kwargs["solution"] = self.solution
        kwargs["solution_tab"] = self.solution_tab
        # Get the users vote on this solution
        try:
            kwargs["vote"] = self.solution.vote_set.get(voter_id=self.user.id)
        except Vote.DoesNotExist:
            kwargs["vote"] = None

        kwargs["comments"] = CommentHolder.get_comments(
            self.solution.comment_set.all().order_by('time_commented'),
            self.user)
        kwargs["subtasks"] = self.solution.subtask_set.filter(
            is_accepted=True).order_by('-time_posted')
        kwargs["suggested_solutions"] = \
            self.solution.solution_set.all().order_by('-time_posted')
        kwargs["is_owner"] = self.solution.is_owner(self.user)

        return super(SolutionBaseView, self).get_context_data(**kwargs)


class SolutionView(VoteableView, CommentableView, TemplateView,
                   SolutionBaseView):

    """ View for displaying solution information. """

    template_name = "solution/solution.html"
    solution_tab = "solution"

    def post(self, request, *args, **kwargs):
        """ Handle POST requests on solution view.

        Directly handles the marking of solution complete/incomplete
        or close/reopen. Requests to comment and vote pass through,
        to CommentableView and VoteableView.

        Returns a HTTP response.

        """
        # Mark solution complete
        if self.solution.is_owner(self.user):

            if request.POST.get('complete')\
                    and not self.solution.is_completed \
                    and not self.solution.is_closed:
                self.solution.mark_complete()

            # Mark solution incomplete
            if request.POST.get('incomplete') \
                and self.solution.is_completed \
                    and not self.solution.is_closed:
                self.solution.mark_incomplete()

            # Close solution
            if request.POST.get('close') \
                and not self.solution.is_completed \
                    and not self.solution.is_closed:
                self.solution.mark_close()

            # Reopen solution
            if request.POST.get('reopen') and self.solution.is_closed:
                self.solution.mark_open()

            if (not 'comment' in request.POST
                    or 'comment_edit' in request.POST
                    or 'comment_delete' in request.POST):

                return redirect('project:solution:solution',
                                project_name=self.project.name,
                                solution_id=self.solution.id)

        return super(SolutionView, self).post(request, *args, **kwargs)

    def get_vote_redirect(self):
        """ Return url to redirect to after vote. """
        return redirect('project:solution:solution',
                        project_name=self.project.name,
                        solution_id=self.solution.id)

    def get_commentable(self):
        """ Return the instance being commented on, in the view. """
        return self.solution

    def get_comment_redirect(self):
        """ Return url to redirect to after comment. """
        return redirect('project:solution:solution',
                        project_name=self.project.name,
                        solution_id=self.solution.id)


class SolutionEditView(TemplateView, SolutionBaseView):

    """ View for editing a solution. """

    template_name = "solution/solution_edit.html"

    def get(self, request, *args, **kwargs):
        """ Handle GET requests.

        Redirect anybody who is not the owner of the solution
        of if the solution is closed.

        Returns HTTP response.

        """
        if not self.is_owner or self.solution.is_closed:
            return redirect('project:solution:solution',
                            project_name=self.project,
                            solution_id=self.solution.id)
        return super(SolutionEditView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """ Handle POST requests.

        Redirect anybody who is not the owner of the solution
        of if the solution is closed, otherwise saves edits.

        Returns HTTP response.

        """
        if not self.is_owner or self.solution.is_closed:
            return redirect('project:solution:solution',
                            project_name=self.project,
                            solution_id=self.solution.id)
        self.solution.title = request.POST.get('title')
        self.solution.description = request.POST.get('description')
        self.solution.save()
        return redirect('project:solution:solution',
                        project_name=self.project.name,
                        solution_id=self.solution.id)


class SolutionReviewView(VoteableView, CommentableView, TemplateView,
                         SolutionBaseView):

    """ View for reviewing a solution. """

    template_name = "solution/review.html"
    solution_tab = "review"

    def get_context_data(self, **kwargs):
        """ Return context to pass to template. Add vote results. """
        kwargs["vote_count"] = self.solution.vote_set.count()
        kwargs["accept_votes"] = \
            self.solution.vote_set.filter(is_accepted=True)
        kwargs["reject_votes"] = \
            self.solution.vote_set.filter(is_accepted=False)
        kwargs["has_commented"] = self.solution.has_commented(self.user.id)
        return super(SolutionReviewView, self).get_context_data(**kwargs)

    def get_vote_redirect(self):
        """ Return url to redirect to after vote. """
        return redirect('project:solution:review',
                        project_name=self.project.name,
                        solution_id=self.solution.id)

    def get_commentable(self):
        """ Return instance being commented on. """
        return self.solution

    def get_comment_redirect(self):
        """ Return url to redirect to after comment. """
        return redirect('project:solution:review',
                        project_name=self.project.name,
                        solution_id=self.solution.id)


class SolutionCommitsView(TemplateView, SolutionBaseView):

    """ View for viewing commits on solution. """

    template_name = "solution/commits.html"
    solution_tab = "commits"

    def initiate_variables(self, request, *args, **kwargs):
        """ Initiate variables for view, add repository set. """
        super(SolutionCommitsView, self).initiate_variables(
            request, *args, **kwargs)
        self.repository_set = self.project.repository_set.filter(
            is_hidden=False).order_by('name')
        repository_name = kwargs.get("repository_name")
        if self.repository_set.count() == 0:
            self.repository = None
        elif repository_name is not None:
            self.repository = get_object_or_404(Repository,
                                                project_id=self.project.id,
                                                name=repository_name)
        else:
            self.repository = self.repository_set[
                0]  # load the default active repository

    def get_context_data(self, **kwargs):
        """ Return context to pass to template.

        Add repositories and commits.

        """
        if self.repository:
            kwargs['repositories'] = self.repository_set
            kwargs['repository'] = self.repository
            try:
                pygit_repository = self.repository.load_pygit_object()
                kwargs['commits'] = self.solution.get_commit_set(
                    pygit_repository)
                kwargs['diff'] = self.solution.get_pygit_diff(pygit_repository)
            except KeyError:
                kwargs['commits'] = []
                kwargs['diff'] = []
        return super(SolutionCommitsView, self).get_context_data(**kwargs)


class SolutionCreateView(TemplateView, ProjectBaseView):

    """ View for creating a new solution. """

    template_name = "solution/new_solution.html"

    def initiate_variables(self, request, *args, **kwargs):
        """ Initiate variables. Add parent task or solution. """
        super(SolutionCreateView, self).initiate_variables(request,
                                                           *args, **kwargs)
        self.parent_task, self.parent_solution = [None] * 2
        task_id = kwargs.get('task_id', None)
        solution_id = kwargs.get('solution_id', None)
        if task_id:
            self.parent_task = get_object_or_404(Task, id=task_id)
        if solution_id:
            self.parent_solution = get_object_or_404(Solution, id=solution_id)

    def get_context_data(self, **kwargs):
        """ Return context to pass to template. Add parent taks or solution. """
        kwargs['task'] = self.parent_task
        kwargs['solution'] = self.parent_solution
        return super(SolutionCreateView, self).get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        """ Handle POST requests.

        Validates whether parent task or solution is still open
        and not completed, if so creates the new solution.

        Title and description are required if there is no parent task -
        a suggested solution.

        Returns HTTP response.

        """
        if self.parent_task and \
                (self.parent_task.is_closed or
                 not self.parent_task.is_accepted):
            return redirect('project:task:task',
                            project_name=self.project.name,
                            task_id=self.parent_task.id)
        if self.parent_solution and \
                (self.parent_solution.is_completed or
                 self.parent_solution.is_closed):
            return redirect('project:solution:solution',
                            project_name=self.project.name,
                            solution_id=self.parent_solution.id)

        title = request.POST.get('title')
        description = request.POST.get('description')

        # If no parent task, title and description of solution required
        if self.parent_task is None \
                and not (title and description):
            context = self.get_context_data(**kwargs)
            context['error'] = "A title and description is required, " \
                               "please explain the suggested solution."
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
            return redirect('project:solution:solution',
                            project_name=self.project.name,
                            solution_id=solution.id)


class SolutionBaseListView(ListView, ProjectBaseView):

    """ Base view for displaying lists of solutions. """

    template_name = 'solution/solutions_list.html'
    context_object_name = 'solutions'
    paginate_by = 10
    project_tab = "solutions"
    solutions_tab = None

    def get_context_data(self, **kwargs):
        """ Return context for template, add solutions tab. """
        kwargs["solutions_tab"] = self.solutions_tab
        return super(SolutionBaseListView, self).get_context_data(**kwargs)


class MyReviewedSolutionsView(SolutionBaseListView):

    """ View for viewing a list of reviewed solutions. """

    solutions_tab = "my_reviewed"

    def reviewed_filter(self):
        """ Yield reviewed solutions. """
        # todo test for this
        solution_type = ContentType.objects.get_for_model(Solution)
        for vote in self.user.vote_set.filter(
                voteable_type_id=solution_type.id).order_by('-time_voted'):
            yield vote.voteable

    def get_queryset(self):
        """ Return generator of reviewed solutions. """
        # TODO: It should return QS.
        return [solution for solution in self.reviewed_filter()]


class MyReviewSolutionsView(SolutionBaseListView):

    """ View for viewing a list of solutions to review. """

    solutions_tab = "my_review"

    def review_filter(self):
        """ Yield solutions to review. """
        # todo test for this
        solution_type = ContentType.objects.get_for_model(Solution)
        reviewed = [vote.voteable
                    for vote in self.user.vote_set.filter(
                        voteable_type_id=solution_type.id
                    ).order_by('-time_voted')]
        for solution in Solution.objects\
                .filter(is_completed=True, is_closed=False)\
                .exclude(owner_id=self.user.id).order_by('-time_completed'):
            if solution not in reviewed:
                yield solution

    def get_queryset(self):
        """ Return generator of solutions to review. """
        # TODO: It should return QS.
        return [solution for solution in self.review_filter()]


class MyIncompleteSolutionsView(SolutionBaseListView):

    """ View for viewing a list of your incomplete solutions. """

    solutions_tab = "my_incomplete"

    def get_queryset(self):
        """ Return queryset of the user's incomplete solutions. """
        return self.project.solution_set.filter(
            is_completed=False, is_closed=False, owner_id=self.user.id)\
            .order_by('-time_posted')


class MyCompleteSolutionsView(SolutionBaseListView):

    """ View for viewing a list of your complete solutions. """

    solutions_tab = "my_complete"

    def get_queryset(self):
        """ Return queryset of the user's complete solutions. """
        return self.project.solution_set.filter(
            is_completed=True, is_closed=False, owner_id=self.user.id)\
            .order_by('-time_completed')


class AllIncompleteSolutionsView(SolutionBaseListView):

    """ View for viewing a list of all incomplete solutions. """

    solutions_tab = "all_incomplete"

    def get_queryset(self):
        """ Return queryset of all incomplete solutions. """
        return self.project.solution_set\
            .select_related('task', 'owner')\
            .filter(is_completed=False, is_closed=False)\
            .order_by('-time_posted')


class AllCompleteSolutionsView(SolutionBaseListView):

    """ View for viewing a list of complete solutions. """

    solutions_tab = "all_complete"

    def get_queryset(self):
        """ Return queryset of complete solutions. """
        return self.project.solution_set\
            .select_related('task', 'owner')\
            .filter(is_completed=True,  is_closed=False)\
            .order_by('-time_completed')
