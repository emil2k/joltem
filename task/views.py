""" Task related views. """

from django.http import Http404
from django.db.models import Sum, Q
from django.shortcuts import redirect, get_object_or_404
from django.core.cache import cache
from django.views.generic import (
    TemplateView, CreateView, UpdateView, ListView,
)
from django.utils import timezone
from django.core.urlresolvers import reverse

from joltem.holders import CommentHolder
from project.models import Impact
from solution.models import Solution
from joltem.views.generic import VoteableView, CommentableView
from project.views import ProjectBaseView

from .models import Task, Vote
from .forms import TaskCreateForm, TaskEditForm


class TaskBaseView(ProjectBaseView):

    """ Abstract class for task rendering. """

    def __init__(self, *args, **kwargs):
        super(TaskBaseView, self).__init__(*args, **kwargs)
        self.task = None
        self.is_owner = False

    def initiate_variables(self, request, *args, **kwargs):
        """ Initialize task. """

        super(TaskBaseView, self).initiate_variables(request, args, kwargs)
        self.task = get_object_or_404(Task, id=self.kwargs.get("task_id"))
        self.is_owner = self.task.is_owner(self.user)

    def get_context_data(self, **kwargs):
        """ Get data for templates.

        :return dict: a context

        """
        kwargs["task"] = self.task
        kwargs["is_owner"] = self.is_owner
        kwargs["comments"] = CommentHolder.get_comments(
            self.task.comment_set.all().order_by('time_commented'), self.user)
        kwargs["solutions"] = self.task.solution_set.all().order_by(
            '-time_posted')
        try:
            kwargs["vote"] = Vote.objects.get(
                task_id=self.task.id,
                voter_id=self.user.id
            )
        except Vote.DoesNotExist:
            kwargs["vote"] = None
        return super(TaskBaseView, self).get_context_data(**kwargs)


class TaskView(VoteableView, CommentableView, TemplateView, TaskBaseView):

    """ Render the task for customer. """

    template_name = "task/task.html"

    def get_context_data(self, **kwargs):
        """ Make context for templates.

        :return dict: a context

        """
        accept_votes_qs = self.task.vote_set.filter(is_accepted=True)
        reject_votes_qs = self.task.vote_set.filter(is_accepted=False)
        impact_total = lambda qs: qs.aggregate(
            impact_total=Sum('voter_impact'))['impact_total'] or 0
        kwargs["task_accept_votes"] = accept_votes_qs.order_by('time_voted')
        kwargs["task_reject_votes"] = reject_votes_qs.order_by('time_voted')
        kwargs["task_accept_total"] = impact_total(accept_votes_qs)
        kwargs["task_reject_total"] = impact_total(reject_votes_qs)
        try:
            impact = Impact.objects.get(
                user_id=self.task.author_id,
                project_id=self.project.id
            )
        except Impact.DoesNotExist:
            kwargs["task_author_impact"] = 0
            kwargs["task_author_completed"] = 0
        else:
            kwargs["task_author_impact"] = impact.impact
            kwargs["task_author_completed"] = impact.completed
        return super(TaskView, self).get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        """ Parse post data.

        :return HttpRedirect:

        """

        # Vote to accept task
        if request.POST.get('accept'):
            self.task.put_vote(self.user, True)
            return redirect(
                'project:task:task', project_id=self.project.id,
                task_id=self.task.id)

        # Vote to reject task
        if request.POST.get('reject'):
            self.task.put_vote(self.user, False)
            return redirect(
                'project:task:task', project_id=self.project.id,
                task_id=self.task.id)

        # Close task
        if self.is_owner and request.POST.get('close'):
            self.task.is_closed = True
            self.task.time_closed = timezone.now()
            self.task.save()
            return redirect(
                'project:task:task', project_id=self.project.id,
                task_id=self.task.id)

        # Reopen task
        if self.is_owner and request.POST.get('reopen'):
            self.task.is_closed = False
            self.task.time_closed = None
            self.task.save()
            return redirect(
                'project:task:task', project_id=self.project.id,
                task_id=self.task.id)

        # to process commenting
        return super(TaskView, self).post(request, *args, **kwargs)

    def get_vote_redirect(self):
        """ Redirect on vote.

        :return django.http.HttpResponseRedirect:

        """
        return redirect(
            'project:task:task', project_id=self.project.id,
            task_id=self.task.id)

    def get_commentable(self):
        """ I should have docstring.

        :return Task:

        """
        return self.task

    def get_comment_redirect(self):
        """ I should have docstring.

        :return HttpRedirect:

        """
        return redirect(
            'project:task:task', project_id=self.project.id,
            task_id=self.task.id)


class TaskEditView(TaskBaseView, UpdateView):

    """ Implement task's edit. """

    form_class = TaskEditForm
    template_name = 'task/task_edit.html'

    def get_object(self):
        """ Check user is owner for the task.

        :return Task:

        """

        if self.is_owner:
            return self.task

        raise Http404

    def get_success_url(self):
        """ Get url on task's view.

        :return str:

        """

        return reverse(
            'project:task:task',
            kwargs={
                'project_id': self.project.id,
                'task_id': self.task.id
            }
        )


