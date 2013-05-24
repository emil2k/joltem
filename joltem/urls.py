from django.conf.urls import patterns, include, url
from joltem import views

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^$', views.home, name='home'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^keys/$', 'git.views.keys', name='keys'),
    url(r'^in/', views.sign_in, name='sign_in'),
    url(r'^out/', views.sign_out, name='sign_out'),
    url(r'^solutions/$', views.solutions, name='solutions'),
    url(r'^(?P<project_name>([-\w])+)/', include('project.urls', namespace='project')),
)