from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from project.models import Project
from task.models import Task
from solution.models import Solution

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

@login_required
def task(request, project_name, task_id):
    project = get_object_or_404(Project, name=project_name)
    task = get_object_or_404(Task, id=task_id)
    is_owner = task.is_owner(request.user)
    if request.POST:
        if not is_owner:
            return redirect('project:task:task', project_name=project_name, task_id=task_id)

        from django.utils import timezone

        if request.POST.get('close'):
            task.is_closed = True
            task.time_closed = timezone.now()
            task.save()

        if request.POST.get('reopen'):
            task.is_closed = False
            task.time_closed = None
            task.save()

        return redirect('project:task:task', project_name=project_name, task_id=task_id)

    context = {
        'project': project,
        'task': task,
        'solutions': task.solution_set.all().order_by('-id'),
        'is_owner': is_owner,
    }
    return render(request, 'task/task.html', context)

@login_required
def edit(request, project_name, task_id):
    project = get_object_or_404(Project, name=project_name)
    task = get_object_or_404(Task, id=task_id)
    is_owner = task.is_owner(request.user)
    if request.POST:
        if not is_owner:
            return redirect('project:task:task', project_name=project_name, task_id=task_id)
        title = request.POST.get('title')
        if title is not None:
            task.title = title
            task.description = request.POST.get('description')
            task.save()
            return redirect('project:task:task', project_name=project_name, task_id=task_id)
    context = {
        'project': project,
        'task': task,
        'is_owner': is_owner,
    }
    return render(request, 'task/task_edit.html', context)


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