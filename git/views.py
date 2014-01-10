""" Git views. """
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404

from git.models import Repository
from project.models import Project


def repository(request, project_id, repository_id):
    """ Render repository template.

    :return str: A rendered template

    """
    project = get_object_or_404(Project, id=project_id)
    repo = get_object_or_404(Repository, id=repository_id)
    context = {
        'project': project,
        'repository': repo
    }
    return render(request, 'git/repository.html', context)


def repositories(request, project_id):
    """ Render list of repositories.

    :return str: A rendered page

    """
    project = get_object_or_404(Project, id=project_id)
    is_admin = project.is_admin(request.user.id)
    is_manager = project.is_manager(request.user.id)
    if (is_admin or is_manager) and request.POST:
        # Hide repository
        hidden_repo_id = request.POST.get('hide_repo')
        if hidden_repo_id is not None:
            hide_repo = Repository.objects.get(id=hidden_repo_id)
            hide_repo.is_hidden = True
            hide_repo.save()
            return redirect(
                'project:git:repositories', project_id=project_id)
    context = {
        'project_tab': "repositories",
        'repositories_tab': "active",
        'project': project,
        'repositories': project.repository_set.filter(is_hidden=False),
        'host': settings.GATEWAY_HOST,
        'action': "hide",
        'is_admin': is_admin,
        'is_manager': is_manager
    }
    return render(request, 'git/repositories_list.html', context)


def repositories_hidden(request, project_id):
    """ Render hidden repository.

    :return str: A rendered page

    """
    project = get_object_or_404(Project, id=project_id)
    is_admin = project.is_admin(request.user.id)
    is_manager = project.is_manager(request.user.id)
    if (is_admin or is_manager) and request.POST:
        # Unhide repository
        unhidden_repo_id = request.POST.get('unhide_repo')
        if unhidden_repo_id is not None:
            unhide_repo = Repository.objects.get(id=unhidden_repo_id)
            unhide_repo.is_hidden = False
            unhide_repo.save()
            return redirect(
                'project:git:repositories_hidden', project_id=project_id)
    context = {
        'project_tab': "repositories",
        'repositories_tab': "hidden",
        'project': project,
        'repositories': project.repository_set.filter(is_hidden=True),
        'host': request.get_host().split(':')[0],
        'action': "unhide",
        'is_admin': is_admin,
        'is_manager': is_manager
    }
    return render(request, 'git/repositories_list.html', context)


def new_repository(request, project_id):
    """ Support creation of new repository.

    :return str: A rendered page

    """
    project = get_object_or_404(Project, id=project_id)
    is_admin = project.is_admin(request.user.id)
    is_manager = project.is_manager(request.user.id)
    if not (is_admin or is_manager):
        return redirect('project:git:repositories', project_id=project_id)
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
                return redirect(
                    'project:git:repositories', project_id=project_id)
    context = {
        'project_tab': "repositories",
        'project': project,
        'repositories': project.repository_set.filter(is_hidden=False),
        'is_admin': is_admin,
        'is_manager': is_manager
    }
    return render(request, 'git/new_repository.html', context)
