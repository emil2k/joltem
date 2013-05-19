from django.conf.urls import patterns, url
from git import views

urlpatterns = patterns(
    '',
    url(r'^(?P<repository_name>([-\w])+)/$', views.repository, name='repository'),
)