# coding: utf-8
""" Joltem views. """
from django.http.response import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import TemplateView, RedirectView, View, DetailView

from joltem.models import Notification, Comment, User
from project.models import Project
from joltem.views.generic import TextContextMixin, RequestBaseView


class HomeView(View):

    """ View to serve up homepage. """

    @staticmethod
    def get(request, *args, **kwargs):
        """ Handle GET request.

        If user is authenticated redirect to project dashboard.
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
        return redirect('sign_in')


class UserView(DetailView):

    """ View for displaying user profile page. """

    model = User
    slug_field = 'username'
    slug_url_kwarg = 'username'
    template_name = 'joltem/user.html'
    context_object_name = 'profile_user'


class CommentView(View):

    """ View for loading markdown of a comment.

    Used by JEditable to load markdown for editing.

    """

    @staticmethod
    def get(request, comment_id):
        """ Return comment markdown.

        :param request:
        :param comment_id: if of comment to load.
        :return: markdown of comment, for jeditable - to edit comments.

        """
        comment = get_object_or_404(Comment, id=comment_id)
        return HttpResponse(comment.comment)


class NotificationsView(TemplateView, RequestBaseView):

    """ Displays the users notifications. """

    template_name = "joltem/notifications.html"

    @staticmethod
    def post(request, *args, **kwargs):
        """ Clear all notification.

        :return redirect:

        """

        if request.POST.get("clear_all"):
            for notification in request.user.notification_set.filter(
                    is_cleared=False):
                notification.mark_cleared()
        return redirect("notifications")

    def get_context_data(self, **kwargs):
        """ Get context.

        :return dict:

        """
        from joltem.holders import NotificationHolder
        kwargs["nav_tab"] = "notifications"
        kwargs["notifications"] = NotificationHolder.get_notifications(
            self.user)
        return super(NotificationsView, self).get_context_data(**kwargs)


class NotificationRedirectView(RedirectView):

    """ A notification redirect.

    That marks a notification cleared and redirects to the notifications url.

    """

    permanent = False
    query_string = False

    def get_redirect_url(self, notification_id):
        """ Get redirect to notification.

        :return str:

        """
        notification = get_object_or_404(Notification, id=notification_id)
        notification.mark_cleared()
        return notification.notifying.get_notification_url(notification)


class IntroductionView(TextContextMixin, TemplateView, RequestBaseView):

    """ A view to display a basic introduction to the site.

    Displayed to new users after sign up.

    """

    template_name = "joltem/introduction.html"
    text_names = ["joltem/introduction.md"]
    text_context_object_prefix = "introduction_"
