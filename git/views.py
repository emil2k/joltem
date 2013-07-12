from django.shortcuts import render, redirect, get_object_or_404
from project.models import Project
from git.models import Repository, Authentication
from joltem.settings import MAIN_DIR


# TODO this should be moved out of here and into some account management app or page
def keys(request):
    keys = Authentication.objects.all()
    context = {
        'nav_tab': "account",
        'account_tab': "keys",
        'keys': keys
    }
    if request.POST:
        action = request.POST.get('action')
        if action == "keys":
            from git.gitolite import keys
            keys.update_keys()
            return redirect('keys')
        elif action == "permissions":
            from git.gitolite import permissions
            permissions.update_permissions()
            return redirect('keys')
    return render(request, 'git/keys.html', context)


def repository(request, project_name, repository_name):
    project = get_object_or_404(Project, name=project_name)
    repository = get_object_or_404(Repository, name=repository_name, project=project)
    context = {
        'repository': repository,
        'commits': repository.commit_set.order_by('-commit_time'),
    }
    return render(request, 'git/repository.html', context)


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
            return redirect('project:git:repositories', project_name=project_name)

    context = {
        'project_tab': "repositories",
        'repositories_tab': "active",
        'project': project,
        'repositories': project.repository_set.filter(is_hidden=False),
        'is_admin': is_admin
    }
    return render(request, 'git/repositories_active.html', context)


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
            return redirect('project:git:repositories_hidden', project_name=project_name)

    context = {
        'project_tab': "repositories",
        'repositories_tab': "hidden",
        'project': project,
        'repositories': project.repository_set.filter(is_hidden=True),
        'is_admin': is_admin
    }
    return render(request, 'git/repositories_hidden.html', context)


def new_repository(request, project_name):
    project = get_object_or_404(Project, name=project_name)
    is_admin = project.is_admin(request.user)
    if not is_admin:
        return redirect('project:git:repositories', project_name=project_name)
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
                return redirect('project:git:repositories', project_name=project_name)

    context = {
        'project_tab': "repositories",
        'repositories_tab': "new",
        'project': project,
        'repositories': project.repository_set.filter(is_hidden=False),
        'is_admin': is_admin
    }
    return render(request, 'git/new_repository.html', context)

