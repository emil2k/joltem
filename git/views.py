from django.shortcuts import render
from git.models import Repository


def repository(request, repository_path):
    repository = Repository.objects.get(path=repository_path)
    context = {
        'repository': repository
    }
    return render(request, 'git/repository.html', context)