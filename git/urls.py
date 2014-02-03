""" Git urls. """

from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required

from . import views


urlpatterns = patterns(
    '',
    url(r'^$', views.ActiveRepositoriesView.as_view(), name='repositories'),
    url(r'^hidden/$', views.HiddenRepositoriesView.as_view(),
        name='repositories_hidden'),
    url(r'^new/$', login_required(views.RepositoryCreateView.as_view()),
        name='new_repository'),
    url(r'^(?P<repository_id>(\d)+)/$',
        views.RepositoryView.as_view(), name='repository'),
)
