from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required
from solution import views

urlpatterns = patterns(
    '',
    url(r'^(?:(?P<solution_id>(\d)+)/)?new/$', login_required(views.SolutionCreateView.as_view()), name='new'),
    url(r'^(?P<solution_id>(\d)+)/$', login_required(views.SolutionView.as_view()), name='solution'),
    url(r'^(?P<solution_id>(\d)+)/edit/$', login_required(views.SolutionEditView.as_view()), name='solution_edit'),
    url(r'^(?P<solution_id>(\d)+)/review/$', views.review, name='review'),
    url(r'^(?P<solution_id>(\d)+)/commits/(?:(?P<repository_name>[-\w]+)/)?$', views.commits, name='commits'),
    url(r'^reviewed/$', views.my_reviewed(), name='my_reviewed'),
    url(r'^incomplete/my/$', views.my_incomplete(), name='my_incomplete'),
    url(r'^complete/my/$', views.my_complete(), name='my_complete'),
    url(r'^incomplete/$', views.all_incomplete(), name='all_incomplete'),
    url(r'^complete/$', views.all_complete(), name='all_complete'),
    )
