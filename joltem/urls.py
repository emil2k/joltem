from django.conf.urls import patterns, include, url
from joltem import views
from git.urls import urlpatterns as git_urls

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    '',
    # Administration
    url(r'^admin/', include(admin.site.urls)),
    # Git
    url(r'^git/', include(git_urls)),
    # Joltem
    url(r'^$', views.home, name='home'),
    url(r'^task/(?P<task_id>(\d)+)/(?P<task_branch_id>(\d)+)/$', views.task_branch, name='task_branch'),
    url(r'^task/(?P<task_id>(\d)+)/$', views.task, name='task'),
    url(r'^(?P<project_name>([-\w])+)/$', views.project, name='project'),
)