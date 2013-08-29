from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required
from task import views
from solution import views as solution_views

urlpatterns = patterns(
    '',
    url(r'^(?:(?P<parent_solution_id>(\d)+)/)?new/$', views.new, name='new'),
    url(r'^(?P<task_id>(\d)+)/$', login_required(views.TaskView.as_view()), name='task'),
    url(r'^(?P<task_id>(\d)+)/edit/$', views.edit, name='edit'),
    url(r'^(?P<task_id>(\d)+)/solve/$', login_required(solution_views.SolutionCreateView.as_view()), name='solve'),
    # Lists of tasks
    url(r'^(?:(?P<parent_task_id>(\d)+)/)?list/$', views.TaskListView.as_view(), name='subtasks'),
    url(r'^open/$', views.all_open(), name='all_open'),
    url(r'^closed/$', views.all_closed(), name='all_closed'),
    url(r'^open/my/$', views.my_open(), name='my_open'),
    url(r'^closed/my/$', views.my_closed(), name='my_closed'),
)