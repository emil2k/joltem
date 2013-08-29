from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from joltem.holders import CommentHolder
from project.models import Project
from task.models import Task
from solution.models import Solution

from django.views.generic import TemplateView
from django.views.generic.list import ListView
from project.views import ProjectBaseView


class TaskBaseView(ProjectBaseView):

    def initiate_variables(self, request, *args, **kwargs):
        super(TaskBaseView, self).initiate_variables(request, args, kwargs)
        self.task = get_object_or_404(Task, id=self.kwargs.get("task_id"))
        self.is_owner = self.task.is_owner(self.user)

    def get_context_data(self, **kwargs):
        kwargs["task"] = self.task
        kwargs["is_owner"] = self.task
        kwargs["comments"] = CommentHolder.get_comments(self.task.comment_set.all().order_by('time_commented'), self.user)
        kwargs["solutions"] = self.task.solution_set.all().order_by('-time_posted')
        return super(TaskBaseView, self).get_context_data(**kwargs)


class TaskView(TemplateView, TaskBaseView):
    template_name = "task/task.html"

    def post(self, request, *args, **kwargs):
        if not self.is_owner:
            return redirect('project:task:task', project_name=self.project.name, task_id=self.task.id)

        from django.utils import timezone

        if request.POST.get('close'):
            self.task.is_closed = True
            self.task.time_closed = timezone.now()
            self.task.save()

        if request.POST.get('reopen'):
            self.task.is_closed = False
            self.task.time_closed = None
            self.task.save()

        return redirect('project:task:task', project_name=self.project.name, task_id=self.task.id)


class TaskEditView(TemplateView, TaskBaseView):
    template_name = "task/task_edit.html"

    def post(self, request, *args, **kwargs):
        if not self.is_owner:
            return redirect('project:task:task', project_name=self.project.name, task_id=self.task.id)
        title = request.POST.get('title')
        if title is not None:
            self.task.title = title
            self.task.description = request.POST.get('description')
            self.task.save()
            return redirect('project:task:task', project_name=self.project.name, task_id=self.task.id)


class TaskCreateView(TemplateView, ProjectBaseView):
    template_name = "task/new_task.html"
    parent_solution = None

    def initiate_variables(self, request, *args, **kwargs):
        super(TaskCreateView, self).initiate_variables(request, *args, **kwargs)
        parent_solution_id = self.kwargs.get("parent_solution_id", None)
        if parent_solution_id is not None:
            self.parent_solution = get_object_or_404(Solution, id=parent_solution_id)
            if not self.parent_solution.is_accepted \
                    or self.parent_solution.is_completed \
                    or not (self.parent_solution.is_owner(self.user) or self.project.is_admin(self.user.id)):
                return redirect('project:solution:solution', project_name=self.project.name, solution_id=self.parent_solution.id)

    def get_context_data(self, **kwargs):
        kwargs["parent_solution"] = self.parent_solution
        return super(TaskCreateView, self).get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') == 'create_task':
            title = request.POST.get('title')
            description = request.POST.get('description')
            if title is not None:
                created_task = Task(
                    project=self.project,
                    parent=self.parent_solution,
                    owner=self.user,
                    title=title,
                    description=description
                )
                created_task.save()
                if self.parent_solution is not None:
                    return redirect('project:solution:solution', project_name=self.project.name, solution_id=self.parent_solution.id)
                return redirect('project:task:task', project_name=self.project.name, task_id=created_task.id)


class TaskBaseListView(ListView, ProjectBaseView):
    """
    Base view for displaying lists of tasks
    """
    template_name = 'task/tasks_list.html'
    context_object_name = 'tasks'
    tasks_tab = None

    def get_context_data(self, **kwargs):
        kwargs["tasks_tab"] = self.tasks_tab
        return super(TaskBaseListView, self).get_context_data(**kwargs)


class MyOpenTasksView(TaskBaseListView):
    tasks_tab = "my_open"

    def get_queryset(self):
        return self.project.task_set.filter(is_closed=False, owner_id=self.user.id).order_by('-time_posted')


class MyClosedTasksView(TaskBaseListView):
    tasks_tab = "my_closed"

    def get_queryset(self):
        return self.project.task_set.filter(is_closed=True, owner_id=self.user.id).order_by('-time_closed')


class AllOpenTasksView(TaskBaseListView):
    tasks_tab = "all_open"

    def get_queryset(self):
        return self.project.task_set.filter(is_closed=False).order_by('-time_posted')


class AllClosedTasksView(TaskBaseListView):
    tasks_tab = "all_closed"

    def get_queryset(self):
        return self.project.task_set.filter(is_closed=True).order_by('-time_closed')


class SubtaskBaseView(ListView, ProjectBaseView):
    """
    Base view for displaying subtasks for a given task, grouped by the solutions they represent
    """
    template_name = "task/tasks_list_parent.html"
    context_object_name = "subtask_groups"

    def initiate_variables(self, request, *args, **kwargs):
        super(SubtaskBaseView, self).initiate_variables(request, *args, **kwargs)
        self.parent_task = get_object_or_404(Task, id=kwargs.get('parent_task_id', None))

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
        return solution.subtask_set.all().order_by('-time_posted')

    def get_queryset(self):
        """Generate subtask groups"""
        return (g for g in self.generate_subtasks())

    def generate_subtasks(self):
        """Generator for subtask groups"""
        for solution in self.get_solution_queryset():
            subtasks = self.get_subtask_queryset(solution)
            if subtasks.count() > 0:
                subtask_group = SubtaskBaseView.SubtaskGroupHolder(solution, subtasks)
                yield subtask_group


class SubtaskView(SubtaskBaseView):
    """Filters out closed subtasks of closed solutions, currently the only view."""

    def get_solution_queryset(self):
        return self.parent_task.solution_set.filter(is_closed=False).order_by('-time_posted')
