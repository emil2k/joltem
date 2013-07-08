from django.shortcuts import render, redirect, get_object_or_404
from project.models import Project
from solution.models import Solution, Vote
from git.models import Repository


def project(request, project_name):
    project = Project.objects.get(name=project_name)
    context = {
        'project_tab': "main",
        'project': project
    }
    return render(request, 'project/project.html', context)


def repositories(request, project_name):
    project = get_object_or_404(Project, name=project_name)
    is_admin = project.is_admin(request.user)
    if is_admin and request.POST:
        # Hide repository
        hidden_repo_id = request.POST.get('hide_repo')
        if hidden_repo_id is not None:
            hide_repo = Repository.objects.get(id=hidden_repo_id)
            hide_repo.is_hidden = True
            hide_repo.save()
            return redirect('project:repositories', project_name=project_name)

    context = {
        'project_tab': "repositories",
        'repositories_tab': "active",
        'project': project,
        'repositories': project.repository_set.filter(is_hidden=False),
        'is_admin': is_admin
    }
    return render(request, 'project/repositories_active.html', context)


def repositories_hidden(request, project_name):
    project = get_object_or_404(Project, name=project_name)
    is_admin = project.is_admin(request.user)
    if is_admin and request.POST:
        # Unhide repository
        unhidden_repo_id = request.POST.get('unhide_repo')
        if unhidden_repo_id is not None:
            unhide_repo = Repository.objects.get(id=unhidden_repo_id)
            unhide_repo.is_hidden = False
            unhide_repo.save()
            return redirect('project:repositories_hidden', project_name=project_name)

    context = {
        'project_tab': "repositories",
        'repositories_tab': "hidden",
        'project': project,
        'repositories': project.repository_set.filter(is_hidden=True),
        'is_admin': is_admin
    }
    return render(request, 'project/repositories_hidden.html', context)


def new_repository(request, project_name):
    project = get_object_or_404(Project, name=project_name)
    is_admin = project.is_admin(request.user)
    if not is_admin:
        return redirect('project:repositories', project_name=project_name)
    if is_admin and request.POST:
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
                return redirect('project:repositories', project_name=project_name)

    context = {
        'project_tab': "repositories",
        'repositories_tab': "new",
        'project': project,
        'repositories': project.repository_set.filter(is_hidden=False),
        'is_admin': is_admin
    }
    return render(request, 'project/new_repository.html', context)


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