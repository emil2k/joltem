# coding: utf-8
""" Project's views. """
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.functional import cached_property
from django.views.generic import TemplateView, CreateView, DeleteView
from django.views.generic.edit import BaseFormView
from haystack.query import SearchQuerySet

from .forms import (ProjectSettingsForm, ProjectSubscribeForm,
                    ProjectCreateForm, ProjectGroupForm)
from .models import Project, Impact, Ratio, Equity
from account.forms import SSHKeyForm
from joltem.models import User
from joltem.views.generic import RequestBaseView


class ProjectMixin():

    """Gets project by name from url."""

    @cached_property
    def project(self):
        """ Return self.project. """
        return get_object_or_404(Project, id=self.kwargs['project_id'])


class ProjectBaseView(RequestBaseView):

    """ Parent class for project-context views. """

    project_tab = None

    def initiate_variables(self, request, *args, **kwargs):
        """ Init current project. """

        super(ProjectBaseView, self).initiate_variables(request, args, kwargs)
        try:
            self.project = Project.objects.get(
                id=self.kwargs.get("project_id"))
        except Project.DoesNotExist:
            raise Http404('Project doesn\'t exist.')

    @cached_property
    def is_admin(self):
        """ Check self.user is admin.

        :returns: bool

        """
        return self.project.is_admin(self.user.pk)

    @cached_property
    def is_manager(self):
        """ Check self.user is manager.

        :returns: bool

        """
        return self.project.is_manager(self.user.pk)

    def get_context_data(self, **kwargs):
        """ Get context for templates.

        :return dict:

        """
        kwargs["project"] = self.project
        kwargs["is_admin"] = self.is_admin
        kwargs["project_tab"] = self.project_tab
        return super(ProjectBaseView, self).get_context_data(**kwargs)


class ProjectCreateView(RequestBaseView, CreateView):

    """ View to create new project. """

    template_name = "project/new_project.html"
    form_class = ProjectCreateForm

    def form_valid(self, form):
        """ Create project and redirect to project page.

        :param form: submitted form object.
        :return:

        """
        project = form.save()
        project.exchange_periodicity = \
            form.cleaned_data.get('exchange_periodicity')
        project.exchange_magnitude = \
            form.cleaned_data.get('exchange_magnitude')
        project.total_shares = 1000000
        ownership = form.cleaned_data.get('ownership')
        owner_shares = project.total_shares / 100 * ownership
        project.impact_shares = project.total_shares - owner_shares
        project.admin_set.add(self.user)
        project.save()

        owner_equity = Equity(
            shares=owner_shares,
            user=self.user,
            project=project
        )
        owner_equity.save()

        return redirect(reverse('project:project', args=[project.id]))


class ProjectView(TemplateView, ProjectBaseView, BaseFormView):

    """ View to display a project's dashboard. """

    template_name = "project/project.html"
    form_class = ProjectSubscribeForm
    project_tab = "overview"

    def get_context_data(self, **kwargs):
        """ Get context for templates.

        :return dict: A context

        """
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
            'project:project', kwargs={'project_id': self.project.id}))

    def form_invalid(self, form):
        """ Redirect user to project page.

        :return HttpResponseRedirect:

        """
        return redirect(reverse(
            'project:project', kwargs={'project_id': self.project.id}))


class ProjectDashboardView(TemplateView, ProjectBaseView, BaseFormView):

    """ View to display a project's dashboard. """

    template_name = "project/dashboard.html"
    form_class = ProjectSubscribeForm
    project_tab = "dashboard"

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
        overview = self.project.get_cached_overview()
        kwargs.update(overview)
        kwargs['subscribe'] = int(self.project.subscriber_set.filter(
            pk=self.request.user.pk).exists())
        return super(ProjectDashboardView, self).get_context_data(**kwargs)

    def form_valid(self, form):
        """ Subscribe current user to project.

        :return HttpResponseRedirect:

        """
        if form.cleaned_data.get('subscribe'):
            self.project.subscriber_set.add(self.request.user)
        else:
            self.project.subscriber_set.remove(self.request.user)

        return redirect(reverse(
            'project:dashboard', kwargs={'project_id': self.project.id}))

    def form_invalid(self, form):
        """ Redirect user to project page.

        :return HttpResponseRedirect:

        """
        return redirect(reverse(
            'project:dashboard', kwargs={'project_id': self.project.id}))


