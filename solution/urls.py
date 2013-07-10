from django.conf.urls import patterns, include, url
from django.contrib.auth.decorators import login_required
from solution import views

urlpatterns = patterns(
    '',
    url(r'^(?P<task_id>(\d)+)/new/$', login_required(views.new_solution), name='new_solution'),
    url(r'^(?P<solution_id>(\d)+)/$', views.solution, name='solution'),
    url(r'^(?P<solution_id>(\d)+)/edit/$', views.solution_edit, name='solution_edit'),
    url(r'^(?P<solution_id>(\d)+)/review/$', views.review, name='review'),
    url(r'^(?P<solution_id>(\d)+)/commits/(?:(?P<repository_name>[-\w]+)/)?$', views.commits, name='commits'),
    url(r'^list/$', views.solutions, name='solutions'),
    url(r'^my/$', views.solutions_my, name='solutions_my'),
    url(r'^review/$', views.solutions_review, name='solutions_review'),
    )
