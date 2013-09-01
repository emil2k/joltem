from django.utils import timezone
from django.views.generic.base import View, ContextMixin
from django.contrib.contenttypes.generic import ContentType
from django.core.exceptions import ImproperlyConfigured

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
        return super(RequestBaseView, self).get_context_data(**kwargs)


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
            # Determine voteable type
            if input_voteable_type == 'solution':
                voteable_model = Solution
            else:
                voteable_model = Comment
            voteable = voteable_model.objects.get(id=input_voteable_id)
            voteable_type = ContentType.objects.get_for_model(voteable)
            # Attempt to reload vote, to update it
            try:
                vote = Vote.objects.get(
                    voteable_type_id=voteable_type.id,
                    voteable_id=voteable.id,
                    voter_id=self.user.id
                )
            except Vote.DoesNotExist:
                vote = None
            if not voteable.is_owner(self.user):  # can't vote for yourself
                input_vote = Vote.MAXIMUM_MAGNITUDE if input_vote > Vote.MAXIMUM_MAGNITUDE else input_vote
                if vote is None:
                    vote = Vote(
                        voteable=voteable,
                        voter=self.user
                    )
                vote.is_accepted = input_vote > 0
                vote.magnitude = input_vote
                vote.time_voted = timezone.now()
                vote.voter_impact = self.user.get_profile().impact
                vote.save()
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
        comment_text = request.POST.get('comment')
        if comment_text is not None:
            comment = Comment(
                time_commented=timezone.now(),
                project=self.project,
                user=self.user,
                commentable=self.get_commentable(),
                comment=comment_text
            )
            comment.save()
            return self.get_comment_redirect()
        return super(CommentableView, self).post(request, *args, **kwargs)

    def get_commentable(self):
        raise ImproperlyConfigured("Commentable needs to be defined in extending class.")

    def get_comment_redirect(self):
        raise ImproperlyConfigured("Comment redirect needs to be defined in extending class.")