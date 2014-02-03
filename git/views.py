""" Git views. """
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView
from git.forms import RepositoryActionForm

from git.models import Repository
from project.models import Project
from project.views import ProjectBaseView


class RepositoryBaseView(ProjectBaseView):

    """ Base view for repository related views. """


    def __init__(self, *args, **kwargs):
        self.repository = None
        super(RepositoryBaseView, self).__init__(*args, **kwargs)

    def initiate_variables(self, request, *args, **kwargs):
        """ Initiate variables for view.

        Initiates the repository instance ( or throws 404 ).

        Returns nothing.

        """
        super(RepositoryBaseView, self).initiate_variables(request, args, kwargs)
        try:
            self.repository = Repository.objects\
                .get(id=self.kwargs.get("repository_id"))
        except Repository.DoesNotExist:
            raise Http404("Repository not found.")

    def get_context_data(self, **kwargs):
        """ Return context for template. """
        kwargs["repository"] = self.repository
        return super(RepositoryBaseView, self).get_context_data(**kwargs)


class RepositoryView(TemplateView, RepositoryBaseView):

    """ View for displaying repository's information. """

    template_name = "git/repository.html"


class RepositoryBaseListView(ListView, ProjectBaseView):

    """ View mixin for repository's list. """

    context_object_name = 'repositories'
    paginate_by = 10
    project_tab = 'repositories'
    repositories_tab = None
    template_name = 'git/repositories_list.html'
    hidden_state = None
    toggle_redirect = None

    def initiate_variables(self, request, *args, **kwargs):
        """ Initiate is_manager variable.

        :param request:
        :param args:
        :param kwargs:
        :return:

        """
        super(RepositoryBaseListView, self).\
            initiate_variables(request, *args, **kwargs)
        self.is_manager = self.project.is_manager(request.user.id)

    def get_context_data(self, **kwargs):
        """ Get context data for templates.

        :return dict:

        """
        ProjectBaseView.get_context_data(self, **kwargs)
        kwargs['host'] = settings.GATEWAY_HOST
        kwargs['is_manager'] = self.is_manager
        kwargs['repositories_tab'] = self.repositories_tab
        kwargs['action'] = "activate" if self.hidden_state else "hide"
        return super(RepositoryBaseListView, self).get_context_data(**kwargs)

    def get_queryset(self, **filters):
        """ Return repositories query set, matching hidden state.

        :return QuerySet:

        """
        return self.project.repository_set.filter(is_hidden=self.hidden_state)\
            .order_by('name')

    def post(self, request, *args, **kwargs):
        """ Process toggling of repository hidden state. """
        form = RepositoryActionForm(request.POST)
        if form.is_valid() and (self.is_admin or self.is_manager):
            repository_id = form.cleaned_data['repository_id']
            repository = Repository.objects.get(
                id=repository_id)
            self.toggle_repository(repository)
        if self.toggle_redirect is None:
            raise ImproperlyConfigured("Toggle redirect undefined in view.")
        return redirect(self.toggle_redirect,
                        **dict(project_id=self.project.id))

    def toggle_repository(self, repository):
        """ Toggle repository state, depends on view.

        :param repository:

        """
        if self.hidden_state is None:
            raise ImproperlyConfigured("Toggle state undefined in view.")
        else:
            repository.is_hidden = not self.hidden_state
            repository.save()


class ActiveRepositoriesView(RepositoryBaseListView):

    repositories_tab = "active"
    hidden_state = False
    toggle_redirect = "project:git:repositories"


class HiddenRepositoriesView(RepositoryBaseListView):

    repositories_tab = "hidden"
    hidden_state = True
    toggle_redirect = "project:git:repositories_hidden"


def new_repository(request, project_id):
    """ Support creation of new repository.

    :return str: A rendered page

    """
    project = get_object_or_404(Project, id=project_id)
    is_admin = project.is_admin(request.user.id)
    is_manager = project.is_manager(request.user.id)
    if not (is_admin or is_manager):
        return redirect('project:git:repositories', project_id=project_id)
    if request.POST:
        action = request.POST.get('action')
        # Create a repository
        if action == 'create_repo':
            name = request.POST.get('name')
            description = request.POST.get('description')
            if name is not None:
                created_repo = Repository(
                    project=project,
                    name=name,
                    description=description
                )
                created_repo.save()
                return redirect(
                    'project:git:repositories', project_id=project_id)
    context = {
        'project_tab': "repositories",
        'project': project,
        'repositories': project.repository_set.filter(is_hidden=False),
        'is_admin': is_admin,
        'is_manager': is_manager
    }
    return render(request, 'git/new_repository.html', context)
