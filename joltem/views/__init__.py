from django.contrib.auth import authenticate, login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404, resolve_url
from django.utils import timezone
from django.views.generic.base import TemplateView, RedirectView

from git.models import Authentication
from joltem.models import User, Invite, Notification
from joltem.views.generic import TextContextMixin, RequestBaseView
from project.models import Project


def home(request):
    if request.user.is_authenticated():
        # Currently there is only one project so just redirect to it
        project = Project.objects.get()
        return redirect('project:project', project_name=project.name)

    elif 'invite_code' in request.COOKIES:
        invite_code = request.COOKIES['invite_code']
        invite = Invite.is_valid(invite_code)
        if invite:
            context = {
                "invite": invite
            }
            return render(request, 'joltem/invitation.html', context)
    return redirect('sign_in')


def is_email_valid(email):
    import re
    return re.match(r'^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.(?:[A-Z]{2}|com|org|net|edu|gov|mil|biz|info|mobi|name|aero|asia|jobs|museum)$', email, re.I )


def sign_up(request):
    if not 'invite_code' in request.COOKIES:
        return redirect('sign_in')
    else:
        invite_code = request.COOKIES['invite_code']
        invite = Invite.is_valid(invite_code)
        if not invite:
            return redirect('sign_in')
        else:
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
                    profile = user.get_profile()
                    if profile.set_gravatar_email(gravatar_email):
                        profile.save()
                        # Login and redirect to authentication keys page
                    user = authenticate(username=username, password=password)
                    login(request, user)
                    # Track invite
                    invite.is_signed_up = True
                    invite.time_signed_up = timezone.now()
                    invite.user = user
                    invite.save()
                    return redirect('intro')
            context = {
                'nav_tab': "up",
                'error': error,
                'invite': invite
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


@login_required
def user(request, username):
    profile_user = get_object_or_404(User, username=username)
    context = {
        'user': request.user,  # user viewing the page
        'profile_user': profile_user  # the user whose profile it is
    }
    return render(request, 'joltem/user.html', context)

@login_required
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

@login_required
def keys(request):
    user = request.user
    keys = user.authentication_set.all().order_by('name')

    if request.POST:
        remove_id = request.POST.get('remove')
        name = request.POST.get('name')
        data = request.POST.get('key')
        if remove_id:
            key = Authentication.objects.get(id=remove_id)
            key.delete()
        elif name and data:
            key = Authentication(
                user=user,
                name=name,
            )
            key.blob = data
            key.save()
        return redirect('account_keys')

    context = {
        'nav_tab': "account",
        'account_tab': "keys",
        'user': user,
        'keys': keys,
    }
    return render(request, 'joltem/keys.html', context)


@login_required
def invites(request):
    user = request.user
    if not user.is_superuser:
        return redirect('home')
    from joltem.models import Invite
    context = {
        'nav_tab': "invite",
        'contacted_invites': Invite.objects.filter(is_contacted=True, is_signed_up=False).order_by('-time_contacted','-time_sent'),
        'signed_up_invites': Invite.objects.filter(is_signed_up=True).order_by('-time_signed_up', '-time_sent'),
        'potential_invites': Invite.objects.filter(is_signed_up=False, is_contacted=False).order_by('-id'),
    }
    if request.POST:
        mark_sent_id = request.POST.get('mark_sent')
        if mark_sent_id:
            mark_sent = Invite.objects.get(id=mark_sent_id)
            mark_sent.is_sent = True
            mark_sent.time_sent = timezone.now()
            mark_sent.save()
            return redirect('invites')
        mark_contacted_id = request.POST.get('mark_contacted')
        if mark_contacted_id:
            mark_contacted = Invite.objects.get(id=mark_contacted_id)
            mark_contacted.is_contacted = True
            mark_contacted.time_contacted = timezone.now()
            mark_contacted.save()
            return redirect('invites')
        first_name = request.POST.get('first_name')
        if first_name:
            from uuid import uuid4
            personal_note = request.POST.get('personal_note')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            personal_site = request.POST.get('personal_site')
            twitter = request.POST.get('twitter')
            facebook = request.POST.get('facebook')
            stackoverflow = request.POST.get('stackoverflow')
            github = request.POST.get('github')
            uuid = uuid4()
            invite_code = uuid.hex
            invite = Invite(
                invite_code=invite_code,
                first_name=first_name,
                last_name=last_name,
                personal_note=personal_note,
                email=email,
                personal_site=personal_site,
                twitter=twitter,
                facebook=facebook,
                stackoverflow=stackoverflow,
                github=github
            )
            invite.save()
        return redirect('invites')
    return render(request, 'joltem/invites.html', context)


def invite(request, invite_id):
    user = request.user
    if not user.is_authenticated():
        from django.http.response import HttpResponseRedirect
        invitation_redirect = HttpResponseRedirect(resolve_url('home'))  # TODO change to redirect to home which is the invitation page
        invite = Invite.is_valid(invite_id)
        if invite:
            invite.is_clicked = True
            invite.time_clicked = timezone.now()
            invite.save()
            invitation_redirect.set_cookie('invite_code', invite_id)
        return invitation_redirect
    elif not user.is_superuser:
        return redirect('home')
    invite = get_object_or_404(Invite, id=invite_id)
    context = {
        'nav_tab': "invite",
        'invite': invite,
        'host': request.get_host(),
    }
    if request.POST:
        action = request.POST.get('action')
        if action == "delete":
            invite.delete()
            return redirect('invites')
        elif action == "mark_sent":
            invite.is_sent = True
            invite.time_sent = timezone.now()
            invite.save()
            return redirect('invite', invite_id=invite_id)
        elif action == "mark_contacted":
            invite.is_contacted = True
            invite.time_contacted = timezone.now()
            invite.save()
            return redirect('invite', invite_id=invite_id)
        first_name = request.POST.get('first_name')
        if first_name:
            personal_note = request.POST.get('personal_note')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            personal_site = request.POST.get('personal_site')
            twitter = request.POST.get('twitter')
            facebook = request.POST.get('facebook')
            stackoverflow = request.POST.get('stackoverflow')
            github = request.POST.get('github')
            invite.first_name = first_name
            invite.last_name = last_name
            invite.personal_note = personal_note
            invite.email = email
            invite.personal_site = personal_site
            invite.twitter = twitter
            invite.facebook = facebook
            invite.stackoverflow = stackoverflow
            invite.github = github
            invite.save()
        return redirect('invite', invite_id=invite_id)
    return render(request, 'joltem/invite.html', context)


# Class based views



class NotificationsView(TemplateView, RequestBaseView):
    """
    Displays the users notifications
    """
    template_name = "joltem/notifications.html"

    def post(self, request, *args, **kwargs):
        if request.POST.get("clear_all"):
            for notification in request.user.notification_set.filter(is_cleared=False):
                notification.mark_cleared()
        return redirect("notifications")

    def get_context_data(self, **kwargs):
        from joltem.holders import NotificationHolder
        kwargs["nav_tab"] = "notifications"
        kwargs["notifications"] = NotificationHolder.get_notifications(self.user)
        return super(NotificationsView, self).get_context_data(**kwargs)


class NotificationRedirectView(RedirectView):
    """
    A notification redirect, that marks a notification cleared and redirects to the notifications url
    """
    permanent = False
    query_string = False

    def get_redirect_url(self, notification_id):
        notification = get_object_or_404(Notification, id=notification_id)
        notification.mark_cleared()
        return notification.notifying.get_notification_url(notification)



class IntroductionView(TextContextMixin, TemplateView, RequestBaseView):
    """
    A view to display a basic introduction to the site, displayed to new users after sign up.
    """
    template_name = "joltem/introduction.html"
    text_names = ["joltem/introduction.md"]
    text_context_object_prefix = "introduction_"
