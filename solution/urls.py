from django.conf.urls import patterns, url
from solution import views

urlpatterns = patterns(
    '',
    url(r'^(?:(?P<solution_id>(\d)+)/)?new/$', views.new, name='new'),
    url(r'^(?P<solution_id>(\d)+)/$', views.solution, name='solution'),
    url(r'^(?P<solution_id>(\d)+)/edit/$', views.solution_edit, name='solution_edit'),
    url(r'^(?P<solution_id>(\d)+)/review/$', views.review, name='review'),
    url(r'^(?P<solution_id>(\d)+)/commits/(?:(?P<repository_name>[-\w]+)/)?$', views.commits, name='commits'),
    url(r'^$', views.all(), name='all'),
    url(r'^accepted/$', views.accepted(), name='accepted'),
    url(r'^completed/$', views.completed(), name='completed'),
    )
