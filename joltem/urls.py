from django.conf.urls import patterns, include, url
from joltem import views
from git import views as git_views

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^$', views.home, name='home'),
    url(r'^keys/$', git_views.keys, name='keys'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^(?P<project_name>([-\w])+)/', include('project.urls', namespace='project')),
)