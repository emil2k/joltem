from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

from joltem import views

urlpatterns = patterns(
    '',
    # Administration
    url(r'^admin/', include(admin.site.urls)),
    # Joltem
    url(r'^$', views.home, name='home'),
    url(r'^task/(?P<task_id>(\d)+)/(?P<task_branch_id>(\d)+)/$', views.task_branch, name='task_branch'),
    url(r'^task/(?P<task_id>(\d)+)/$', views.task, name='task'),
    url(r'^repo/(?P<repository_path>([-\w.])+)/$', views.repository, name='repository'),
    url(r'^(?P<project_name>([-\w])+)/$', views.project, name='project'),
)


