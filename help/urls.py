""" URL routing for help section. """

from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required
from help import views

urlpatterns = patterns(
    '',
    url(r'^$', login_required(views.HelpIndexView.as_view()), name='index')
)
