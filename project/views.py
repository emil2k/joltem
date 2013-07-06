from django.shortcuts import render, get_object_or_404
from project.models import Project
from task.models import Task
from solution.models import Solution, Vote
from git.models import Repository


def project(request, project_name):
    project = Project.objects.get(name=project_name)
    context = {
        'project_tab': "main",
        'project': project
    }
    if request.POST:
        action = request.POST.get('action')
        # Create a repository
        if action == 'create_repo':
            name = request.POST.get('name')
            description = request.POST.get('description')
            if name is not None:
                created_repo = Repository(
                    project=project,
                    name=name,
                    description=description
                )
                created_repo.save()
                context['created_repo'] = created_repo
        # Remove repository
        removed_repo_id = request.POST.get('remove_repo')
        if removed_repo_id is not None:
            removed_repo = Repository.objects.get(id=removed_repo_id)
            removed_repo.delete()
            context['removed_repo'] = removed_repo
        # Remove task
        removed_task_id = request.POST.get('remove_task')
        if removed_task_id is not None:
            removed_task = Task.objects.get(id=removed_task_id)
            removed_task.delete()
            context['removed_task'] = removed_task
    return render(request, 'project/project.html', context)


def tasks(request, project_name):
    project = get_object_or_404(Project, name=project_name)
    context = {
        'project_tab': "tasks",
        'project': project
    }
    return render(request, 'project/tasks.html', context)


def repositories(request, project_name):
    project = get_object_or_404(Project, name=project_name)
    context = {
        'project_tab': "repositories",
        'project': project,
        'repositories': project.repository_set.all(),
    }
    return render(request, 'project/repositories.html', context)


def solutions(request, project_name):
    project = get_object_or_404(Project, name=project_name)
    context = {
        'solutions_tab': "all",
        'project_tab': "solutions",
        'project': project,
        'solutions': project.solution_set.all().order_by('-id')
    }
    return render(request, 'project/solutions_all.html', context)


def solutions_my(request, project_name):
    project = get_object_or_404(Project, name=project_name)
    context = {
        'solutions_tab': "my",
        'project_tab': "solutions",
        'project': project,
        'solutions': request.user.solution_set.filter(project_id=project.id).order_by('-id')
    }
    return render(request, 'project/solutions_my.html', context)


def solutions_review(request, project_name):
    project = get_object_or_404(Project, name=project_name)
    need_review = []
    for solution in Solution.objects.filter(project_id=project.id, is_completed=True).order_by('-id'):
        if solution.user_id != request.user.id \
                and Vote.objects.filter(solution_id=solution.id, voter_id=request.user.id).count() == 0:
            need_review.append(solution)
    context = {
        'solutions_tab': "review",
        'project_tab': "solutions",
        'project': project,
        'solutions': need_review
    }
    return render(request, 'project/solutions_review.html', context)