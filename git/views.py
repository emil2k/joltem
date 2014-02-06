""" Git views. """
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, CreateView
from git.forms import RepositoryActionForm, RepositoryCreateForm

from git.models import Repository
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


class RepositoryCreateView(CreateView, ProjectBaseView):

    """ View to create new repository. """

    repositories_tab = "create"
    template_name = 'git/new_repository.html'
    form_class = RepositoryCreateForm

    def initiate_variables(self, request, *args, **kwargs):
        """ Enforce access, only admins and managers.

        Raises 404 if access not permitted.

        :param request:
        :param args:
        :param kwargs:
        :return:

        """
        super(RepositoryCreateView, self).\
            initiate_variables(request, *args, **kwargs)
        if not (self.is_admin or self.project.is_manager(request.user.id)):
            raise Http404

    def get_context_data(self, **kwargs):
        """ Add repository tab.

        :param kwargs:
        :return:

        """
        kwargs['repositories_tab'] = self.repositories_tab
        return super(RepositoryCreateView, self).get_context_data(**kwargs)

    def form_valid(self, form):
        """ Create new repository, and redirect.

        :param form:
        :return:

        """
        repository = form.save(commit=False)
        repository.project = self.project
        repository.save()
        return redirect('project:git:repository',
                        **dict(project_id=self.project.id,
                               repository_id=repository.id))