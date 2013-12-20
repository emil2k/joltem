""" Git urls. """

from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required

from . import views


urlpatterns = patterns(
    '',
    url(r'^$', views.repositories, name='repositories'),
    url(r'^hidden/$', views.repositories_hidden,
        name='repositories_hidden'),
    url(r'^new/$', login_required(views.new_repository),
        name='new_repository'),
    url(r'^(?P<repository_id>(\d)+)/$',
        views.repository, name='repository'),
)
