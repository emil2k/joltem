from django.conf.urls import patterns, include, url
from django.contrib.auth.decorators import login_required
from solution import views

urlpatterns = patterns(
    '',
    url(r'^(?P<task_id>(\d)+)/new/$', login_required(views.new_solution), name='new_solution'),
    url(r'^(?P<solution_id>(\d)+)/$', views.solution, name='solution'),
    url(r'^(?P<solution_id>(\d)+)/commits/(?:(?P<repository_name>[-\w]+)/)?$', views.commits, name='commits'),
)