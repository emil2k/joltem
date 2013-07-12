from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout as auth_logout
from joltem.models import User, Profile
from project.models import Project
from git.models import Authentication


def home(request):
    # Currently there is only one project so just redirect to it
    project = Project.objects.get()
    return redirect('project:project', project_name=project.name)


def is_email_valid(email):
    import re
    return re.match(r'^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.(?:[A-Z]{2}|com|org|net|edu|gov|mil|biz|info|mobi|name|aero|asia|jobs|museum)$', email, re.I )


def sign_up(request):
    error = None
    if request.POST:
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        gravatar_email = request.POST.get('gravatar_email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        # Check if username is available
        import re
        if not username:
            error = "Username is required."
        elif not first_name:
            error = "First name is required."
        elif not email:
            error = "Email is required."
        elif not password:
            error = "Password is required."
        elif not password_confirm:
            error = "Confirming the password is required."
        elif not is_email_valid(email):
            error = "Email address is not valid."
        elif gravatar_email and not is_email_valid(gravatar_email):
            error = "Your gravatar must have a valid email address."
        elif not re.match(r'^[A-Za-z0-9_]+$', username):
            error = "This username is not valid."
        elif User.objects.filter(username=username).count() > 0:
            error = "This username already exists."
        elif User.objects.filter(email=email).count() > 0:
            error = "Somebody already has an account with this password. Did you forget your password?"
        elif password != password_confirm:
            error = "Passwords don't match."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."
        else:
            user = User.objects.create_user(username, email, password)
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            # Setup profile
            profile = Profile(
                user=user
            )
            if profile.set_gravatar_email(gravatar_email):
                profile.save()
                # Login and redirect to authentication keys page
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('account_keys')
    context = {
        'nav_tab': "up",
        'error': error,
    }
    if error:
        context['username'] = username
        context['email'] = email
        context['first_name'] = first_name
        context['last_name'] = last_name
        context['gravatar_email'] = gravatar_email
    return render(request, 'joltem/sign_up.html', context)


def sign_in(request):
    context = {
        'nav_tab': "in"
    }
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
    error = None
    user = request.user
    if request.POST:
        first_name = request.POST.get('first_name') # Required
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')  # Required
        gravatar_email = request.POST.get('gravatar_email')
        # Validate inputs
        if not first_name:
            error = "First name is required."
        elif not email:
            error = "Email is required."
        elif not is_email_valid(email):
            error = "Email address (%s) is not valid." % email
        elif gravatar_email and not is_email_valid(gravatar_email):
            error = "Your gravatar (%s) must have a valid email address." % gravatar_email
        else:
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()
            profile = user.get_profile()
            if profile.set_gravatar_email(gravatar_email):
                profile.save()
        if not error:
            return redirect('account')

    context = {
        'nav_tab': "account",
        'account_tab': "account",
        'user': user,
        'error': error,
    }
    return render(request, 'joltem/account.html', context)


def keys(request):
    user = request.user
    keys = user.authentication_set.all().order_by('name')

    if request.POST:
        remove_id = request.POST.get('remove')
        name = request.POST.get('name')
        key = request.POST.get('key')
        if remove_id:
            key = Authentication.objects.get(id=remove_id)
            key.delete()
        elif name and key:
            key = Authentication(
                user=user,
                name=name,
                key=key
            )
            key.save()
        return redirect('account_keys')

    context = {
        'nav_tab': "account",
        'account_tab': "keys",
        'user': user,
        'keys': keys,
    }
    return render(request, 'joltem/keys.html', context)
