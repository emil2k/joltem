from django.conf.urls import patterns, url

from git import views

urlpatterns = patterns(
    '',
    url(r'^keys/$', views.keys, name='keys'),
    url(r'^(?P<repository_path>([-\w.])+)/$', views.repository, name='repository'),
)