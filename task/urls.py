from django.conf.urls import patterns, include, url
from django.contrib.auth.decorators import login_required
from task import views

urlpatterns = patterns(
    '',
    url(r'^(?:(?P<parent_solution_id>(\d)+)/)?new/$', login_required(views.new), name='new'),
    url(r'^(?P<task_id>(\d)+)/$', views.task, name='task'),
    url(r'^list/$', views.list, name='list'),
    url(r'^browse/$', views.browse, name='browse'),
)