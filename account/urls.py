# coding: utf-8
from django.conf.urls import patterns, url


urlpatterns = patterns(
    '',

    url(r'^password_change/$', 'django.contrib.auth.views.password_change',
        {'extra_context': {'account_tab': 'change_password'}},
        'password_change'),

    url(r'^password_change/done/$',
        'django.contrib.auth.views.password_change_done',
        {'extra_context': {'account_tab': 'change_password'}},
        'password_change_done',),
)
