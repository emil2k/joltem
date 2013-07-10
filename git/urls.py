from django.conf.urls import patterns, url
from git import views

urlpatterns = patterns(
    '',
    url(r'^$', views.repositories, name='repositories'),
    url(r'^hidden/$', views.repositories_hidden, name='repositories_hidden'),
    url(r'^new/$', views.new_repository, name='new_repository'),
    url(r'^(?P<repository_name>([-\w])+)/$', views.repository, name='repository'),
)