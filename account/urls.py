# coding: utf-8
from django.conf.urls import patterns, url

from account.views import SignUpView


urlpatterns = patterns(
    '',

    url(r'^sign-up/$', SignUpView.as_view(),
        {'extra_context': {'nav_tab': 'up'}},
        'sign_up'),

    url(r'^sign-in/$', 'django.contrib.auth.views.login',
        {'extra_context': {'nav_tab': 'in'}},
        'sign_in'),

    url(r'^sign-out/$', 'django.contrib.auth.views.logout', name='sign_out'),

    url(r'^password_change/$', 'django.contrib.auth.views.password_change',
        {'extra_context': {'account_tab': 'change_password'}},
        'password_change'),

    url(r'^password_change/done/$',
        'django.contrib.auth.views.password_change_done',
        {'extra_context': {'account_tab': 'change_password'}},
        'password_change_done',),

    url(r'^password_reset/$', 'django.contrib.auth.views.password_reset',
        name='password_reset'),

    url(r'^password_reset/done/$',
        'django.contrib.auth.views.password_reset_done',
        name='password_reset_done'),

    url(r'^reset/(?P<uidb64>[0-9A-z_\-]+)/(?P<token>[0-9A-z]{1,13}-[0-9A-z]{1,20})/$',
        'django.contrib.auth.views.password_reset_confirm',
        name='password_reset_confirm'),

    url(r'^reset/done/$', 'django.contrib.auth.views.password_reset_complete',
        name='password_reset_complete'),
)
