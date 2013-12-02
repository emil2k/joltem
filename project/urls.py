from django.conf.urls import patterns, include, url
from django.contrib.auth.decorators import login_required
from project import views

urlpatterns = patterns(
    '',
    url(r'^$', login_required(views.ProjectView.as_view()), name='project'),
    url(r'^settings/$', login_required(views.ProjectSettingsView.as_view()),
        name='settings'),
    url(r'^git/', include('git.urls', namespace='git')),
    url(r'^task/', include('task.urls', namespace='task')),
    url(r'^solution/', include('solution.urls', namespace='solution')),
)
