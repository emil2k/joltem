from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout as auth_logout
from project.models import Project


def home(request):
    # Currently there is only one project so just redirect to it
    project = Project.objects.get()
    return redirect('project:project', project_name=project.name)


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


def account(request):
    user = request.user
    if request.POST:
        first_name = request.POST.get('first_name') # Required
        last_name = request.POST.get('last_name')
        # TODO validate emails
        email = request.POST.get('email')  # Required
        gravatar_email = request.POST.get('gravatar_email')
        if first_name and email:
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()
            if gravatar_email is not None:
                import hashlib
                # Calculate gravatar hash
                m = hashlib.md5(gravatar_email)

                user_profile = user.get_profile()
                user_profile.gravatar_email = gravatar_email
                user_profile.gravatar_hash = m.hexdigest()
                user_profile.save()
        return redirect('account')

    context = {
        'account_tab': "account",
        'user': user
    }
    return render(request, 'joltem/account.html', context)