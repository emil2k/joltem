from django.shortcuts import render, redirect
from joltem.models import User, Project, Task, TaskBranch


def new_task(request, project_name, parent_task_id):
    project = Project.objects.get(name=project_name)
    context = {
        'project': project
    }
    if parent_task_id is not None:
        parent = Task.objects.get(id=parent_task_id)
        context['parent'] = parent
    # Create a task
    if request.POST and request.POST.get('action') == 'create_task':
        title = request.POST.get('title')
        description = request.POST.get('description')
        if title is not None:
            created_task = Task(
                project=project,
                parent=parent,
                title=title,
                description=description
            )
            created_task.save()
            if parent is not None:
                return redirect('project:task:task', project_name=project.name, task_id=parent_task_id)
            return redirect('project:project', project_name=project.name)
    return render(request, 'task/new_task.html', context)


def task(request, project_name, task_id):
    project = Project.objects.get(name=project_name)
    task = Task.objects.get(id=task_id)
    sub_tasks = task.task_set.all()
    context = {
        'project': project,
        'task': task,
        'sub_tasks': sub_tasks
    }
    return render(request, 'task/task.html', context)


def task_branch(request, project_name, task_id, task_branch_id):
    task_branch = TaskBranch.objects.get(id=task_branch_id)
    context = {}
    if request.POST:
        modified = False;
        if request.POST.get('action') == "assign":
            try:
                assignee = User.objects.get(username=request.POST.get('assignee'))
            except User.DoesNotExist:
                # do nothing
                print "Trying to assign user that does not exist."
            else:
                task_branch.assignees.add(assignee)
                task_branch.save()
                context['assigned'] = assignee
                modified = True
        if request.POST.get('remove') is not None:
            try:
                remove = User.objects.get(username=request.POST.get('remove'))
            except User.DoesNotExist:
                # do nothing
                print "Trying to delete user that does not exist."
            else:
                task_branch.assignees.remove(remove)
                task_branch.save()
                context['removed'] = remove
                modified = True
        if modified:
            from git.gitolite import permissions
            permissions.update_permissions()

    context['task_branch'] = task_branch
    return render(request, 'task/task_branch.html', context)
