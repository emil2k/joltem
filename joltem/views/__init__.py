from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404, resolve_url
from django.utils import timezone
from django.views.generic.base import TemplateView, RedirectView, View
from git.models import Authentication

from joltem.models import User, Invite, Notification, Comment
from project.models import Project
from joltem.views.generic import TextContextMixin, RequestBaseView


class HomeView(View):

    """ View to serve up homepage. """

    def get(self, request, *args, **kwargs):
        """ Handle GET request.

        If user is authenticated redirect to project dashboard, if not
        check that the user has an invite cookie.

        Otherwise redirect to sign in while closed alpha.

        :param request:
        :param args:
        :param kwargs:
        :return:

        """
        if request.user.is_authenticated():
            # Currently there is only one project so just redirect to it
            project = Project.objects.get()
            return redirect('project:project', project_name=project.name)
        elif 'invite_code' in request.COOKIES:
            invite_code = request.COOKIES['invite_code']
            invite = Invite.is_valid(invite_code)
            if invite:
                context = { "invite": invite }
                return render(request, 'joltem/invitation.html', context)
        return redirect('sign_in')


class UserView(View):

    """ View for displaying user profile page. """

    def get(self, request, username):
        """ Handle GET request.

        :param request:
        :param username:
        :return:

        """
        profile_user = get_object_or_404(User, username=username)
        context = {
            'user': request.user,  # user viewing the page
            'profile_user': profile_user  # the user whose profile it is
        }
        return render(request, 'joltem/user.html', context)


# todo make form for this
class AccountView(View):

    """ View for displaying and editing user's account & profile. """

    def get(self, request, *args, **kwargs):
        """ Handle GET request.

        :param request:
        :param args:
        :param kwargs:
        :return:

        """
        user = request.user
        context = {
            'nav_tab': "account",
            'account_tab': "account",
            'user': user,
        }
        return render(request, 'joltem/account.html', context)

    def post(self, request, *args, **kwargs):
        """ Handle POST request.

        :param request:
        :param args:
        :param kwargs:
        :return:

        """
        error = None
        user = request.user
        first_name = request.POST.get('first_name') # Required
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')  # Required
        gravatar_email = request.POST.get('gravatar_email')
        # Validate inputs
        if not first_name:
            error = "First name is required."
        elif not email:
            error = "Email is required."
        # elif not is_valid_email(email):
        #     error = "Email address (%s) is not valid." % email
        # elif gravatar_email and not is_valid_email(gravatar_email):
        #     error = "Your gravatar (%s) must have a valid email address." % gravatar_email
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
        else:
            context = {
                'nav_tab': "account",
                'account_tab': "account",
                'user': user,
                'error': error,
            }
            return render(request, 'joltem/account.html', context)


# todo make a form for this
# todo make the form handle BadKeyError at /account/keys/, add test for a bad key
class KeysView(View):

    """ View for adding and removing SSH keys. """

    def get(self, request, *args, **kwargs):
        """ Handle GET request.

        :param request:
        :param args:
        :param kwargs:
        :return: HTTP response.

        """
        user = request.user
        keys = user.authentication_set.all().order_by('name')
        context = {
            'nav_tab': "account",
            'account_tab': "keys",
            'user': user,
            'keys': keys,
        }
        return render(request, 'joltem/keys.html', context)

    def post(self, request, *args, **kwargs):
        """ Handle POST request.

        :param request:
        :param args:
        :param kwargs:
        :return: HTTP response.

        """
        remove_id = request.POST.get('remove')
        name = request.POST.get('name')
        data = request.POST.get('key')
        if remove_id:
            key = Authentication.objects.get(id=remove_id)
            key.delete()
        elif name and data:
            key = Authentication(
                user=request.user,
                name=name,
            )
            key.blob = data
            key.save()
        return redirect('account_keys')

class CommentView(View):

    """ View for loading markdown of a comment.

    Used by JEditable to load markdown for editing.

    """

    def get(self, request, comment_id):
        """ Return comment markdown.

        :param request:
        :param comment_id: if of comment to load.
        :return: markdown of comment, for jeditable - to edit comments.

        """
        comment = get_object_or_404(Comment, id=comment_id)
        return HttpResponse(comment.comment)

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


# TODO Invitation views, deprecated no need to rewrite will be removed soon

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
