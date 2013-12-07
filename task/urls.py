""" Tasks urls. """
from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required

from solution import views as solution_views
from task import views


urlpatterns = patterns(
    '',
    url(r'^(?:(?P<parent_solution_id>(\d)+)/)?new/$', login_required(
        views.TaskCreateView.as_view()), name='new'),
    url(r'^(?P<task_id>(\d)+)/$', login_required(
        views.TaskView.as_view()), name='task'),
    url(r'^(?P<task_id>(\d)+)/edit/$', login_required(
        views.TaskEditView.as_view()), name='edit'),
    url(r'^(?P<task_id>(\d)+)/solve/$', login_required(
        solution_views.SolutionCreateView.as_view()), name='solve'),

    # Lists of tasks
    url(r'^open/$', login_required(
        views.AllOpenTasksView.as_view()), name='all_open'),
    url(r'^closed/$', login_required(
        views.AllClosedTasksView.as_view()), name='all_closed'),
    url(r'^open/my/$', login_required(
        views.MyOpenTasksView.as_view()), name='my_open'),
    url(r'^closed/my/$', login_required(
        views.MyClosedTasksView.as_view()), name='my_closed'),
    url(r'^review/$', login_required(
        views.MyReviewTasksView.as_view()), name='my_review'),
    url(r'^reviewed/my/$', login_required(
        views.MyReviewedTasksView.as_view()), name='my_reviewed'),
)
