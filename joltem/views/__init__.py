# coding: utf-8
""" Joltem views. """
from django.http.response import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import (
    TemplateView, RedirectView, View, DetailView, ListView)
from collections import defaultdict

from joltem.models import Notification, Comment, User
from project.models import Project
from joltem.views.generic import TextContextMixin, RequestBaseView


class HomeView(TemplateView):

    """ View to serve up homepage. """

    template_name = 'joltem/landing.html'

    def get(self, request, *args, **kwargs):
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
        else:
            return self.render_to_response(context={})

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


class NotificationsView(RequestBaseView, ListView):

    """ Displays the users notifications. """

    template_name = "joltem/notifications.html"
    paginate_by = 10

    @staticmethod
    def post(request, *args, **kwargs):
        """ Clear all notification.

        :return redirect:

        """

        if request.POST.get("clear_all"):
            request.user.notification_set.filter(
                is_cleared=False).mark_cleared()
        return redirect("notifications")

    def get_context_data(self, **kwargs):
        """ Get context.

        :return dict:

        """
        kwargs["nav_tab"] = "notifications"

        return super(NotificationsView, self).get_context_data(**kwargs)

    def get_queryset(self):
        """ Preload notifications.

        :return list:

        """
        notifications = self.user.notification_set.select_related()\
            .order_by('-time_notified')
        cache = defaultdict(list)
        for notify in notifications:
            cache[notify.notifying_type].append(notify.notifying_id)

        for ct_type in cache.keys():
            cache[ct_type] = ct_type.model_class().objects.select_related()\
                .in_bulk(cache[ct_type])

        for notify in notifications:
            notify.notifying = cache[notify.notifying_type][notify.notifying_id]

        return notifications


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


class IntroductionView(TemplateView, RequestBaseView):

    """ A view to display a basic introduction to the site.

    Displayed to new users after sign up.

    """

    template_name = "joltem/introduction.html"