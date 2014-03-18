""" Joltem URLS. """
from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth.decorators import login_required

from . import views
from project.views import ProjectCreateView


urlpatterns = [
    url(r'^$', views.HomeView.as_view(), name='home'),
    url(r'^tags/$', views.TagsView.as_view(), name='tags'),
    url(r'^intro/', login_required(
        views.IntroductionView.as_view()), name='intro'),
    url(r'^notifications/(?P<notification_id>([0-9])+)/', login_required(
        views.NotificationRedirectView.as_view()),
        name='notification_redirect'),
    url(r'^notifications/', login_required(
        views.NotificationsView.as_view()), name='notifications'),
    url(r'^comment/(?P<comment_id>([0-9])+)/', login_required(
        views.CommentView.as_view()), name='comment'),
    url(r'^user/(?P<username>([-\w\.])+)/$',
        views.UserView.as_view(), name='user'),
    url(r'^account/', include('account.urls')),
    url(r'^help/$', include('help.urls', namespace='help')),
    url(r'^new/$', login_required(ProjectCreateView.as_view()), name='new'),
    url(r'^(?P<project_id>\d+)/', include(
        'project.urls', namespace='project')),
]

# Django-markdown support
urlpatterns += [url(r'^markdown/', include('django_markdown.urls'))]

# Django admin
admin.autodiscover()
urlpatterns += [url(r'^admin/', include(admin.site.urls))]

# Staticfiles
if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT)
