from django.conf.urls import patterns, include, url
from project import views

urlpatterns = patterns(
    '',
    url(r'^$', views.project, name='project'),
    url(r'^git/', include('git.urls', namespace='git')),
    url(r'^task/', include('task.urls', namespace='task')),
    url(r'^solution/', include('solution.urls', namespace='solution')),
)