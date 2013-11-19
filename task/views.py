""" Task related views. """

from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, CreateView, ListView
from django.core.urlresolvers import reverse_lazy
from django.utils import timezone

from joltem.holders import CommentHolder
from solution.models import Solution
from joltem.views.generic import VoteableView, CommentableView
from project.views import ProjectBaseView

from .models import Task, Vote
from .forms import TaskCreateForm


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
        return super(TaskView, self).get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        """ Parse post data.

        :return HttpRedirect:

        """

        # Vote to accept task
        if request.POST.get('accept'):
            self.task.put_vote(self.user, True)
            return redirect(
                'project:task:task', project_name=self.project.name,
                task_id=self.task.id)

        # Vote to reject task
        if request.POST.get('reject'):
            self.task.put_vote(self.user, False)
            return redirect(
                'project:task:task', project_name=self.project.name,
                task_id=self.task.id)

        # Close task
        if self.is_owner and request.POST.get('close'):
            self.task.is_closed = True
            self.task.time_closed = timezone.now()
            self.task.save()
            return redirect(
                'project:task:task', project_name=self.project.name,
                task_id=self.task.id)

        # Reopen task
        if self.is_owner and request.POST.get('reopen'):
            self.task.is_closed = False
            self.task.time_closed = None
            self.task.save()
            return redirect(
                'project:task:task', project_name=self.project.name,
                task_id=self.task.id)

        # to process commenting
        return super(TaskView, self).post(request, *args, **kwargs)

    def get_vote_redirect(self):
        """ Redirect on vote.

        :return django.http.HttpResponseRedirect:

        """
        return redirect(
            'project:task:task', project_name=self.project.name,
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
            'project:task:task', project_name=self.project.name,
            task_id=self.task.id)


class TaskEditView(TemplateView, TaskBaseView):
    template_name = "task/task_edit.html"

    def post(self, request, *args, **kwargs):
        if not self.is_owner:
            return redirect(
                'project:task:task', project_name=self.project.name,
                task_id=self.task.id)
        title = request.POST.get('title')
        if title and title.strip():
            self.task.title = title
            self.task.description = request.POST.get('description')
            self.task.save()
            return redirect(
                'project:task:task', project_name=self.project.name,
                task_id=self.task.id)
        else:
            context = self.get_context_data(**kwargs)
            context['error'] = "Title is required."
            return render(request, 'task/task_edit.html', context)


class TaskCreateView(ProjectBaseView, CreateView):

    form_class = TaskCreateForm
    template_name = 'task/new_task.html'

    parent_solution = None

    def initiate_variables(self, request, *args, **kwargs):
        super(TaskCreateView, self).initiate_variables(request, *args, **kwargs)

        parent_solution_id = self.kwargs.get('parent_solution_id')
        if parent_solution_id is not None:
            self.parent_solution = get_object_or_404(
                Solution,
                pk=parent_solution_id,
            )
            if self.parent_solution.is_completed:
                return redirect(
                    'project:solution:solution',
                    project_name=self.project.name,
                    solution_id=self.parent_solution.id,
                )

    def get_context_data(self, **kwargs):
        kwargs['parent_solution'] = self.parent_solution
        return super(TaskCreateView, self).get_context_data(**kwargs)

    def get_form_kwargs(self):
        """Overrides ``POST`` values to pass model validation.

        Make sure that ``project`` and ``owner`` are listed in
        ``TaskCreateForm.Meta.fields``.

        """
        form_kwargs = super(TaskCreateView, self).get_form_kwargs()

        if 'data' in form_kwargs:
            form_kwargs['data'] = dict(
                project=self.project.pk,
                owner=self.user.pk,
                **form_kwargs['data'].dict()
            )

        return form_kwargs

    def form_valid(self, form):
        task = form.save(commit=False)
        task.parent = self.parent_solution
        task.author = self.user
        task.save()

        return redirect('project:task:task', project_name=self.project.name,
                        task_id=task.id)


