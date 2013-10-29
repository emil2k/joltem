from django.utils import timezone
from django.views.generic.base import View, ContextMixin
from django.contrib.contenttypes.generic import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.core import context_processors
from django.http import HttpResponse, HttpResponseNotFound
from django.template import RequestContext

from solution.models import Solution
from joltem.models import Comment, Vote


class RequestBaseView(ContextMixin, View):
    """
    A view that renders a template for GET request, where the context depends on the request or the user
    """

    def initiate_variables(self, request, *args, **kwargs):
        """Override to initiate other variables, make sure to call super on first line"""
        self.request = request
        self.user = request.user

    def dispatch(self, request, *args, **kwargs):
        self.initiate_variables(request, *args, **kwargs)
        return super(RequestBaseView, self).dispatch(request, args, kwargs)

    def get_context_data(self, **kwargs):
        kwargs["user"] = self.user
        return RequestContext(
            self.request,
            super(RequestBaseView, self).get_context_data(**kwargs),
            [context_processors.request]
        )


class TextContextMixin(ContextMixin):
    """
    Passes text file contents to into context, from texts folder into context.

    The context of each file are loaded into context object identified by iteration variable,
    i.e. text_1, text_2, text_3
    """
    text_names = []
    text_context_object_prefix = "text_"

    def get_context_data(self, **kwargs):
        from joltem.libs.loaders.text import TextLoader
        text_loader = TextLoader()
        for i, text_name in enumerate(self.text_names):
            kwargs[self.text_context_object_prefix + str(i+1)], filepath = text_loader(text_name)
        return super(TextContextMixin, self).get_context_data(**kwargs)


class VoteableView(RequestBaseView):
    """
    View that contains a voteable, processes the voting
    """

    def post(self, request, *args, **kwargs):
        """Determine voteable model and process vote, otherwise pass to """
        input_vote = request.POST.get('voteable_vote', None)
        input_voteable_id = request.POST.get('voteable_id', None)
        input_voteable_type = request.POST.get('voteable_type', None)

        if input_vote is not None \
                and input_voteable_id is not None \
                and input_voteable_type is not None:
            input_vote = int(input_vote)
            input_voteable_id = int(input_voteable_id)
            input_vote = Vote.MAXIMUM_MAGNITUDE if input_vote > Vote.MAXIMUM_MAGNITUDE else input_vote  # enforce max
            input_vote = 0 if input_vote < 0 else input_vote  # enforce min
            # Determine voteable type
            if input_voteable_type == 'solution':
                voteable_model = Solution
            else:
                voteable_model = Comment
            voteable = voteable_model.objects.get(id=input_voteable_id)
            if not voteable.is_owner(self.user):  # can't vote for yourself
                voteable.put_vote(self.user, input_vote)
                return self.get_vote_redirect()

        return super(VoteableView, self).post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs["maximum_magnitude"] = Vote.MAXIMUM_MAGNITUDE
        return super(VoteableView, self).get_context_data(**kwargs)

    def get_vote_redirect(self):
        raise ImproperlyConfigured("Vote redirect needs to be defined in extending class.")


class CommentableView(RequestBaseView):
    """
    View that contains a commentable, processes the commenting form
    """

    def post(self, request, *args, **kwargs):
        commentable = self.get_commentable()
        comment_edit = request.POST.get('comment_edit')
        comment_id = request.POST.get('comment_id')
        if request.is_ajax() and comment_edit is not None and comment_id is not None:
            try:
                comment = Comment.objects.get(id=comment_id)
            except Comment.DoesNotExist, Comment.MultipleObjectsReturned:
                return HttpResponseNotFound("Comment with not found with id : %s" % comment_id)
            else:
                comment.comment = comment_edit
                comment.save()
                return HttpResponse(comment.comment)  # for Jeditable return data to display # todo run thrown markdown filter
        comment_text = request.POST.get('comment')
        if comment_text is not None:
            commentable.add_comment(self.user, comment_text)
            return self.get_comment_redirect()

        return super(CommentableView, self).post(request, *args, **kwargs)

    def get_commentable(self):
        raise ImproperlyConfigured("Commentable needs to be defined in extending class.")

    def get_commentable_owner(self):
        """
        Return the owner of the commentable if there is one, so that user may be notified if comments are posted
        """
        return None

    def get_comment_redirect(self):
        raise ImproperlyConfigured("Comment redirect needs to be defined in extending class.")