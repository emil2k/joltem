from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required
from git import views

urlpatterns = patterns(
    '',
    url(r'^$', login_required(views.repositories), name='repositories'),
    url(r'^hidden/$', login_required(views.repositories_hidden),
        name='repositories_hidden'),
    url(r'^new/$', login_required(views.new_repository),
        name='new_repository'),
    url(r'^(?P<repository_id>(\d)+)/$',
        login_required(views.repository), name='repository'),
)
