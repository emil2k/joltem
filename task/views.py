from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from joltem.holders import CommentHolder
from project.models import Project
from task.models import Task
from solution.models import Solution

from django.views.generic import TemplateView
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

#### todo refactor all below

@login_required
def new(request, project_name, parent_solution_id):
    project = get_object_or_404(Project, name=project_name)
    user = request.user
    context = {
        'tasks_tab': "new",
        'project': project
    }
    parent_solution = None
    if parent_solution_id is not None:
        parent_solution = get_object_or_404(Solution, id=parent_solution_id)
        if not parent_solution.is_accepted or parent_solution.is_completed or not (parent_solution.is_owner(user) or project.is_admin(user.id)):
            return redirect('project:solution:solution', project_name=project_name, solution_id=parent_solution.id)
        context['parent_solution'] = parent_solution
    # Create a task
    if request.POST and request.POST.get('action') == 'create_task':
        title = request.POST.get('title')
        description = request.POST.get('description')
        if title is not None:
            created_task = Task(
                project=project,
                parent=parent_solution,
                owner=user,
                title=title,
                description=description
            )
            created_task.save()
            if parent_solution is not None:
                return redirect('project:solution:solution', project_name=project.name, solution_id=parent_solution_id)
            return redirect('project:task:my_open', project_name=project.name)
    return render(request, 'task/new_task.html', context)

# Generic views
from project.views import ProjectListView


class TaskListView(ProjectListView):
    model = Task
    project_tab = 'tasks'
    tasks_tab = None

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        parent_task_id = kwargs.get('parent_task_id')
        if parent_task_id:
            self.parent_task = get_object_or_404(Task, id=parent_task_id)
        else:
            self.parent_task = None
        return super(TaskListView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        if self.parent_task:
            class SubtaskGroup:
                def __init__(self, solution, tasks):
                    self.solution = solution
                    self.subtask_set = tasks
            subtask_groups = []
            for solution in self.parent_task.solution_set.all().order_by('-id'):
                subtasks = solution.subtask_set.all().order_by('-id')
                if subtasks.count() > 0:
                    subtask_group = SubtaskGroup(solution, subtasks)
                    subtask_groups.append(subtask_group)
            return subtask_groups
        elif self.tasks_tab == 'my_closed':
            return self.project.task_set.filter(is_closed=True, owner_id=self.user.id).order_by('-time_posted')
        elif self.tasks_tab == 'my_open':
            return self.project.task_set.filter(is_closed=False, owner_id=self.user.id).order_by('-time_posted')
        elif self.tasks_tab == 'all_closed':
            return self.project.task_set.filter(is_closed=True).order_by('-time_posted')
        elif self.tasks_tab == 'all_open':
            return self.project.task_set.filter(is_closed=False).order_by('-time_posted')

    def get_context_object_name(self, object_list):
        if self.parent_task:
            return 'subtask_groups'
        else:
            return 'tasks'

    def get_template_names(self):
        if self.parent_task:
            return 'task/tasks_list_parent.html'
        else:
            return 'task/tasks_list.html'

    def get_context_data(self, **kwargs):
        context = super(TaskListView, self).get_context_data(**kwargs)
        context['tasks_tab'] = self.tasks_tab
        context['parent_task'] = self.parent_task
        return context


# Various task lists

def my_open():
    return TaskListView.as_view(
        tasks_tab="my_open"
    )


def my_closed():
    return TaskListView.as_view(
        tasks_tab="my_closed"
    )


def all_open():
    return TaskListView.as_view(
        tasks_tab="all_open"
    )


def all_closed():
    return TaskListView.as_view(
        tasks_tab="all_closed"
    )