from django.conf.urls import patterns, include, url
from project import views

urlpatterns = patterns(
    '',
    url(r'^$', views.project, name='project'),
    url(r'^git/', include('git.urls', namespace='git')),
    url(r'^tasks/$', views.tasks, name='tasks'),
    url(r'^repositories/$', views.repositories, name='repositories'),
    url(r'^solutions/$', views.solutions, name='solutions'),
    url(r'^solutions/mine/$', views.solutions_my, name='solutions_my'),
    url(r'^solutions/need-review/$', views.solutions_review, name='solutions_review'),
    url(r'^task/', include('task.urls', namespace='task')),
    url(r'^solution/', include('solution.urls', namespace='solution')),
)