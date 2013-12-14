""" Search's indexes. """
from haystack import indexes

from .models import Task


class TaskIndex(indexes.SearchIndex, indexes.Indexable):

    """ Index by tasks. """

    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    time_updated = indexes.DateTimeField(model_attr='time_updated')
    project = indexes.CharField(model_attr='project__title')

    def get_model(self):
        """ Point to model.

        :return Task:

        """
        return Task

    def get_updated_field(self):
        """ Point to updated field.

        :return str:

        """
        return 'time_updated'
