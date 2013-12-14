# coding: utf-8
""" Project's views. """
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.functional import cached_property
from django.views.generic import TemplateView, UpdateView
from django.views.generic.edit import BaseFormView

from .forms import ProjectSettingsForm, ProjectSubscribeForm
from .models import Project, Impact, Ratio
from joltem.views.generic import RequestBaseView, ValidUserMixin
from haystack.query import SearchQuerySet


class ProjectMixin(ValidUserMixin):

    """Gets project by name from url."""

    @cached_property
    def project(self):
        """ Return self.project. """
        return get_object_or_404(Project, name=self.kwargs['project_name'])


class ProjectBaseView(RequestBaseView):

    """ Parent class for project-context views. """

    project_tab = None

    def initiate_variables(self, request, *args, **kwargs):
        """ Init current project. """

        super(ProjectBaseView, self).initiate_variables(request, args, kwargs)
        try:
            name = self.kwargs.get("project_name")
            self.project = Project.objects.get(name=name)
        except Project.DoesNotExist:
            raise Http404('Project %s doesn\'t exists.' % name)
        self.is_admin = self.project.is_admin(request.user.id)

    def get_context_data(self, **kwargs):
        """ Get context for templates.

        :return dict:

        """
        kwargs["project"] = self.project
        kwargs["is_admin"] = self.is_admin
        kwargs["project_tab"] = self.project_tab
        return super(ProjectBaseView, self).get_context_data(**kwargs)


class ProjectView(TemplateView, ProjectBaseView, BaseFormView):

    """ View to display a project's information. """

    template_name = "project/project.html"
    form_class = ProjectSubscribeForm

    def load_project_impact(self):
        """ Load the user's project impact.

        :return Impact: defaults to None if DoesNotExist

        """
        try:
            return Impact.objects.get(
                project_id=self.project.id, user_id=self.user.id)
        except Impact.DoesNotExist:
            return None

    def load_project_ratio(self):
        """ Load the user's project ratio.

        :return Ratio: defaults to None if DoesNotExist

        """
        try:
            return Ratio.objects.get(
                project_id=self.project.id, user_id=self.user.id)
        except Ratio.DoesNotExist:
            return None

    def get_context_data(self, **kwargs):
        """ Get context for templates.


        Loads and caches a project specific overview, also loads the user's
        project specific impact and ratio to pass to the context.


        :return dict: A context

        """
        # User specific
        kwargs['project_impact'] = self.load_project_impact()
        kwargs['project_ratio'] = self.load_project_ratio()
        # Project specific
        key = 'project:overview:%s' % self.project.id
        overview = cache.get(key)
        if not overview:
            overview = self.project.get_overview()
            cache.set(key, overview)
        kwargs.update(overview)
        kwargs['subscribe'] = int(self.project.subscriber_set.filter(
            pk=self.request.user.pk).exists())
        return super(ProjectView, self).get_context_data(**kwargs)

    def form_valid(self, form):
        """ Subscribe current user to project.

        :return HttpResponseRedirect:

        """
        if form.cleaned_data.get('subscribe'):
            self.project.subscriber_set.add(self.request.user)
        else:
            self.project.subscriber_set.remove(self.request.user)

        return redirect(reverse(
            'project:project', kwargs={'project_name': self.project.name}))

    def form_invalid(self, form):
        """ Redirect user to project page.

        :return HttpResponseRedirect:

        """
        return redirect(reverse(
            'project:project', kwargs={'project_name': self.project.name}))


class ProjectSettingsView(UpdateView, ProjectBaseView):

    """ View to display and modify a project's settings. """

    object = None
    form_class = ProjectSettingsForm
    template_name = "project/settings.html"

    def get_object(self):
        """ Check if user is an admin.

        Only admins are allowed to modify project settings.

        :return Project:

        """
        if self.is_admin:
            return self.project
        raise Http404

    def get_success_url(self):
        """ Get url to redirect to after successful form submission.

        :return str: url of project settings.

        """
        return reverse('project:settings', kwargs={
            'project_name': self.project.name
        })


class ProjectSearchView(ProjectBaseView, TemplateView):

    """ Search by project. """

    template_name = 'project/search.html'

    def get_context_data(self, **kwargs):
        """ Search by project.

        :return dict:

        """
        query = self.request.GET.get('q', '')
        results = []
        if query:
            results = SearchQuerySet().filter(
                content=query, project=self.project.title).load_all()
        return super(ProjectSearchView, self).get_context_data(
            results=results, query=query, **kwargs)
