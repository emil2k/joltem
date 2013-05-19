from django.conf.urls import patterns, include, url
from task import views

urlpatterns = patterns(
    '',
    url(r'^(?:(?P<parent_task_id>(\d)+)/)?new/$', views.new_task, name='new_task'),
    url(r'^(?P<task_id>(\d)+)/$', views.task, name='task'),
    url(r'^(?P<task_id>(\d)+)/(?P<task_branch_id>(\d)+)/$', views.task_branch, name='task_branch'),
)