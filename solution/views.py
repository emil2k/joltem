""" Solution related views. """
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db.models import Q
from django.http import Http404
from django.shortcuts import redirect, get_object_or_404
from django.utils.functional import cached_property
from django.views.generic import TemplateView, ListView

from git.models import Repository
from joltem.holders import CommentHolder
from joltem.models import Comment
from joltem.views.generic import VoteableView, CommentableView
from project.models import Impact
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
        try:
            self.solution = Solution.objects\
                .prefetch_related('vote_set__voter')\
                .select_related('owner')\
                .get(id=self.kwargs.get("solution_id"))
            print self.solution
        except Solution.DoesNotExist:
            raise Http404("Solution not found.")
        else:
            self.is_owner = self.solution.is_owner(self.user)

    def get_context_data(self, **kwargs):
        """ Return context for template. """
        kwargs["solution"] = self.solution
        kwargs["solution_tab"] = self.solution_tab
        # Get the users vote on this solution
        kwargs["vote"] = None
        for vote in self.solution.vote_set.all():
            if vote.voter_id == self.user.id:
                kwargs["vote"] = vote
                kwargs["vote_valid"] = self.solution.is_vote_valid(vote)
                break
        comment_qs = Comment.objects\
            .filter(commentable_id=self.solution.id,
                    commentable_type_id=
                    ContentType.objects.get_for_model(Solution))\
            .select_related('project', 'owner')\
            .order_by('time_commented')
        kwargs["comments"] = CommentHolder.get_comments(
            comment_qs,
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

    def get_context_data(self, **kwargs):
        """ Get data for templates.

        :return dict: a context

        """
        try:
            impact = Impact.objects.get(
                user_id=self.solution.owner_id,
                project_id=self.project.id
            )
        except Impact.DoesNotExist:
            kwargs["solution_owner_impact"] = 0
            kwargs["solution_owner_completed"] = 0
        else:
            kwargs["solution_owner_impact"] = impact.impact
            kwargs["solution_owner_completed"] = impact.completed
        return super(SolutionView, self).get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        """ Handle POST requests on solution view.

        Directly handles the marking of solution complete/incomplete
        or close/reopen. Requests to comment and vote pass through,
        to CommentableView and VoteableView.

        Returns a HTTP response.

        """
        if self.solution.is_owner(self.user) and not (
            'comment' in request.POST
            or 'comment_id' in request.POST
            or 'voteable_id' in request.POST
        ):
            # Mark solution complete
            if request.POST.get('complete')\
                    and request.POST.get('compensation_value')\
                    and not self.solution.is_completed \
                    and not self.solution.is_closed:
                compensation = int(request.POST.get('compensation_value'))
                self.solution.mark_complete(compensation)

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

            return redirect('project:solution:solution',
                            project_id=self.project.id,
                            solution_id=self.solution.id)

        return super(SolutionView, self).post(request, *args, **kwargs)

    def get_vote_redirect(self):
        """ Return url to redirect to after vote. """
        return redirect('project:solution:solution',
                        project_id=self.project.id,
                        solution_id=self.solution.id)

    def get_commentable(self):
        """ Return the instance being commented on, in the view. """
        return self.solution

    def get_comment_redirect(self):
        """ Return url to redirect to after comment. """
        return redirect('project:solution:solution',
                        project_id=self.project.id,
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
                            project_id=self.project.id,
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
                            project_id=self.project.id,
                            solution_id=self.solution.id)
        self.solution.title = request.POST.get('title')
        self.solution.description = request.POST.get('description')
        self.solution.save()
        return redirect('project:solution:solution',
                        project_id=self.project.id,
                        solution_id=self.solution.id)


class SolutionReviewView(VoteableView, CommentableView, TemplateView,
                         SolutionBaseView):

    """ View for reviewing a solution. """

    template_name = "solution/review.html"
    solution_tab = "review"

    def post(self, request, *args, **kwargs):
        """ Handle POST requests.

        Handle changing of solution evaluation, and passing everything to
        super class.

        :param request:
        :param args:
        :param kwargs:
        :return: HTTP response

        """
        if self.is_owner and request.POST.get('change_value'):
            compensation_value = int(request.POST.get('compensation_value'))
            self.solution.change_evaluation(compensation_value)
            return redirect('project:solution:review',
                            project_id=self.project.id,
                            solution_id=self.solution.id)
        return super(SolutionReviewView, self).post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """ Return context to pass to template. Add vote results. """
        vote_count = 0
        accept_votes = []
        reject_votes = []
        for v in self.solution.vote_set.all():
            vote_count += 1
            if v.is_accepted:
                accept_votes.append(v)
            else:
                reject_votes.append(v)
        kwargs["vote_count"] = vote_count
        kwargs["accept_votes"] = accept_votes
        kwargs["reject_votes"] = reject_votes
        return super(SolutionReviewView, self).get_context_data(**kwargs)

    def get_vote_redirect(self):
        """ Return url to redirect to after vote. """
        return redirect('project:solution:review',
                        project_id=self.project.id,
                        solution_id=self.solution.id)

    def get_commentable(self):
        """ Return instance being commented on. """
        return self.solution

    def get_comment_redirect(self):
        """ Return url to redirect to after comment. """
        return redirect('project:solution:review',
                        project_id=self.project.id,
                        solution_id=self.solution.id)


class SolutionCommitsView(TemplateView, SolutionBaseView):

    """Shows solution's commits.

    Repository can be specified by user or used by default.

    """

    template_name = 'solution/commits.html'
    solution_tab = "commits"

    @cached_property
    def current_repo(self):
        """Return current repository instance.

        First it tries to get repo by name if it is specified in URL.
        Otherwise it uses first repo of project.

        """
        repository_id = self.kwargs.get('repository_id')

        if repository_id:
            return get_object_or_404(
                Repository,
                project_id=self.project.id,
                id=repository_id,
            )

        if self.project_repo_list:
            return self.project_repo_list[0]

    @cached_property
    def project_repo_list(self):
        """Return visible repos of project."""
        return self.project.repository_set.visible()

    def get_context_data(self, **kwargs):
        """Add repositories and commits to context.

        :return dict: A context

        """
        context = super(SolutionCommitsView, self).get_context_data(**kwargs)
        commit_list = []
        if self.current_repo:
            pygit_repository = self.current_repo.load_pygit_object()
            if pygit_repository:
                try:
                    commit_list = self.solution.get_commit_set(pygit_repository)
                except KeyError:
                    pass
        context['commit_list'] = commit_list
        context['current_repo'] = self.current_repo
        context['project_repo_list'] = self.project_repo_list
        context['project'] = self.project
        return context


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
                            project_id=self.project.id,
                            task_id=self.parent_task.id)
        if self.parent_solution and \
                (self.parent_solution.is_completed or
                 self.parent_solution.is_closed):
            return redirect('project:solution:solution',
                            project_id=self.project.id,
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
                            project_id=self.project.id,
                            solution_id=solution.id)