class TaskBaseListView(ListView, ProjectBaseView):

    """ Base view for displaying lists of tasks. """

    template_name = 'task/tasks_list.html'
    context_object_name = 'tasks'
    paginate_by = 10
    project_tab = "tasks"
    tasks_tab = None

    def get_context_data(self, **kwargs):
        kwargs["tasks_tab"] = self.tasks_tab
        return super(TaskBaseListView, self).get_context_data(**kwargs)


class MyOpenTasksView(TaskBaseListView):
    tasks_tab = "my_open"

    def get_queryset(self):
        return self.project.task_set.filter(
            is_accepted=True, is_closed=False,
            owner_id=self.user.id).order_by('-time_posted')


class MyClosedTasksView(TaskBaseListView):
    tasks_tab = "my_closed"

    def get_queryset(self):
        return self.project.task_set.filter(
            is_accepted=True, is_closed=True,
            owner_id=self.user.id).order_by('-time_closed')


class MyReviewTasksView(TaskBaseListView):

    """
    List of tasks the user should review.

    """
    tasks_tab = "my_review"

    def iterate_tasks_to_review(self):
        for task in Task.objects.filter(
                is_reviewed=False, is_closed=False).order_by('-time_posted'):
            if not self.user.task_vote_set.filter(task_id=task.id).exists():
                yield task

    def get_queryset(self):
        # TODO: It should return QS.
        return [task for task in self.iterate_tasks_to_review()]


class MyReviewedTasksView(TaskBaseListView):

    """
    List of tasks the user has reviewed.

    """
    tasks_tab = "my_reviewed"

    def get_queryset(self):
        # TODO: It should return QS.
        return [
            task_vote.task for task_vote in self.user.task_vote_set.order_by(
                '-time_voted')
        ]


class AllOpenTasksView(TaskBaseListView):

    """ Render all open tasks. """

    tasks_tab = "all_open"

    def get_queryset(self):
        """ Load data to list.

        :return Queryset:

        """
        return self.project.task_set \
                           .filter(is_accepted=True, is_closed=False) \
                           .order_by('-priority', '-time_posted')


class AllClosedTasksView(TaskBaseListView):
    tasks_tab = "all_closed"

    def get_queryset(self):
        return self.project.task_set \
                           .filter(is_accepted=True, is_closed=True) \
                           .order_by('-priority', '-time_closed')


class SubtaskBaseView(ListView, ProjectBaseView):

    """ Base view for displaying subtasks for a given task.

    Grouped by the solutions they represent.

    """

    template_name = "task/tasks_list_parent.html"
    context_object_name = "subtask_groups"
    project_tab = "tasks"

    def initiate_variables(self, request, *args, **kwargs):
        super(SubtaskBaseView, self).initiate_variables(
            request, *args, **kwargs)
        self.parent_task = get_object_or_404(
            Task, id=kwargs.get('parent_task_id', None))

    def get_context_data(self, **kwargs):
        kwargs["parent_task"] = self.parent_task
        return super(SubtaskBaseView, self).get_context_data(**kwargs)

    class SubtaskGroupHolder:

        def __init__(self, solution, tasks):
            self.solution = solution
            self.subtask_set = tasks

    def get_solution_queryset(self):
        """Queryset of solutions for which to get subtasks for, default is all"""
        return self.parent_task.solution_set.all().order_by('-time_posted')

    def get_subtask_queryset(self, solution):
        """Query set for subtasks of each solution, default is all"""
        return solution.subtask_set.filter(is_accepted=True).order_by('-time_posted')

    def get_queryset(self):
        """Generate subtask groups"""
        # TODO: It should return QS.
        return [g for g in self.generate_subtasks()]

    def generate_subtasks(self):
        """Generator for subtask groups"""
        for solution in self.get_solution_queryset():
            subtasks = self.get_subtask_queryset(solution)
            if subtasks.count() > 0:
                subtask_group = SubtaskBaseView.SubtaskGroupHolder(
                    solution, subtasks)
                yield subtask_group


class SubtaskView(SubtaskBaseView):

    """Filters out closed subtasks of closed solutions, currently the only view."""

    def get_solution_queryset(self):
        return self.parent_task.solution_set.filter(is_closed=False).order_by('-time_posted')
