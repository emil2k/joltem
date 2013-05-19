from django.shortcuts import render
from joltem.models import Project


def home(request):
    context = {
        'projects': Project.objects.all()
    }
    return render(request, 'joltem/home.html', context)