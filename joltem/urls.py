""" Joltem URLS. """

from django.conf.urls import patterns, include, url
from django.contrib.auth.decorators import login_required

from joltem import views


from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^$', views.home, name='home'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^up/', views.sign_up, name='sign_up'),
    url(r'^in/', views.sign_in, name='sign_in'),
    url(r'^out/', views.sign_out, name='sign_out'),
    url(r'^intro/', login_required(
        views.IntroductionView.as_view()), name='intro'),
    url(r'^notifications/(?P<notification_id>([0-9])+)/', login_required(
        views.NotificationRedirectView.as_view()),
        name='notification_redirect'),
    url(r'^notifications/', login_required(
        views.NotificationsView.as_view()), name='notifications'),
    url(r'^comment/(?P<comment_id>([0-9])+)/', login_required(
        views.comment), name='comment'),
    url(r'^user/(?P<username>([-\w])+)/$', views.user, name='user'),
    url(r'^account/$', views.account, name='account'),
    url(r'^account/keys/$', views.keys, name='account_keys'),
    url(r'^invite/$', views.invites, name='invites'),
    url(r'^invite/(?P<invite_id>([-A-za-z0-9]+))/$',
        views.invite, name='invite'),
    url(r'^(?P<project_name>([-\w])+)/', include(
        'project.urls', namespace='project')),
)

from django.conf import settings
if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# lint_ignore=E1120