class SolutionBaseListMeta(type):

    """ Build views hierarchy. """

    solutions_tabs = []

    def __new__(mcs, name, bases, params):
        cls = super(SolutionBaseListMeta, mcs).__new__(mcs, name, bases, params)
        if cls.solutions_tab:
            mcs.solutions_tabs.append((cls.solutions_tab, cls))
        return cls


class SolutionBaseListView(ListView, ProjectBaseView):

    """ View mixin for solution's list. """

    __metaclass__ = SolutionBaseListMeta

    context_object_name = 'solutions'
    paginate_by = 10
    project_tab = 'solutions'
    solutions_tab = None
    template_name = 'solution/solutions_list.html'

    def get_context_data(self, **kwargs):
        """ Get context data for templates.

        :return dict:

        """
        kwargs['project'] = self.project
        kwargs['project_tab'] = self.project_tab
        kwargs['solutions_tab'] = self.solutions_tab
        kwargs["solutions_tabs"] = cache.get("%s:solutions_tabs"
                                             % self.project.pk)
        if not kwargs["solutions_tabs"]:
            kwargs["solutions_tabs"] = {
                n: self.get_queryset(**c.filters).count()
                for n, c in SolutionBaseListView.solutions_tabs
            }
            cache.set("%s:solutions_tabs" % self.project.pk,
                      kwargs["solutions_tabs"])
        return super(SolutionBaseListView, self).get_context_data(**kwargs)

    def get_queryset(self, **filters):
        """ Filter solutions by current project.

        :return QuerySet:

        """
        filters = filters or self.filters
        qs = self.project.solution_set.select_related('task', 'owner')\
            .prefetch_related('vote_set')
        for k in filters:
            if callable(filters[k]):
                filters[k] = filters[k](self)
            if k.endswith('__ne'):
                qs = qs.filter(~Q(**{k[:-4]: filters[k]}))
            else:
                qs = qs.filter(**{k: filters[k]})

        return qs.order_by('-time_posted')


class AllIncompleteSolutionsView(SolutionBaseListView):

    """ View for viewing a list of all incomplete solutions. """

    solutions_tab = 'all_incomplete'
    filters = {'is_completed': False, 'is_closed': False}


class AllCompleteSolutionsView(SolutionBaseListView):

    """ View for viewing a list of complete solutions. """

    solutions_tab = 'all_complete'
    filters = {'is_completed': True, 'is_closed': False}


class MyIncompleteSolutionsView(SolutionBaseListView):

    """ View for viewing a list of your incomplete solutions. """

    solutions_tab = 'my_incomplete'
    filters = {
        'is_completed': False, 'is_closed': False,
        'owner': lambda s: s.request.user}


class MyCompleteSolutionsView(SolutionBaseListView):

    """ View for viewing a list of your complete solutions. """

    solutions_tab = 'my_complete'
    filters = {
        'is_completed': True, 'is_closed': False,
        'owner': lambda s: s.request.user}


class MyReviewSolutionsView(SolutionBaseListView):

    """ View for viewing a list of solutions to review. """

    solutions_tab = 'my_review'
    filters = {
        'is_completed': True, 'is_closed': False,
        'owner__ne': lambda s: s.request.user,
        'vote_set__voter__ne': lambda s: s.request.user}


class MyReviewedSolutionsView(SolutionBaseListView):

    """ View for viewing a list of reviewed solutions. """

    solutions_tab = 'my_reviewed'
    filters = {'vote_set__voter': lambda s: s.request.user}
