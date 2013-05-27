from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout as auth_logout
from project.models import Project
from solution.models import Solution


def home(request):
    context = {
        'projects': Project.objects.all()
    }
    return render(request, 'joltem/home.html', context)


def solutions(request):
    solutions = Solution.objects.filter(user_id=request.user.id)
    solutions_to_review = Solution.objects.filter(is_completed=True).exclude(user_id=request.user.id)
    context = {
        'solutions': solutions,
        'solutions_to_review': solutions_to_review,
    }
    return render(request, 'joltem/solutions.html', context)


def sign_in(request):
    context = {}
    if request.POST:
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                next = request.GET.get('next')
                if next is not None:
                    return redirect(next)
                else:
                    return redirect('home')
            else:
                context['error'] = "This account is disabled."
        else:
            context['error'] = "Password incorrect."
    return render(request, 'joltem/sign_in.html', context)


def sign_out(request):
    if request.user.is_authenticated():
        auth_logout(request)
    return render(request, 'joltem/sign_out.html')