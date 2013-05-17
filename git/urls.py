from django.conf.urls import patterns, url

from git import views

urlpatterns = patterns(
    '',
    url(r'^keys/$', views.keys, name='keys'),
    url(r'^(?P<repository_name>([-\w.])+)/$', views.repository, name='repository'), # TODO this should have a project name parameter
)