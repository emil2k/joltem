from django.conf.urls import patterns, include, url
from django.contrib.auth.decorators import login_required
from task import views

urlpatterns = patterns(
    '',
    url(r'^(?:(?P<parent_task_id>(\d)+)/)?new/$', login_required(views.new_task), name='new_task'),
    url(r'^(?P<task_id>(\d)+)/$', views.task, name='task'),
)