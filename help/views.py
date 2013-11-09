""" Help related views. """

from django.views.generic import TemplateView

from joltem.views.generic import TextContextMixin, NavTabContextMixin

class HelpIndexView(TextContextMixin, NavTabContextMixin, TemplateView):
    """ View to display index of help section. """
    template_name = "help/index.html"
    text_names = ["help/index.md"]
    text_context_object_prefix = "help_"
    nav_tab = "help"

