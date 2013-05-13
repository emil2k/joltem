from django.conf.urls import patterns, include, url

from git import views

urlpatterns = patterns(
    '',
    url(r'^(?P<repository_path>([-\w.])+)/$', views.repository, name='repository'),
)