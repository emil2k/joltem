""" Project's urls. """

from django.conf.urls import patterns, include, url
from django.contrib.auth.decorators import login_required
from project import views

urlpatterns = patterns(
    '',
    url(r'^$', views.ProjectView.as_view(), name='project'),
    url(r'^settings/$', login_required(views.ProjectSettingsView.as_view()),
        name='settings'),
    url(r'^keys/$', login_required(views.ProjectKeysView.as_view()),
        name='keys'),
    url(r'^keys/(?P<pk>[0-9]+)/delete/$',
        login_required(views.ProjectKeysDeleteView.as_view()),
        name='keys_delete'),
    url(r'^git/', include('git.urls', namespace='git')),
    url(r'^task/', include('task.urls', namespace='task')),
    url(r'^solution/', include('solution.urls', namespace='solution')),
    url(r'^search/', views.ProjectSearchView.as_view(),
        name='search'),
)
