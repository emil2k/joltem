# coding: utf-8

""" Project's views. """
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.functional import cached_property
from django.views.generic import TemplateView, CreateView, DeleteView, ListView
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
        """ Initiate project related variables.

        After initiating variables determines if user has rights to access
        project.

        """
        super(ProjectBaseView, self).initiate_variables(request, args, kwargs)
        try:
            self.project = Project.objects.get(
                id=self.kwargs.get("project_id"))
        except Project.DoesNotExist:
            raise Http404('Project doesn\'t exist.')
        else:
            if not self.project.has_access(request.user.id):
                raise Http404

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
        kwargs[u'project'] = self.project
        kwargs[u'is_admin'] = self.is_admin
        kwargs[u'project_tab'] = self.project_tab
        return super(ProjectBaseView, self).get_context_data(**kwargs)


class ProjectBaseListMeta(type):

    """ Build views hierarchy. """

    tabs = []

    def __new__(mcs, name, bases, params):
        cls = super(ProjectBaseListMeta, mcs).__new__(mcs, name, bases, params)
        if cls.tab:
            mcs.tabs.append(cls)
        return cls

class ProjectBaseListView(ProjectBaseView, ListView):

    """ Parent class for project-context lists.

    For example lists of tasks & solutions.

    :param is_personal: whether list depends on user.
    :param order_by: list of fields to order list by

    """

    __metaclass__ = ProjectBaseListMeta

    filters = {}
    paginate_by = 10
    tab = None
    is_personal = False
    order_by = ()

    def get_tab_counts(self, is_personal=False):
        """ Get the counts for each list.

        :param is_personal: filter views by is_personal attribute
        :return dict: name => count

        """
        return { cls.tab: cls._get_queryset(self, **cls.filters).count()
                 for cls in ProjectBaseListView.tabs
                 if cls.is_personal == is_personal }

    def get_cached_tab_counts(self, is_personal=False):
        """ Get the cached counts, if cached, otherwise query and set.

        :param is_personal: filter views by is_personal attribute
        :return dict: name => count

        """
        key = self.personal_tab_counts_cache_key if is_personal \
            else self.tab_counts_cache_key
        value = cache.get(key)
        if not value:
            value = self.get_tab_counts(is_personal)
            cache.set(key, value)
        return value

    @cached_property
    def tab_counts_cache_key(self):
        return "%s:tabs" % self.project.pk

    @cached_property
    def personal_tab_counts_cache_key(self):
        return "%s:%s:tabs" % (self.project.pk, self.user.pk)

    def get_context_data(self, **kwargs):
        """ Get context data for templates.

        :return dict:

        """
        ProjectBaseView.get_context_data(self, **kwargs)
        kwargs[u'tab'] = self.tab
        kwargs[u'tabs'] = self.get_cached_tab_counts()
        kwargs[u'personal_tabs'] = \
            self.get_cached_tab_counts(is_personal=True)
        return super(ProjectBaseListView, self).get_context_data(**kwargs)

    @classmethod
    def _get_raw_queryset(cls, project):
        """ Provide unfiltered queryset, must configure for optimizations.

        :param project: the project in context.
        :return QuerySet:

        """
        raise ImproperlyConfigured("Unfiltered queryset not defined.")

    @classmethod
    def _get_queryset(cls, context, **filters):
        """ Prepare queryset for a given view in the project.

        General, used to calculate counts and produce lists.

        :param context: an instance of a ProjectBaseView, needs
            `project` and `user` attributes.
        :param view:
        :return:

        """
        filters = filters or cls.filters.copy()
        qs = cls._get_raw_queryset(context.project)
        for k in filters:
            if callable(filters[k]):
                filters[k] = filters[k](context)
            if k.endswith('__ne'):
                qs = qs.filter(~Q(**{k[:-4]: filters[k]}))
            else:
                qs = qs.filter(**{k: filters[k]})
        return qs.order_by(*cls.order_by)

    def get_queryset(self, **filters):
        """ Return queryset for the extending class.

        Used by ListView to list items.

        :return QuerySet:

        """
        return self.__class__._get_queryset(self, **filters)


class ProjectCreateView(RequestBaseView, CreateView):

    """ View to create new project. """

    template_name = "project/new_project.html"
    form_class = ProjectCreateForm

    def form_valid(self, form):
        """ Create project and redirect to project page.

        :param form: submitted form object.
        :return:

        """
        project = form.save(commit=False)
        project.is_private = form.cleaned_data.get('is_private')
        project.exchange_periodicity = \
            form.cleaned_data.get('exchange_periodicity')
        project.exchange_magnitude = \
            form.cleaned_data.get('exchange_magnitude')
        # Initialize ownership
        project.total_shares = 1000000
        ownership = form.cleaned_data.get('ownership')
        owner_shares = project.total_shares / 100 * ownership
        project.impact_shares = project.total_shares - owner_shares
        project.save()
        owner_equity = Equity(
            shares=owner_shares,
            user=self.user,
            project=project
        )
        owner_equity.save()
        # Initiate groups
        project.admin_set.add(self.user)
        project.subscriber_set.add(self.user)
        project.founder_set.add(self.user)
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
        kwargs['founders'] = self.project.founder_set.all()\
            .order_by('first_name')
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
        overview = self.project.get_cached_overview(limit=30)
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

        elif 'submit_add_invitee' in request.POST \
                or 'submit_remove_invitee' in request.POST:
            form = ProjectGroupForm(request.POST)
            if not form.is_valid():
                context['invitee_form'] = form
                return self.render_to_response(context)
            user = User.objects.get(username=form.cleaned_data['username'])
            if 'submit_remove_invitee' in request.POST:
                self.project.invitee_set.remove(user)
            else:
                self.project.invitee_set.add(user)
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
        kwargs['invitee_form'] = ProjectGroupForm()
        kwargs['admins'] = order(self.project.admin_set.all())
        kwargs['managers'] = order(self.project.manager_set.all())
        kwargs['developers'] = order(self.project.developer_set.all())
        kwargs['invitees'] = order(self.project.invitee_set.all())
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
