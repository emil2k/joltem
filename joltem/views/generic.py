""" Generic base views used across the site. """

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic.base import View, ContextMixin
from django.core.exceptions import ImproperlyConfigured
from django.core import context_processors
from django.http import (HttpResponse, HttpResponseNotFound,
                         HttpResponseForbidden)
from django.template import RequestContext
from django_markdown.utils import markdown

from solution.models import Solution
from joltem.models import Comment, Vote
from joltem.libs.loaders.text import TextLoader


class RequestBaseView(ContextMixin, View):

    """ A view that depends on the user and request. """

    def initiate_variables(self, request, *args, **kwargs):
        """ Add the request and requesting user to view. """
        self.request = request
        self.user = request.user

    def dispatch(self, request, *args, **kwargs):
        """ Initiate variables before running regular dispatch.

        Routes to appropriate class method based on HTTP request,
        and returns an HTTP response. If method not defined, returns
        a 405.

        """
        self.initiate_variables(request, *args, **kwargs)
        return super(RequestBaseView, self).dispatch(request, args, kwargs)

    def get_context_data(self, **kwargs):
        """ Return context for template, adds user and request. """
        kwargs["user"] = self.user
        return RequestContext(
            self.request,
            super(RequestBaseView, self).get_context_data(**kwargs),
            [context_processors.request]
        )


class NavTabContextMixin(ContextMixin):

    """ Mixin to pass the navigation tab to the template. """

    nav_tab = None

    def get_context_data(self, **kwargs):
        """ Return context for template, add nav tab identifier. """
        kwargs["nav_tab"] = self.nav_tab
        return super(NavTabContextMixin, self).get_context_data(**kwargs)


class TextContextMixin(ContextMixin):

    """ View to pass text file contents to into context.

    Text files are loaded from `texts` folder in each app,
    just like `templates` folder for templates.

    The context of each file is loaded into a context object
    identified by an iterating variable,
    i.e. text_1, text_2, text_3

    """

    text_names = []
    text_context_object_prefix = "text_"

    def get_context_data(self, **kwargs):
        """ Return context for template, load file contents into context. """
        text_loader = TextLoader()
        for i, text_name in enumerate(self.text_names):
            template_var_name = '{prefix}{index}'.format(
                prefix=self.text_context_object_prefix,
                index=i + 1,
            )
            kwargs[template_var_name], _ = text_loader(text_name)
        return super(TextContextMixin, self).get_context_data(**kwargs)


class VoteableView(RequestBaseView):

    """ View that contains a voteable, processes voting. """

    def post(self, request, *args, **kwargs):
        """ Handle POST request.

        Determine voteable model and process vote, otherwise
        pass to super class. Returns HTTP response.

        """
        input_vote = request.POST.get('voteable_vote', None)
        input_voteable_id = request.POST.get('voteable_id', None)
        input_voteable_type = request.POST.get('voteable_type', None)

        if input_vote is not None \
                and input_voteable_id is not None \
                and input_voteable_type is not None:
            input_vote = int(input_vote) == 1
            input_voteable_id = int(input_voteable_id)
            voteable = Solution.objects.get(id=input_voteable_id)
            if not voteable.is_owner(self.user):  # can't vote for yourself
                voteable.put_vote(self.user, input_vote)
                return self.get_vote_redirect()

        return super(VoteableView, self).post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """ Return template context, add maximum vote magnitude. """
        kwargs["maximum_magnitude"] = Vote.MAXIMUM_MAGNITUDE
        return super(VoteableView, self).get_context_data(**kwargs)

    @staticmethod
    def get_vote_redirect():
        """ Override to return url to redirect to after voting. """
        raise ImproperlyConfigured(
            "Vote redirect needs to be defined in extending class.")


class CommentableView(RequestBaseView):

    """ View that contains a commentable, processes commenting. """

    def post(self, request, *args, **kwargs):
        """ Handle POST request.

        Process the addition, deletion, and editing of comments
        on the commentable instance. Returns HTTP response.

        """
        commentable = self.get_commentable()  # noqa
        # Edit or delete comment
        comment_edit = request.POST.get('comment_edit')
        comment_delete = request.POST.get('comment_delete')
        comment_id = request.POST.get('comment_id')
        if request.is_ajax() and \
                (comment_edit or comment_delete) and comment_id:
            try:
                comment = Comment.objects.get(id=comment_id)
            except Comment.DoesNotExist as xxx_todo_changeme:
                Comment.MultipleObjectsReturned = xxx_todo_changeme
                return HttpResponseNotFound(
                    "Comment with not found with id : %s" % comment_id)
            else:
                if not comment.is_owner(request.user):
                    return HttpResponseForbidden("Not your comment.")
                if comment_delete:
                    commentable.delete_comment(comment)
                    return HttpResponse("Comment deleted")
                elif comment_edit:
                    comment.comment = comment_edit
                    comment.save()
                    # For jeditable return data to display
                    return HttpResponse(markdown(comment.comment))
        # Post a comment
        comment_text = request.POST.get('comment')
        if comment_text is not None:
            commentable.add_comment(self.user, comment_text)
            return self.get_comment_redirect()

        return self.get_comment_redirect()

    @staticmethod
    def get_commentable():
        """ Override to return the commentable instance. """
        raise ImproperlyConfigured(
            "Commentable needs to be defined in extending class.")

    @staticmethod
    def get_commentable_owner():
        """ Override to return commentable owner. """
        return None

    @staticmethod
    def get_comment_redirect():
        """ Override to return url to redirect to after commenting. """
        raise ImproperlyConfigured(
            "Comment redirect needs to be defined in extending class.")


class ValidUserMixin(object):

    """Provides authorization checking."""

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        """Provide authorized page access by ``login_required`` decorator.

        :return HttpRequest:

        """
        self.request = request
        self.args = args
        self.kwargs = kwargs

        response = self.prepare(request, *args, **kwargs)
        if response:
            return response

        return super(ValidUserMixin, self).dispatch(request, *args, **kwargs)

    def prepare(self, request, *args, **kwargs):
        """It is executed before built in request dispatcher.

        It can be used as early access checker.

        """


class ExtraContextMixin(object):

    """Accepts ``extra_context`` dict in ``django.contrib.auth`` way."""

    def get_context_data(self, **kwargs):
        """ Make template context.

        :return dict:

        """
        context = super(ExtraContextMixin, self).get_context_data(**kwargs)

        extra_context = self.kwargs.get('extra_context')
        if extra_context is not None:
            context.update(extra_context)

        return context
