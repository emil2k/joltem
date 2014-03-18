""" Joltem model utils. """
from django.db import models
from django.utils import timezone
from taggit.models import TagBase, GenericTaggedItemBase


class Tag(TagBase):

    """ A custom tag for Joltem.

    Forces tags to lowercase.

    """

    class Meta:
        app_label = "joltem"

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        super(Tag, self).save(*args, **kwargs)


class TaggedItem(GenericTaggedItemBase):

    """ A custom through model for django-taggit

    Utilizes custom Tag object.

    """

    class Meta:
        app_label = "joltem"

    tag = models.ForeignKey(Tag, related_name="tagged_items")
    time_tagged = models.DateTimeField(default=timezone.now)


class Choices(object):

    """ Useful class for Field.choices.

    ::

        class SomeModel:

            STATUS = Choices(
                (1, "new"),
                (2, "progress"),
                (3, "done"),
            )

            field = CharField(choices=STATUS)

        SomeModel.STATUS.new -> 1

        Choices("one", "second") -> Choices(("new"), ("second"))

    """

    def __init__(self, *choices):

        self.__choices__ = []
        self.__lookup__ = {}

        for choice in choices:
            if isinstance(choice, (list, tuple)):
                if len(choice) == 2:
                    choice = (choice[0], choice[1], choice[1])

                elif len(choice) != 3:
                    raise ValueError(
                        "Choices can't handle a list/tuple of length {0}, only\
                        2 or 3".format(choice))
            else:
                choice = (choice, choice, choice)

            self.__choices__.append((choice[0], choice[2]))
            self.__lookup__[choice[1].replace(' ', '_')] = choice[0]

    def __getattr__(self, attname):
        try:
            return self.__lookup__[attname]
        except KeyError:
            raise AttributeError(attname)

    def __iter__(self):
        return iter(self.__choices__)

    def __getitem__(self, index):
        return self.__choices__[index]

    def __delitem__(self, index):
        del self.__choices__[index]

    def __setitem__(self, index, value):
        self.__choices__[index] = value

    def __repr__(self):
        return "{0}({1})".format(
            self.__class__.__name__,
            self.__choices__
        )

    def __len__(self):
        return len(self.__choices__)
