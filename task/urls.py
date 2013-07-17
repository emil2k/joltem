from django.conf.urls import patterns, include, url
from django.contrib.auth.decorators import login_required
from task import views

urlpatterns = patterns(
    '',
    url(r'^(?:(?P<parent_solution_id>(\d)+)/)?new/$', login_required(views.new), name='new'),
    url(r'^(?P<task_id>(\d)+)/$', login_required(views.task), name='task'),
    url(r'^(?P<task_id>(\d)+)/edit/$', login_required(views.edit), name='edit'),
    # Lists of tasks
    url(r'^(?:(?P<parent_task_id>(\d)+)/)?list/$', views.open(), name='open'),
    url(r'^closed/$', views.closed(), name='closed'),
)