""" Notifications fabric. """

from django.conf import settings
from django.db import models


def get_notify(notification, notifyng=None):
    """ Get notify interface class for notification.

    :returns: A Notify instance

    """
    model = type(notifyng)
    if notifyng is None:
        model = notification.notifying_type.model_class()

    return _NotifyInterface.get_notify(notification, model)


class _MetaNotifyInterface(type):

    nclasses = dict()
    _inited = False

    def __new__(mcs, name, bases, params): # noqa
        model = params['model']
        if isinstance(model, str):
            app_label, model_name = model.split(".")
            params['model'] = models.get_model(app_label, model_name)

        ntype = params['ntype']
        if ntype:
            settings.NOTIFICATION_TYPES(ntype)

        cls = super(_MetaNotifyInterface, mcs).__new__(mcs, name, bases, params)
        mcs.nclasses[(cls.ntype, cls.model)] = cls
        return cls

    def get_notify(cls, notification, model): # noqa
        """ Init Notify class by type and model.

        :returns: A inited notify

        """
        if not cls._inited:
            for app in settings.INSTALLED_APPS:
                mname = '%s.notifications' % app
                try:
                    __import__(mname)
                except ImportError:
                    pass
            cls._inited = True
        try:
            return cls.nclasses[notification.type, model](notification)
        except KeyError:
            raise Exception("Unknown notification: %s (%s)" % (
                notification.type, model
            ))


class _NotifyInterface(object):

    __metaclass__ = _MetaNotifyInterface

    ntype = None
    model = None

    def __init__(self, notification):
        self.notification = notification

    def get_text(self, notifyng=None, user=None):
        """ Get notification text. """
        raise NotImplementedError
