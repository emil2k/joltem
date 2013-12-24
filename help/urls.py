""" URL routing for help section. """

from django.conf.urls import patterns, url

from help import views


urlpatterns = patterns(
    '',
    url(r'^$', views.HelpIndexView.as_view(), name='index')
)
