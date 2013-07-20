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
    url(r'^account/$', views.account, name='account'),
    url(r'^account/keys/$', views.keys, name='account_keys'),
    url(r'^invite/$', views.invite, name='invite'),
    url(r'^(?P<project_name>([-\w])+)/', include('project.urls', namespace='project')),
)