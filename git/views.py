from django.shortcuts import render
from git.models import Repository, Authentication


def repository(request, repository_path):
    repository = Repository.objects.get(path=repository_path)
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