class TaskCreateView(ProjectBaseView, CreateView):

    """ Implement task's creation. """

    form_class = TaskCreateForm
    template_name = 'task/new_task.html'

    parent_solution = None

    def initiate_variables(self, request, *args, **kwargs):
        """ Check parent solution.

        :return HttpResponse: Make redirect if parent solution is completed

        """

        super(TaskCreateView, self).initiate_variables(
            request, *args, **kwargs)

        parent_solution_id = self.kwargs.get('parent_solution_id')
        if parent_solution_id is not None:
            self.parent_solution = get_object_or_404(
                Solution,
                pk=parent_solution_id,
            )
            if self.parent_solution.is_completed:
                return redirect(
                    'project:solution:solution',
                    project_id=self.project.id,
                    solution_id=self.parent_solution.id,
                )

    def get_context_data(self, **kwargs):
        """ Get context for templates.

        :return dict:

        """
        kwargs['parent_solution'] = self.parent_solution
        return super(TaskCreateView, self).get_context_data(**kwargs)

    def get_form_kwargs(self):
        """Override ``POST`` values to pass model validation.

        Make sure that ``project`` and ``owner`` are listed in
        ``TaskCreateForm.Meta.fields``.

        :return dict:

        """
        form_kwargs = super(TaskCreateView, self).get_form_kwargs()

        if 'data' in form_kwargs:
            form_data = form_kwargs['data'].dict()
            form_data['project'] = self.project.pk
            form_data['owner'] = self.user.pk

            form_kwargs['data'] = form_data

        return form_kwargs

    def form_valid(self, form):
        """ Update created task.

        :return HttpResponse:

        """
        task = form.save(commit=False)
        task.parent = self.parent_solution
        task.author = self.user
        task.save()

        return redirect('project:task:task', project_id=self.project.id,
                        task_id=task.id)


class TaskBaseListMeta(type):

    """ Build views hierarchy. """

    tasks_tabs = []

    def __new__(mcs, name, bases, params):
        cls = super(TaskBaseListMeta, mcs).__new__(mcs, name, bases, params)
        if cls.tasks_tab:
            mcs.tasks_tabs.append((cls.tasks_tab, cls))
        return cls


class TaskBaseListView(ListView, ProjectBaseView):

    """ Base view for displaying lists of tasks. """

    __metaclass__ = TaskBaseListMeta

    context_object_name = 'tasks'
    filters = {}
    paginate_by = 10
    project_tab = "tasks"
    tasks_tab = None
    template_name = 'task/tasks_list.html'

    def get_context_data(self, **kwargs):
        """ Get template's context.

        :return dict:

        """
        kwargs["tasks_tabs"] = cache.get("%s:tasks_tabs" % self.project.pk)
        kwargs["tasks_tab"] = self.tasks_tab

        if not kwargs["tasks_tabs"]:
            kwargs["tasks_tabs"] = {
                n: self.get_queryset(**c.filters).count()
                for n, c in TaskBaseListView.tasks_tabs
            }
            cache.set("%s:tasks_tabs" % self.project.pk, kwargs["tasks_tabs"])

        return super(TaskBaseListView, self).get_context_data(**kwargs)

    def get_queryset(self, **filters):
        """ Filter tasks by current project.

        :return QuerySet:

        """
        filters = filters or self.filters
        qs = self.project.task_set.select_related('author')\
            .prefetch_related('solution_set')

        for k in filters:
            if callable(filters[k]):
                filters[k] = filters[k](self)
            if k.endswith('__ne'):
                qs = qs.filter(~Q(**{k[:-4]: filters[k]}))
            else:
                qs = qs.filter(**{k: filters[k]})

        return qs.order_by('-priority', '-time_posted')


class AllOpenTasksView(TaskBaseListView):

    """ List all opened tasks. """

    tasks_tab = "all_open"
    filters = {'is_accepted': True, 'is_closed': False}


class AllClosedTasksView(TaskBaseListView):

    """ List all closed tasks. """

    tasks_tab = "all_closed"
    filters = {'is_accepted': True, 'is_closed': True}


class MyOpenTasksView(TaskBaseListView):

    """ List opened tasks. """

    tasks_tab = "my_open"
    filters = {
        'is_accepted': True, 'is_closed': False, 'owner': lambda s: s.user}


class MyClosedTasksView(TaskBaseListView):

    """ List closed tasks. """

    tasks_tab = "my_closed"
    filters = {
        'is_accepted': True, 'is_closed': True, 'owner': lambda s: s.user}


class MyReviewTasksView(TaskBaseListView):

    """ List of tasks the user should review. """

    tasks_tab = "my_review"
    filters = {'is_reviewed': False, 'is_closed': False,
               'vote__voter__ne': lambda s: s.user}


class MyReviewedTasksView(TaskBaseListView):

    """ List of tasks the user has reviewed. """

    tasks_tab = "my_reviewed"
    filters = {'vote__voter': lambda s: s.user}
