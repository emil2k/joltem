""" Solution URLS. """

from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required
from solution import views

urlpatterns = patterns(
    '',
    url(r'^(?:(?P<solution_id>(\d)+)/)?new/$', login_required(
        views.SolutionCreateView.as_view()), name='new'),
    url(r'^(?P<solution_id>(\d)+)/$',
        views.SolutionView.as_view(), name='solution'),
    url(r'^(?P<solution_id>(\d)+)/edit/$', login_required(
        views.SolutionEditView.as_view()), name='solution_edit'),
    url(r'^(?P<solution_id>(\d)+)/review/$',
        views.SolutionReviewView.as_view(), name='review'),

    url(r'^(?P<solution_id>(\d)+)/commits/(?:repository/(?P<repository_id>[0-9]+)/)?$',
        views.SolutionCommitsView.as_view(),
        {'extra_context': {'solution_tab': 'commits'}},
        'commits'),

    url(r'^review/my/$',
        login_required(views.MyReviewSolutionsView.as_view()),
        name='my_review'),

    url(r'^reviewed/my/$',
        login_required(views.MyReviewedSolutionsView.as_view()),
        name='my_reviewed'),

    url(r'^incomplete/my/$',
        login_required(views.MyIncompleteSolutionsView.as_view()),
        name='my_incomplete'),

    url(r'^complete/my/$',
        login_required(views.MyCompleteSolutionsView.as_view()),
        name='my_complete'),

    url(r'^closed/my/$',
        login_required(views.MyClosedSolutionsView.as_view()),
        name='my_closed'),

    url(r'^incomplete/$',
        views.AllIncompleteSolutionsView.as_view(), name='all_incomplete'),

    url(r'^complete/$',
        views.AllCompleteSolutionsView.as_view(), name='all_complete'),
)
