""" Account views. """

from django.conf.urls import patterns, url

from account.views import (
    SignUpView, GeneralSettingsView, SSHKeyCreateView, SSHKeyDeleteView,
    authomatic_login
)


urlpatterns = patterns(
    '',

    url(r'^$', GeneralSettingsView.as_view(),
        {'extra_context': {'nav_tab': 'account', 'account_tab': 'account'}},
        'account'),

    url(r'^keys/$', SSHKeyCreateView.as_view(),
        {'extra_context': {'nav_tab': 'account', 'account_tab': 'keys'}},
        'account_keys'),

    url(r'^keys/(?P<pk>[0-9]+)/delete/$', SSHKeyDeleteView.as_view(),
        {'extra_context': {'nav_tab': 'account', 'account_tab': 'keys'}},
        'account_key_delete'),

    url(r'^sign-up/$', SignUpView.as_view(),
        {'extra_context': {'nav_tab': 'up'}},
        'sign_up'),

    url(r'^sign-in/(\w+)/?$', authomatic_login, name='oauth'),

    url(r'^sign-in/$', 'django.contrib.auth.views.login',
        {'extra_context': {'nav_tab': 'in'}}, 'sign_in'),

    url(r'^sign-out/$', 'django.contrib.auth.views.logout', name='sign_out'),

    url(r'^password-change/$', 'django.contrib.auth.views.password_change',
        {'extra_context': {'account_tab': 'change_password'}},
        'password_change'),

    url(r'^password-change/done/$',
        'django.contrib.auth.views.password_change_done',
        {'extra_context': {'account_tab': 'change_password'}},
        'password_change_done',),

    url(r'^password-reset/$', 'django.contrib.auth.views.password_reset',
        name='password_reset'),

    url(r'^password-reset/done/$',
        'django.contrib.auth.views.password_reset_done',
        name='password_reset_done'),

    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        'django.contrib.auth.views.password_reset_confirm',
        name='password_reset_confirm'),

    url(r'^reset/done/$', 'django.contrib.auth.views.password_reset_complete',
        name='password_reset_complete'),
)
