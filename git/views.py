from django.shortcuts import render, redirect
from project.models import Project
from git.models import Repository, Authentication
from joltem.settings import MAIN_DIR


def repository(request, project_name, repository_name):
    project = Project.objects.get(name=project_name)
    repository = Repository.objects.get(name=repository_name, project=project)
    from pygit2 import Repository as GitRepository, GitError, GIT_SORT_TIME
    repo = GitRepository(repository.absolute_path)
    context = {
        'repository': repository,
        'main_dir': MAIN_DIR,
        'loaded': repo,
    }
    commits = []
    if not repo.is_empty:
        try:
            head = repo.head
        except GitError, e:
            head = None
            context['error'] = e.message
        if head is not None:
            for commit in repo.walk(repo.head.target.hex, GIT_SORT_TIME):
                commits.append(commit)
            context['commits'] = commits
    return render(request, 'git/repository.html', context)


def keys(request):
    keys = Authentication.objects.all()
    context = {
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