class ProjectSettingsView(TemplateView, ProjectBaseView):

    """ View to display and modify a project's settings. """

    template_name = "project/settings.html"
    project_tab = "settings"

    def initiate_variables(self, request, *args, **kwargs):
        """ Check for current user is admin. """
        super(ProjectSettingsView, self).initiate_variables(
            request, *args, **kwargs)
        if not self.is_admin:
            raise Http404

    def get(self, request, *args, **kwargs):
        """ Render project's settings page.

        :returns: A rendered page

        """
        context = self.get_context_data(**kwargs)
        context['form'] = ProjectSettingsForm(instance=self.project)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        """ Update the project.

        :returns: A Response

        """
        context = self.get_context_data(**kwargs)
        if 'submit_settings' in request.POST:
            form = ProjectSettingsForm(request.POST)
            if not form.is_valid():
                context['form'] = form
                return self.render_to_response(context)
            self.project.title = form.cleaned_data['title']
            self.project.description = form.cleaned_data['description']
            self.project.save()

        elif 'submit_add_admin' in request.POST \
                or 'submit_remove_admin' in request.POST:
            form = ProjectGroupForm(request.POST)
            if not form.is_valid():
                context['admin_form'] = form
                return self.render_to_response(context)
            user = User.objects.get(username=form.cleaned_data['username'])
            if 'submit_remove_admin' in request.POST:
                self.project.admin_set.remove(user)
            else:
                self.project.admin_set.add(user)
            self.project.save()

        elif 'submit_add_manager' in request.POST \
                or 'submit_remove_manager' in request.POST:
            form = ProjectGroupForm(request.POST)
            if not form.is_valid():
                context['manager_form'] = form
                return self.render_to_response(context)

            user = User.objects.get(username=form.cleaned_data['username'])
            if 'submit_remove_manager' in request.POST:
                self.project.manager_set.remove(user)
            else:
                self.project.manager_set.add(user)
            self.project.save()

        elif 'submit_add_developer' in request.POST \
                or 'submit_remove_developer' in request.POST:
            form = ProjectGroupForm(request.POST)
            if not form.is_valid():
                context['developer_form'] = form
                return self.render_to_response(context)
            user = User.objects.get(username=form.cleaned_data['username'])
            if 'submit_remove_developer' in request.POST:
                self.project.developer_set.remove(user)
            else:
                self.project.developer_set.add(user)
            self.project.save()

        return redirect(reverse('project:settings', args=[self.project.id]))

    def get_context_data(self, **kwargs):
        """ Added groups users.

        :param kwargs:
        :return: context

        """
        order = lambda qs: qs.order_by('first_name')
        kwargs['form'] = ProjectSettingsForm(instance=self.project)
        kwargs['admin_form'] = ProjectGroupForm()
        kwargs['manager_form'] = ProjectGroupForm()
        kwargs['developer_form'] = ProjectGroupForm()
        kwargs['admins'] = order(self.project.admin_set.all())
        kwargs['managers'] = order(self.project.manager_set.all())
        kwargs['developers'] = order(self.project.developer_set.all())
        return super(ProjectSettingsView, self).get_context_data(**kwargs)


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


class ProjectKeysView(CreateView, ProjectBaseView):

    """ Setup project deployment keys. """

    form_class = SSHKeyForm
    template_name = "project/ssh_keys.html"

    def form_valid(self, form):
        """ Save form.

        :return HttpResponseRedirect:

        """
        ssh_key_instance = form.save(commit=False)
        ssh_key_instance.project = self.project
        ssh_key_instance.save()

        return redirect('project:keys', project_id=self.project.id)

    def get_context_data(self, **kwargs):
        """ Make context.

        :return dict: a context

        """
        if not self.is_admin:
            raise Http404

        context = super(ProjectKeysView, self).get_context_data(**kwargs)

        context['ssh_key_list'] = self.project.authentication_set.all()

        return context


class ProjectKeysDeleteView(ProjectBaseView, DeleteView):

    """Deletes public SSH key by id from project."""

    template_name = 'project/ssh_keys_confirm_delete.html'

    def delete(self, *args, **kwargs):
        """ Check for current user is project's admin.

        :return:

        """
        if not self.is_admin:
            raise Http404
        return super(ProjectKeysDeleteView, self).delete(*args, **kwargs)

    def get_queryset(self):
        """ Get queryset.

        :return Queryset:

        """
        return self.project.authentication_set

    def get_success_url(self):
        """ Redirect to project keys.

        :returns: str

        """
        return reverse('project:keys', kwargs=dict(
            project_id=self.project.id))
