from django.shortcuts import render
from joltem.models import Project
from git.models import Repository, Authentication


def repository(request, project_name, repository_name):
    project = Project.objects.get(name=project_name)
    repository = Repository.objects.get(name=repository_name, project=project)
    context = {
        'repository': repository
    }
    return render(request, 'git/repository.html', context)


def keys(request):
    keys = Authentication.objects.all()
    context = {
        'keys': keys
    }

    if request.POST:
        if request.POST.get('action') == "update":
            from git.gitolite import keys
            keys.update_keys()

    return render(request, 'git/keys.html', context)

